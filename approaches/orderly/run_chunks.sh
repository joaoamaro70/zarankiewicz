#!/bin/bash
# run_chunks.sh NAME P W S N F T Z  -- W pedacos (divisao no nivel S), P em paralelo.
# Retomavel: pedacos cujo log ja tem a linha "time" sao pulados.
cd /work/approaches/orderly
NAME=$1; P=$2; W=$3; S=$4; N=$5; F=$6; T=$7; Z=$8
mkdir -p runs/$NAME
one() {
  i=$1; log=runs/$NAME/c$i.log
  grep -q '^time' $log 2>/dev/null && return
  mkdir runs/$NAME/lock_$i 2>/dev/null || return   # um processo por pedaco
  nice -n 10 ./orderly $N $F $T $Z -s $S $W $i -o runs/$NAME/found_$i.txt > $log.tmp 2>&1 && mv $log.tmp $log; rmdir runs/$NAME/lock_$i
}
export -f one; export NAME N F T Z S W
seq 0 $((W-1)) | shuf --random-source=<(yes) | xargs -P $P -I{} bash -c 'one {}'
n=$(grep -l '^time' runs/$NAME/c*.log | wc -l); echo "$n/$W chunks complete" > runs/$NAME/STATUS
