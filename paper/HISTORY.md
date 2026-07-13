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
