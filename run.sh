#!/bin/bash
# Compila dentro do container (-march=native) e executa o comando passado.
# Uso: ./run.sh ./zaran2 -t 8
set -e
cd /work
gcc -O3 -march=native -fopenmp -Wall -o zaran2 zaran2.c -lm
gcc -O3 -march=native -fopenmp -o zaran zaran.c
[ -f bars.csv ] || python3 bars.py
exec nice -n 10 "$@"
