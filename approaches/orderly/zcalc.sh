#!/bin/bash
# zcalc.sh N JMAX : calcula z(j,N) exatos para j=1..JMAX com o proprio orderly
# (desce T a partir de floor(z(j-1)*j/(j-1)) ate achar uma matriz)
cd /work/approaches/orderly
N=$1; JMAX=$2; Zs=""; prev=0
for ((j=1;j<=JMAX;j++)); do
  if ((j==1)); then T=$N; else T=$(( prev*j/(j-1) )); fi
  if ((T > j*N)); then T=$((j*N)); fi
  while true; do
    if ./orderly $N $j $T "${Zs}${T}" -x | grep -q FOUND; then break; fi
    T=$((T-1))
  done
  prev=$T; Zs="${Zs}${T},"
  echo "z($j,$N)=$T"
done
echo "Z=${Zs%,}"
