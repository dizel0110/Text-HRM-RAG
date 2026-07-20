# VORTEX-HRM Experiment Log

## Tag: v1.0-sspp (submitted)

### Run 1 — VORTEX + qwen2.5:7b (baseline match)
- **Date:** 2026-07-17
- **Hardware:** T4 GPU (Colab)
- **Config:** colab-gpu.yaml (max_spirals=15)
- **Results:** Contains 74% (37/50), No evidence 10% (5/50), Avg spirals 1.6, Avg time 59s/Q

### Run 2 — Baseline + qwen2.5:7b
- **Date:** 2026-07-17
- **Hardware:** T4 GPU (Colab)
- **Config:** baseline_rag.py + colab-gpu.yaml
- **Results:** Contains 68% (34/50), No evidence 24% (12/50), Avg time 3s/Q
- **Δ vs Run 1:** VORTEX +6%, hallucination 2.4× lower

### Run 3 — Ablation: max_spirals=1
- **Date:** 2026-07-17
- **Hardware:** T4 GPU (Colab)
- **Config:** colab-gpu.yaml (override max_spirals=1)
- **Results:** Contains 60% (30/50)

### Run 4 — Ablation: max_spirals=5
- **Date:** 2026-07-17
- **Hardware:** T4 GPU (Colab)
- **Results:** Contains 74% (37/50)
- **Finding:** Plateau reached at 5 spirals

### Run 5 — Ablation: max_spirals=10
- **Date:** 2026-07-17
- **Hardware:** T4 GPU (Colab)
- **Results:** Contains 70% (35/50) — within noise (±2% for 50 QA)

### Run 6 — VORTEX + mistral (7B v0.1)
- **Date:** 2026-07-18
- **Hardware:** T4 GPU (Colab)
- **Results:** Contains 56% (28/50), 6 timeouts (120s), Avg spirals 2.07, Avg time 73s/Q
- **Hypothesis:** Mistral too weak for multi-step planning in VORTEX

### Run 7 — Baseline + mistral
- **Date:** 2026-07-18
- **Hardware:** T4 GPU (Colab)
- **Results:** Contains 68% (34/50), 0% no evidence
- **Finding:** Mistral answers well from chunks but can't plan → VORTEX hurts (−12%)

### Run 8 — VORTEX + llama3.1:8b
- **Date:** 2026-07-19
- **Hardware:** T4 GPU (Colab)
- **Config:** colab-gpu.yaml (original sci-fi prompts)
- **Results:** Contains 62% (31/50), Avg spirals 3.4, Avg time 88s/Q, Total 73 min
- **Hypothesis:** Llama3.1 optimized for chat, struggles with sci-fi XML prompts

### Run 9 — Baseline + llama3.1:8b
- **Date:** 2026-07-19
- **Hardware:** CPU (Colab, no T4 available)
- **Results:** Contains 72% (36/50), No evidence 18% (9/50), Total 28 min
- **Finding:** Llama3.1 strongest baseline (72%) but VORTEX degrades it to 62%

---

## Tag: v1.2-sspp (in-progress)

### Run 11 — Cross-model Router: fast=llama3.1:8b, slow=qwen2.5:7b VORTEX
- **Date:** pending (Colab)
- **Hypothesis:** llama3.1 has stronger direct answers (72% baseline) but qwen2.5 excels at VORTEX spirals (74%) → combining via "Insufficient evidence." gate → >82%
- **Config:** `FAST_MODEL=llama3.1:8b`, `SLOW_MODEL=qwen2.5:7b`, `RUN_TYPE=router`
- **Expected range:** 82–88% (depends on llama3.1's fallback triggering reliability)
- **Status:** PENDING (ready for Colab)

### Run 12 (optional) — VORTEX + llama3.1:8b (simplified prompts)
- **Conditional:** If cross-model router succeeds, skip this. Otherwise, try plain-English prompts.
- **Status:** BACKUP
