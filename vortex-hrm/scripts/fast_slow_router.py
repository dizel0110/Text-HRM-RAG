"""
Fast/Slow Router for VORTEX-HRM.

Usage:
    python scripts/fast_slow_router.py --config configs/colab-gpu.yaml ^
        --questions data/multi_domain/questions.json ^
        --corpus data/multi_domain/corpus.json ^
        --output results/router

Strategy:
    1. Fast path (baseline): retrieve top-3 chunks + LLM answer
       - If answer is "Insufficient evidence." → fallback to VORTEX
       - Otherwise → return fast answer
    2. Slow path (VORTEX): full spiral engine
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
from executor import KeywordSearchTool, ChunkReadTool, Chunk
from orchestrator import VortexEngine
from planner import GravitationalCore
from executor import CentrifugalIngestor


def load_data(path: str) -> tuple[list[dict], list[str], list[str]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    questions, ground_truths = [], []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                questions.append(item.get("question", ""))
                ground_truths.append(item.get("ground_truth", ""))
    return data, questions, ground_truths


def load_corpus(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [Chunk(chunk_id=item["id"], text=item["text"]) for item in data]


def fast_answer(question: str, chunks, backend, model, temperature, max_tokens) -> tuple[str, float]:
    """Fast path: retrieve + LLM answer with confidence."""
    kws = KeywordSearchTool(chunks)
    cr = ChunkReadTool(chunks)

    # Retrieve top-3 chunks
    candidates = kws.search(question, top_k=3)
    context_parts = [cr.read(c.chunk_id, adjacent=True) for c in candidates if c]
    context = "\n---\n".join([c for c in context_parts if c])

    prompt = (
        "Answer the question using only the provided passages. "
        "If the answer is not in the passages, say \"Insufficient evidence.\" "
        "Then rate your confidence (0.0-1.0) on a new line: CONFIDENCE: <score>\n\n"
        "Passages:\n{context}\n\n"
        "Question: {question}\nAnswer:"
    ).format(context=context, question=question)

    start = time.time()
    response = backend.chat_completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    elapsed = time.time() - start
    text = response.get("choices", [{}])[0].get("message", {}).get("content", "")

    # Parse answer and confidence
    answer = text.strip()
    confidence = 0.0
    for line in answer.split("\n"):
        if line.startswith("CONFIDENCE:"):
            try:
                confidence = float(line.split(":")[1].strip())
            except ValueError:
                confidence = 0.0
            answer = answer.replace(line, "").strip()

    return answer, confidence, elapsed


def main():
    parser = argparse.ArgumentParser(description="Fast/Slow Router")
    parser.add_argument("--config", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--corpus", default=None)
    parser.add_argument("--output", default="results")
    parser.add_argument("--confidence-threshold", type=float, default=0.8,
                        help="Confidence threshold for fast path (default: 0.8)")
    args = parser.parse_args()

    cfg = VORTEXConfig.from_yaml(args.config)
    backend = backend_from_config(cfg.llm)

    chunks = load_corpus(args.corpus) if args.corpus else []
    _, questions, ground_truths = load_data(args.questions)

    # Init VORTEX engine (slow path)
    planner = GravitationalCore(
        llm_client=backend,
        model=cfg.llm.model,
        temperature=cfg.llm.temperature,
        max_tokens=cfg.llm.max_tokens or 2048,
        confidence_threshold=cfg.engine.confidence_threshold,
        entropy_stall_limit=cfg.engine.entropy_stall_limit,
    )
    executor = CentrifugalIngestor(
        llm_client=backend,
        model=cfg.llm.model,
        temperature=cfg.llm.temperature,
        chunks=chunks,
    )
    vortex = VortexEngine(
        planner=planner,
        executor=executor,
        max_spirals=cfg.engine.max_spirals,
        context_budget=cfg.engine.context_budget,
    )

    os.makedirs(args.output, exist_ok=True)
    out_path = os.path.join(args.output, "predictions.jsonl")
    err_path = os.path.join(args.output, "errors.log")

    total_fast, total_slow = 0, 0
    total_fast_time, total_slow_time = 0.0, 0.0

    print(f"Fast/Slow Router — model={cfg.llm.model}, threshold={args.confidence_threshold}")
    print(f"  Questions: {len(questions)}")
    print(f"  Output:    {args.output}\n")

    with open(out_path, "w", encoding="utf-8") as out_f, \
         open(err_path, "w", encoding="utf-8") as err_f:
        for idx, question in enumerate(questions):
            start_all = time.time()
            ground_truth = ground_truths[idx] if idx < len(ground_truths) else ""

            # Fast path
            answer, confidence, fast_time = fast_answer(
                question, chunks, backend, cfg.llm.model,
                cfg.llm.temperature, cfg.llm.max_tokens,
            )

            route = "fast"
            if answer == "Insufficient evidence." or confidence < args.confidence_threshold:
                # Slow path fallback
                route = "slow"
                slow_start = time.time()
                answer = vortex.run(question)
                slow_time = time.time() - slow_start
                total_slow += 1
                total_slow_time += slow_time
            else:
                slow_time = 0.0
                total_fast += 1
                total_fast_time += fast_time

            elapsed = time.time() - start_all

            record = {
                "index": idx,
                "question": question,
                "ground_truth": ground_truth,
                "prediction": answer,
                "route": route,
                "fast_confidence": round(confidence, 2),
                "time_s": round(elapsed, 2),
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

            ok = "✓" if answer and ground_truth and ground_truth in answer else "✗"
            print(f"  [{ok}] Q{idx}: [{route}] {question[:50]}...  [{elapsed:.0f}s]")
            out_f.flush()

    n = len(questions)
    print(f"\nDone. {n} questions, fast={total_fast}, slow={total_slow}")
    print(f"  Fast avg:  {total_fast_time/max(total_fast,1):.0f}s")
    print(f"  Slow avg:  {total_slow_time/max(total_slow,1):.0f}s")
    print(f"  Avg total: {(total_fast_time+total_slow_time)/n:.0f}s")


if __name__ == "__main__":
    main()
