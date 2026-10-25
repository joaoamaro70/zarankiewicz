#!/bin/bash
cd /work/approaches/orderly; mkdir -p runs/cmp2; rm -f runs/cmp2/*
Z17=17,34,36,42,52,58,66,74,81,90,96,999
for opt in "-a" "-r 7" "-r 6" "-r 5" "-a -r 6" "-a -r 5"; do
  nice ./orderly 17 12 104 $Z17 $opt > "runs/cmp2/17_12_${opt// /}.log" &
done
wait
