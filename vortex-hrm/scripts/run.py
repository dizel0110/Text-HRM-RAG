"""
Config-driven VORTEX runner.
Usage:
    python scripts/run.py --config configs/mock.yaml --question "Who wrote X?"
    python scripts/run.py --config configs/local.yaml --questions data/sample.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.config import VORTEXConfig, LLMConfig
from core.llm import backend_from_config, MockBackend
from planner import GravitationalCore
from executor import CentrifugalIngestor, KeywordSearchTool, SemanticSearchTool, ChunkReadTool, Chunk
from orchestrator import VortexEngine
import numpy as np


MOCK_RESPONSES = [
    "<think>Find the author first, then find their birth year.</think><step>Who wrote 'The Silent Sea'?</step>",
    "<think>The author is Jane Doe. Now find when she was born.</think><step>What year was Jane Doe born?</step>",
    "<think>Jane Doe was born in 1985.</think><final_answer>1985</final_answer>",
]

MOCK_EXECUTOR_RESPONSES = [
    "<fact source=\"chunk_1\">\nJane Doe wrote 'The Silent Sea'.\n</fact>",
    "<fact source=\"chunk_2\">\nJane Doe was born in 1985 in London.\n</fact>",
]


def build_synthetic_corpus() -> list[Chunk]:
    return [
        Chunk(chunk_id="0", text="Jane Doe is a novelist from England. She wrote many books."),
        Chunk(chunk_id="1", text="Jane Doe's most famous novel is 'The Silent Sea'."),
        Chunk(chunk_id="2", text="Jane Doe was born in 1985 in London, UK."),
        Chunk(chunk_id="3", text="'The Silent Sea' won the Booker Prize in 2010."),
        Chunk(chunk_id="4", text="Jane Doe studied at Oxford University."),
    ]


def main():
    parser = argparse.ArgumentParser(description="VORTEX: run a question through the engine")
    parser.add_argument("--config", default=None, help="Path to YAML config (optional — uses mock mode)")
    parser.add_argument("--question", default=None, help="Single question to answer")
    parser.add_argument("--questions", default=None, help="JSON file with questions array")
    parser.add_argument("--verbose", action="store_true", help="Print spiral details")
    args = parser.parse_args()

    if args.config:
        cfg = VORTEXConfig.from_yaml(args.config)
    else:
        cfg = VORTEXConfig()

    if args.verbose:
        cfg.engine.verbose = True

    if cfg.llm.mode == "mock":
        planner_backend = MockBackend(responses=MOCK_RESPONSES)
        executor_backend = MockBackend(responses=MOCK_EXECUTOR_RESPONSES)
    else:
        planner_backend = backend_from_config(cfg.llm)
        executor_backend = backend_from_config(cfg.llm)

    chunks = build_synthetic_corpus()
    kws = KeywordSearchTool(chunks)
    ss = SemanticSearchTool(chunks, np.zeros((len(chunks), 1)))
    cr = ChunkReadTool(chunks)

    planner = GravitationalCore(
        llm_client=planner_backend,
        model=cfg.llm.model,
        temperature=cfg.llm.temperature,
        max_tokens=cfg.llm.max_tokens,
        confidence_threshold=cfg.engine.confidence_threshold,
    )

    executor = CentrifugalIngestor(
        llm_client=executor_backend,
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

    questions = []
    if args.question:
        questions.append(args.question)
    if args.questions:
        with open(args.questions, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                questions.extend(data)
            elif isinstance(data, dict) and "questions" in data:
                questions.extend(data["questions"])

    if not questions:
        questions.append("What year was Jane Doe born?")

    print(f"VORTEX Engine — mode={cfg.llm.mode}, model={cfg.llm.model}")
    print(f"Questions: {len(questions)}\n")

    for q in questions:
        print(f"Q: {q}")
        start = time.time()
        answer = engine.run(q)
        elapsed = time.time() - start
        print(f"A: {answer}")
        print(f"  [{elapsed:.1f}s, {planner.state.hop_count if planner.state else 0} spirals]\n")


if __name__ == "__main__":
    main()
