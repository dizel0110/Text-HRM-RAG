"""
VORTEX Orchestration Engine — cyclic attractor loop.
Design philosophy: ../vortex_philosophy.md
"""

import re

from planner import GravitationalCore, SpinOutput, jaccard_redundancy
from executor import CentrifugalIngestor, Fact, IngestionResult


REDUNDANCY_THRESHOLD = 0.85


class VortexEngine:
    def __init__(
        self,
        planner: GravitationalCore,
        executor: CentrifugalIngestor,
        max_spirals: int = 15,
        confidence_threshold: float = 0.85,
        context_budget: int = 8192,
    ):
        self.planner = planner
        self.executor = executor
        self.max_spirals = max_spirals
        self.confidence_threshold = confidence_threshold
        self.context_budget = context_budget

    def run(self, question: str) -> str:
        self.planner.initialize(
            question,
            max_hops=self.max_spirals,
            context_budget=self.context_budget,
        )

        for spiral in range(self.max_spirals):
            spin_output = self.planner.spin()

            if spin_output.final_answer:
                return self.extract_answer(spin_output.final_answer)

            if spin_output.stop_search:
                return self.extract_answer(self._synthesize_answer())

            if spin_output.step:
                step_to_resolve = self._current_step_index()

                ingestion = self.executor.ingest(spin_output.step)

                ingested_any = False
                for fact in ingestion.facts:
                    if self._gate_fact(fact):
                        ingested_any = True
                        condensed = f'<fact source="{fact.source}">\n{fact.text}\n</fact>'
                        confidence_delta = 0.05 if fact.source != "none" and not fact.redundant else 0.0
                        self.planner.ingest_fact(condensed, confidence_delta=confidence_delta)

                if not ingested_any and ingestion.facts:
                    pass

                if not ingestion.remaining_step and ingested_any:
                    self.planner.mark_step_resolved(step_idx=step_to_resolve)

            if self.planner.state and self.planner.state.is_context_exceeded():
                break

        return self.extract_answer(self._synthesize_answer())

    def _current_step_index(self) -> int:
        if self.planner.state is None:
            return 0
        if not self.planner.state.remaining_steps:
            return 0
        return len(self.planner.state.remaining_steps) - 1

    @staticmethod
    def _clean_xml(text: str) -> str:
        text = re.sub(r'<fact\s+source="[^"]*">\s*', '', text)
        text = re.sub(r'\s*</fact>', '', text)
        return text.strip()

    @staticmethod
    def _clean_text(text: str) -> str:
        """Strip XML tags, normalize whitespace."""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def extract_answer(text: str) -> str:
        """Clean VORTEX output: strip XML, remove noise, de-duplicate, return concise answer."""
        if not text:
            return "Insufficient evidence."

        lines = text.split("\n")
        facts = []
        for line in lines:
            if "<fact" in line or "</fact>" in line:
                continue
            if "No evidence found for this sub-question" in line:
                continue
            if "Insufficient evidence" in line and len(line.strip()) < 30:
                continue
            cleaned = re.sub(r'<[^>]+>', ' ', line).strip()
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            if cleaned and cleaned not in facts:
                facts.append(cleaned)

        if not facts:
            return "Insufficient evidence."

        return "\n".join(facts)

    def _gate_fact(self, fact: Fact) -> bool:
        if fact.source == "none":
            return False

        if self.planner.state is None:
            return True

        prior_cleaned = [self._clean_xml(f) for f in self.planner.state.spiral_memory]
        fact_text = fact.text

        redundancy = jaccard_redundancy(fact_text, prior_cleaned)
        if redundancy > REDUNDANCY_THRESHOLD:
            fact.redundant = True
            return False

        return True

    def _synthesize_answer(self) -> str:
        if self.planner.state is None:
            return ""

        facts = [f.strip() for f in self.planner.state.spiral_memory]
        if not facts:
            return "Insufficient evidence."

        return "\n".join(facts)
