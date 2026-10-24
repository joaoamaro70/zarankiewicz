#!/bin/bash
# Compila a busca dentro do container (-march=native) e roda, retomando de results/.
# Uso (da raiz do projeto):
#   docker run --rm -v "$PWD:/work" zaran bash search/run.sh -t 1
# Os argumentos vao direto para o programa (ver o cabecalho de search/zaran.c).
set -e
cd /work
gcc -O3 -march=native -fopenmp -Wall -o /tmp/zaran search/zaran.c -lm
nice -n 10 /tmp/zaran -d results "$@"
python3 verify.py results/Z_*.txt
