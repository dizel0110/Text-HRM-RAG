---
marp: true
theme: uncover
class:
  - lead
  - invert
paginate: true
backgroundColor: #1a1a2e
color: #eee
---

<!-- _class: lead invert -->

# **VORTEX-HRM**
## Hierarchical Retrieval-Augmented Generation for Multi-Hop Question Answering

**Smiles-2026 Summer School — Project Track**

dizel0110 — July 2026

---

<!-- _class: invert -->

# Motivation

**Problem:** Multi-hop QA requires retrieving and reasoning over multiple documents. Standard RAG retrieves once — single-hop only.

**Goal:** An agentic RAG engine that:
- Decomposes complex questions into atomic sub-questions
- Retrieves evidence for each sub-question independently
- Converges on an answer when evidence is sufficient
- Runs **offline-first**, zero API keys, on any machine

---

# Architecture: VORTEX Engine

**VORTEX = V**ortical **O**ptimization of **R**etrieval and **T**okenized Information Flow **Ex**ecution

```
┌──────────────────────┐         ┌──────────────────────┐
│  Gravitational Core  │  step   │  Centrifugal         │
│  (Planner)           │────────►│  Ingestor            │
│  0 facts in weights  │◄────────│  (Executor)          │
│  Pure router         │  fact   │  auto-retrieve       │
└──────────────────────┘         └──────────────────────┘
```

---

# Gravitational Core (Planner)

**Planner:** `src/planner.py`

- **Fact-Free** — holds zero knowledge in weights
- **State per spiral:**
  - `goal_vector` — original question (immutable)
  - `spiral_memory` — condensed `<fact>` entries
  - `hop_history` — full chronological reasoning log
  - `confidence` / `entropy` — convergence metrics
  - `remaining_steps` — sub-questions pending

- **Termination:** emits `<final_answer>` or `<stop_search>` when confidence ≥ threshold or entropy stalls

---

# Centrifugal Ingestor (Executor)

**Executor:** `src/executor.py`

- **Chained retrieval pipeline** (no LLM tool selection):
  1. `keyword_search(query)` — lexical match, top-k chunks
  2. `chunk_read(id, adjacent=True)` — full text + neighbors
  3. LLM condensation → `<fact>` extraction

- **Tools available:**
  - `keyword_search` — narrow, exact match
  - `semantic_search` — medium, dense embedding
  - `chunk_read` — wide, + adjacent context

---

# Cyclic Spiral Flow

```
Spiral 1: Planner emits <step> → Executor retrieves → Fact returned
                  ↓
         State updated (confidence +0.05, entropy -0.15)
                  ↓
Spiral 2: Planner sees new fact → emits next <step> →
         Executor retrieves more evidence
                  ↓
         ... repeats until convergence ...
                  ↓
         <final_answer> or entropic collapse
```

---

# Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Fact-Free Synapses** | Planner uses 0% capacity for facts — 100% for routing |
| **Entropic Collapse** | Terminates when no new information (entropy plateau) |
| **Offline-First** | Default `mock` mode — no network, no keys, no downloads |
| **Same Code, Any Hardware** | Config-driven backend swap: mock → Ollama → OpenAI |

---

# LLM Backends

| Mode | Backend | Dependencies | API Key | Use Case |
|------|---------|-------------|---------|----------|
| `mock` | MockBackend | None | No | Smoke tests, validation |
| `ollama` | OllamaBackend | requests | No | Local CPU inference |
| `openai` | OpenAIBackend | openai | Yes | Production / cluster |

```python
VORTEXConfig(llm=LLMConfig(mode="mock"))           # offline default
VORTEXConfig(llm=LLMConfig(mode="ollama", ...))     # local laptop
VORTEXConfig(llm=LLMConfig(mode="openai", ...))     # cloud GPU
```

---

# Project Structure

```
Text-HRM-RAG/
├── vortex-hrm/
│   ├── src/
│   │   ├── core/config.py      # VORTEXConfig (typed, YAML)
│   │   ├── core/llm.py         # 3 backends (mock/ollama/openai)
│   │   ├── planner.py          # GravitationalCore
│   │   ├── executor.py         # CentrifugalIngestor
│   │   └── orchestrator.py     # VortexEngine (cyclic loop)
│   ├── configs/mock.yaml       # Offline (default)
│   │            local.yaml     # Ollama + qwen2.5:7b
│   │            gpu.yaml       # OpenAI (cluster)
│   └── scripts/run.py          # Config-driven runner
│              demo.py          # Synthetic demo
│              eval.py          # EM/F1/Contains metrics
│              batch_runner.py  # Evaluation with checkpoint
```

---

# Current Progress

| Component | Status |
|-----------|--------|
| VORTEXConfig (typed config) | ✅ Done |
| MockBackend (offline) | ✅ Done |
| OllamaBackend (local) | ✅ Done |
| OpenAIBackend (cloud) | ✅ Done |
| GravitationalCore (planner) | ✅ Done |
| CentrifugalIngestor (executor) | ✅ Done |
| VortexEngine (orchestrator) | ✅ Done |
| Smoke tests (17/17) | ✅ Pass |
| Synthetic demo | ✅ Works |
| HotpotQA benchmark | 🔄 Pending (model download) |
| EM/F1 evaluation | ✅ Script ready |

---

# Key Learnings

- **Model size matters** — ≤0.5B cannot follow XML contracts. Minimum viable: **7B**.
- **Chained pipeline > LLM tool selection** — fixed retrieval is simpler and cheaper.
- **Fact-free planning works** — planner routes correctly with zero factual knowledge.
- **Entropic collapse is reliable** — convergence detection terminates naturally.

**Work done by dizel0110 (solo):** Full VORTEX engine — config, 3 backends, planner, executor, orchestrator, 17 smoke tests, evaluation scripts, docs.

---

# Timeline & Next Steps

**Phase 1 — Pre-deadline** (Jul 7–12, intermediate submission)

| Date | Milestone | Status |
|------|-----------|--------|
| Jul 7–8 | Core engine + smoke tests | ✅ Done |
| Jul 9 | Presentation materials | ✅ Done |
| Jul 9–10 | Pull qwen2.5:7b, test run.py | 🔄 Pending |
| Jul 10–11 | HotpotQA benchmark (10–50 questions) | 🔄 Pending |
| Jul 11 | Finalize with real results | 🔄 Pending |
| **Jul 12** | **Submission deadline (23:00 MSK)** | 🔄 Pending |

**Phase 2 — Post-deadline** (with curator)

| Date | Milestone |
|------|-----------|
| Jul 13–14 | Architecture review with curator |
| Jul 15–18 | Full HotpotQA evaluation (500 questions) |
| Jul 19–25 | Iterate: retrieval precision, FAISS, prompts |
| Jul 26–27 | Final results, poster at Smiles-2026 |

---

<!-- _class: invert -->

# Evaluation Metrics

| Metric | Description |
|--------|-------------|
| **Exact Match (EM)** | Prediction exactly matches ground truth |
| **Token F1** | Token-level overlap between prediction and ground truth |
| **Contains** | Ground truth is substring of prediction |
| **Spirals** | Average vortex rotations per question |
| **Cost** | Total inference tokens / API cost |

---

# Deployment: Two Tracks

| Track | Machine | Model | Speed | Accuracy |
|-------|---------|-------|-------|----------|
| **A: Laptop** | i5, 8GB, CPU | qwen2.5:7b (Ollama) | ~2-3 tok/s | Good |
| **B: Cluster** | ≥8GB VRAM | GPT-4o-mini | ~10 s/QA | Paper-level (~77%) |

**Same code.** Only the config file changes.

---

<!-- _class: lead invert -->

# Thank You

**Repository:** [github.com/dizel0110/Text-HRM-RAG](https://github.com/dizel0110/Text-HRM-RAG)

**References:**
- A-RAG: [arXiv:2602.03442](https://arxiv.org/abs/2602.03442)
- HotpotQA: [huggingface.co/datasets/hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)

**Smiles-2026:** [smiles.skoltech.ru](https://smiles.skoltech.ru/)
