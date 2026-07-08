"""
VORTEX batch runner — runs multiple questions with checkpoint resume.

Usage:
    python scripts/batch_runner.py \
        --config configs/local.yaml \
        --questions data/sample.json \
        --output results/run1 \
        --workers 1
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
from planner import GravitationalCore
from executor import CentrifugalIngestor, KeywordSearchTool, SemanticSearchTool, ChunkReadTool, Chunk
from orchestrator import VortexEngine
import numpy as np


def build_synthetic_corpus() -> list[Chunk]:
    return [
        Chunk(chunk_id="0", text="Jane Doe is a novelist from England. She wrote many books."),
        Chunk(chunk_id="1", text="Jane Doe's most famous novel is 'The Silent Sea'."),
        Chunk(chunk_id="2", text="Jane Doe was born in 1985 in London, UK."),
        Chunk(chunk_id="3", text="'The Silent Sea' won the Booker Prize in 2010."),
        Chunk(chunk_id="4", text="Jane Doe studied at Oxford University."),
    ]


def load_questions(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("questions", "data", "items", "examples"):
            if key in data:
                return data[key]
    raise ValueError(f"Cannot parse questions from {path}")


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
    parser = argparse.ArgumentParser(description="VORTEX batch runner")
    parser.add_argument("--config", required=True, help="YAML config path")
    parser.add_argument("--questions", required=True, help="JSON file with questions")
    parser.add_argument("--output", default="results", help="Output directory")
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers (1 = sequential)")
    args = parser.parse_args()

    cfg = VORTEXConfig.from_yaml(args.config)
    backend = backend_from_config(cfg.llm)

    chunks = build_synthetic_corpus()
    kws = KeywordSearchTool(chunks)
    ss = SemanticSearchTool(chunks, np.zeros((len(chunks), 1)))
    cr = ChunkReadTool(chunks)

    planner = GravitationalCore(
        llm_client=backend,
        model=cfg.llm.model,
        temperature=cfg.llm.temperature,
        max_tokens=cfg.llm.max_tokens,
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

    engine = VortexEngine(
        planner=planner,
        executor=executor,
        max_spirals=cfg.engine.max_spirals,
    )

    questions = load_questions(args.questions)
    completed = load_checkpoint(args.output)

    print(f"VORTEX Batch — mode={cfg.llm.mode}, questions={len(questions)}, completed={len(completed)}")

    os.makedirs(args.output, exist_ok=True)
    predictions_path = os.path.join(args.output, "predictions.jsonl")

    with open(predictions_path, "a", encoding="utf-8") as out_f:
        for idx, question in enumerate(questions):
            if idx in completed:
                continue

            try:
                start = time.time()
                answer = engine.run(question)
                elapsed = time.time() - start
                hops = planner.state.hop_count if planner.state else 0

                record = {
                    "index": idx,
                    "question": question,
                    "prediction": answer,
                    "ground_truth": "",
                    "spirals": hops,
                    "time_s": round(elapsed, 2),
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_f.flush()

                completed.add(idx)
                save_checkpoint(args.output, completed)

                if (idx + 1) % 10 == 0:
                    print(f"  [{idx+1}/{len(questions)}] — {len(completed)} done")

            except Exception as e:
                print(f"  [ERROR] index={idx}: {e}")
                completed.add(idx)
                save_checkpoint(args.output, completed)

    print(f"Done. {len(completed)}/{len(questions)} completed.")
    print(f"Predictions: {predictions_path}")


if __name__ == "__main__":
    main()
