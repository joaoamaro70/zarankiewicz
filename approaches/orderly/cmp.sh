#!/bin/bash
cd /work/approaches/orderly; mkdir -p runs/cmp; rm -f runs/cmp/*
# Z[F] = 999 (sem usar o valor que se quer provar)
Z17_10=17,34,36,42,52,58,66,74,81,90
Z19_10=19,38,40,46,57,64,72,81,89,98
nice ./orderly 17 11 97 ${Z17_10},999 > runs/cmp/a17_11.log &
nice ./orderly 17 11 97 ${Z17_10},999 -a > runs/cmp/b17_11.log &
nice ./orderly 19 11 107 ${Z19_10},999 > runs/cmp/a19_11.log &
nice ./orderly 19 11 107 ${Z19_10},999 -a > runs/cmp/b19_11.log &
nice ./orderly 17 12 104 ${Z17_10},96,999 > runs/cmp/a17_12.log &
nice ./orderly 17 12 104 ${Z17_10},96,999 -a > runs/cmp/b17_12.log &
wait
