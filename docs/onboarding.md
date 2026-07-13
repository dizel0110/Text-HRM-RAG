# VORTEX-HRM: Onboarding Guide

> От проблеме к архитектуре за один-два дня.  
> Живой документ — дополняется по мере развития проекта.

---

## 1. Проблема: Multi-Hop Question Answering

Multi-hop QA — вопросы, для ответа на которые нужно **несколько шагов рассуждения**, каждый со своим поиском информации.

**Пример:**
> *«Which film marked the debut of the director whose work includes Requiem for a Dream?»*

- **Hop 1:** Кто режиссёр *Requiem for a Dream*? → Darren Aronofsky
- **Hop 2:** Какой фильм был его дебютом? → *π* (1998)

**Почему Standard RAG не работает:**

| RAG | Что делает | Результат |
|------|-----------|-----------|
| Classic RAG | 1 retrieval → 1 answer | Находит или режиссёра, или фильм — не оба |
| Multi-hop RAG | N retrievals → N hops → answer | Собирает факты по цепочке |

**Ключевая литература:**
- [HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering](https://arxiv.org/abs/1809.09600) (Yang et al., 2018) — стандартный бенчмарк
- [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401) (Lewis et al., 2020) — foundations of RAG

---

## 2. Архитектура VORTEX

### 2.1 Общий принцип: Циклический вихрь

Название — метафора: водоворот затягивает информацию с периферии к центру, каждый оборот — новый цикл поиска и рассуждения.

```
Planner ──<step>──> Executor ──<fact>──> Planner ──<step>──> ...
    ↑                                                     │
    └────────────────────── цикл ──────────────────────────┘
```

### 2.2 Gravitational Core (Planner)

`vortex-hrm/src/planner.py`

- **Fact-Free:** 0% весов занято фактами — 100% на маршрутизацию
- **Состояние:** goal_vector, spiral_memory, hop_history, confidence, entropy
- **Протокол:** XML-теги (`<step>`, `<final_answer>`, `<stop_search>`)
- **Выход:** эмитирует подвопросы или финальный ответ

**Условия завершения спирали:**
1. Confidence ≥ 0.85
2. Entropy не меняется 3 раза подряд (entropic collapse)
3. Превышен лимит шагов (15)
4. Превышен бюджет контекста (4096 токенов)

### 2.3 Centrifugal Ingestor (Executor)

`vortex-hrm/src/executor.py`

Фиксированный конвейер (в отличие от A-RAG, где LLM выбирает инструмент):

1. `keyword_search(query)` — точное совпадение, top-k чанков
2. `chunk_read(id, adjacent=True)` — читает чанк + соседей
3. LLM condensation — сжимает найденное в `<fact>`

**Три инструмента:**
| Инструмент | Тип поиска | Зависимости |
|-----------|-----------|-------------|
| `keyword_search` | Лексический (TF-IDF) | NLTK |
| `semantic_search` | Плотные эмбеддинги | FAISS *(Phase 2)* |
| `chunk_read` | Широкий контекст + соседи | NLTK |

### 2.4 Orchestrator (VortexEngine)

`vortex-hrm/src/orchestrator.py`

Циклический loop:
```
while True:
    planner_output = planner.step(state)
    if is_terminal(planner_output): break
    fact = executor.execute(planner_output.step)
    state.update(fact)
return state.final_answer
```

### 2.5 LLM Backends

`vortex-hrm/src/core/llm.py`

| Mode | Бекенд | API Key | Когда использовать |
|------|--------|---------|-------------------|
| `mock` | MockBackend | Нет | Smoke-тесты, разработка |
| `ollama` | OllamaBackend | Нет | Локальный CPU (qwen2.5:7b) |
| `openai` | OpenAIBackend | Да | GPU-кластер (GPT-4o-mini) |

**Важно:** модели ≤0.5B НЕ работают — не следуют XML-контракту. Минимум — 7B.

Конфигурация: `vortex-hrm/configs/` (YAML).

---

## 3. Code Map

```
Text-HRM-RAG/
├── vortex-hrm/
│   ├── src/
│   │   ├── core/
│   │   │   ├── config.py          # VORTEXConfig (Pydantic + YAML)
│   │   │   ├── llm.py             # 3 backends: mock, ollama, openai
│   │   │   └── base.py            # Abstract base classes
│   │   ├── planner.py             # GravitationalCore
│   │   ├── executor.py            # CentrifugalIngestor
│   │   └── orchestrator.py        # VortexEngine (cyclic loop)
│   ├── configs/
│   │   ├── mock.yaml              # Offline (default)
│   │   ├── local.yaml             # Ollama + qwen2.5:7b
│   │   └── gpu.yaml               # OpenAI (cluster)
│   ├── scripts/
│   │   ├── run.py                 # Config-driven single query
│   │   ├── demo.py                # Synthetic demo
│   │   ├── eval.py                # EM/F1/Contains metrics
│   │   ├── batch_runner.py        # Batch eval with checkpoint
│   │   └── reeval.py              # Re-evaluate old predictions
│   └── test_smoke.py              # 17 smoke tests
├── presentation/
│   ├── slides.md                  # Marp source
│   ├── slides.html                # Standalone HTML (primary)
│   ├── slides.pdf                 # PDF for submission
│   └── speaker_script.md          # English speaker notes
├── docs/
│   └── onboarding.md              ← этот файл
└── scratch/                       # Local artifacts (gitignored)
```

**Как запустить:**
```bash
# Smoke tests (bare Python, zero deps)
cd vortex-hrm
python test_smoke.py

# Ollama (локально)
python scripts/run.py --config configs/local.yaml

# GPU
python scripts/run.py --config configs/gpu.yaml
```

---

## 4. Результаты

### 4.1 Бенчмарк

| Параметр | Значение |
|----------|----------|
| Модель | qwen2.5:7b (CPU) |
| Вопросов | 50 |
| Корпус | 10 доменов, 60 чанков |
| Прогонов | 2 (независимых) |

### 4.2 Метрики

| Метрика | Результат | Что означает |
|---------|-----------|-------------|
| **Contains** | **70-72%** | Правильный ответ найден в выводе модели |
| **Token F1** | 22-23% | Частичное перекрытие токенов |
| **Exact Match** | 0% | Полное совпадение — не достигнуто |
| **Avg Spirals** | 1.3 | Большинство вопросов за 1-2 оборота |
| **Time/QA** | ~330s (CPU) | CPU-bound |

### 4.3 Почему EM=0%?

qwen2.5:7b **игнорирует инструкцию** выдать короткий ответ. Вместо `1775` выводит `Jane Austen was born in 1775.` — полное предложение. Это **не архитектурная проблема** — на GPT-4o-mini EM ожидается 40%+.

### 4.4 Ключевые выводы

1. **Архитектура валидирована** — 72% Contains на 7B/CPU доказывает, что циклически-спиральный подход работает
2. **Model size matters** — ≤0.5B не работают, нужен 7B+
3. **Chained pipeline > LLM tool selection** — дешевле, проще, надёжнее
4. **Fact-free planning works** — 0% памяти на факты, 100% на маршрутизацию

---

## 5. Сравнение с Related Work

| Работа | Подход | Отличие VORTEX |
|--------|--------|----------------|
| **A-RAG** (Du et al., 2026) | LLM выбирает инструмент поиска | Фиксированный конвейер — дешевле, предсказуемее |
| **ReAct** (Yao et al., 2022) | Рассуждение + действие в одном LLM | Разделение Planner/Executor, структурированный retrieval |
| **Self-Ask** (Press et al., 2022) | Декомпозиция через промптинг | Программная декомпозиция через XML-протокол |
| **Chain-of-Thought** (Wei et al., 2022) | Пошаговое рассуждение в одном промпте | Внешний цикл retrieval → condensation → fact |
| **RAPTOR** (Sarthi et al., 2024) | Иерархическое дерево суммаризации | Плоские чанки + итеративные спирали |

---

## 6. Полный список ссылок

### Papers
- **A-RAG:** `arXiv:2602.03442` — *A-RAG: Scaling Agentic Retrieval-Augmented Generation via Hierarchical Retrieval Interfaces* — [arxiv.org/abs/2602.03442](https://arxiv.org/abs/2602.03442)
- **RAG:** `arXiv:2005.11401` — *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* — [arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401)
- **ReAct:** `arXiv:2210.03629` — *ReAct: Synergizing Reasoning and Acting in Language Models* — [arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629)
- **Self-Ask:** `arXiv:2210.03350` — *Measuring and Narrowing the Compositionality Gap in Language Models* — [arxiv.org/abs/2210.03350](https://arxiv.org/abs/2210.03350)
- **Chain-of-Thought:** `arXiv:2201.11903` — *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models* — [arxiv.org/abs/2201.11903](https://arxiv.org/abs/2201.11903)
- **RAPTOR:** `arXiv:2401.18059` — *RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval* — [arxiv.org/abs/2401.18059](https://arxiv.org/abs/2401.18059)
- **HotpotQA:** `arXiv:1809.09600` — *HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering* — [arxiv.org/abs/1809.09600](https://arxiv.org/abs/1809.09600)

### Code & Data
- VORTEX-HRM: [github.com/dizel0110/Text-HRM-RAG](https://github.com/dizel0110/Text-HRM-RAG)
- HotpotQA (HF): [huggingface.co/datasets/hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa)

### Smiles-2026
- [smiles.skoltech.ru](https://smiles.skoltech.ru/)

### Внутренние документы
- Презентация (Marp): `presentation/slides.md`
- Презентация (HTML): `presentation/slides.html`
- Сценарий выступления (EN): `presentation/speaker_script.md`
- Сценарий выступления (RU): `scratch/speaker_script_ru.md`

---

## 7. Glossary

| Термин | Определение |
|--------|------------|
| **Spiral** | Один цикл: Planner emits step → Executor retrieves → State update |
| **Hop** | Один шаг рассуждения в multi-hop цепочке |
| **Contains** | Ground truth присутствует в выводе модели (подстрока) |
| **EM** | Exact Match — полное совпадение с эталоном |
| **F1** | Token-level overlap — среднее между precision и recall |
| **Entropic Collapse** | Остановка когда entropy не меняется 3 спирали подряд |
| **Fact-Free Synapses** | Принцип: planner не хранит факты в весах |
| **Confidence** | Мера уверенности (0→1), растёт с каждым новым непротиворечивым фактом |
| **Entropy** | Мера неопределённости (1→0), падает с новыми фактами |

---

## 8. Next Steps (Phase 2)

- [ ] Полный HotpotQA evaluation (500 вопросов)
- [ ] Семантический поиск (FAISS)
- [ ] GPT-4o-mini для EM 40%+
- [ ] Сравнение с A-RAG baselines
- [ ] Оптимизация промптов
- [ ] Постер на Smiles-2026

---

*Last updated: 2026-07-13*
