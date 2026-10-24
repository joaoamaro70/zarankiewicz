#!/bin/bash
# Fila de perfis de grau em paralelo. Uso: profile_queue.sh m n total workers timeout_s "perfil a pular" ...
# Resultado de cada perfil vai para prun/queue.log (uma linha por perfil).
cd /work/sat
mkdir -p prun/q
m=$1; n=$2; total=$3; P=$4; T=$5; shift 5
skip=$(printf '%s\n' "$@")
export m n T

one() {
  prof="$1"; id=$(echo "$prof" | tr ' ' '_' | md5sum | cut -c1-10)
  f=prun/q/$id.cnf
  python3 profile_sat.py encode $m $n "$prof" $f > /dev/null
  t0=$(date +%s)
  r=$(timeout $T kissat -q $f > prun/q/$id.out; grep '^s ' prun/q/$id.out || echo timeout)
  echo "$(( $(date +%s)-t0 ))s | $r | $prof" >> prun/queue.log
  rm -f $f
  grep -q '^s UNSAT' prun/q/$id.out && rm -f prun/q/$id.out
}
export -f one

python3 profile_sat.py profiles $m $n $total | grep -vxF "$skip" | xargs -P $P -I{} bash -c 'one "{}"'
echo "fila terminou" >> prun/queue.log
