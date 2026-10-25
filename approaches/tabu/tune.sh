#!/bin/bash
# Ajuste de parametros: tempo ate o alvo em modo subida, 6 sementes por configuracao.
# Uso: ./tune.sh m n alvo segundos "cfg1" "cfg2" ...   (cfg = args do tabu entre aspas)
cd "$(dirname "$0")"
gcc -O3 -march=native -o tabu tabu.c
m=$1; n=$2; k=$3; T=$4; shift 4
mkdir -p tune
for cfg in "$@"; do
  tag=$(echo "$cfg" | tr -d ' -')
  times=$(seq 1 6 | xargs -P 6 -I{} bash -c "nice -n 10 ./tabu -m $m -n $n -k $((k-12)) -s {} -t $T -c -v 1000 $cfg 2>/dev/null | grep 'k=$k ' | sed 's/.* t=\([0-9.]*\)s.*/\1/' || true" | sort -n | tr '\n' ' ')
  echo "($m,$n) alvo=$k cfg=[$cfg] tempos(s)= $times"
done
