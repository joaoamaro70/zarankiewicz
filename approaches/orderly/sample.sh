#!/bin/bash
# sample.sh NAME W S N F T Z id1 id2 ... : roda pedacos de amostra (1/W cada) em paralelo
cd /work/approaches/orderly
NAME=$1; W=$2; S=$3; N=$4; F=$5; T=$6; Z=$7; shift 7
mkdir -p runs/$NAME
for i in "$@"; do nice -n 10 ./orderly $N $F $T $Z -s $S $W $i $EXTRA > runs/$NAME/s$i.log 2>&1 & done
wait
