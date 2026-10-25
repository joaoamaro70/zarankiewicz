#!/bin/bash
# amostras uniformes de custo: 6 pedacos aleatorios de 1/2000 por config (timeout 300 s)
cd /work/approaches/orderly; mkdir -p runs/samp3
job() { tag=$1; i=$2; shift 2; timeout 300 nice -n 10 ./orderly "$@" -s 4 2000 $i > runs/samp3/${tag}_$i.log 2>&1; echo "$tag $i rc=$? $(grep -h '^time' runs/samp3/${tag}_$i.log)"; }
export -f job
{
for i in 113 517 911 1288 1603 1977; do
  echo "D2 $i 20 13 127 20,40,42,48,60,66,75,84,93,102,111,120,999"
  echo "E $i 21 13 134 21,42,44,50,62,69,78,87,96,106,116,126,999"
  echo "Ap $i 16 17 133 16,32,34,40,49,56,63,70,77,85,92,99,107,115,123,128,999"
done
} | xargs -P 6 -L 1 bash -c 'job "$@"' _
