#!/bin/bash
# Extrai arxiv.tar.gz numa pasta limpa e compila como o arXiv faria (sem bibtex: usa main.bbl).
set -e
rm -rf /tmp/t && mkdir -p /tmp/t
tar xzf /work/paper/arxiv.tar.gz -C /tmp/t
cd /tmp/t
echo "comentarios % no pacote:"; grep -rn '%' main.tex refs.bib gen || echo "  nenhum"
pdflatex -interaction=nonstopmode main.tex > /dev/null
pdflatex -interaction=nonstopmode main.tex > /dev/null
pdfinfo main.pdf | grep Pages
echo "avisos de referencia indefinida: $(grep -c 'undefined' main.log || true)"
