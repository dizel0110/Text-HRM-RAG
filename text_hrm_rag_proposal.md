# Text-HRM-RAG: Hierarchical Retrieval-Augmented Generation for Multi-Hop Text Question Answering

## Project Goal
Build an **Agentic RAG** system for **multi-hop question answering** over textual data (HotpotQA). The system uses a hierarchical two-level architecture:

1. **High-Level Planner** — decomposes complex multi-hop questions into a chain of atomic sub-questions (XML: `<think>` + `<step>` tags).
2. **Low-Level Executor** — answers each sub-question by autonomously orchestrating A-RAG style hierarchical retrieval tools (`keyword_search`, `semantic_search`, `chunk_read`).

## Proposed Approach

We follow the **[A-RAG](https://arxiv.org/abs/2602.03442)** paradigm: expose hierarchical retrieval interfaces directly to the LLM agent, giving it full autonomy over search strategy, execution order, and information consumption.

### VORTEX Architecture

> **VORTEX** = **Vo**rtical **O**ptimization of **R**etrieval and **T**okenized Information Flow **Ex**ecution Engine

Instead of a flat, linear ReAct loop or standard sequential RAG, our system treats data flow as a dynamic, cyclic spiral (vortex) centered around a compact, fact-free hierarchical reasoning engine.

#### VORTEX Core Engine

The system is a cyclical informational vortex where tokenized reasoning steps (`<think>`, `<step>`) control the **rotational depth** of retrieval:

```
                            ┌─────────────────────┐
                            │   VORTEX Core Loop   │
                            │  (up to N spirals)   │
                            └──────┬──────┬───────┘
                                   │      │
                    ┌──────────────▼┐    ┌▼──────────────┐
                    │ Gravitational │    │  Centrifugal  │
                    │  Core (7B)    │◄──►│  Ingestion    │
                    │ (0 facts)     │    │ (A-RAG tools) │
                    └──────────────┘    └───────┬────────┘
                                                │
                                      ┌─────────▼────────┐
                                      │  Document Corpus  │
                                      └──────────────────┘
```

- **Planner → Executor**: A `<step>` sub-question is launched from the core toward the factual perimeter.
- **Executor → Planner**: Condensed facts (`<fact>...</fact>`) are spun back inward, updating the planner's hidden state.
- **Spiral count** $N$: The number of structural hops before the vortex collapses via `<stop_search>` or `<final_answer>`.

#### The Gravitational Core (High-Level Planner)

The 7B model acts as a **factual vacuum** — it holds **zero facts** in its weights. Its capacity is used strictly for:

- **Structural orientation**: maintaining the multi-hop routing graph
- **Goal gradients**: tracking which sub-questions remain and how they connect to the original question
- **Spiral memory**: accumulating condensed fact signatures from prior executor spins

The core never stores or memorizes factual content. Each `<think>` block is a fresh structural computation based on the current spiral state, not a cached lookup.

```
Planner State (per spiral):
  goal_vector: str          # original question (immutable)
  spiral_memory: list[str]  # condensed <fact> entries from prior executor spins
  remaining_steps: list[str] # steps yet to execute
  hop_count: int            # current spiral depth
  confidence: float         # accumulated evidence score (0..1)
```

#### The Centrifugal Ingestion (Low-Level Executor)

The executor's three tools dynamically adjust the **radius of context ingestion**:

| Tool | Radius | Use Case |
|------|--------|----------|
| `keyword_search` | Narrow (exact entity match) | Known entities, names, IDs |
| `semantic_search` | Medium (dense embedding) | Conceptual / fuzzy matches |
| `chunk_read` | Wide (full context + adjacent) | Deep evidence gathering |

Raw text retrieved by these tools is **condensed** into isolated `<fact>` entries before being returned to the vortex core. The executor never dumps raw passages into the planner's context window — it extracts, filters, and compresses.

```
Executor Output Contract:
<fact source="chunk_42">
The author of "Book X" is Jane Doe.
</fact>
```

#### Vortex Termination

The loop collapses when any of these conditions are met:

1. **`<stop_search>`** — emitted by the planner when confidence > threshold (self-termination)
2. **`<final_answer>`** — emitted by the planner when all steps are resolved
3. **Max spirals** $N$ — hard upper bound (default 15) to prevent infinite loops

```
Example Collapse Sequence:
<think>
All sub-questions resolved. Confidence=0.94 > 0.85. Collapsing vortex.
</think>
<final_answer>
Jane Doe was born in 1925.
</final_answer>
```

### Architecture Diagram

```
                 ┌──────────────────────────────────────┐
                 │          VORTEX Engine                │
                 │  ┌─────────────┐   ┌──────────────┐   │
  Question ──────┼─►│ Gravitational│   │ Centrifugal  │   ├──────► Answer
                 │  │ Core        │◄──►│ Ingestion    │   │
                 │  │ (Planner)   │   │ (Executor)   │   │
                 │  └──────┬──────┘   └──────┬───────┘   │
                 │         │  condensed facts  │          │
                 │         │◄─────────────────│          │
                 │         │  sub-question     │          │
                 │         │─────────────────►│          │
                 └──────────────────────────────────────┘
```

### Data Contract

| Component | Input | Output |
|-----------|-------|--------|
| Planner (spin) | `condensed_facts: list[str]` | XML: `<think>...</think>` + `<step>Q</step>` / `<stop_search>` / `<final_answer>` |
| Executor (execute) | `sub_question: str` | `<fact source="id">text</fact>` (condensed) |
| VORTEX Engine | `question: str` | `final_answer: str` |

## Planned Experiments

1. **Baseline comparison** (HotpotQA):
   - Direct Answer (no retrieval)
   - Naive RAG (single-shot embedding retrieval)
   - A-RAG Full (hierarchical retrieval)
2. **Ablation**: Remove one tool at a time (w/o keyword, w/o semantic, w/o chunk read).
3. **Scaling**: Measure EM/F1 vs number of agent loops and token budget.
4. **Vortex depth**: Impact of spiral count $N$ on answer accuracy and cost.

## Expected Results

Based on A-RAG paper results on HotpotQA:

| Method | LLM-Acc | Cont-Acc |
|--------|---------|----------|
| Direct Answer | 45.4 | 40.7 |
| Naive RAG | 74.5 | 72.9 |
| **VORTEX (ours)** | **77.1+** | **74.0+** |

We expect the VORTEX cyclic architecture to match or exceed the monolithic A-RAG agent by enforcing strict separation of structural reasoning (planner) and factual retrieval (executor).

## Current Progress

- [x] Project skeleton (`vortex-hrm/`)
  - `src/planner.py` — GravitationalCore with spiral state management
  - `src/executor.py` — CentrifugalIngestor with condensed fact output
  - `src/orchestrator.py` — VortexEngine cyclic loop controller
  - `src/utils/metrics.py` — EM / F1 evaluation
  - `requirements.txt` — dependencies
- [x] This proposal document with VORTEX architectural breakdown

## Key References

- **A-RAG Paper**: [arXiv:2602.03442](https://arxiv.org/abs/2602.03442)
- **A-RAG Code**: [github.com/Ayanami0730/arag](https://github.com/Ayanami0730/arag)
- **HotpotQA Dataset**: [huggingface.co/datasets/hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)
- **MA-RAG**: [arXiv:2505.20096](https://arxiv.org/abs/2505.20096)
- **Qwen3-Embedding**: [huggingface.co/Qwen/Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
