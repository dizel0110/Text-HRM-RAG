# Paper History

## 2026-07-13 — LaTeX project bootstrap

### Papers downloaded

```bash
python scripts/download_papers.py
```

All 9 papers downloaded to `papers/` (gitignored):

| # | Paper | arXiv | File |
|---|-------|-------|------|
| 1 | A-RAG (Du et al., 2026) | 2602.03442 | `papers/2602.03442v1.pdf` |
| 2 | RAG (Lewis et al., 2020) | 2005.11401 | `papers/2005.11401v4.pdf` |
| 3 | ReAct (Yao et al., 2022) | 2210.03629 | `papers/2210.03629v3.pdf` |
| 4 | Self-Ask (Press et al., 2022) | 2210.03350 | `papers/2210.03350v1.pdf` |
| 5 | CoT (Wei et al., 2022) | 2201.11903 | `papers/2201.11903v6.pdf` |
| 6 | RAPTOR (Sarthi et al., 2024) | 2401.18059 | `papers/2401.18059v1.pdf` |
| 7 | HotpotQA (Yang et al., 2018) | 1809.09600 | `papers/1809.09600v3.pdf` |
| 8 | GRASP (2026) | 2605.16598 | `papers/2605.16598v1.pdf` |
| 9 | HERA (2026) | 2604.00901 | `papers/2604.00901v1.pdf` |

### Files created

| File | Purpose |
|------|---------|
| `paper/outline.md` | Section-by-section paper plan with content mapping |
| `paper/sspp-paper.tex` | SSPP proceedings paper (4–6 pp, NeurIPS workshop style) |
| `paper/poster.tex` | A0 portrait poster (3-column, dark theme) |
| `paper/neurips_2026.sty` | Official NeurIPS 2026 style file (workshop with `dblblindworkshop` option) |
| `paper/refs.bib` | 9 BibTeX references |
| `paper/figs/architecture.py` | Matplotlib diagram generator for Vortex architecture |
| `paper/Makefile` | Build targets: `make paper`, `make poster`, `make clean` |
| `paper/HISTORY.md` | This file |

### Compilation

LaTeX distribution installed via Scoop:

```powershell
scoop install latex
# Installs MiKTeX 25.12 Portable to %USERPROFILE%\scoop\apps\latex\current\
```

Initial fix required: `\documentclass{dblblindworkshop}{neurips_2026}` was invalid.
Correct form:

```latex
\documentclass{article}
\usepackage[dblblindworkshop]{neurips_2026}
```

Compilation:

```powershell
pdflatex -interaction=nonstopmode sspp-paper.tex
pdflatex -interaction=nonstopmode poster.tex
```

Output:

| PDF | Pages | Size |
|-----|-------|------|
| `paper/sspp-paper.pdf` | 3 | 82 KB |
| `paper/poster.pdf` | 1 | 143 KB |

### Online API attempts (failed)

- `latexonline.cc` — 404 on POST `/compile`
- `texlive.net` — "Bad form type"
- Conclusion: local MiKTeX via Scoop is the reliable path

## 2026-07-16 — Adapted to Zapiski POMI template (SSPP OpenReview)

### Context

Smiles-2026 organizers announced paper submission via OpenReview:
- Platform: https://openreview.net/group?id=smiles.skoltech.ru/SSPP/2026
- Template: Zapiski POMI (https://github.com/madrugado/template-zapiski)
- Deadline: August 2, 2026 (21:00 MSK)
- Requirements: ≤10 pp, not anonymized, list authors + mentor, Contribution section

### Changes

- `sspp-paper.tex` fully rewritten from `article`+`neurips_2026.sty` to `\documentclass{zapiski}`
- Template files downloaded: `zapiski.cls`, `template.tex`
- `refs.bib` replaced by inline `thebibliography` environment (template requirement)
- Author metadata: real name (Valentin Malykh as mentor), GitHub handle, DOI-style formatting
- Added Acknowledgments (mentor credit) and Contribution sections
- Removed unused build artifacts

### Compilation

```powershell
pdflatex -interaction=nonstopmode sspp-paper.tex
```

| PDF | Pages | Size |
|-----|-------|------|
| `paper/sspp-paper.pdf` | 5 | 95 KB |

### Known issues

- T2A (Cyrillic) not available in basic MiKTeX — Russian abstract after `\end{document}` included as comment
- Deadline discrepancy: OpenReview shows Jul 22, email says Aug 2 — to clarify with organizers

## 2026-07-16 — GPU benchmarking infrastructure plan

### Context

Yandex DataSphere credentials received (5M units limit), but captcha blocks automated access.
Decision: start with Google Colab (free, instant), keep DataSphere as fallback.

### Platform comparison

| Feature | Google Colab | Kaggle | Yandex DataSphere |
|---------|-------------|--------|-------------------|
| Free GPU | T4 (sometimes V100/A100) | P100 / T4, 30h/week | 5M units (school allocation) |
| Session limit | 12h (~4-6h without Pro) | 9h max | until units run out |
| Auto-shutdown | **yes** (~4h idle) | **yes** (~1h idle) | configurable |
| Install ollama | ✅ `!curl ...` | ✅ `!curl ...` | ✅ via Docker/job |
| Save results | Google Drive | Kaggle Datasets | built-in storage |
| Reliability | medium (drops sessions) | medium | high (managed cloud) |
| Setup time | 5 min | 5 min | 30 min (+ captcha/CLI) |

### Strategy

1. **Primary**: Google Colab — instant setup, public notebook, checkpoint to Google Drive
2. **Fallback**: Yandex DataSphere — 5M units, g1.1 V100 for longer runs
3. **Checkpoint design**: serialize results as JSON every N questions → resume on reconnect

### Google Colab notebook design

File: `notebooks/vortex_benchmark_colab.ipynb`

Structure:
1. Mount Google Drive (persistent storage)
2. Clone `dizel0110/Text-HRM-RAG` (public repo, no token)
3. Install ollama + pull `qwen2.5:7b`
4. Run benchmark in batches of 10 questions
5. After each batch: save `results_checkpoint.json` to Drive
6. On restart: detect existing checkpoint → skip completed → resume from next
7. Final: aggregate all checkpoints → full report

Badge: `[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](...)`

### Final colab-notebook design (v2 — auto-push)

Notebook: `notebooks/vortex_benchmark_colab.ipynb`

**Workflow (для пользователя):**
1. Создать GitHub token (классический, scope `repo`) → сохранить в Colab (🔑 Secrets → `GITHUB_TOKEN`)
2. Открыть [ноутбук](https://colab.research.google.com/github/dizel0110/Text-HRM-RAG/blob/main/notebooks/vortex_benchmark_colab.ipynb) → Run All
3. Результаты автоматом сохраняются в `notebooks/colab_runs/<timestamp>/` и пушатся на GitHub
4. Пользователь пишет мне: «результат в колабе»
5. Я захожу в репо, вижу метрики, предлагаю следующий эксперимент

**Workflow (для меня):**
1. Анализирую `predictions.jsonl` + `meta.json`
2. Меняю код/конфиг → `git push`
3. Пользователь: Run All → новый `colab_runs/<timestamp>/` с новыми параметрами
4. Сравниваю runs между собой

**Структура runs:**
```
notebooks/colab_runs/
├── _test/                      ← test-прогоны (5 вопросов, ~25 мин)
│   ├── 2026-07-16_22-05-00/
│   │   ├── meta.json
│   │   ├── predictions.jsonl
│   │   ├── checkpoint.json
│   │   └── errors.log
│   └── ...
├── 2026-07-17_14-30-00/        ← полные прогоны (50 вопросов, ~4.5 ч)
│   ├── meta.json              ← параметры эксперимента
│   ├── predictions.jsonl      ← 50 ответов (question, prediction, ground_truth, spirals, time_s)
│   ├── checkpoint.json        ← чекпоинт для resume
│   └── errors.log             ← ошибки
├── ...
└── .gitkeep
```

**Режимы запуска** (переменная `MODE` в начале ноутбука):
- `"test"` — первые 5 вопросов из questions.json, результат в `_test/<timestamp>/`
- `"full"` — все 50 вопросов, результат в `<timestamp>/`

### 2026-07-16 — Fix: data/ in gitignore broke Colab clone

`data/` в корневом `.gitignore` — при клоне репо `vortex-hrm/data/multi_domain/questions.json` и `corpus.json` не скачивались. Colab выдавал `FileNotFoundError`.

**Fix:** Убрал `data/` из `.gitignore` (заменил на `results/` — результаты действительно не нужно трекать). Добавил JSON с вопросами и корпусом в Git — это маленькие файлы (202 и 302 строки), задающие бенчмарк, должны быть под версиями.
