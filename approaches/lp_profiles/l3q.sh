#!/bin/bash
# fila de nivel 3 (v2). uso: l3q.sh "m n k" ...   (reaproveita certs2 se existir)
cd /work/approaches/lp_profiles
export ROWFIRST=0
for c in "$@"; do
  set -- $c
  re=""; [ -f certs2/z$1_$2_k$3.json ] && re="--reuse certs2/z$1_$2_k$3.json"
  nice python3 search.py $1 $2 $3 --level 3 --jobs 2 $re --out certs4 > logs4/z$1_$2_k$3.log 2>&1
  echo "z($1,$2) k=$3: $(tail -1 logs4/z$1_$2_k$3.log)"
done
