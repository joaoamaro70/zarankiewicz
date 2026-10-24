#!/bin/bash
# Regera tabelas a partir de results/ e compila a nota. Rodar no container: ./paper/build.sh
set -e
cd /work
python3 literature.py > /dev/null
python3 paper/make_tables.py
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > build.log 2>&1 || { tail -30 build.log; exit 1; }
grep -E "Warning.*(undefined|Citation)" main.log || true
echo "paper/main.pdf ok"
