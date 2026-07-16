# VORTEX-HRM Paper

Status: **Zapiski POMI template, ready for OpenReview submission**.

## Files

| File | Purpose |
|------|---------|
| `sspp-paper.tex` | Paper source (Zapiski POMI class) |
| `zapiski.cls` | Zapiski POMI document class |
| `template.tex` | Original Zapiski POMI template (reference) |
| `poster.tex` | A0 poster (Smiles-2026, dark theme) |
| `outline.md` | Section-by-section plan |
| `figs/architecture.py` | Vortex architecture diagram generator |
| `Makefile` | Build: `make paper`, `make poster`, `make clean` |
| `HISTORY.md` | Full project history |

## Submission

- **Platform**: OpenReview — https://openreview.net/group?id=smiles.skoltech.ru/SSPP/2026
- **Deadline**: August 2, 2026 (21:00 MSK) — verify with organizers
- **Template**: Zapiski POMI (NOT submission to journal, school report format)

## Requirements

- ≤10 pages + unlimited appendices
- Not anonymized (full author list + mentor)
- Contribution section required
- All authors registered on OpenReview

## Build

```powershell
pdflatex sspp-paper.tex
# or: make paper
```
