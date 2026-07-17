# Experiment Plan for SSPP Paper

Goal: build a coherent Results section showing VORTEX-HRM improves over naive RAG.

## Phase 1 — Baseline comparison (сейчас)
| Что | Зачем | Статус |
|-----|-------|--------|
| VORTEX-HRM qwen2.5:7b (50 Q) | Основной результат | ✅ 74% Contains, 49 мин |
| Naive RAG qwen2.5:7b (50 Q) | Показать, что VORTEX лучше | ❌ нужно сделать |

Naive RAG = без цикла, один retrieve+answer. Показывает прирост от спиральной архитектуры.

## Phase 2 — Ablation: max_spirals
max_spirals = 1, 5, 10, 15, 25 — график spirals vs accuracy для статьи.
Показывает, что больше витков = лучше для multi-hop, но есть плато.

## Phase 3 — LLM swap
qwen2.5:7b → qwen2.5:14b (если влезет в T4 16GB) или phi-4.
Показывает, что архитектура не привязана к модели.

## Phase 4 — LLM Judge eval
Пересчитать Contains через LLM (уже есть в eval.py) — уберёт ложные misses из-за перефразирования (Beethoven hearing и др.).

## Порядок действий
1. **Сейчас**: Naive RAG baseline (1 запуск на T4, ~20 мин)
2. если прирост есть → пишем в статью
3. Ablation max_spirals
4. LLM swap
5. Финальный анализ + метрики в статью
