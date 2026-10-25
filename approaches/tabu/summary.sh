#!/bin/bash
# Tabela por celula: maior k achado pela tabu (todos os logs) e menor custo final em nosso+1.
# Confere com verify.py todas as matrizes gravadas em runs/ e copia para found/ as que superam o nosso.
cd "$(dirname "$0")"
mkdir -p found
echo "| (m,n) | nosso | UB | maior k (tabu) | jobs | custo mínimo em nosso+1 |"
echo "|---|---|---|---|---|---|"
while IFS=, read m n k ub; do
  best=$(cat logs/${m}_${n}_*.out 2>/dev/null | tr -d '\0' | grep ACHOU | sed 's/.* k=\([0-9]*\) .*/\1/' | sort -n | tail -1)
  jobs=$(ls logs/${m}_${n}_*.out 2>/dev/null | wc -l)
  mc=$(cat logs/${m}_${n}_*.out 2>/dev/null | tr -d '\0' | grep "FALHOU.* k=$((k+1)) " | sed 's/.*melhor_custo=\([0-9]*\).*/\1/' | sort -n | head -1)
  echo "| ($m,$n) | $k | $ub | ${best:--} | $jobs | ${mc:--} |"
  for f in runs/Z_${m}_${n}_*.txt; do
    [ -e "$f" ] || continue
    ones=$(grep -v '^#' "$f" | tr -cd 1 | wc -c)
    if [ "$ones" -gt "$k" ]; then cp "$f" found/Z_${m}_${n}.txt; echo "MELHORA: $f ($ones uns)" >&2; fi
  done
done < open.txt
python3 /work/verify.py runs/*.txt found/*.txt 2>/dev/null | grep -c '^OK' | sed 's/^/verify OK: /' >&2
python3 /work/verify.py runs/*.txt found/*.txt 2>/dev/null | grep -v '^OK' >&2
