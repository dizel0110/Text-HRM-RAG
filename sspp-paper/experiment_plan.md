# Experiment Plan for SSPP Paper

Goal: build a coherent Results section showing VORTEX-HRM improves over naive RAG.

## ✅ Phase 1 — Baseline comparison (DONE)

| Метод | Contains | No evidence | Avg time |
|-------|----------|-------------|----------|
| VORTEX-HRM | **74%** | **10%** | 59s |
| Naive RAG | 68% | 24% | **3s** |
| **Δ** | **+6%** | **-14%** | slower |

**Вывод:** VORTEX превосходит baseline по полноте за счёт многошагового поиска.

## ⏳ Phase 2 — Ablation: max_spirals
max_spirals = 1, 5, 10, 15, 25 → график spirals vs accuracy.
Показывает плато: сколько витков достаточно.

## ⏳ Phase 3 — LLM swap
qwen2.5:7b → qwen2.5:14b (если влезет в T4 16GB).
Показывает, что архитектура не привязана к модели.

## ❌ Phase 4 — Error analysis + LLM Judge
Пересчитать Contains через LLM (убрать ложные misses из-за перефразирования).

## Что дальше
1. Ablation max_spirals (VORTEX, 50 Q, на T4: 5× ~20 мин = ~1.5 ч)
2. LLM swap
3. LLM Judge
