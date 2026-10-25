#!/usr/bin/env python3
"""Teste: L1 + refinamento (com rowsplit).  try2.py m n k "d^c ..." f g mode depth [bnb]"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refine import prove  # noqa: E402
from search import l1_cases  # noqa: E402


def count(node):
    if "children" in node:
        return sum(count(c) for c in node["children"])
    return 1


m, n, k = map(int, sys.argv[1:4])
p = {int(x.split("^")[0]): int(x.split("^")[1]) for x in sys.argv[4].split()}
f, g, mode, depth = int(sys.argv[5]), int(sys.argv[6]), sys.argv[7], int(sys.argv[8])
bn = int(sys.argv[9]) if len(sys.argv) > 9 else 0
cases = [dict(s=1, sz=[m - f, f], excl=[])] if mode == "L0" else l1_cases(m, f, g, mode)
for c in cases:
    t0 = time.time()
    r = prove(m, p, c, depth, bn, None, (n, k))
    print(c["sz"], "OK" if r else "FALHA", (r["kind"], count(r)) if r else "",
          f"{time.time() - t0:.1f}s", flush=True)
