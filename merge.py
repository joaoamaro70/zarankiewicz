#!/usr/bin/env python3
"""Copia para results/ a melhor matriz verificada de cada caso entre os diretorios dados.
Uso: merge.py destino origem1 [origem2 ...]"""
import glob
import os
import shutil
import sys
from verify import check

dest, srcs = sys.argv[1], sys.argv[2:]
os.makedirs(dest, exist_ok=True)
best = {}
for d in [dest] + srcs:
    for p in glob.glob(os.path.join(d, "Z_*_*.txt")):
        ok, v = check(p)
        k = os.path.basename(p)
        if ok and v > best.get(k, (-1, None))[0]:
            best[k] = (v, p)
for k, (v, p) in sorted(best.items()):
    tgt = os.path.join(dest, k)
    if os.path.abspath(p) != os.path.abspath(tgt):
        shutil.copyfile(p, tgt)
print(f"{len(best)} casos mesclados em {dest}")
