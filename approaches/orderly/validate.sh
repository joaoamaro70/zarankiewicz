#!/bin/bash
# compara contagem rotulada do orderly (sum F!N!/|Aut|) com a forca bruta
cd /work/approaches/orderly
triv() { local s=""; for ((j=1;j<=$2;j++)); do s="$s$((j*$1)),"; done; echo ${s%,}; }
for c in "5 4 14" "6 4 15" "6 5 18" "5 5 17" "6 5 20" "6 6 24" "6 6 25" "7 4 17" "7 5 21" "8 4 19"; do
  set -- $c; N=$1; F=$2; T=$3
  a=$(./orderly $N $F $T $(triv $N $F) -c | grep -E "labeled|final")
  b=$(timeout 600 ./brute $N $F $T)
  echo "N=$N F=$F T>=$T | orderly: $(echo $a | tr '\n' ' ') | brute: $b"
done
