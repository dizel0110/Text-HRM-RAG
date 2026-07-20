"""
Fast/Slow Router for VORTEX-HRM.

Strategy:
  1. Fast path (baseline): retrieve top-3 chunks + LLM answer
     - If "Insufficient evidence." or low confidence → fallback to VORTEX
     - Otherwise → return fast answer
  2. Slow path (VORTEX): full spiral engine (only for uncertain questions)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.config import VORTEXConfig
from core.llm import backend_from_config
import numpy as np
from executor import KeywordSearchTool, SemanticSearchTool, ChunkReadTool, Chunk
from orchestrator import VortexEngine
from planner import GravitationalCore
from executor import CentrifugalIngestor


def load_checkpoint(out_dir: str) -> set:
    path = os.path.join(out_dir, "predictions.jsonl")
    if not os.path.exists(path):
        return set()
    seen = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            seen.add(r["index"])
    return seen


def load_questions(path: str) -> tuple[list[str], list[str]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    questions, ground_truths = [], []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                questions.append(item.get("question", ""))
                ground_truths.append(item.get("ground_truth", ""))
    return questions, ground_truths


def load_corpus(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [Chunk(chunk_id=item["id"], text=item["text"]) for item in data]


def build_fast_prompt(context: str, question: str) -> str:
    return (
        "Answer the question using only the provided passages. "
        'If the answer is not in the passages, say "Insufficient evidence." '
        "Then rate your confidence (0.0-1.0) on a new line: CONFIDENCE: <score>\n\n"
        "Passages:\n{context}\n\n"
        "Question: {question}\nAnswer:"
    ).format(context=context, question=question)


def parse_fast_response(text: str) -> tuple[str, float]:
    answer = text.strip()
    confidence = 1.0
    lines = answer.split("\n")
    cleaned = []
    for line in lines:
        if line.strip().startswith("CONFIDENCE:"):
            try:
                confidence = float(line.split(":", 1)[1].strip())
            except (ValueError, IndexError):
                confidence = 1.0
        else:
            cleaned.append(line)
    return "\n".join(cleaned).strip(), confidence


def fast_answer(question: str, kws: KeywordSearchTool, cr: ChunkReadTool,
                backend, model: str, temperature: float, max_tokens: int) -> tuple[str, float, float]:
    candidates = kws.search(question, top_k=3)
    context_parts = [cr.read(c.chunk_id, adjacent=True) for c in candidates if c]
    context = "\n---\n".join([c for c in context_parts if c])

    prompt = build_fast_prompt(context, question)
    start = time.time()
    response = backend.chat_completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    elapsed = time.time() - start
    text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    return parse_fast_response(text) + (elapsed,)


def main():
    parser = argparse.ArgumentParser(description="Fast/Slow Router")
    parser.add_argument("--config", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--output", default="results")
    parser.add_argument("--confidence-threshold", type=float, default=0.8)
    args = parser.parse_args()

    cfg = VORTEXConfig.from_yaml(args.config)
    backend = backend_from_config(cfg.llm)

    chunks = load_corpus(args.corpus)
    questions, ground_truths = load_questions(args.questions)
    completed = load_checkpoint(args.output)

    # Shared search tools (fast path)
    kws = KeywordSearchTool(chunks)
    cr = ChunkReadTool(chunks)

    # VORTEX engine (slow path)
    ss = SemanticSearchTool(chunks, np.zeros((len(chunks), 1)))
    planner = GravitationalCore(
        llm_client=backend,
        model=cfg.llm.model,
        temperature=cfg.llm.temperature,
        max_tokens=cfg.llm.max_tokens or 2048,
        confidence_threshold=cfg.engine.confidence_threshold,
    )
    executor = CentrifugalIngestor(
        llm_client=backend,
        keyword_search=kws,
        semantic_search=ss,
        chunk_read=cr,
        model=cfg.llm.model,
        temperature=cfg.llm.temperature,
    )
    vortex = VortexEngine(
        planner=planner,
        executor=executor,
        max_spirals=cfg.engine.max_spirals,
    )

    os.makedirs(args.output, exist_ok=True)
    out_path = os.path.join(args.output, "predictions.jsonl")
    err_path = os.path.join(args.output, "errors.log")

    total_fast = 0
    total_slow = 0
    total_fast_time = 0.0
    total_slow_time = 0.0
    max_tokens = cfg.llm.max_tokens or 2048

    print(f"Fast/Slow Router — model={cfg.llm.model}, threshold={args.confidence_threshold}")
    print(f"  Questions: {len(questions)} total, {len(completed)} already done")
    print(f"  Corpus: {len(chunks)} chunks")
    print(f"  Output: {args.output}\n")

    with open(out_path, "a", encoding="utf-8") as out_f, \
         open(err_path, "a", encoding="utf-8") as err_f:
        for idx, question in enumerate(questions):
            if idx in completed:
                continue

            start_all = time.time()
            ground_truth = ground_truths[idx] if idx < len(ground_truths) else ""
            answer = ""
            route = "error"

            # Fast path
            try:
                answer, confidence, fast_time = fast_answer(
                    question, kws, cr, backend, cfg.llm.model,
                    cfg.llm.temperature, max_tokens,
                )
                if "Insufficient evidence." in answer or confidence < args.confidence_threshold:
                    route = "slow"
                    slow_start = time.time()
                    answer = vortex.run(question)
                    slow_time = time.time() - slow_start
                    total_slow += 1
                    total_slow_time += slow_time
                else:
                    route = "fast"
                    slow_time = 0.0
                    total_fast += 1
                    total_fast_time += fast_time
            except Exception as e:
                elapsed = time.time() - start_all
                err_f.write(f"Q{idx}: {e}\n")
                err_f.flush()
                answer = ""
                route = "error"
                slow_time = 0.0
                fast_time = 0.0

            elapsed = time.time() - start_all
            record = {
                "index": idx,
                "question": question,
                "ground_truth": ground_truth,
                "prediction": answer,
                "route": route,
                "time_s": round(elapsed, 2),
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()

            ok = "✓" if answer and ground_truth and ground_truth in answer else "✗"
            print(f"  [{ok}] Q{idx}: [{route}] {question[:50]}...  [{elapsed:.0f}s]")

    n = len(questions)
    done = n - len(completed)
    print(f"\nDone. {done} new, {len(completed)} cached / {n} total")
    print(f"  Fast: {total_fast}, Slow: {total_slow}")
    if total_fast:
        print(f"  Fast avg:  {total_fast_time / total_fast:.0f}s")
    if total_slow:
        print(f"  Slow avg:  {total_slow_time / total_slow:.0f}s")


if __name__ == "__main__":
    main()
