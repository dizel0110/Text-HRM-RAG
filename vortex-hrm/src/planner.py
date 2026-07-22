"""
VORTEX Gravitational Core.
Design philosophy: ../vortex_philosophy.md
"""

import re
from dataclasses import dataclass, field
from typing import Optional

GRAVITATIONAL_CORE_PROMPT = """You are a QA planner. Your job is to decompose multi-hop questions and manage evidence retrieval.

CRITICAL RULES:
- Do NOT answer the question directly. Only use facts from spiral_memory.
- If no facts are available, emit a <step> to retrieve more data.
- Do NOT guess. Every claim must cite a fact from spiral_memory.

Your state:
- question: the original question
- spiral_memory: facts found so far (from executor)
- remaining_steps: sub-questions not yet answered
- hop_count: steps taken so far

Output one of:

<think>Your reasoning here</think>
<step>Atomic sub-question to retrieve next</step>

<think>Reason for stopping</think>
<stop_search>Why no more retrieval is needed</stop_search>

<think>All sub-questions answered</think>
<final_answer>Short answer only, no XML tags, no explanation. Examples: "1775", "Pride and Prejudice", "Marie Curie, 1867"</final_answer>

Rules:
- Each <step> must retrieve one fact only.
- Never repeat a resolved step.
- Base answers only on facts from spiral_memory.
- If spiral_memory is empty, emit a <step> — never a final_answer first."""

GRAVITATIONAL_CORE_PROMPT_PLAIN = """You are a QA planner. Your job is to decompose multi-hop questions and manage evidence retrieval.

CRITICAL RULES:
- Do NOT answer the question directly. Only use facts from spiral_memory.
- If no facts are available, ask a sub-question to retrieve more data.
- Do NOT guess. Every claim must cite a fact from spiral_memory.

Your state:
- question: the original question
- spiral_memory: facts found so far (from executor)
- remaining_steps: sub-questions not yet answered
- hop_count: steps taken so far

Output exactly ONE of these three actions:

1. RETRIEVE: Ask a sub-question to retrieve more evidence.
   Format: RETRIEVE: [your sub-question here]

2. STOP: You have enough evidence to answer.
   Format: STOP: [reason why no more retrieval is needed]

3. ANSWER: All sub-questions answered, provide final answer.
   Format: ANSWER: [short answer only, no explanation]

Examples:
- RETRIEVE: Who was the first president of the United States?
- STOP: I have found all required facts from spiral_memory.
- ANSWER: George Washington

Rules:
- Each RETRIEVE must ask for one fact only.
- Never repeat a resolved step.
- Base answers only on facts from spiral_memory.
- If spiral_memory is empty, emit a RETRIEVE — never an ANSWER first."""


def token_fingerprint(text: str) -> set[str]:
    return set(text.lower().split())


def jaccard_redundancy(new_text: str, existing_texts: list[str]) -> float:
    new_tokens = token_fingerprint(new_text)
    if not new_tokens:
        return 1.0
    max_overlap = 0.0
    for existing in existing_texts:
        existing_tokens = token_fingerprint(existing)
        if not existing_tokens:
            continue
        intersection = len(new_tokens & existing_tokens)
        union = len(new_tokens | existing_tokens)
        overlap = intersection / union if union > 0 else 0.0
        if overlap > max_overlap:
            max_overlap = overlap
    return max_overlap


@dataclass
class HistoryEntry:
    hop: int
    reasoning: str
    step_emitted: Optional[str] = None
    facts_received: list[str] = field(default_factory=list)
    stop_reason: Optional[str] = None
    final_answer: Optional[str] = None


@dataclass
class GravitationalState:
    goal_vector: str
    spiral_memory: list[str] = field(default_factory=list)
    remaining_steps: list[str] = field(default_factory=list)
    hop_count: int = 0
    confidence: float = 0.0
    entropy: float = 1.0
    entropy_history: list[float] = field(default_factory=list)
    consecutive_stalled_spins: int = 0
    entropy_stall_limit: int = 3
    max_hops: int = 15
    context_budget: int = 8192
    _redundant_count: int = 0
    history: list[HistoryEntry] = field(default_factory=list)

    def build_prompt(self) -> str:
        parts = [f"Goal vector: {self.goal_vector}"]
        parts.append(f"Hop count: {self.hop_count}/{self.max_hops}")
        parts.append(f"Confidence: {self.confidence:.2f}")
        parts.append(f"Entropy: {self.entropy:.4f}")

        if self.history:
            parts.append("\nFull hop history (oldest → newest):")
            for entry in self.history:
                parts.append(f"  Hop {entry.hop}:")
                if entry.reasoning:
                    parts.append(f"    Reasoning: {entry.reasoning[:200]}")
                if entry.step_emitted:
                    parts.append(f"    Query: {entry.step_emitted}")
                if entry.facts_received:
                    for fact in entry.facts_received:
                        parts.append(f"    → {fact}")
                if entry.stop_reason:
                    parts.append(f"    Stop: {entry.stop_reason}")
                if entry.final_answer:
                    parts.append(f"    Answer: {entry.final_answer}")

        if self.remaining_steps:
            parts.append("\nRemaining steps:")
            for i, step in enumerate(self.remaining_steps):
                parts.append(f"  [{i}] {step}")

        return "\n".join(parts)

    def record_hop(self, spin: "SpinOutput", ingested_facts: Optional[list[str]] = None):
        self.history.append(HistoryEntry(
            hop=self.hop_count,
            reasoning=spin.reasoning,
            step_emitted=spin.step,
            facts_received=ingested_facts or [],
            stop_reason=spin.stop_search,
            final_answer=spin.final_answer,
        ))

    def ingest_fact(self, fact_entry: str):
        self.spiral_memory.append(fact_entry)
        self.hop_count += 1

        redundancy = self._compute_redundancy(fact_entry)
        if redundancy > 0.85:
            self._redundant_count += 1
            delta_entropy = 0.0
        else:
            novelty = 1.0 - redundancy
            delta_entropy = -0.15 * novelty

        self.entropy = max(0.0, min(1.0, self.entropy + delta_entropy))
        self.entropy_history.append(self.entropy)

        if delta_entropy >= 0 or (len(self.entropy_history) >= 2 and
                                   abs(self.entropy_history[-1] - self.entropy_history[-2]) < 0.01):
            self.consecutive_stalled_spins += 1
        else:
            self.consecutive_stalled_spins = 0

    def _compute_redundancy(self, fact_entry: str) -> float:
        fact_text = re.sub(r'<fact\s+source=[\'"][^\'"]*[\'"]>\s*', '', fact_entry)
        fact_text = re.sub(r'\s*</fact>', '', fact_text)
        prior_texts = []
        for existing in self.spiral_memory[:-1]:
            cleaned = re.sub(r'<fact\s+source=[\'"][^\'"]*[\'"]>\s*', '', existing)
            cleaned = re.sub(r'\s*</fact>', '', cleaned)
            prior_texts.append(cleaned)
        return jaccard_redundancy(fact_text, prior_texts)

    def is_context_exceeded(self) -> bool:
        total_tokens = sum(len(f.split()) for f in self.spiral_memory)
        total_tokens += sum(len(s.split()) for s in self.remaining_steps)
        return total_tokens > self.context_budget

    def mark_step_resolved(self, step_idx: int = 0):
        if 0 <= step_idx < len(self.remaining_steps):
            self.remaining_steps.pop(step_idx)

    def update_confidence(self, delta: float):
        self.confidence = min(1.0, max(0.0, self.confidence + delta))


@dataclass
class SpinOutput:
    reasoning: str = ""
    step: Optional[str] = None
    stop_search: Optional[str] = None
    final_answer: Optional[str] = None
    entropic_collapse: bool = False

    @classmethod
    def parse(cls, text: str, use_xml: bool = True) -> "SpinOutput":
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        reasoning = think_match.group(1).strip() if think_match else ""

        if use_xml:
            step_match = re.search(r"<step>(.*?)</step>", text, re.DOTALL)
            stop_match = re.search(r"<stop_search>(.*?)</stop_search>", text, re.DOTALL)
            final_match = re.search(r"<final_answer>(.*?)</final_answer>", text, re.DOTALL)

            return cls(
                reasoning=reasoning,
                step=step_match.group(1).strip() if step_match else None,
                stop_search=stop_match.group(1).strip() if stop_match else None,
                final_answer=final_match.group(1).strip() if final_match else None,
            )
        else:
            retrieve_match = re.search(r"RETRIEVE:\s*(.*?)(?:\n|$)", text, re.DOTALL)
            stop_match = re.search(r"STOP:\s*(.*?)(?:\n|$)", text, re.DOTALL)
            answer_match = re.search(r"ANSWER:\s*(.*?)(?:\n|$)", text, re.DOTALL)

            return cls(
                reasoning=reasoning,
                step=retrieve_match.group(1).strip() if retrieve_match else None,
                stop_search=stop_match.group(1).strip() if stop_match else None,
                final_answer=answer_match.group(1).strip() if answer_match else None,
            )


class GravitationalCore:
    def __init__(
        self,
        llm_client,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 2048,
        confidence_threshold: float = 0.85,
        use_xml: bool = True,
    ):
        self.llm_client = llm_client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.confidence_threshold = confidence_threshold
        self.use_xml = use_xml
        self.state: Optional[GravitationalState] = None

    def initialize(self, question: str, max_hops: int = 15, context_budget: int = 8192):
        self.state = GravitationalState(
            goal_vector=question,
            max_hops=max_hops,
            context_budget=context_budget,
        )

    def spin(self) -> SpinOutput:
        if self.state is None:
            raise RuntimeError("GravitationalCore not initialized. Call .initialize(question) first.")

        if self.state.hop_count >= self.state.max_hops:
            return SpinOutput(
                reasoning="Max spiral depth reached. Force collapsing vortex.",
                final_answer=self._synthesize_fallback(),
            )

        if self.state.consecutive_stalled_spins >= self.state.entropy_stall_limit:
            return SpinOutput(
                reasoning=f"Entropy stalled for {self.state.entropy_stall_limit} consecutive spins. Attractor converged. Collapsing vortex.",
                stop_search=f"Entropy plateau detected at hop {self.state.hop_count}. No new information.",
                entropic_collapse=True,
            )

        if self.state.is_context_exceeded():
            return SpinOutput(
                reasoning="Context budget exceeded. Gating further ingestion. Collapsing vortex.",
                stop_search=f"Context budget ({self.state.context_budget} tokens) exceeded at hop {self.state.hop_count}.",
                entropic_collapse=True,
            )

        if self.state.confidence >= self.confidence_threshold:
            return SpinOutput(
                reasoning=f"Confidence {self.state.confidence:.2f} >= threshold {self.confidence_threshold}. Collapsing vortex.",
                stop_search=f"Confidence threshold met at hop {self.state.hop_count}.",
            )

        state_prompt = self.state.build_prompt()

        prompt = GRAVITATIONAL_CORE_PROMPT if self.use_xml else GRAVITATIONAL_CORE_PROMPT_PLAIN
        action_hint = "step / stop_search / final_answer" if self.use_xml else "RETRIEVE / STOP / ANSWER"

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Current VORTEX state:\n\n{state_prompt}\n\nEmit next action ({action_hint}):"},
        ]

        response = self.llm_client.chat_completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        content = response["choices"][0]["message"]["content"]
        output = SpinOutput.parse(content, use_xml=self.use_xml)

        if output.final_answer:
            pass
        elif output.stop_search:
            pass
        elif output.step:
            self.state.remaining_steps.append(output.step)

        return output

    def ingest_fact(self, condensed_fact: str, confidence_delta: float = 0.1):
        if self.state is None:
            return
        self.state.ingest_fact(condensed_fact)
        self.state.update_confidence(confidence_delta)

    def mark_step_resolved(self, step_idx: int = 0):
        if self.state is None:
            return
        self.state.mark_step_resolved(step_idx)
        if not self.state.remaining_steps:
            self.state.update_confidence(0.05)
            self.state.entropy = max(0.0, self.state.entropy - 0.1)

    def _synthesize_fallback(self) -> str:
        if self.state is None:
            return ""
        facts = [f.strip() for f in self.state.spiral_memory]
        return "\n".join(facts) if facts else "Insufficient evidence."
