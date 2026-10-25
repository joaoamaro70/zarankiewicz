#!/bin/bash
# Calibracao: tempo para reproduzir o "nosso" valor em celulas conhecidas.
# Uso (no container, em /work/approaches/tabu): ./calibrate.sh SEGUNDOS [args extras do tabu]
# Cada job: modo subida (-c) a partir de matriz aleatoria com k = nosso-12.
set -e
cd "$(dirname "$0")"
gcc -O3 -march=native -o tabu tabu.c
T=${1:-300}; shift || true
EXTRA="$*"
mkdir -p calib
CELLS="14,19,128 13,19,120 16,17,132 15,20,139 16,23,163 13,23,140"
JOBS=""
for c in $CELLS; do
  IFS=, read m n k <<< "$c"
  for s in 1 2 3; do JOBS="$JOBS $m,$n,$k,$s"; done
done
echo $JOBS | tr ' ' '\n' | xargs -P 6 -I{} bash -c '
  IFS=, read m n k s <<< "{}"
  nice -n 10 ./tabu -m $m -n $n -k $((k-12)) -s $s -t '"$T"' -c -v 1000 '"$EXTRA"' \
     -o calib/Z_${m}_${n}_s$s.txt > calib/log_${m}_${n}_s$s.txt 2>/dev/null || true
  last=$(grep ACHOU calib/log_${m}_${n}_s$s.txt | tail -1)
  hit=$(grep "k=$k " calib/log_${m}_${n}_s$s.txt | grep ACHOU || true)
  echo "($m,$n) alvo=$k seed=$s :: ultimo: $last :: alvo: ${hit:-NAO}"
'
