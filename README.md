# Text-HRM-RAG

> Hierarchical Retrieval-Augmented Generation with biomimetic spiral architecture.

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
| Laptop | CPU, 8 GB RAM | qwen2.5:0.5b via Ollama | `configs/local.yaml` |
| Cluster | GPU ≥ 8 GB VRAM | GPT-4o-mini | `configs/gpu.yaml` |

## References

- A-RAG paper: [arXiv:2602.03442](https://arxiv.org/abs/2602.03442)
- A-RAG code: [github.com/Ayanami0730/arag](https://github.com/Ayanami0730/arag)
- MA-RAG: [arXiv:2505.20096](https://arxiv.org/abs/2505.20096)
- HotpotQA: [huggingface.co/datasets/hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)
