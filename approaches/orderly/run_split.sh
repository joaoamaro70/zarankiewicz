#!/bin/bash
# run_split.sh NAME W S N F T Z [extra]  -- W processos, divisao no nivel S
cd /work/approaches/orderly
NAME=$1; W=$2; S=$3; N=$4; F=$5; T=$6; Z=$7; shift 7
mkdir -p runs/$NAME
for ((i=0;i<W;i++)); do
  nice -n 10 ./orderly $N $F $T $Z -s $S $W $i -o runs/$NAME/found_$i.txt "$@" > runs/$NAME/w$i.log 2>&1 &
done
wait
echo done > runs/$NAME/DONE
