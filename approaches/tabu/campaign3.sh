#!/bin/bash
# Rodada 3: partida aleatoria direta em k = nosso+1 (sem subida), pesos -w 10 e -w 30.
# Uso (no container): ./campaign3.sh SEGUNDOS [celulas.txt]
cd "$(dirname "$0")"
gcc -O3 -march=native -o tabu tabu.c
T=$1; CELLS=${2:-open.txt}
mkdir -p runs logs
JOBS=""
while IFS=, read m n k ub; do JOBS="$JOBS $m,$n,$k,10 $m,$n,$k,30"; done < $CELLS
echo $JOBS | tr ' ' '\n' | xargs -P 7 -I{} bash -c '
  IFS=, read m n k w <<< "{}"
  tag=${m}_${n}_directw${w}_r3
  nice -n 10 ./tabu -m $m -n $n -k $((k+1)) -s $((3000 + m * 31 + n + w)) -t '"$T"' -w $w -v 60 -o runs/Z_$tag.txt > logs/$tag.out 2> logs/$tag.err || true
  echo "($m,$n) nosso=$k directw$w: $(grep ACHOU logs/$tag.out | tail -1 | cut -d" " -f4) | $(grep FALHOU logs/$tag.out)"
' > round3.txt
