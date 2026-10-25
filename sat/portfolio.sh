#!/bin/bash
# Portfolio: cada perfil roda com varias sementes do Kissat em paralelo; a primeira
# resposta (SAT ou UNSAT) vale e encerra as outras sementes daquele perfil.
# Uso: portfolio.sh timeout_s m n sementes "nome:graus" ...
# Resultados em sat/pf/<nome>.res (e a matriz em sat/pf/<nome>.txt se SAT).
cd /work/sat
mkdir -p pf
T=$1; m=$2; n=$3; S=$4; shift 4
for job in "$@"; do
  name=${job%%:*}; prof=${job#*:}
  (
    python3 profile_sat.py encode $m $n "$prof" pf/$name.cnf > /dev/null
    t0=$(date +%s)
    pids=()
    for s in $(seq 1 $S); do
      ( timeout $T kissat -q --seed=$s pf/$name.cnf > pf/$name.s$s.out ) &
      pids+=($!)
    done
    res=timeout
    while :; do
      for s in $(seq 1 $S); do
        r=$(grep -m1 '^s ' pf/$name.s$s.out 2>/dev/null)
        if [ -n "$r" ]; then res="$r (semente $s)"; win=$s; break 2; fi
      done
      alive=0; for p in "${pids[@]}"; do kill -0 $p 2>/dev/null && alive=1; done
      [ $alive = 0 ] && break
      sleep 5
    done
    pkill -f "kissat -q --seed=[0-9]* pf/$name.cnf" 2>/dev/null
    wait
    echo "$name | $(( $(date +%s)-t0 ))s | $res | $prof" > pf/$name.res
    if [[ "$res" == "s SATISFIABLE"* ]]; then
      python3 zsat.py decode $m $n pf/$name.s$win.out pf/$name.txt >> pf/$name.res
      python3 ../verify.py pf/$name.txt >> pf/$name.res || true
    fi
    rm -f pf/$name.cnf pf/$name.s*.out
  ) &
done
wait
echo "fim" > pf/done
