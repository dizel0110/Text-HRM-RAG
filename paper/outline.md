# VORTEX-HRM: Paper Outline

> Vortical Optimization of Retrieval and Tokenized Information Flow Execution
> Hierarchical Retrieval-Augmented Generation for Multi-Hop Question Answering

---

## Abstract (~150 words)

**What we did.** We present VORTEX-HRM, an agentic retrieval-augmented generation system for multi-hop question answering. Unlike prior work that uses LLM-driven tool selection (A-RAG) or flat ReAct loops, VORTEX separates planning from execution with a fact-free planner and a fixed chained retrieval pipeline.

**How it works.** A Gravitational Core (planner) holds zero factual knowledge in its weights — it is a pure structural router. It emits sub-questions via XML contract (`<step>`), which a Centrifugal Ingestor (executor) resolves through a deterministic pipeline: keyword search → chunk reading → LLM condensation. The cycle repeats (spirals) until convergence via entropic collapse.

**Results.** On a 50-question multi-domain benchmark (qwen2.5:7b CPU, 60 chunks, ×2 runs): Contains 70-72%, F1 22-23%, 1.3 avg spirals. EM=0% due to 7B model output formatting, not architecture — Phase 2 with GPT-4o-mini targets EM 40%+. The system is offline-first (zero API keys), config-driven, and validated across three backends (mock/ollama/openai).

> Already exists: slides (Metrics, Results sections), onboarding (Section 4), speaker script (S13 Evaluation Metrics).
> Need: condense to ~150 words, add comparison point.

---

## 1. Introduction (~0.5 page)

**Problem.** Multi-hop question answering requires retrieving and reasoning over multiple documents. Standard RAG retrieves once and answers in a single step — it cannot chain evidence across documents.

**Limitations of existing solutions.** (1) Agentic RAG systems (A-RAG) use LLM-driven tool selection, which wastes tokens and adds failure modes. (2) ReAct loops have no convergence signal — they terminate by hard step limit or LLM's arbitrary decision. (3) Tree-based retrieval (RAPTOR) requires expensive index-time summarization.

**Our contribution.** VORTEX replaces LLM tool selection with a fixed chained pipeline, replaces arbitrary termination with entropic collapse, and replaces parametric knowledge with fact-free routing. System is offline-first (zero API keys), runs on any hardware via config-driven backend swap.

**Results preview.** Contains 72% on 7B CPU with 1.3 avg spirals — validates cyclic-spiral architecture. Architecture is model-agnostic and scales with hardware.

> Already exists: slides (Motivation), onboarding (Section 1), speaker script (S1 Title, S2 Motivation).
> Need: concise problem statement, explicit contribution list (3-4 bullet points).

---

## 2. Related Work (~1 page)

### 2.1 Retrieval-Augmented Generation

- **RAG** (Lewis et al., 2020): Foundation.
- **Self-Ask** (Press et al., 2022): Decomposition via sub-question prompting. VORTEX replaces prompting with programmatic XML protocol.
- **Chain-of-Thought** (Wei et al., 2022): Stepwise reasoning. VORTEX externalizes reasoning steps into explicit retrieval cycles.

### 2.2 Agentic RAG

- **ReAct** (Yao et al., 2022): Reasoning+acting loop. VORTEX separates planner from executor with structured retrieval.
- **A-RAG** (Du et al., 2026): LLM-driven tool selection. VORTEX uses fixed chained pipeline — cheaper, more predictable.
- **GRASP** (arXiv:2605.16598, 2026): Graph agentic search with sub-agents. Different: uses graph structure, VORTEX uses flat chunks + spiral iteration.
- **HERA** (arXiv:2604.00901, 2026): Multi-agent evolving orchestration. Different: uses GPT-4o-mini + prompt evolution, VORTEX is offline-first with fixed pipeline.

### 2.3 Hierarchical Retrieval

- **RAPTOR** (Sarthi et al., 2024): Tree-structured retrieval via recursive summarization. VORTEX uses flat chunks with iterative spirals — no index-time overhead.

> Mostly exists: onboarding (Section 5 table), speaker script (deep understanding sections), vortex_philosophy.md (Section 2).
> Need: restructure as prose, add GRASP and HERA comparisons, formalize "why fixed pipeline is better" argument.

---

## 3. Method: VORTEX Architecture (~2 pages)

### 3.1 Design Principles

1. **Fact-Free Synapses** — planner holds zero facts in weights, 100% capacity for routing
2. **Entropic Collapse** — convergence via entropy plateau detection
3. **Offline-First** — mock mode with zero dependencies
4. **Same Code, Any Hardware** — config-driven backend swap

### 3.2 Gravitational Core (Planner)

- **Input:** question + spiral state (goal_vector, spiral_memory, hop_history, confidence, entropy)
- **Output:** XML tags — `<step>`, `<final_answer>`, `<stop_search>`
- **Fact-Free:** model weights encode routing logic only
- **State management:** `goal_vector` (immutable), `spiral_memory` (accumulated `<fact>` entries), `hop_history` (full reasoning log)

### 3.3 Centrifugal Ingestor (Executor)

- **Chained pipeline** (no LLM tool selection):
  1. `keyword_search(query)` — lexical match, top-k chunk IDs
  2. `chunk_read(id, adjacent=True)` — full text + neighbor chunks
  3. LLM condensation → structured `<fact>`
- **Three tools:** keyword_search (narrow), semantic_search (medium, Phase 2), chunk_read (wide)

### 3.4 Cyclic Spiral Flow

```
Spiral t=0: Planner(empty state) → <step>"Who directed..." → Executor retrieves → fact("Aronofsky") → state update
Spiral t=1: Planner(state+fact) → <step>"What was debut..." → Executor retrieves → fact("Pi, 1998") → state update
Spiral t=N: Planner(confidence≥τ) → <final_answer>
```

- **Confidence** increases monotonically with novel facts
- **Entropy** decreases monotonically
- **Gating:** Jaccard redundancy check before fact admission

### 3.5 Convergence and Termination

- **Primary:** Confidence ≥ τ (default 0.85)
- **Backup:** Entropy stall for κ=3 consecutive spirals (entropic collapse)
- **Safety:** Max hops (15), context budget (4096 tokens)
- **Guarantee:** Termination in O(N) where N ≤ max_spirals

### 3.6 LLM Backends

- **MockBackend:** canned responses, zero deps — for tests
- **OllamaBackend:** local CPU, no API key
- **OpenAIBackend:** production GPU cluster

> Mostly exists: slides (S2-8, Principles, Backends), onboarding (Section 2), vortex_philosophy.md (Sections 1-2), speaker script (S3-8).
> Need: unify into prose, add algorithm pseudocode, formalize confidence/entropy formulas, diagram description.

---

## 4. Experiments (~1.5 pages)

### 4.1 Setup

| Parameter | Value |
|-----------|-------|
| Model | qwen2.5:7b (CPU, ~2-3 tok/s) |
| Dataset | Multi-domain synthetic QA (60 chunks, 10 domains) |
| Questions | 50 |
| Runs | 2 (independent) |

### 4.2 Metrics

- **Contains:** ground truth is substring of prediction
- **Token F1:** token-level overlap
- **Exact Match:** strict equality
- **Spirals:** average cycles per question
- **Time:** wall-clock seconds per question

### 4.3 Results

| Metric | Run 1 | Run 2 | Avg |
|--------|-------|-------|-----|
| Contains | 72% | 70% | 71% |
| F1 | 23% | 22% | 22.5% |
| EM | 0% | 0% | 0% |
| Spirals | 1.3 | 1.3 | 1.3 |
| Time/QA | 324s | 336s | 330s |

### 4.4 Analysis

**Spiral distribution:** 64% of questions solved in 0-1 spirals (direct answer). 31% in 2 spirals. 5% in 3+ spirals. System converges efficiently — unnecessary cycles are rare.

**EM=0% analysis:** qwen2.5:7b ignores "output short answer" instruction. Outputs full sentences (e.g. "Jane Austen was born in 1775.") vs ground truth ("1775"). Not an architecture limitation — GPT-4o-mini in Phase 2 expected to reach EM 40%+.

**Model size finding:** ≤0.5B models cannot follow XML contract (qwen2.5:0.5b copied format strings verbatim). Minimum viable: 7B.

> Mostly exists: slides (S9-10 Progress, S12 Evaluation Metrics), onboarding (Section 4), speaker script (S10 Current Progress, S13 Evaluation Metrics, S11 Key Learnings).
> Need: spiral distribution table, explicit comparison to baselines (even if re-implemented), formalize "model size finding" as ablation.

---

## 5. Discussion (~0.5 page)

### 5.1 Limitations

- **7B model ceiling:** Contains 72% is promising but EM/F1 are low — format issue, not architecture
- **Small benchmark:** 50 questions — needs full HotpotQA (500+) for statistical significance
- **No semantic search yet:** FAISS integration planned
- **Single corpus:** not tested on large-scale heterogeneous corpora

### 5.2 Phase 2 Plans

- Full HotpotQA evaluation (500 questions, distractor setting)
- GPT-4o-mini backend → target EM 40%+
- Semantic search via FAISS
- Comparison with A-RAG baselines (reproduce their 77.1% setting)
- Architecture review with curator (Jul 13-14)

> Partially exists: slides (S11 Timeline), speaker script (S12 Timeline).
> Need: expand limitations, add "failure modes" subsection.

---

## 6. Conclusion (~0.25 page)

**Summary.** VORTEX demonstrates that a fact-free planner + fixed chained pipeline + entropic collapse is a viable architecture for multi-hop QA. Contains 72% on 7B CPU validates the approach.

**Broader impact.** Offline-first design enables multi-hop QA on hardware where it was previously impossible. Config-driven architecture scales from laptop to cluster without code changes.

> Exists: slides (Thank You), speaker script (S16 Thank You, Q&A).
> Need: condense to 3-4 sentences.

---

## References

1. A-RAG (Du et al., 2026) — arXiv:2602.03442
2. RAG (Lewis et al., 2020) — arXiv:2005.11401
3. ReAct (Yao et al., 2022) — arXiv:2210.03629
4. Self-Ask (Press et al., 2022) — arXiv:2210.03350
5. CoT (Wei et al., 2022) — arXiv:2201.11903
6. RAPTOR (Sarthi et al., 2024) — arXiv:2401.18059
7. HotpotQA (Yang et al., 2018) — arXiv:1809.09600
8. GRASP (2026) — arXiv:2605.16598 *(to add)*
9. HERA (2026) — arXiv:2604.00901 *(to add)*

> All 7 existing papers downloaded in papers/. Need GRASP and HERA.

---

## Appendix: Existing Content Mapping

| Section | Existing file(s) | Status |
|---------|-----------------|--------|
| Abstract | — | **Draft needed** |
| 1. Introduction | slides.md (Motivation), onboarding.md §1 | Good base |
| 2. Related Work | onboarding.md §5, speaker_script.md (deep understanding) | **Need prose** |
| 3.1 Design Principles | slides.md (Principles), vortex_philosophy.md §2 | Good |
| 3.2 Gravitational Core | slides.md (Planner), onboarding.md §2.2, vortex_philosophy.md §1 | Good |
| 3.3 Centrifugal Ingestor | slides.md (Executor), onboarding.md §2.3 | Good |
| 3.4 Cyclic Spiral Flow | slides.md (Spiral), onboarding.md §2.1, vortex_philosophy.md §2 | Good |
| 3.5 Convergence | vortex_philosophy.md §2.3 (formal), onboarding.md §2.2 | **Need formalization** |
| 3.6 Backends | slides.md (Backends), onboarding.md §2.5 | Good |
| 4. Experiments | slides.md (Progress, Metrics), onboarding.md §4 | Good base |
| 5. Discussion | slides.md (Timeline) | **Expand** |
| 6. Conclusion | slides.md (Thank You) | **Draft needed** |
| References | slides.md (References), onboarding.md §6 | Complete |

---

## Template Options

### Option A: NeurIPS Workshop (recommended)

```
\documentclass[workshop,dblblindworkshop]{neurips_2026}
```
- 4-6 page limit (varies by workshop)
- Standard ML audience
- Available: `neurips_2026.sty` online

### Option B: ACL / *ACL Workshop

```
\documentclass[11pt,a4paper]{article}
\usepackage{acl}
```
- 4-8 page limit
- NLP audience — natural for RAG/QA work
- Available: github.com/acl-org/acl-style-files

### Recommendation

If targeting Smiles-2026 → poster is enough, paper is secondary.
If targeting a workshop → ACL-related (e.g., Workshop on Retrieval-Augmented Generation or EMNLP workshop) fits better because RAG+QA is core NLP territory.
