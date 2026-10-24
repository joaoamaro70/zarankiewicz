#!/usr/bin/env python3
"""Compara diretorios de resultados nos casos abertos (so conta matrizes verificadas).
Uso: compare.py dir1 [dir2 ...]"""
import csv
import glob
import os
import sys
from table import MS, NS, up, lo
from verify import check

bars = {}
with open("bars.csv") as f:
    for r in csv.DictReader(f):
        bars[(int(r["m"]), int(r["n"]))] = int(r["BARRA_trivial"])
opens = [(m, n) for m in MS for n in NS if up(m, n) > lo(m, n)]


def load(d):
    best = {}
    for p in glob.glob(os.path.join(d, "Z_*_*.txt")):
        ok, v = check(p)
        if ok:
            m, n = map(int, os.path.basename(p)[2:-4].split("_"))
            best[(m, n)] = v
    return best


print(f"{'dir':28s} {'soma':>6s} {'>artigo':>8s} {'>barra':>7s} {'fechados':>9s}")
for d in sys.argv[1:]:
    b = load(d)
    s = sum(b.get(k, 0) for k in opens)
    gl = sum(b.get(k, 0) > lo(*k) for k in opens)
    gb = sum(b.get(k, 0) > bars[k] for k in opens)
    cl = sum(b.get(k, 0) >= up(*k) for k in opens)
    print(f"{d:28s} {s:6d} {gl:8d} {gb:7d} {cl:9d}")
