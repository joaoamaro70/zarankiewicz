#!/bin/bash
# Roda perfis de grau em paralelo. Uso: profile_run.sh timeout_s m n "nome:graus" ...
cd /work/sat
mkdir -p prun
T=$1; m=$2; n=$3; shift 3
for job in "$@"; do
  name=${job%%:*}; prof=${job#*:}
  (
    f=prun/$name.cnf
    python3 profile_sat.py encode $m $n "$prof" $f > prun/$name.info
    t0=$(date +%s)
    timeout $T kissat -q $f > prun/$name.out
    echo "perfil: $prof" >> prun/$name.info
    echo "tempo $(( $(date +%s)-t0 )) s, resultado: $(grep '^s ' prun/$name.out || echo timeout)" >> prun/$name.info
    if grep -q '^s SATISFIABLE' prun/$name.out; then
      python3 zsat.py decode $m $n prun/$name.out prun/Z_${m}_${n}_$name.txt >> prun/$name.info
      mv prun/Z_${m}_${n}_$name.txt prun/check/Z_${m}_${n}.txt 2>/dev/null || true
    fi
    rm -f $f
  ) &
done
wait
echo "fim"
