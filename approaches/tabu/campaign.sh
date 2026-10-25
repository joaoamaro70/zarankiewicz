#!/bin/bash
# Campanha nas celulas abertas. Uso (no container): ./campaign.sh ROUND SEGUNDOS [celulas.txt]
# Para cada celula (m,n,nosso) e cada variante (d = padrao, w = pesos -w 10), dois jobs:
#   rand: matriz aleatoria com k = nosso-12, modo subida (-c) -> passa por nosso e tenta nosso+1, ...
#   best: results/Z_m_n.txt + 1 um extra (k = nosso+1), modo subida.
# Matrizes gravadas em runs/Z_m_n_<modo><variante>_r<round>.txt (sobrescritas a cada k achado).
cd "$(dirname "$0")"
gcc -O3 -march=native -o tabu tabu.c
R=$1; T=$2; CELLS=${3:-open.txt}
mkdir -p runs logs
JOBS=""
while IFS=, read m n k ub; do
  for v in d w; do JOBS="$JOBS $m,$n,$k,rand,$v $m,$n,$k,best,$v"; done
done < $CELLS
echo $JOBS | tr ' ' '\n' | xargs -P 7 -I{} bash -c '
  IFS=, read m n k mode v <<< "{}"
  s=$(( '"$R"' * 1000 + m * 31 + n ))
  [ $v = w ] && s=$((s + 7))
  tag=${m}_${n}_${mode}${v}_r'"$R"'
  if [ $mode = rand ]; then a="-k $((k-12))"; else a="-k $((k+1)) -i /work/results/Z_${m}_${n}.txt"; fi
  [ $v = w ] && a="$a -w 10"
  nice -n 10 ./tabu -m $m -n $n $a -s $s -t '"$T"' -c -v 60 -o runs/Z_$tag.txt > logs/$tag.out 2> logs/$tag.err || true
  echo "($m,$n) nosso=$k $mode$v: $(grep ACHOU logs/$tag.out | tail -1 | cut -d" " -f4) | $(grep FALHOU logs/$tag.out)"
'
