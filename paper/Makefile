.PHONY: all paper poster clean

all: paper poster

paper:
	pdflatex sspp-paper.tex
	bibtex sspp-paper
	pdflatex sspp-paper.tex
	pdflatex sspp-paper.tex

poster:
	pdflatex poster.tex

clean:
	del /Q *.aux *.log *.out *.bbl *.blg *.nav *.snm *.toc 2>nul || true
