#!/bin/bash
set -e
cd /work/approaches/orderly
gcc -O3 -march=native -DWORDSIZE=64 -DMAXN=WORDSIZE -I/usr/include/nauty -I/usr/include/x86_64-linux-gnu/nauty -o orderly.new orderly.c -lnautyL1 -lm && mv orderly.new orderly
gcc -O3 -march=native -o brute brute.c
