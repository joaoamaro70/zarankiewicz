#!/bin/bash
# amostras de custo: para cada config, 3 pedacos de 1/W (timeout 400 s)
cd /work/approaches/orderly; mkdir -p runs/samp
W=2000
job() { tag=$1; shift; i=$1; shift; timeout 400 nice -n 10 ./orderly "$@" -s 4 $W $i > runs/samp/${tag}_$i.log 2>&1; echo "$tag $i rc=$? $(grep -h '^time' runs/samp/${tag}_$i.log)"; }
A="17 16 133 17,34,36,42,52,58,66,74,81,90,96,103,110,118,126,999"
Ap="16 17 133 16,32,34,40,49,56,63,70,77,85,92,99,107,115,123,128,999"
B="19 14 130 19,38,40,46,57,64,72,81,89,98,106,114,121,999"
D="20 13 128 20,40,42,48,60,66,75,84,93,102,111,120,999"
for i in 7 707 1407; do job A $i $A & job Ap $i $Ap & done; wait
for i in 7 707 1407; do job B $i $B & job D $i $D & done; wait
