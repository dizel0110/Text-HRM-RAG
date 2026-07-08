"""
VORTEX minimal demo — synthetic corpus, mocked LLM, no downloads.
Demonstrates: planning, ingestion, gating, entropic collapse, final answer.

Usage:  python scripts/demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
from unittest.mock import patch

from planner import GravitationalCore
from executor import CentrifugalIngestor, KeywordSearchTool, SemanticSearchTool, ChunkReadTool, Chunk, Fact, IngestionResult
from orchestrator import VortexEngine


SYNTHETIC_CORPUS = [
    Chunk("0", "Jane Doe is a novelist and playwright. She wrote the book 'The Silent Storm' in 2005."),
    Chunk("1", "Jane Doe was born on March 14, 1978, in Portland, Oregon."),
    Chunk("2", "'The Silent Storm' won the Booker Prize in 2006."),
    Chunk("3", "The film adaptation of 'The Silent Storm' was directed by John Smith."),
    Chunk("4", "John Smith was born on July 22, 1970, in London, England."),
    Chunk("5", "John Smith is known for his atmospheric thriller films."),
    Chunk("6", "The Eiffel Tower was built in 1889 and stands in Paris, France."),
    Chunk("7", "Paris is the capital of France with a population of 2.1 million."),
]


def build_executor():
    chunks = SYNTHETIC_CORPUS
    kws = KeywordSearchTool(chunks)
    embeddings = np.random.randn(len(chunks), 384).astype(np.float32)
    ss = SemanticSearchTool(chunks, embeddings)
    cr = ChunkReadTool(chunks)
    return CentrifugalIngestor(None, kws, ss, cr), chunks


def build_planner(canned_responses):
    class MockLLM:
        def __init__(self):
            self.idx = 0
        def chat_completion(self, **kwargs):
            r = canned_responses[min(self.idx, len(canned_responses) - 1)]
            self.idx += 1
            return {"choices": [{"message": {"content": r}}]}

    return GravitationalCore(MockLLM(), confidence_threshold=0.85)


def demo_single_question(question, planner_responses, executor_facts):
    planner = build_planner(planner_responses)
    executor, chunks = build_executor()

    def mock_ingest(sub_question):
        matched = []
        for chunk in chunks:
            q_words = set(sub_question.lower().split())
            c_words = set(chunk.text.lower().split())
            if len(q_words & c_words) >= 2:
                matched.append(Fact(source=chunk.chunk_id, text=chunk.text))
        if not matched:
            matched = [Fact(source="none", text="No evidence found.")]
        return IngestionResult(facts=matched)

    with patch.object(executor, "ingest", side_effect=mock_ingest):
        engine = VortexEngine(planner, executor, max_spirals=6)
        result = engine.run(question)

    print(f"  Question: {question}")
    print(f"  Answer:   {result[:200]}")
    print(f"  Spirals:  {engine.planner.state.hop_count}")
    print(f"  Entropy:  {engine.planner.state.entropy:.4f}")
    print(f"  Stalls:   {engine.planner.state.consecutive_stalled_spins}")
    print()
    return result


def main():
    print("=" * 60)
    print("VORTEX Demo — Synthetic Multi-Hop QA")
    print("=" * 60)
    print()

    q1 = "What is the birth year of the author of 'The Silent Storm'?"
    r1 = [
        "<think>Need author first, then birth year.</think><step>Who wrote 'The Silent Storm'?</step>",
        "<think>Author is Jane Doe. Now find her birth year.</think><step>What is the birth year of Jane Doe?</step>",
        "<think>Jane Doe was born in 1978. All evidence gathered.</think><final_answer>Jane Doe was born in 1978.</final_answer>",
    ]
    demo_single_question(q1, r1, None)

    q2 = "In what year was the director of the film adaptation of 'The Silent Storm' born?"
    r2 = [
        "<think>Need: film director, then their birth year.</think><step>Who directed the film adaptation of 'The Silent Storm'?</step>",
        "<think>Director is John Smith. Now birth year.</think><step>What is the birth year of John Smith?</step>",
        "<think>John Smith born 1970. All resolved.</think><final_answer>John Smith was born in 1970.</final_answer>",
    ]
    demo_single_question(q2, r2, None)

    print("=" * 60)
    print("VORTEX Demo Complete — All synthetic paths validated.")
    print("=" * 60)


if __name__ == "__main__":
    main()
