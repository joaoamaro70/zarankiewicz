#!/bin/bash
# repete os casos de validate.sh so com o orderly (a forca bruta ja foi conferida)
cd /work/approaches/orderly
triv() { local s=""; for ((j=1;j<=$2;j++)); do s="$s$((j*$1)),"; done; echo ${s%,}; }
for c in "5 4 14" "6 4 15" "6 5 18" "5 5 17" "6 5 20" "6 6 24" "6 6 25" "7 5 21" "7 6 26"; do
  set -- $c; echo "N=$1 F=$2 T>=$3 $(./orderly $1 $2 $3 $(triv $1 $2) -c | grep -E 'labeled|final' | tr '\n' ' ')"
done
./orderly 9 8 45 9,18,27,36,45,54,63,72 -c | grep final
./orderly 11 10 64 11,22,33,44,55,66,77,88,99,110 -c | grep final
