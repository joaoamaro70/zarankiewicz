#!/bin/bash
# Execucao longa (M4) retomando de results/. Uso: ./longrun.sh horas
set -e
cd /work
gcc -O3 -march=native -fopenmp -Wall -o zaran2 zaran2.c -lm
nice -n 10 ./zaran2 -t "${1:-8}" -d results >> results/run.log
python3 verify.py results/Z_*.txt > results/verify.txt && echo "verify OK" || echo "verify FALHOU"
python3 literature.py > results/literature.txt
python3 report.py
