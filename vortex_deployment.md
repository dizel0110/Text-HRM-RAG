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
| Free disk | ~2 GB (after reboot) |
| Verdict | **Средний ультрабук 2021.** Офис, код, маленькие ML-модели — норм. Для 7B+ моделей не предназначен. VORTEX как раз про работу на таком железе. |

**Goal:** Install Ollama + tiny model (0.5B), run 50 HotpotQA questions.

```bash
# 1. Install Ollama from https://ollama.com  (~300 MB)
# 2. Pull tiny model
ollama pull qwen2.5:0.5b       # ~398 MB

# 3. Create venv
python -m venv .venv
.venv\Scripts\activate
pip install numpy pyyaml

# 4. Create configs/local.yaml:
#     llm:
#       mode: ollama
#       model: qwen2.5:0.5b
#       base_url: http://localhost:11434/v1
#     engine:
#       max_spirals: 10
#       verbose: true

# 5. Download 50 HotpotQA questions
python -c "
import json, urllib.request
url = 'https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/main/hotpot_dev_fullwiki_1.json'
urllib.request.urlretrieve(url, 'data/sample.json')
"

# 6. Run
python scripts/run.py --config configs/local.yaml --questions data/sample.json
```

**Expected performance (qwen2.5:0.5b, CPU):**

| Metric | Value |
|--------|-------|
| Tokens/sec | ~12 t/s |
| Time per spiral | ~2 s |
| Memory | ~1.2 GB RAM |
| Accuracy vs paper | Lower (0.5B vs 7B) — expected |

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
| 1A. Laptop (0.5B) | 4 cores | 4 GB | — | ~2 GB | No | ✅ Yes |
| 1B. GPU cluster | 8 cores | 16 GB | ≥8 GB | ~20 GB | Optional | 🟡 Partial |
| 2. Production | 16+ cores | 32 GB | ≥24 GB | ~100 GB | Yes | ❌ No |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Ollama OOM on 1.5B | Not enough RAM | Use `qwen2.5:0.5b` instead |
| Planner loops infinitely | Entropy stall not triggered | Lower `entropy_stall_limit` to 2 |
| Executor returns empty facts | Corpus too small | Add more chunks to `data/` |
| Low accuracy compared to paper | Using 0.5B vs 7B+ model | Normal — upgrade model for production |
| Wants to run without any installs | Just testing architecture | `python test_smoke.py` — pure Python |

---

## Files Created

| Phase | Files |
|-------|-------|
| 0 | — |
| 1A | `configs/local.yaml`, `data/sample.json` |
| 1B | `configs/gpu.yaml`, `data/index/`, `results/` |
| 2 | `data/hotpotqa/` (full), `configs/prod.yaml` |
