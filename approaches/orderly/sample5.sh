#!/bin/bash
cd /work/approaches/orderly; mkdir -p runs/samp5
job() { tag=$1; i=$2; shift 2; timeout 300 nice -n 10 ./orderly "$@" -s 4 2000 $i > runs/samp5/${tag}_$i.log 2>&1; echo "$tag $i rc=$? $(grep -h '^time' runs/samp5/${tag}_$i.log)"; }
export -f job
Z=23,46,48,54,66,74,84,94,103,112,123,134,999
for i in 37 401 777 1150 1499 1888; do
  echo "G143 $i 23 13 143 $Z"
done | xargs -P 6 -L 1 bash -c 'job "$@"' _
for i in 37 401 777 1150 1499 1888; do
  echo "G142 $i 23 13 142 $Z"
done | xargs -P 6 -L 1 bash -c 'job "$@"' _
