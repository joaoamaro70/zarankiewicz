#!/bin/bash
# Valida o metodo por perfil: z(m,n)=v => com v uns algum perfil e SAT; com v+1 todos UNSAT.
# Uso: profile_test.sh m n v [timeout_s]
cd /work/sat
m=$1; n=$2; v=$3; T=${4:-600}
mkdir -p ptest
for k in $v $((v+1)); do
  sat=0; uns=0; to=0; i=0
  t0=$(date +%s)
  while read -r prof; do
    i=$((i+1)); f=ptest/p_${m}_${n}_${k}_$i.cnf
    python3 profile_sat.py encode $m $n "$prof" $f > /dev/null
    r=$(timeout $T kissat -q $f | grep '^s ')
    case "$r" in
      "s SATISFIABLE") sat=$((sat+1));;
      "s UNSATISFIABLE") uns=$((uns+1));;
      *) to=$((to+1));;
    esac
    rm -f $f
  done < <(python3 profile_sat.py profiles $m $n $k)
  echo "z($m,$n) com $k uns: $i perfis -> SAT $sat, UNSAT $uns, timeout $to  ($(( $(date +%s)-t0 )) s)"
done
