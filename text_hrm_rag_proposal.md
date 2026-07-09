# Text-HRM-RAG: Hierarchical Retrieval-Augmented Generation for Multi-Hop Question Answering

## Project Goal

Build an **Agentic RAG** system for **multi-hop question answering** (HotpotQA) using a hierarchical planner-executor architecture with a cyclic spiral (vortex) control flow. The system runs **offline-first with zero API keys** and scales from a laptop (4-core CPU, 8 GB RAM) to a GPU cluster.

## Architecture

### VORTEX Engine

> **VORTEX** = **Vo**rtical **O**ptimization of **R**etrieval and **T**okenized Information Flow **Ex**ecution

A two-level recurrent attractor network. A fact-free planner (GravitationalCore) decomposes questions into sub-queries; an executor (CentrifugalIngestor) retrieves evidence via a chained tool pipeline. Each rotation (spiral) feeds condensed facts back to the planner, updating its state until entropy converges or confidence crosses threshold.

```
                        ┌───────────────────────────┐
                        │     VORTEX Engine          │
                        │ ┌─────────────┐ ┌────────┐ │
 Question ──────────────┼─►Gravitational│ │Centrif.│ ├──► Answer
                        │ │ Core        │◄┤Ingestor│ │
                        │ │ (0 facts)   │ │(tools) │ │
                        │ └──────┬──────┘ └───┬────┘ │
                        │        │ <step>      │      │
                        │        │────────────►│      │
                        │        │◄────────────│      │
                        │        │ <fact>      │      │
                        └───────────────────────────┘
```

### GravitationalCore (`src/planner.py`)

**Fact-Free reasoning axis.** Holds zero facts in weights — 100% of model capacity is used for structural routing, not memorization.

**State per spiral:**
- `goal_vector` — original question (immutable)
- `spiral_memory` — condensed `<fact>` entries from prior executor spins
- `hop_history` — full chronological log of reasoning, queries, and results
- `confidence` / `entropy` — accumulated evidence signal and remaining uncertainty
- `remaining_steps` — sub-questions yet to execute

**Termination conditions:**
1. `<final_answer>` — planner emits answer from accumulated facts
2. `<stop_search>` — confidence ≥ threshold or entropy plateau
3. Max hops — hard upper bound (default 15)
4. Context budget exceeded

### CentrifugalIngestor (`src/executor.py`)

**Chained retrieval pipeline** — no LLM tool selection. The executor automatically:

1. **keyword_search(query)** — lexical match, top-k chunk IDs
2. **chunk_read(id, adjacent=True)** — full chunk text + sliding window neighbors
3. **LLM condensation** — retrieved text fed to LLM only for `<fact>` extraction

Three tools available (pipeline uses keyword + chunk_read by default; semantic_search requires FAISS index):

| Tool | Radius | Use |
|------|--------|-----|
| `keyword_search` | Narrow (exact match) | Entities, names, IDs |
| `semantic_search` | Medium (dense embedding) | Conceptual matches |
| `chunk_read` | Wide (+ adjacent) | Deep evidence + context |

### Orchestration (`src/orchestrator.py`)

```
loop:
  spin_output = planner.spin()       # emit <step> or <final_answer>
  if final_answer: return answer
  if stop_search:   return synthesize
  
  ingestion = executor.ingest(step)  # auto-retrieve + condense
  for each fact:
    if not redundant:
      planner.ingest_fact(fact)      # update state
```

## Project Structure

```
Text-HRM-RAG/
├── vortex-hrm/
│   ├── src/
│   │   ├── core/
│   │   │   ├── config.py       # VORTEXConfig (typed, dict/YAML, no deps)
│   │   │   └── llm.py          # MockBackend / OllamaBackend / OpenAIBackend
│   │   ├── planner.py          # GravitationalCore, GravitationalState, HistoryEntry
│   │   ├── executor.py         # CentrifugalIngestor, chained retrieval
│   │   ├── orchestrator.py     # VortexEngine cyclic loop
│   │   └── utils/metrics.py    # EM + F1
│   ├── scripts/
│   │   ├── run.py              # Config-driven runner
│   │   ├── demo.py             # Synthetic corpus demo (mock LLM)
│   │   ├── eval.py             # EM/F1/Contains/LLM-as-judge
│   │   ├── batch_runner.py     # Offline evaluation with checkpoint resume
│   │   └── build_index.py      # FAISS index builder (Phase 3)
│   ├── configs/
│   │   ├── mock.yaml           # Offline (default, zero deps)
│   │   ├── local.yaml          # Ollama + qwen2.5:7b (recommended)
│   │   ├── local-tiny.yaml     # Ollama + qwen2.5:0.5b (experimental)
│   │   └── gpu.yaml            # OpenAI (cluster track)
│   ├── test_smoke.py           # 17 zero-dependency smoke tests
│   ├── requirements.txt        # Full deps (Phase 3 — vllm, faiss, transformers)
│   └── requirements-local.txt  # Light deps (Phase 2 — numpy, pyyaml, requests)
├── vortex_philosophy.md        # Biomimetic design manifesto
├── vortex_deployment.md        # Dual-track deployment guide
└── text_hrm_rag_proposal.md    # This document
```

## LLM Backends

Config-driven, same code on any hardware:

| Mode | Backend | Dependencies | API Key | Use Case |
|------|---------|-------------|---------|----------|
| `mock` | MockBackend | None | No | Smoke tests, architecture validation |
| `ollama` | OllamaBackend | requests or openai | No | Local CPU inference |
| `openai` | OpenAIBackend | openai | Yes | Production / GPU cluster |

**Model size constraint:** The planner uses an XML-based contract (`<think>`, `<step>`, `<final_answer>`, `<stop_search>`). Models ≤0.5B parameters **cannot** follow this contract — they pattern-match format strings instead of executing logic. Minimum viable model: **7B** (e.g. `qwen2.5:7b`). Smaller models (1.5B-3B) may partially work but should be tested.

```
VORTEXConfig(llm=LLMConfig(mode="mock"))           # offline
VORTEXConfig(llm=LLMConfig(mode="ollama", ...))     # local
VORTEXConfig(llm=LLMConfig(mode="openai", ...))     # cloud
```

## Design Principles

1. **Fact-Free Synapses** — Planner holds zero facts. Every inference is a fresh structural computation from circulating state.
2. **Entropic Collapse** — Vortex terminates when entropy plateaus (no new information) or confidence crosses threshold.
3. **Offline-First** — Default mode (`mock`) runs without network, API keys, or model downloads.
4. **Same Code, Any Hardware** — Config-driven swap between backends. Laptop today, cluster tomorrow.

## Evaluation

| Metric | Description |
|--------|-------------|
| Exact Match (EM) | Predicted answer exactly matches ground truth |
| Token F1 | Token-level overlap between prediction and ground truth |
| Contains | Ground truth is a substring of prediction |
| Spirals | Average number of vortex rotations per question |
| Cost (Phase 3) | Total inference tokens / API cost |

## References

- A-RAG: [arXiv:2602.03442](https://arxiv.org/abs/2602.03442)
- A-RAG code: [github.com/Ayanami0730/arag](https://github.com/Ayanami0730/arag)
- MA-RAG: [arXiv:2505.20096](https://arxiv.org/abs/2505.20096)
- HotpotQA: [huggingface.co/datasets/hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)
