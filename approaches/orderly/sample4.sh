#!/bin/bash
cd /work/approaches/orderly; mkdir -p runs/samp4
job() { tag=$1; i=$2; shift 2; timeout 400 nice -n 10 ./orderly "$@" -s 4 2000 $i > runs/samp4/${tag}_$i.log 2>&1; echo "$tag $i rc=$? $(grep -h '^time' runs/samp4/${tag}_$i.log)"; }
export -f job
for i in 113 517 911 1288 1603 1977; do
  echo "F134 $i 20 14 134 20,40,42,48,60,66,75,84,93,102,111,120,125,999"
done | xargs -P 6 -L 1 bash -c 'job "$@"' _
