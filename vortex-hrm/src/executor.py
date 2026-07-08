"""
VORTEX Centrifugal Ingestion layer.
Design philosophy: ../vortex_philosophy.md
"""

import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

CENTRIFUGAL_PROMPT = """You are the Centrifugal Ingestion layer of a VORTEX retrieval engine.
Your job is to extract condensed, isolated facts from the corpus using hierarchical retrieval tools.

[Available Tools]
- keyword_search(query): Exact lexical match. Use for known entities, names.
- semantic_search(query): Dense embedding similarity. Use for conceptual queries.
- chunk_read(chunk_id): Full content of a chunk (+ adjacent for context).

[Strategy]
1. Search (keyword or semantic) → get candidate chunk IDs
2. Read the most promising chunks in full
3. Extract only the relevant sentences as condensed facts
4. Never dump raw text — always condense

[Output Contract]
Return extraction results as synthesized analysis capped with either:

If more searching is needed:
<step>
Remaining sub-question to retrieve
</step>

If the sub-question is resolved:
<fact source="chunk_X">
The specific fact extracted from the corpus (1-2 sentences, no fluff).
</fact>

If the sub-question cannot be answered:
<fact source="none">
No evidence found for this sub-question.
</fact>

Rules:
- Each <fact> must be self-contained and cite its source chunk.
- Condense: extract only what is needed, not full paragraphs.
- Do NOT inject knowledge from training data — only from retrieved chunks."""


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
    ):
        self.llm_client = llm_client
        self.keyword_search = keyword_search
        self.semantic_search = semantic_search
        self.chunk_read = chunk_read
        self.model = model
        self.max_loops = max_loops
        self.temperature = temperature

    def ingest(self, sub_question: str) -> IngestionResult:
        self.chunk_read.reset()
        messages = [
            {"role": "system", "content": CENTRIFUGAL_PROMPT},
            {"role": "user", "content": f"Ingest evidence for: {sub_question}"},
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
                if result.remaining_step:
                    messages.append({"role": "user", "content": f"Further sub-step: {result.remaining_step}"})
                    result = self._continue_ingestion(result.remaining_step, messages)
                return result

            if result.remaining_step:
                messages.append({"role": "user", "content": f"Further sub-step: {result.remaining_step}"})
                result = self._continue_ingestion(result.remaining_step, messages)
                return result

            tool_call = self._parse_tool_call(content)
            if tool_call:
                tool_name, tool_args = tool_call
                observation = self._run_tool(tool_name, tool_args)
                messages.append({"role": "user", "content": f"Observation: {observation}"})

        return IngestionResult(facts=[Fact(source="none", text="Max ingestion loops reached without resolution.")])

    def _continue_ingestion(self, step: str, prior_messages: list) -> IngestionResult:
        messages = prior_messages[:2] + [
            {"role": "user", "content": f"Ingest evidence for nested sub-step: {step}"},
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

            tool_call = self._parse_tool_call(content)
            if tool_call:
                tool_name, tool_args = tool_call
                observation = self._run_tool(tool_name, tool_args)
                messages.append({"role": "user", "content": f"Observation: {observation}"})

        return IngestionResult(facts=[Fact(source="none", text="Nested ingestion exhausted.")])

    def _parse_tool_call(self, text: str) -> Optional[tuple[str, dict]]:
        func_match = re.search(
            r"(keyword_search|semantic_search|chunk_read)\((.*?)\)\s*$",
            text,
            re.MULTILINE | re.DOTALL,
        )
        if not func_match:
            return None

        tool_name = func_match.group(1)
        args_text = func_match.group(2).strip()

        try:
            if tool_name == "chunk_read":
                args_text = args_text.strip("\"'")
                return (tool_name, {"chunk_id": args_text})
            else:
                args_text = args_text.strip("\"'")
                return (tool_name, {"query": args_text})
        except Exception:
            return None

    def _run_tool(self, tool_name: str, args: dict) -> str:
        try:
            if tool_name == "keyword_search":
                results = self.keyword_search(args.get("query", ""))
                if not results:
                    return "No results found."
                snippets = []
                for chunk, score in results:
                    preview = chunk.text[:200].replace("\n", " ")
                    snippets.append(f"Chunk {chunk.chunk_id} (score={score:.2f}): {preview}...")
                return "\n".join(snippets)

            elif tool_name == "semantic_search":
                return "semantic_search requires a query embedding. Use keyword_search or chunk_read directly."

            elif tool_name == "chunk_read":
                text = self.chunk_read(args.get("chunk_id", ""))
                return text

            else:
                return f"Unknown tool: {tool_name}"

        except KeyError as e:
            return f"Error: chunk {e} not found."
        except Exception as e:
            return f"Error: {e}"
