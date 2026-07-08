"""
VORTEX smoke test — validates core logic WITHOUT a real LLM or disk downloads.
Runs on bare Python 3.11 + numpy only. No GPU, no internet.

Usage:  python test_smoke.py
"""

import sys
import re
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, "src")

from planner import (
    GravitationalState,
    GravitationalCore,
    SpinOutput,
    jaccard_redundancy,
    token_fingerprint,
)
from executor import Fact, IngestionResult, CentrifugalIngestor, ChunkReadTool
from orchestrator import VortexEngine, REDUNDANCY_THRESHOLD


class MockLLM:
    def __init__(self, responses=None):
        self.call_count = 0
        self.responses = responses or []

    def chat_completion(self, **kwargs) -> dict:
        idx = min(self.call_count, len(self.responses) - 1) if self.responses else 0
        content = self.responses[idx] if self.responses else "<think>mock</think><final_answer>mock answer</final_answer>"
        self.call_count += 1
        return {"choices": [{"message": {"content": content}}]}


def test_jaccard_redundancy():
    assert jaccard_redundancy("hello world", []) == 0.0
    assert jaccard_redundancy("hello world", ["hello world"]) > 0.99
    assert jaccard_redundancy("hello world", ["goodbye moon"]) == 0.0
    overlap = jaccard_redundancy("hello world foo", ["hello world bar"])
    assert 0.3 < overlap < 0.8
    print("  [OK] jaccard_redundancy")


def test_token_fingerprint():
    fp = token_fingerprint("Hello World!")
    assert "hello" in fp
    assert "world!" in fp
    print("  [OK] token_fingerprint")


def test_gravitational_state_entropy():
    gs = GravitationalState(goal_vector="test")
    assert gs.entropy == 1.0
    assert gs.confidence == 0.0

    gs.ingest_fact("<fact source='chunk_0'>\nFirst fact\n</fact>")
    assert gs.entropy < 1.0
    assert gs.hop_count == 1

    prev_entropy = gs.entropy
    gs.ingest_fact("<fact source='chunk_1'>\nFirst fact\n</fact>")
    assert gs.entropy == prev_entropy, f"Expected {prev_entropy}, got {gs.entropy}"
    assert gs.consecutive_stalled_spins >= 1

    gs.ingest_fact("<fact source='chunk_2'>\nCompletely different novel information now\n</fact>")
    assert gs.entropy < prev_entropy
    assert gs.consecutive_stalled_spins == 0

    print("  [OK] GravitationalState entropy tracking")


def test_gravitational_state_context_budget():
    gs = GravitationalState(goal_vector="x", context_budget=3)
    gs.spiral_memory = ["very long fact that exceeds"]
    assert gs.is_context_exceeded()

    gs2 = GravitationalState(goal_vector="x", context_budget=10000)
    assert not gs2.is_context_exceeded()
    print("  [OK] GravitationalState context budget")


def test_spin_output_parse():
    text = """
    <think>
    First find the author, then find their birth year.
    </think>
    <step>
    Who wrote the book "The Great Gatsby"?
    </step>
    """
    out = SpinOutput.parse(text)
    assert out.reasoning == "First find the author, then find their birth year."
    assert out.step == 'Who wrote the book "The Great Gatsby"?'
    assert out.final_answer is None
    assert out.stop_search is None
    print("  [OK] SpinOutput.parse — step")

    text2 = """
    <think>
    All evidence gathered.
    </think>
    <final_answer>
    F. Scott Fitzgerald
    </final_answer>
    """
    out2 = SpinOutput.parse(text2)
    assert out2.final_answer == "F. Scott Fitzgerald"
    assert out2.step is None
    print("  [OK] SpinOutput.parse — final_answer")

    text3 = """
    <think>
    Entropy stalled.
    </think>
    <stop_search>
    No new information after 3 spins.
    </stop_search>
    """
    out3 = SpinOutput.parse(text3)
    assert out3.stop_search == "No new information after 3 spins."
    print("  [OK] SpinOutput.parse — stop_search")


def test_fact_redundancy():
    f1 = Fact(source="chunk_0", text="The capital of France is Paris.")
    f2 = Fact(source="chunk_1", text="The capital of France is Paris.")
    f3 = Fact(source="chunk_2", text="The population of Paris is 2 million.")

    assert f1.redundancy_against([f2]) > 0.99
    assert f1.redundancy_against([f3]) < 0.4
    print("  [OK] Fact.redundancy_against")


def test_ingestion_result_parse():
    text = """
    <fact source="chunk_42">
    The author of "Book X" is Jane Doe.
    </fact>
    """
    result = IngestionResult.parse(text)
    assert len(result.facts) == 1
    assert result.facts[0].source == "chunk_42"
    assert "Jane Doe" in result.facts[0].text
    print("  [OK] IngestionResult.parse — single fact")

    text2 = """
    <step>
    Find the birth year of the director.
    </step>
    """
    result2 = IngestionResult.parse(text2)
    assert result2.remaining_step == "Find the birth year of the director."
    print("  [OK] IngestionResult.parse — step only")


def test_gravitational_core_entropic_collapse():
    mock = MockLLM()
    core = GravitationalCore(mock, confidence_threshold=0.85)
    core.initialize("Test question", max_hops=15)

    core.state.entropy = 0.5
    core.state.consecutive_stalled_spins = 3
    core.state.entropy_history = [0.5, 0.5, 0.5, 0.5]

    result = core.spin()
    assert result.stop_search is not None
    assert result.entropic_collapse
    print("  [OK] GravitationalCore — entropic collapse")


def test_gravitational_core_confidence_termination():
    mock = MockLLM()
    core = GravitationalCore(mock, confidence_threshold=0.85)
    core.initialize("Test question")
    core.state.confidence = 0.90

    result = core.spin()
    assert result.stop_search is not None
    print("  [OK] GravitationalCore — confidence termination")


def test_gravitational_core_final_answer():
    mock = MockLLM(responses=["<think>Done</think><final_answer>42</final_answer>"])
    core = GravitationalCore(mock)
    core.initialize("Life universe everything")

    result = core.spin()
    assert result.final_answer == "42"
    print("  [OK] GravitationalCore — final answer passthrough")


def test_gravitational_core_step_generation():
    mock = MockLLM(responses=["<think>Decompose</think><step>Who wrote X?</step>"])
    core = GravitationalCore(mock)
    core.initialize("Birth year of author of X")

    result = core.spin()
    assert result.step == "Who wrote X?"
    assert len(core.state.remaining_steps) == 1
    print("  [OK] GravitationalCore — step generation")


def test_vortex_engine_simple():
    responses = iter([
        "<think>Decompose</think><step>Who wrote X?</step>",
        "<think>Need birth year</think><step>Birth year of the author?</step>",
        "<think>All done</think><final_answer>1925</final_answer>",
    ])

    class StreamingMockLLM:
        def __init__(self):
            self.call_count = 0
        def chat_completion(self, **kwargs):
            val = next(responses)
            self.call_count += 1
            return {"choices": [{"message": {"content": val}}]}

    from executor import KeywordSearchTool, ChunkReadTool, SemanticSearchTool
    import numpy as np

    planner = GravitationalCore(StreamingMockLLM())
    chunks = []
    kws = KeywordSearchTool(chunks)
    ss = SemanticSearchTool(chunks, np.zeros((0, 1)))
    cr = ChunkReadTool(chunks)
    executor = CentrifugalIngestor(StreamingMockLLM(), kws, ss, cr)

    engine = VortexEngine(planner, executor, max_spirals=10)

    fact_batches = [
        [Fact(source="chunk_1", text="Jane Doe wrote X.")],
        [Fact(source="chunk_2", text="Jane Doe was born in 1925.")],
    ]

    from unittest.mock import patch

    def side_effect(sub_question):
        batch = fact_batches.pop(0) if fact_batches else []
        return IngestionResult(facts=batch)

    with patch.object(executor, "ingest", side_effect=side_effect):
        result = engine.run("Birth year of author of X?")

    assert "1925" in result
    print("  [OK] VortexEngine — full cycle with mocked ingestion")


def test_vortex_engine_stall_termination():
    from executor import KeywordSearchTool, ChunkReadTool, SemanticSearchTool
    import numpy as np

    mock = MockLLM()
    planner = GravitationalCore(mock)
    chunks = []
    kws = KeywordSearchTool(chunks)
    ss = SemanticSearchTool(chunks, np.zeros((0, 1)))
    cr = ChunkReadTool(chunks)
    executor = CentrifugalIngestor(mock, kws, ss, cr)
    engine = VortexEngine(planner, executor, max_spirals=10)
    engine.planner.initialize("Test stall")
    engine.planner.state.entropy = 0.5
    engine.planner.state.consecutive_stalled_spins = 3

    result = engine._synthesize_answer()
    assert isinstance(result, str)
    print("  [OK] VortexEngine — stall termination path")


def test_redundancy_gate():
    from executor import KeywordSearchTool, ChunkReadTool, SemanticSearchTool
    import numpy as np

    mock = MockLLM()
    core = GravitationalCore(mock)
    core.initialize("Test gating")
    core.state.spiral_memory = [
        '<fact source="chunk_1">\nParis is capital of France\n</fact>',
    ]

    redundant_fact = Fact(source="chunk_2", text="Paris is capital of France")
    novel_fact = Fact(source="chunk_2", text="France has a population of 67 million")

    chunks = []
    kws = KeywordSearchTool(chunks)
    ss = SemanticSearchTool(chunks, np.zeros((0, 1)))
    cr = ChunkReadTool(chunks)
    executor = CentrifugalIngestor(mock, kws, ss, cr)

    engine = VortexEngine(core, executor)
    assert not engine._gate_fact(redundant_fact), "Redundant fact should be gated"
    assert engine._gate_fact(novel_fact), "Novel fact should pass"
    assert redundant_fact.redundant
    print("  [OK] VortexEngine._gate_fact — redundancy detection")


def test_centrifugal_ingestor_parse():
    text = """
    <fact source="chunk_10">
    The Eiffel Tower is in Paris.
    </fact>
    <fact source="chunk_11">
    Paris is the capital of France.
    </fact>
    """
    result = IngestionResult.parse(text)
    assert len(result.facts) == 2
    assert result.facts[0].source == "chunk_10"
    assert result.facts[1].source == "chunk_11"
    print("  [OK] IngestionResult.parse — multiple facts")


def test_edge_empty_spiral_memory():
    gs = GravitationalState(goal_vector="test")
    assert gs.is_context_exceeded() is False
    assert gs.ingest_fact is not None
    print("  [OK] Edge: empty GravitationalState")


def test_edge_max_hops_termination():
    mock = MockLLM()
    core = GravitationalCore(mock)
    core.initialize("Test", max_hops=1)
    core.state.hop_count = 1
    result = core.spin()
    assert result.final_answer is not None
    print("  [OK] Edge: max_hops termination")


if __name__ == "__main__":
    tests = [
        ("token_fingerprint", test_token_fingerprint),
        ("jaccard_redundancy", test_jaccard_redundancy),
        ("GravitationalState entropy", test_gravitational_state_entropy),
        ("GravitationalState context budget", test_gravitational_state_context_budget),
        ("SpinOutput parse", test_spin_output_parse),
        ("Fact redundancy", test_fact_redundancy),
        ("IngestionResult parse", test_ingestion_result_parse),
        ("GravitationalCore entropic collapse", test_gravitational_core_entropic_collapse),
        ("GravitationalCore confidence termination", test_gravitational_core_confidence_termination),
        ("GravitationalCore final answer", test_gravitational_core_final_answer),
        ("GravitationalCore step generation", test_gravitational_core_step_generation),
        ("VortexEngine full cycle", test_vortex_engine_simple),
        ("VortexEngine stall termination", test_vortex_engine_stall_termination),
        ("VortexEngine gate_fact", test_redundancy_gate),
        ("CentrifugalIngestor parse", test_centrifugal_ingestor_parse),
        ("Edge: empty state", test_edge_empty_spiral_memory),
        ("Edge: max_hops", test_edge_max_hops_termination),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*40}")
    print(f"VORTEX Smoke Test: {passed}/{passed + failed} passed")
    if failed:
        print(f"FAILURES: {failed}")
        sys.exit(1)
    else:
        print("All core logic validated. Ready for GitHub.")
