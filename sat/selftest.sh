#!/bin/bash
# Valida a codificacao com valores exatos de Tan (2022), Tabela 3: z(m,n)=v => k=v SAT, k=v+1 UNSAT.
cd /work/sat
mkdir -p test
for case in "8 9 45" "9 10 54" "10 11 64"; do
  set -- $case; m=$1; n=$2; v=$3
  for k in $v $((v+1)); do
    for sym in ""; do
      f=test/t_${m}_${n}_${k}${sym}.cnf
      python3 zsat.py encode $m $n $k $f $sym > /dev/null
      t0=$(date +%s.%N)
      r=$(timeout 600 kissat -q $f > $f.out; grep '^s ' $f.out)
      t1=$(date +%s.%N)
      ok=""
      if [ "$r" = "s SATISFIABLE" ]; then
        python3 zsat.py decode $m $n $f.out test/Z_${m}_${n}.txt > /dev/null
        python3 ../verify.py test/Z_${m}_${n}.txt | grep -q OK && ok="(verify OK)" || ok="(VERIFY FALHOU)"
      fi
      printf "z(%d,%d)=%d  k=%d %-8s -> %s %s  %.1fs\n" $m $n $v $k "${sym:-sym}" "$r" "$ok" $(echo "$t1-$t0" | bc)
    done
  done
done
