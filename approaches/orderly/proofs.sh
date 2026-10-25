#!/bin/bash
# proofs.sh [P] -- refaz todas as provas de limite superior desta pasta (P processos).
# Cada linha: nome, pedacos W, nivel de divisao S, N, F, T, Z1..ZF (Z[F] = 999, nao usado).
# Prova completa = os W pedacos terminam com "final (>= T=...): 0".
# Uso (na raiz do repositorio):
#   docker run --rm -v "${PWD}:/work" zaran-orderly bash /work/approaches/orderly/build.sh
#   docker run --rm -v "${PWD}:/work" zaran-orderly bash /work/approaches/orderly/proofs.sh 6
cd /work/approaches/orderly
P=${1:-6}
while read -r NAME W S N F T Z; do
  [ -z "$NAME" ] && continue
  bash run_chunks.sh "$NAME" "$P" "$W" "$S" "$N" "$F" "$T" "$Z"
  ok=$(grep -h '^final' runs/$NAME/c*.log | grep -c ': 0 raw')
  echo "$NAME: $ok/$W pedacos sem matriz com >= $T uns"
done <<'EOF'
C_13_19_T122 60 4 19 13 122 19,38,40,46,57,64,72,81,89,98,106,114,999
D_13_20_T128 60 4 20 13 128 20,40,42,48,60,66,75,84,93,102,111,120,999
D_13_20_T127 60 4 20 13 127 20,40,42,48,60,66,75,84,93,102,111,120,999
D_13_20_T126 60 4 20 13 126 20,40,42,48,60,66,75,84,93,102,111,120,999
F_14_20_T134 120 4 20 14 134 20,40,42,48,60,66,75,84,93,102,111,120,125,999
EOF
