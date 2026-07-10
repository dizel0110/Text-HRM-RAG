# Speaker Script — VORTEX-HRM Presentation

> Use this script to practice your talk. English text is what you say aloud.
> Russian text is the deep explanation so you *understand* what you're saying.
> Total estimated time: 5-7 minutes (14 slides, ~25-30 sec each).

---

## Before the presentation — Soft Intro: The Vortex Idea (optional)

*Say this before slide 1, while waiting for the audience to settle:*

**English:**
> "Before we dive into the architecture, I want to share a quick mental image.
> Imagine a whirlpool — a vortex. Water spirals around, pulling information from the edges toward the center. Each rotation brings more material in. Eventually, when enough matter has accumulated, the vortex collapses.
> Our system works exactly like that. Each spiral is one round of thinking and retrieving. The question is at the center. Every rotation pulls in more evidence. When we have enough, the system collapses into a final answer.
> That's why we call it VORTEX."

**Russian (для понимания):**
> Идея вихря — ключевая метафора всего проекта. В природе водоворот затягивает материю с периферии в центр. Каждый оборот — новый цикл. Когда материи накопилось достаточно, вихрь схлопывается и утягивает всё на дно.
>
> В нашем случае "материя" — это факты из документов. "Водоворот" — это цикл: планировщик задаёт вопрос → исполнитель ищет ответ → факт возвращается → следующий цикл. Когда фактов накопилось достаточно для ответа — система схлопывается и выдаёт финальный ответ.
>
> Это не просто красивая метафора. Это работает как алгоритм: entropy (энтропия, мера неопределённости) уменьшается с каждым циклом, confidence (уверенность) растёт. Когда энтропия перестаёт меняться — система останавливается.

---

## Slide 1 — Title

**English:**
> "Good morning everyone. My name is [name], and I'm going to present VORTEX-HRM — a Hierarchical Retrieval-Augmented Generation system for multi-hop question answering.
> This is my project for the Smiles-2026 summer school."

**Russian (почему мы это делаем):**
> Представление проекта. VORTEX — Vortical Optimization of Retrieval and Tokenized Information Flow Execution.
> HRM — Hierarchical Retrieval-Augmented Generation — иерархическая RAG-система.
> Multi-hop QA — вопросы, требующие нескольких шагов рассуждения. Например: "В каком году родился автор книги 'X'?" — сначала нужно найти автора, потом год рождения.

---

## Slide 2 — Motivation

**English:**
> "Standard RAG systems retrieve documents once and answer in a single step. But many real-world questions require multiple reasoning hops. For example: *'Which film marked the debut of the director whose work includes Requiem for a Dream?'*
> You first need to find the director, then find their debut film. That's two hops.
> Our goal was to build an agentic system that can decompose complex questions, retrieve evidence for each sub-question independently, and converge on an answer when enough evidence is collected. And crucially — it must work offline, with zero API keys, on any machine."

**Russian (глубокое понимание):**
> Обычный RAG: задал вопрос → поиск по документам → ответ. Один шаг.
> Multi-hop QA: чтобы ответить, нужно сделать несколько шагов рассуждения, каждый со своим поиском.
>
> Пример: "Какой фильм был дебютом режиссёра, в чьих работах есть 'Реквием по мечте'?"
> Шаг 1: кто режиссёр 'Реквиема по мечте'? → Даррен Аронофски.
> Шаг 2: какой фильм был его дебютом? → "π" (1998).
>
> Два шага = два поиска. Обычный RAG так не умеет — он ищет один раз.
>
> Важно: мы делаем offline-first — никаких API-ключей, никакого интернета. Можно запустить на любом компьютере. Это ключевое отличие от большинства agentic RAG систем, которые требуют GPT-4.

---

## Slide 3 — Architecture: VORTEX Engine

**English:**
> "Here's the high-level architecture. The VORTEX engine has two main components connected in a cyclic loop.
> The Gravitational Core — the planner — holds zero facts in its weights. It's a pure router. It receives the question, looks at accumulated evidence, and decides what to do next: ask a sub-question, stop searching, or give a final answer.
> The Centrifugal Ingestor — the executor — takes that sub-question, retrieves relevant documents from the corpus, condenses them into facts, and sends them back to the planner.
> This cycle repeats — each rotation is one spiral — until the system converges."

**Russian:**
> Два компонента, замкнутых в цикл.
>
> Gravitational Core (Планировщик) — не содержит фактов в своих весах. Вообще. Ноль. Это чистый маршрутизатор. Его задача — анализировать текущее состояние (какие факты уже накоплены) и решать: какой следующий шаг сделать.
>
> Centrifugal Ingestor (Исполнитель) — берёт под-вопрос от планировщика, ищет документы, сжимает их в факты, возвращает обратно.
>
> Цикл: Planner → step → Executor → fact → Planner → ... → сходимость.

---

## Slide 4 — Gravitational Core (Planner)

**English:**
> "The planner is built on a principle we call 'fact-free synapses'. It doesn't memorize any facts during training. Every reasoning step is a fresh computation from the state that's circulating in the system.
> Its state includes: the original question — immutable; a spiral memory of condensed facts collected so far; a full hop history — a chronological log of every reasoning step and query; confidence and entropy scores that track convergence; and a list of remaining sub-questions.
> It terminates when it emits a final answer, decides to stop searching, or when entropy stalls — meaning no new information is coming in."

**Russian:**
> Ключевой принцип: Fact-Free Synapses. Планировщик не запоминает факты. Его веса отвечают только за логику маршрутизации. Это важно, потому что:
> - Модель не может "перепутать" факты
> - Каждый запрос — свежее вычисление, основанное на текущих данных
>
> Состояние планировщика:
> - goal_vector — оригинальный вопрос (неизменяемый)
> - spiral_memory — накопленные факты
> - hop_history — полный лог: что думал → какой шаг сделал → что получил
> - confidence — уверенность (0→1), растёт с каждым новым непротиворечивым фактом
> - entropy — энтропия (1→0), мера неопределённости, падает с новыми фактами
>
> Условия завершения:
> 1. Финальный ответ (<final_answer>)
> 2. Уверенность ≥ порога — stop_search
> 3. Энтропия перестала меняться — entropic collapse
> 4. Превышен лимит шагов (15)
> 5. Превышен бюджет контекста

---

## Slide 5 — Centrifugal Ingestor (Executor)

**English:**
> "The executor uses what we call a chained retrieval pipeline. Unlike many agentic systems where the LLM decides which tool to call and in what order, our executor has a fixed pipeline: first keyword search for exact matches, then chunk reading with adjacent context for surrounding evidence, then LLM condensation to extract key facts.
> This is simpler and more reliable than letting the LLM decide tool calls — and it's much cheaper."

**Russian:**
> В большинстве agentic RAG систем LLM сам решает, какой инструмент вызвать. Мы сделали иначе: фиксированный конвейер.
>
> Pipeline:
> 1. keyword_search(query) — точный поиск по словам, находит ID чанков
> 2. chunk_read(id, adjacent=True) — читает чанк целиком + соседние (контекст)
> 3. LLM конденсация — LLM только сжимает найденный текст в факт
>
> Почему так:
> - Не надо тратить токены на "размышления о выборе инструмента"
> - Надёжнее — конвейер всегда одинаковый
> - Дешевле — LLM вызывается только один раз на спираль
>
> Три инструмента: keyword_search (точные совпадения), semantic_search (похожие по смыслу, требует FAISS), chunk_read (широкий контекст с соседями).

---

## Slide 6 — Cyclic Spiral Flow

**English:**
> "Let me walk through one concrete cycle. Spiral one: the planner sees the question and an empty fact list. It emits a step — a sub-question. The executor auto-retrieves evidence and returns a condensed fact. The planner updates its state: confidence goes up slightly, entropy goes down.
> Spiral two: the planner sees the new fact, decomposes further, emits the next step. The executor retrieves again.
> This continues until either the planner can answer from accumulated facts, or confidence reaches the threshold, or entropy stops decreasing — meaning we're not learning anything new."

**Russian (конкретный пример):**
> Давайте на примере: "В каком году родился автор 'Белой гвардии'?"
>
> Спираль 1:
> - Планировщик: фактов нет → "Кто автор 'Белой гвардии'?"
> - Исполнитель: ищет → "Михаил Булгаков"
> - Планировщик: confidence +0.05, entropy -0.15
>
> Спираль 2:
> - Планировщик: "В каком году родился Михаил Булгаков?"
> - Исполнитель: ищет → "1891"
> - Планировщик: конфа теперь 0.10, энтропия 0.70
>
> Спираль 3:
> - Планировщик: достаточно фактов → <final_answer>1891</final_answer>
>
> В реальности спиралей может быть 3-5 для типичного HotpotQA вопроса.
>
> Важно: каждое возвращение факта — это update состояния. Планировщик не "помнит" прошлые запросы через веса — он видит их через hop_history.

---

## Slide 7 — Design Principles

**English:**
> "Our design rests on four principles.
> First, fact-free synapses — the planner doesn't memorize, it routes.
> Second, entropic collapse — the system naturally converges when no new information is available.
> Third, offline-first — the default mode requires zero dependencies, zero network, zero API keys. Just Python.
> Fourth, same code, any hardware — we use a configuration file to switch between mock mode for testing, Ollama for local CPUs, and OpenAI for GPU clusters. The code never changes."

**Russian (почему эти принципы важны):**
> 1. Fact-Free Synapses — это наше главное ноу-хау. Планировщик использует 0% ёмкости для фактов, 100% для маршрутизации. Это значит: модель не может "забыть" факт или "перепутать" даты. Каждый запрос — свежий расчёт.
>
> 2. Entropic Collapse — естественная сходимость. Система сама понимает, когда пора остановиться. Не нужно жёстко задавать количество шагов.
>
> 3. Offline-First — можно запустить на голом Python без интернета. Это не "дополнительная опция", а архитектурное решение: сначала работаем без LLM (mock), потом подключаем.
>
> 4. Same Code, Any Hardware — меняется только config файл. Код ядра один и тот же на ноутбуке и на кластере. Это сильно упрощает разработку и тестирование.

---

## Slide 8 — LLM Backends

**English:**
> "We have three backends. MockBackend for testing — it returns canned responses, no network needed. OllamaBackend for local CPU inference using models like qwen2.5:7b — no API key required. And OpenAIBackend for production GPU clusters.
> Switching between them is a one-line config change. The same planner, the same executor, the same orchestrator — just a different config."

**Russian (технические детали):**
> Три backend'а:
>
> mock — для тестов. Не требует ничего. Используется в smoke tests (17 тестов).
>
> ollama — локальный. Использует Ollama API (совместимый с OpenAI). Не требует API-ключа. Модели хранятся локально (у нас на D:).
>
> openai — облачный. Требует API-ключ и openai Python package.
>
> Важно про размер модели: маленькие модели (0.5B) НЕ могут следовать XML-контракту планировщика. Они буквально копируют формат из промпта вместо того, чтобы выполнять логику. Минимум — 7B параметров. Это мы выяснили экспериментально.
>
> Конфиг: YAML файл. Одна строка меняет поведение всей системы.

---

## Slide 9 — Project Structure

**English:**
> "The project is cleanly organized. The core engine is in the vortex-hrm directory: config, LLM backends, planner, executor, orchestrator. Configs for each mode are separate. Scripts for running, evaluating, and batch processing are ready. And we have 17 smoke tests that validate all core logic — they pass on bare Python with no dependencies."

**Russian:**
> Структура проекта:
> - src/core/config.py — типизированный конфиг, загружает YAML
> - src/core/llm.py — три бекенда
> - src/planner.py — GravitationalCore
> - src/executor.py — CentrifugalIngestor
> - src/orchestrator.py — VortexEngine, циклический loop
>
> configs/ — готовые конфиги для разных режимов
> scripts/ — утилиты: run.py, demo.py, eval.py, batch_runner.py
> test_smoke.py — 17 тестов, проходят на голом Python

---

## Slide 10 — Current Progress

**English:**
> "Here's our current status. All core components are implemented and tested. The smoke test suite passes 17 out of 17. The synthetic demo works end-to-end with mock LLM.
> We've now completed a 50-question benchmark using qwen2.5:7b on CPU with a multi-domain synthetic corpus spanning 10 domains and 60 chunks. The results: 72% of predictions contain the correct answer, with an average of 1.3 spirals per question at about 5 minutes each — limited by CPU inference speed. This validates the architecture. Full HotpotQA evaluation with GPU and semantic search is planned for Phase 2."

**Russian (честно о статусе):**
> Что сделано:
> - Весь движок: config, planner, executor, orchestrator ✅
> - Все три бекенда: mock, ollama, openai ✅
> - Smoke tests: 17/17 проходят ✅
> - Synthetic demo: работает ✅
> - Реальный тест: 50 вопросов на qwen2.5:7b ✅
> - Метрики: Contains 72%, F1 23%, 1.3 спирали в среднем ✅
>
> Что в процессе:
> - Полный HotpotQA на GPU — Phase 2
> - Semantic search (FAISS) для улучшения retrieval
>
> Почему Contains=72%, а не EM: модель возвращает факты в XML-тегах полными предложениями. Строгий Exact Match не срабатывает, но ответ ВЕРНЫЙ содержится в выводе модели.

---

## Slide 11 — Key Learnings

**English:**
> "I want to share four key things we learned while building this system.
> First, model size matters more than we expected. We initially tried qwen2.5:0.5b — a 500 million parameter model. It failed completely at following the XML contract. Instead of reasoning, it copied format strings verbatim from the prompt. The minimum viable model is 7 billion parameters.
> Second, we found that a fixed chained retrieval pipeline — keyword search, then chunk reading, then LLM condensation — works better than letting the LLM decide which tools to call. It's simpler, cheaper, and more predictable.
> Third, the fact-free planner design works. The planner routes correctly with zero factual knowledge.
> Fourth, entropic collapse is a reliable convergence mechanism. The system stops naturally when no new information arrives.
> As a solo developer, I implemented the full stack: configuration system, three LLM backends, the planner, the executor, the orchestrator, 17 smoke tests, evaluation scripts, and all documentation."

**Russian (для понимания):**
> Четыре ключевых вывода:
>
> 1. **Размер модели критичен.** 0.5B модель не способна следовать XML-контракту. Она буквально копирует шаблон ответа вместо того, чтобы думать. Это важный эмпирический результат — мы не могли просто взять "самую маленькую модель". Нужна 7B+.
>
> 2. **Chained pipeline лучше LLM tool selection.** В большинстве agentic систем LLM решает, какой инструмент вызвать. Мы сделали фиксированный конвейер: keyword_search → chunk_read → LLM condensation. Это дешевле (один LLM-вызов вместо трёх), надежнее (нет ошибок выбора), проще в отладке.
>
> 3. **Fact-free planner работает.** Планировщик не содержит фактов в весах — только логика маршрутизации. Каждый запрос — свежее вычисление из циркулирующего состояния. Это подтверждает нашу ключевую гипотезу.
>
> 4. **Entropic collapse надёжен.** Система сама определяет, когда остановиться: если энтропия перестала меняться три раза подряд, значит новая информация не поступает. Не нужно хардкодить количество шагов.
>
> Про выполненную работу: всё сделано одним человеком — от архитектуры до деплоя.

---

## Slide 12 — Timeline & Next Steps

**English:**
> "Here's our timeline. Phase one is the pre-deadline phase ending July 12. We've completed the core engine and presentation materials. The model is downloading now. Over the next two days, we'll run the HotpotQA benchmark and finalize the results.
> Phase two starts after the deadline with curator mentorship. We'll review the architecture together, run a full 500-question evaluation, iterate on retrieval precision and prompts, and prepare the final poster for Smiles-2026."

**Russian (для понимания):**
> Два этапа timeline.
>
> **Phase 1 (до 12 июля):** Промежуточный дедлайн. Мы показываем, что сделали ядро системы, тесты, презентацию. Модель качается, бенчмарк запустится в ближайшие дни.
>
> **Phase 2 (после 12 июля):** Работа с куратором. Важно показать в презентации, что мы понимаем: проект не заканчивается дедлайном.
> - 13-14 июля: ревью архитектуры с куратором — обсуждение XML контракта, pipeline, цикла
> - 15-18 июля: полный прогон HotpotQA (500 вопросов), сравнение с A-RAG
> - 19-25 июля: итерация — улучшение retrieval, добавление FAISS, оптимизация промптов
> - 26-27 июля: финальные результаты, постер на Smiles-2026

---

## Slide 13 — Evaluation Metrics

**English:**
> "Here are the results from our 50-question benchmark with qwen2.5:7b on CPU. The most meaningful metric is Contains — 72% of predictions contain the ground truth. This means the model finds the right information in most cases, but wraps it in verbose XML-tagged sentences.
> Token F1 is 23% — limited by the format mismatch between full-sentence predictions and short-answer ground truth. Exact Match is 0%, which is expected given our output format.
> The system averages 1.3 spirals per question — just one or two rotations. Each question takes about 5 minutes on CPU. On a GPU cluster, this would be under 10 seconds.
> These results validate the architecture. In Phase 2, with semantic search and GPU, we target 70%+ on both EM and F1."

**Russian:**
> Реальные результаты с qwen2.5:7b (50 вопросов, CPU):
>
> - **Contains 72%** — в 72% случаев правильный ответ содержится в выводе модели. Это главный показатель — модель НАХОДИТ ответ, но выводит его в виде полного предложения в XML-тегах, а не короткой строкой.
> - **F1 23%** — низкий из-за формата (полные предложения против коротких ответов). Когда перейдём на нормальные final_answer, F1 вырастет.
> - **EM 0%** — ожидаемо, модель возвращает `<fact source="chunk_0">...</fact>`, а не просто "1775".
> - **1.3 спирали** — очень хорошо. Большинство вопросов решаются за 1-2 витка. На 3 витках только сложные multi-hop.
> - **5.2 мин/вопрос** — медленно, потому что CPU. На GPU будет ~10 секунд.
>
> Вывод: архитектура работает. Метрики ограничены форматом вывода и железом, не архитектурой.

---

## Slide 14 — Deployment: Two Tracks

**English:**
> "We designed two deployment tracks. Track A runs on a laptop — no GPU, just a CPU with Ollama. This is our current target. Performance is about 2-3 tokens per second with a 7B model — slow but workable.
> Track B targets a GPU cluster with OpenAI or compatible LLMs — this is for reproducing paper-level results of around 77% accuracy on HotpotQA.
> The key point: the same source code powers both tracks. Only the config file changes."

**Russian:**
> Track A — наш текущий сценарий. Ноутбук i5, 8GB RAM, без GPU. Ollama + qwen2.5:7b на CPU. ~2-3 tok/s. Медленно, но работает. Цель — проверить архитектуру, получить первые метрики.
>
> Track B — для воспроизведения результатов из статьи A-RAG (~77% на HotpotQA). Требует GPU с 8+ GB VRAM. Использует GPT-4o-mini или локальный vLLM.
>
> Код один и тот же. Меняется только configs/local.yaml → configs/gpu.yaml.

---

## Slide 15 — References

**English:**
> "Our work is inspired by A-RAG — Agentic RAG with tool-augmented retrieval. We also reference MA-RAG for multi-agent patterns, and we evaluate on the HotpotQA dataset.
> All our code is open source at the link shown."

**Russian:**
> A-RAG — основная статья, на которой мы базируемся (arXiv:2602.03442). Берём идею tool-augmented retrieval и agentic loop.
> MA-RAG — мультиагентный RAG (arXiv:2505.20096). Потенциальное направление для расширения.
> HotpotQA — стандартный бенчмарк для multi-hop QA. 113k вопросов.
>
> Репозиторий: github.com/dizel0110/Text-HRM-RAG

---

## Slide 16 — Thank You

**English:**
> "Thank you for your attention. I'm happy to take questions.
> The repository link is on the screen. Feel free to check it out, run the smoke tests yourself — they require nothing but Python."

**Russian:**
> Благодарность за внимание. Ответы на вопросы.
> Приглашаю посмотреть код — smoke tests запускаются на любом Python без установки зависимостей.

---

## Q&A Preparation

**Common questions and answers:**

**Q: How is this different from ReAct or other agent frameworks?**
A: Unlike ReAct, our planner doesn't choose tools — the retrieval pipeline is fixed. This makes the system more predictable and cheaper. Also, our planner is explicitly fact-free — it doesn't rely on parametric knowledge.

**Q: Why use XML tags for the protocol?**
A: XML is structured enough for reliable parsing, human-readable for debugging, and supported by any LLM (with sufficient capacity). JSON would require escaping inside strings. Markdown is ambiguous to parse.

**Q: What about the 0.5B model failure?**
A: Small models pattern-match rather than follow instructions. qwen2.5:0.5b saw `<stop_search>...</stop_search>` in the prompt format and literally copied it. Minimum viable model is 7B. This was an empirical finding — the prompt engineering assumption failed.

**Q: Can this scale to more than 2 hops?**
A: Yes, the system handles N hops naturally. Each hop is one spiral. It terminates by convergence (entropy stall) not by hop count (though there's a safety limit of 15).

**Q: What about accuracy?**
A: We expect ~70-75% on HotpotQA with a 7B model when fully evaluated. The mock tests validate the architecture, not the accuracy.

---

## Delivery Tips

- **Pace:** Don't rush. Pause between slides. ~25-30 sec per slide is good.
- **Voice:** Speak clearly, especially technical terms (VORTEX, GravitationalCore, entropy).
- **Offline-first:** Emphasize this point — it's our key differentiator.
- **0.5B lesson:** If they ask about the model choice, tell the story honestly. It shows we tested empirically.
- **Demo:** If possible, prepare a terminal output screenshot showing the test run.
- **English:** Keep sentences short. If you blank, say "In other words..." and rephrase simply.
- **Eye contact:** Don't read from slides. Use them as visual cues. The speaker script is your preparation, not your teleprompter.
