#!/bin/bash
# Roda Kissat em paralelo. Uso: run_sat.sh segundos "m n k seed" ["m n k seed" ...]
cd /work/sat
mkdir -p runs
T=$1; shift
for job in "$@"; do
  set -- $job; m=$1; n=$2; k=$3; seed=$4
  base=runs/z_${m}_${n}_k${k}_s${seed}
  (
    python3 zsat.py encode $m $n $k $base.cnf > $base.info
    start=$(date +%s)
    timeout $T kissat -q --seed=$seed $base.cnf > $base.out
    echo "tempo $(( $(date +%s) - start )) s, resultado: $(grep '^s ' $base.out || echo 'timeout')" >> $base.info
    if grep -q '^s SATISFIABLE' $base.out; then
      python3 zsat.py decode $m $n $base.out $base.txt >> $base.info
      cp $base.txt runs/Z_${m}_${n}.txt
      python3 ../verify.py runs/Z_${m}_${n}.txt >> $base.info
    fi
    rm -f $base.cnf
  ) &
done
wait
echo "todos os jobs terminaram"
