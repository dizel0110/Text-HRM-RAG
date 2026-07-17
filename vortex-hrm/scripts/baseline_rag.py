"""
Naive RAG baseline — single-pass retrieve + answer (no vortex loop).

Usage:
    python scripts/baseline_rag.py --config configs/colab-gpu.yaml ^
        --questions data/multi_domain/questions.json ^
        --corpus data/multi_domain/corpus.json ^
        --output results/baseline_run

Output: same predictions.jsonl format as batch_runner.py
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
from executor import KeywordSearchTool, SemanticSearchTool, ChunkReadTool, Chunk
import numpy as np


def load_corpus(path: str) -> list[Chunk]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [Chunk(chunk_id=item["id"], text=item["text"]) for item in data]


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


def load_checkpoint(output_dir: str) -> set[int]:
    ckpt_path = os.path.join(output_dir, "checkpoint.json")
    if os.path.exists(ckpt_path):
        with open(ckpt_path) as f:
            return set(json.load(f))
    return set()


def save_checkpoint(output_dir: str, completed: set[int]):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "checkpoint.json"), "w") as f:
        json.dump(list(completed), f)


def main():
    parser = argparse.ArgumentParser(description="Naive RAG baseline")
    parser.add_argument("--config", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--corpus", default=None)
    parser.add_argument("--output", default="results")
    args = parser.parse_args()

    cfg = VORTEXConfig.from_yaml(args.config)
    backend = backend_from_config(cfg.llm)

    chunks = load_corpus(args.corpus) if args.corpus else []
    kws = KeywordSearchTool(chunks)
    cr = ChunkReadTool(chunks)

    questions, ground_truths = load_questions(args.questions)
    completed = load_checkpoint(args.output)

    print(f"Naive RAG baseline — mode={cfg.llm.mode}, model={cfg.llm.model}")
    print(f"  Questions: {len(questions)} total, {len(completed)} already done")
    print(f"  Corpus: {len(chunks)} chunks")
    print(f"  Output: {args.output}\n")

    os.makedirs(args.output, exist_ok=True)
    predictions_path = os.path.join(args.output, "predictions.jsonl")
    errors_path = os.path.join(args.output, "errors.log")

    prompt_template = (
        "Answer the question using only the provided passages.\n"
        "If the answer is not in the passages, say \"Insufficient evidence.\"\n\n"
        "Passages:\n{context}\n\n"
        "Question: {question}\nAnswer:"
    )

    with open(predictions_path, "a", encoding="utf-8") as out_f, \
         open(errors_path, "a", encoding="utf-8") as err_f:
        for idx, question in enumerate(questions):
            if idx in completed:
                continue

            ground_truth = ground_truths[idx] if idx < len(ground_truths) else ""
            print(f"[{len(completed)+1}/{len(questions)}] Q: {question[:80]}{'...' if len(question) > 80 else ''}")

            try:
                start = time.time()
                top_k = kws(question, top_k=3)
                context = "\n---\n".join(f"[{c.chunk_id}] {c.text}" for c, _ in top_k)
                prompt = prompt_template.format(context=context, question=question)
                response = backend.chat_completion(
                    model=cfg.llm.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=cfg.llm.temperature,
                    max_tokens=cfg.llm.max_tokens,
                )
                answer = response["choices"][0]["message"]["content"].strip()
                elapsed = time.time() - start

                record = {
                    "index": idx,
                    "question": question,
                    "prediction": answer,
                    "ground_truth": ground_truth,
                    "spirals": 0,
                    "time_s": round(elapsed, 2),
                    "mode": cfg.llm.mode,
                    "model": cfg.llm.model,
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_f.flush()

                completed.add(idx)
                save_checkpoint(args.output, completed)

                print(f"  → {answer[:80]}{'...' if len(answer) > 80 else ''} [{elapsed:.0f}s, baseline]")

            except Exception as e:
                err_f.write(f"[{idx}] {question[:60]}: {e}\n")
                err_f.flush()
                print(f"  ! ERROR: {e}")
                completed.add(idx)
                save_checkpoint(args.output, completed)

    print(f"\nDone. {len(completed)}/{len(questions)} completed.")
    print(f"Predictions: {predictions_path}")
    print(f"Errors:      {errors_path}")


if __name__ == "__main__":
    main()
