#!/bin/bash
# Imprime (uma vez) cada ACHOU com k > nosso nos logs e cada linha nova de round*.txt.
export LC_ALL=C
cd "$(dirname "$0")"
seen=""
while true; do
  while IFS=, read m n k ub; do
    for f in logs/${m}_${n}_*.out; do
      [ -e "$f" ] || continue
      grep ACHOU "$f" | while read -r line; do
        kk=$(echo "$line" | sed 's/.* k=\([0-9]*\) .*/\1/')
        if [ "$kk" -gt "$k" ]; then echo "MELHORA $f: $line"; fi
      done
    done
  done < open.txt > .watch_now 2>/dev/null
  cat round*.txt 2>/dev/null >> .watch_now
  sort -u .watch_now > .watch_sorted
  if [ -n "$seen" ]; then comm -13 .watch_seen .watch_sorted; fi
  cp .watch_sorted .watch_seen; seen=1
  sleep 60
done
