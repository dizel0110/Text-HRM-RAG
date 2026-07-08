# VORTEX-HRM

> **VORTEX** — *Vortical Optimization of Retrieval and Tokenized Information Flow Execution*
>
> **Offline-first, zero API keys, same code on any machine.**
>
> **Design manifesto:** [`vortex_philosophy.md`](../vortex_philosophy.md)

Hierarchical (Planner + Executor) agentic RAG for multi-hop QA, inspired by [A-RAG](https://arxiv.org/abs/2602.03442). The planner is a fact-free gravitational core; the executor performs centrifugal ingestion via `keyword_search`, `semantic_search`, `chunk_read`.

## Quick start (any machine, zero deps)

```bash
python test_smoke.py      # 17/17 tests — validates all core logic
python scripts/demo.py     # synthetic corpus, offline mock LLM
```

No GPU. No network. No API keys. Just Python 3.10+ and numpy.

## Choose your track

| Track | Machine | LLM | Time | Accuracy |
|-------|---------|-----|------|----------|
| **A: Laptop** | i5, 8 GB, no GPU | qwen2.5:0.5b via Ollama | ~2 min/QA | Lower (expected) |
| **B: GPU cluster** | ≥8 GB VRAM, ≥16 GB RAM | GPT-4o-mini | ~10 s/QA | Paper-level (~77%) |

Same `VORTEXConfig`, same source code. Only the config file changes.

```python
# Track A — offline mock (no install)
VORTEXConfig(llm=LLMConfig(mode="mock"))

# Track A — local Ollama
VORTEXConfig(llm=LLMConfig(mode="ollama", model="qwen2.5:0.5b"))

# Track B — cloud OpenAI
VORTEXConfig(llm=LLMConfig(mode="openai", model="gpt-4o-mini", api_key="..."))
```

See [`vortex_deployment.md`](../vortex_deployment.md) for full walkthrough.

## Project structure

```
vortex-hrm/
├── src/
│   ├── core/
│   │   ├── config.py        # VORTEXConfig — typed, dict/YAML, no deps
│   │   ├── llm.py           # MockBackend / OllamaBackend / OpenAIBackend
│   │   └── __init__.py
│   ├── planner.py           # GravitationalCore (0-fact router)
│   ├── executor.py          # CentrifugalIngestor (A-RAG tools)
│   ├── orchestrator.py      # VortexEngine (cyclic attractor loop)
│   └── utils/metrics.py     # EM + F1
├── scripts/
│   ├── demo.py              # End-to-end demo with synthetic corpus
│   ├── run.py               # Config-driven runner (to be written)
│   ├── build_index.py       # FAISS index builder (Phase 2+)
│   ├── batch_runner.py      # Offline evaluation (Phase 2+)
│   └── eval.py              # LLM-as-judge + metrics (Phase 2+)
├── test_smoke.py            # 17 zero-dependency smoke tests
├── requirements.txt         # Full dependencies (cluster track)
└── vortex_deployment.md     # Dual-track deployment guide
```

## Design principles

1. **Fact-Free Synapses** — The planner holds zero facts in weights. Every inference is a fresh structural computation from circulating state.
2. **Entropic Collapse** — The vortex terminates when entropy plateaus (no new information) or confidence crosses the threshold.
3. **Offline-First** — Default mode (`mock`) runs without network, API keys, or model downloads. Add backends as the machine allows.
4. **Same Code, Any Hardware** — Config-driven swap between mock/Ollama/OpenAI backends. Laptop today, cluster tomorrow.

## Key links

- A-RAG paper: [arXiv:2602.03442](https://arxiv.org/abs/2602.03442)
- A-RAG code: [github.com/Ayanami0730/arag](https://github.com/Ayanami0730/arag)
- HotpotQA: [huggingface.co/datasets/hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)
- Philosophy: [`vortex_philosophy.md`](../vortex_philosophy.md)
