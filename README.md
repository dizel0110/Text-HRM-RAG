# Text-HRM-RAG

> Hierarchical Retrieval-Augmented Generation with biomimetic spiral architecture.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/dizel0110/Text-HRM-RAG/blob/main/notebooks/vortex_benchmark_colab.ipynb)

Multi-hop question answering over HotpotQA — a planner-executor agentic RAG system inspired by [A-RAG (arXiv:2602.03442)](https://arxiv.org/abs/2602.03442).

**Design principle:** The planner holds zero facts in its weights (fact-free synapses). Every inference is a fresh structural computation from circulating state. The system terminates when entropy plateaus or confidence crosses threshold.

## Structure

| Path | What |
|------|------|
| [`vortex-hrm/`](vortex-hrm/) | Implementation: engine, tools, scripts |
| [`vortex_philosophy.md`](vortex_philosophy.md) | Biomimetic design manifesto |
| [`vortex_deployment.md`](vortex_deployment.md) | Dual-track deployment guide |
| [`vortex-hrm/test_smoke.py`](vortex-hrm/test_smoke.py) | Zero-dependency smoke test (17/17 ✅) |

## Quick start

```bash
cd vortex-hrm
python test_smoke.py        # 17 tests, no internet, no GPU
python scripts/demo.py       # synthetic multi-hop QA
python scripts/run.py        # config-driven runner (default: mock)
```

Dependencies: [`vortex-hrm/requirements.txt`](vortex-hrm/requirements.txt).

See [`vortex-hrm/README.md`](vortex-hrm/README.md) for full documentation.

## Tracks

| Track | Machine | LLM | Config |
|-------|---------|-----|--------|
| Offline mock | Any | — | `mode: mock` (default) |
| Laptop | CPU, 8 GB RAM | qwen2.5:7b via Ollama | `configs/local.yaml` |
| Colab (test) | CPU/GPU, ~25 мин | qwen2.5:7b via Ollama | `configs/local.yaml` |
| Colab (full) | T4 GPU, 12h session | qwen2.5:7b via Ollama | `configs/colab-gpu.yaml` |
| Cluster | GPU ≥ 8 GB VRAM | GPT-4o-mini | `configs/gpu.yaml` |

## Paper

This project has an associated paper accepted at Smiles-2026 / SSPP (Zapiski POMI).

- 📄 [`sspp-paper.pdf`](sspp-paper.pdf) — latest version

### Version history

Paper versions are tagged in git. Switch between them on GitHub via the tag dropdown, or directly compare:

```
# Compare any two versions on GitHub:
https://github.com/dizel0110/Text-HRM-RAG/compare/v1.0-sspp...v1.1-sspp
https://github.com/dizel0110/Text-HRM-RAG/compare/v1.1-sspp...main

# List all tags:
git tag -l "v*"
```

| Tag | Date | Summary |
|-----|------|---------|
| [`v1.0-sspp`](https://github.com/dizel0110/Text-HRM-RAG/releases/tag/v1.0-sspp) | 2026-07-18 | Initial SSPP submission. VORTEX 74% vs baseline 68% (+6%) on qwen2.5:7b. Ablation (spirals 1→5→15). 3 LLMs tested (qwen2.5, llama3.1, mistral). LLM sensitivity discussed. |
| [`v1.1-sspp`](https://github.com/dizel0110/Text-HRM-RAG/releases/tag/v1.1-sspp) | 2026-07-20 | **Fast/Slow Router** — dynamic gate between Naive RAG and VORTEX. 82% Contains on qwen2.5:7b (+14% vs baseline, +8% vs VORTEX alone). Uncertainty signal (``Insufficient evidence.'') as zero-training fallback trigger. Single-model router, 5× faster than VORTEX. Cross-model routing deferred to future work. |

Future tags will follow the `v<major>.<minor>-sspp` scheme.

## References

- A-RAG paper: [arXiv:2602.03442](https://arxiv.org/abs/2602.03442)
- A-RAG code: [github.com/Ayanami0730/arag](https://github.com/Ayanami0730/arag)
- MA-RAG: [arXiv:2505.20096](https://arxiv.org/abs/2505.20096)
- HotpotQA: [huggingface.co/datasets/hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)
