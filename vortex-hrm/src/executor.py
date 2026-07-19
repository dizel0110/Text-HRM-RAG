"""
VORTEX Centrifugal Ingestion layer.
Design philosophy: ../vortex_philosophy.md
"""

import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

CENTRIFUGAL_PROMPT = """You extract facts from retrieved text.

Given a sub-question and a retrieved passage, extract relevant evidence as a <fact>.

If relevant evidence exists:
<fact source="chunk_X">
The specific fact (1-2 sentences).
</fact>

If NO relevant evidence:
<fact source="none">
No evidence found.
</fact>

If evidence is partial and needs refinement:
<step>
Refined sub-query for better retrieval.
</step>

Rules:
- Extract only what is needed, not full paragraphs.
- Do NOT use your own knowledge — only the provided text.
- Each <fact> must cite its source chunk."""


@dataclass
class Fact:
    source: str
    text: str
    confidence: float = 1.0
    redundant: bool = False

    def fingerprint(self) -> set[str]:
        return set(self.text.lower().split())

    def redundancy_against(self, prior_facts: list["Fact"]) -> float:
        new_tokens = self.fingerprint()
        if not new_tokens:
            return 1.0
        max_overlap = 0.0
        for existing in prior_facts:
            existing_tokens = existing.fingerprint()
            if not existing_tokens:
                continue
            intersection = len(new_tokens & existing_tokens)
            union = len(new_tokens | existing_tokens)
            overlap = intersection / union if union > 0 else 0.0
            if overlap > max_overlap:
                max_overlap = overlap
        return max_overlap


@dataclass
class IngestionResult:
    facts: list[Fact] = field(default_factory=list)
    remaining_step: Optional[str] = None
    step_to_resolve: int = 0

    @classmethod
    def parse(cls, text: str) -> "IngestionResult":
        facts = []
        for match in re.finditer(r'<fact\s+source="([^"]*)">(.*?)</fact>', text, re.DOTALL):
            facts.append(Fact(source=match.group(1), text=match.group(2).strip()))

        step_match = re.search(r"<step>(.*?)</step>", text, re.DOTALL)
        remaining_step = step_match.group(1).strip() if step_match else None

        return cls(facts=facts, remaining_step=remaining_step)


@dataclass
class Chunk:
    chunk_id: str
    text: str


class KeywordSearchTool:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks

    def __call__(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        keywords = set(re.findall(r"\w+", query.lower()))
        scored = []
        for chunk in self.chunks:
            chunk_text_lower = chunk.text.lower()
            count = sum(chunk_text_lower.count(kw) for kw in keywords)
            score = count * sum(len(kw) for kw in keywords)
            if score > 0:
                scored.append((chunk, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


class SemanticSearchTool:
    def __init__(self, chunks: list[Chunk], embeddings: np.ndarray):
        self.chunks = chunks
        self.embeddings = embeddings

    def __call__(self, query_embedding: np.ndarray, top_k: int = 5) -> list[tuple[Chunk, float]]:
        scores = np.dot(self.embeddings, query_embedding)
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[i], float(scores[i])) for i in top_indices]


class ChunkReadTool:
    def __init__(self, chunks: list[Chunk]):
        self.chunks_map = {c.chunk_id: c for c in chunks}
        self.seen_ids: set[str] = set()

    def __call__(self, chunk_id: str, read_adjacent: bool = False) -> str:
        if chunk_id in self.seen_ids:
            return f"[Already read] {self.chunks_map[chunk_id].text}"

        self.seen_ids.add(chunk_id)
        result = self.chunks_map[chunk_id].text

        if read_adjacent:
            chunk_ids = sorted(self.chunks_map.keys(), key=lambda x: int(x) if x.isdigit() else 0)
            try:
                idx = chunk_ids.index(chunk_id)
                for offset in [-1, 1]:
                    adj_idx = idx + offset
                    if 0 <= adj_idx < len(chunk_ids):
                        adj_id = chunk_ids[adj_idx]
                        if adj_id not in self.seen_ids:
                            self.seen_ids.add(adj_id)
                            result += f"\n--- Adjacent chunk {adj_id} ---\n{self.chunks_map[adj_id].text}"
            except ValueError:
                pass

        return result

    def reset(self):
        self.seen_ids.clear()


class CentrifugalIngestor:
    def __init__(
        self,
        llm_client,
        keyword_search: KeywordSearchTool,
        semantic_search: SemanticSearchTool,
        chunk_read: ChunkReadTool,
        model: str = "gpt-4o-mini",
        max_loops: int = 10,
        temperature: float = 0.0,
        top_k_retrieve: int = 3,
    ):
        self.llm_client = llm_client
        self.keyword_search = keyword_search
        self.semantic_search = semantic_search
        self.chunk_read = chunk_read
        self.model = model
        self.max_loops = max_loops
        self.temperature = temperature
        self.top_k_retrieve = top_k_retrieve

    def _auto_retrieve(self, query: str) -> str:
        results = self.keyword_search(query, top_k=self.top_k_retrieve)
        if not results:
            return ""

        seen = set()
        passages = []
        for chunk, _ in results:
            if chunk.chunk_id in seen:
                continue
            seen.add(chunk.chunk_id)
            text = self.chunk_read(chunk.chunk_id, read_adjacent=True)
            passages.append(f"[Chunk {chunk.chunk_id}]\n{text}")

        return "\n\n".join(passages)

    def ingest(self, sub_question: str) -> IngestionResult:
        self.chunk_read.reset()
        retrieved = self._auto_retrieve(sub_question)

        if not retrieved:
            return IngestionResult(facts=[Fact(source="none", text="No evidence found in corpus for this sub-question.")])

        messages = [
            {"role": "system", "content": CENTRIFUGAL_PROMPT},
            {"role": "user", "content": f"Sub-question: {sub_question}\n\nRetrieved text:\n{retrieved}\n\nCondense the relevant evidence into <fact> entries."},
        ]

        for turn in range(self.max_loops):
            response = self.llm_client.chat_completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=4096,
            )

            content = response["choices"][0]["message"]["content"]
            messages.append({"role": "assistant", "content": content})

            result = IngestionResult.parse(content)
            if result.facts:
                return result

            if result.remaining_step:
                new_retrieved = self._auto_retrieve(result.remaining_step)
                if new_retrieved:
                    messages.append({"role": "user", "content": f"Additional retrieval for refined query:\n{new_retrieved}"})
                    continue

            return IngestionResult(facts=[Fact(source="none", text=f"No relevant facts extractable after {turn + 1} turns.")])

        return IngestionResult(facts=[Fact(source="none", text="Max ingestion loops reached without resolution.")])
