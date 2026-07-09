# VORTEX Deployment Guide

> **Principle:** Same code, any machine. Default mode runs offline with zero keys.
>
> Two parallel tracks from Phase 1 onward — choose yours.

---

## Phase 0 — Smoke Test (any machine, zero deps)

**Runs on bare Python 3.10+ + numpy. No network, no GPU, no API keys.**

```bash
cd vortex-hrm
python test_smoke.py      # 17/17 tests
python scripts/demo.py     # synthetic corpus, offline mock LLM
```

**Purpose:** Validate architecture — entropy, gating, orchestration, collapse.

---

## Phase 1 — Choose Your Track

### Track A: Laptop (this machine — i5, 8 GB, no GPU)

| Spec | Value |
|------|-------|
| CPU | i5-1135G7 (4 cores) |
| RAM | 8 GB |
| GPU | Intel Iris Xe (1 GB, no CUDA) |
| Free disk | C: ~7 GB, D: ~38 GB |
| Verdict | **Средний ультрабук 2021.** Офис, код, маленькие ML-модели — норм. Для 7B+ на CPU — тяжко, но жить можно (~2-3 tok/s). VORTEX как раз про работу на таком железе. |

**Goal:** Install Ollama + 7B model, run 50 HotpotQA questions.

**Note on model size:** qwen2.5:0.5b (~398 MB) is **too small** for the XML-based planner contract. It pattern-matches format strings instead of executing logic — e.g. it copies `<stop_search>...</stop_search>` verbatim from the prompt. Minimum viable model: **qwen2.5:7b** (~4.7 GB, ~8 GB RAM required).

**Ollama на D: диск:**
- Модели храни на D::
  ```cmd
  setx OLLAMA_MODELS D:\ollama\models
  ```
  Затем перезапусти терминал и `ollama pull qwen2.5:7b`

```bash
# 1. Install Ollama from https://ollama.com  (~300 MB)

# 2. Pull 7B model (модель сохранится на D: если задан OLLAMA_MODELS)
ollama pull qwen2.5:7b       # ~4.7 GB, ~8 GB RAM required for CPU

# 3. Create venv
python -m venv .venv
.venv\Scripts\activate

# 4. Install lightweight deps (не путай с тяжёлым requirements.txt для Phase 3!)
pip install -r requirements-local.txt

# 5. Config already exists at configs/local.yaml (points to qwen2.5:7b)

# 6. Run with synthetic corpus (первый тест — без скачивания данных)
python scripts/run.py --config configs/local.yaml
```

**Expected performance (qwen2.5:7b, CPU, 4 cores):**

| Metric | Value |
|--------|-------|
| Tokens/sec | ~2-3 t/s |
| Time per spiral | ~10-15 s |
| Memory | ~6-8 GB RAM |
| Accuracy | Good XML contract compliance |

> **Note:** If RAM is too tight for 7B, try `qwen2.5:3b` (~2.1 GB) or `qwen2.5:1.5b` (~1.1 GB).
> The 0.5B model (`qwen2.5:0.5b`) is documented in `configs/local-tiny.yaml` but is NOT recommended — it cannot follow the XML planner contract.

### Track B: GPU Cluster (for reproduction of paper results)

**Hardware target:** GPU ≥ 8 GB VRAM, RAM ≥ 16 GB, Disk ≥ 20 GB.

```bash
pip install -r requirements.txt       # vllm, faiss-gpu, transformers, openai

# Create configs/gpu.yaml:
#   llm:
#     mode: openai
#     model: gpt-4o-mini
#     api_key: ${OPENAI_API_KEY}
#   engine:
#     max_spirals: 15
#     verbose: true

# Build FAISS index
python scripts/build_index.py \
    --chunks data/hotpotqa/chunks.json \
    --output data/hotpotqa/index \
    --model nomic-embed-text

# Run full benchmark (8 workers)
python scripts/batch_runner.py \
    --config configs/gpu.yaml \
    --questions data/hotpotqa/questions.json \
    --output results/hotpotqa \
    --workers 8

# Evaluate
python scripts/eval.py --predictions results/hotpotqa/predictions.jsonl
```

**Expected results (GPT-4o-mini, HotpotQA):**

| Method | LLM-Acc | Cont-Acc |
|--------|---------|----------|
| Naive RAG | 74.5 | 72.9 |
| A-RAG Full | 77.1 | 74.0 |
| VORTEX | ~77+ | ~74+ |

---

## Phase 2 — Production API Server

**Architecture:**
```
Client ──HTTP──► FastAPI ──► VORTEX Engine ──► vLLM (multi-GPU)
                              │
                              └──► FAISS index (sharded)
```

```bash
pip install fastapi uvicorn
uvicorn scripts.server:app --port 8000
curl -X POST http://localhost:8000/vortex/run \
  -H "Content-Type: application/json" \
  -d '{"question":"..."}'
```

---

## Resource Budget

| Phase | CPU | RAM | GPU | Disk | API Keys? | Offline? |
|-------|-----|-----|-----|------|-----------|----------|
| 0. Smoke | 1 core | 256 MB | — | 1 MB | No | ✅ Yes |
| 1A. Laptop (7B) | 4 cores | 8 GB | — | ~6 GB | No | ✅ Yes |
| 1B. GPU cluster | 8 cores | 16 GB | ≥8 GB | ~20 GB | Optional | 🟡 Partial |
| 2. Production | 16+ cores | 32 GB | ≥24 GB | ~100 GB | Yes | ❌ No |

**Requirements by track:**
- Phase 0–1A: `pip install -r requirements-local.txt` (numpy, pyyaml, requests — ~15 MB)
- Phase 1B–2: `pip install -r requirements.txt` (transformers, vllm, faiss — ~2 GB)

**Model requirements:**
- 0.5B models — **not suitable** for XML contract (pattern-match format, not logic)
- 1.5B–3B — partial compliance, test before committing
- 7B+ — full XML compliance, recommended

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Ollama OOM on 7B | Not enough RAM | Try `qwen2.5:3b` or `qwen2.5:1.5b` |
| Planner outputs "stop_search" immediately | Model too small (0.5B can't follow XML) | Upgrade to `qwen2.5:7b` |
| Planner loops infinitely | Entropy stall not triggered | Lower `entropy_stall_limit` to 2 |
| Executor returns empty facts | Corpus too small | Add more chunks to `data/` |
| Low accuracy | Using 0.5B vs 7B+ model | Normal — upgrade model for production |
| No installs, just testing | Fast arch check | `python test_smoke.py` — requires only stdlib |

---

## Files Created

| Phase | Files |
|-------|-------|
| 0 | — |
| 1A | `configs/local.yaml` (7B), `configs/local-tiny.yaml` (0.5B, experimental) |
| 1B | `configs/gpu.yaml`, `data/index/`, `results/` |
| 2 | `data/hotpotqa/` (full), `configs/prod.yaml` |
