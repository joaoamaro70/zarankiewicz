#!/bin/bash
# Regera tabelas a partir de results/, compila a nota e gera as figuras PNG do README.
# Rodar no container: ./paper/build.sh
set -e
cd /work
python3 literature.py > /dev/null
python3 paper/make_tables.py
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > build.log 2>&1 || { tail -30 build.log; exit 1; }
grep -E "Warning.*(undefined|Citation)" main.log || true
echo "paper/main.pdf ok"

# figuras para o README (mesmas fontes da nota)
cd figures
for fig in bounds matrices; do
  pdflatex -interaction=nonstopmode -halt-on-error $fig.tex > $fig.log 2>&1 || { tail -20 $fig.log; exit 1; }
  pdftoppm -r 160 -png -singlefile $fig.pdf $fig
  rm -f $fig.aux $fig.log $fig.pdf
done
echo "paper/figures/*.png ok"
