#!/usr/bin/env python3
"""Verificacao independente (nao reaproveita o C) de results/Z_m_n.txt.
Uso: verify.py arquivo [arquivo ...]   (sai com codigo 1 se algum falhar)"""
import re
import sys
from itertools import combinations


def check(path):
    with open(path) as f:
        lines = [l.strip() for l in f if l.strip()]
    header = [l for l in lines if l.startswith("#")]
    mat = [l for l in lines if not l.startswith("#")]
    mm = re.search(r"Z_(\d+)_(\d+)", path)
    m, n = int(mm.group(1)), int(mm.group(2))
    if len(mat) != m:
        return False, f"{len(mat)} linhas, esperado {m}"
    for l in mat:
        if len(l) != n or set(l) - {"0", "1"}:
            return False, f"linha invalida: {l!r}"
    A = [[int(ch) for ch in l] for l in mat]
    ones = sum(map(sum, A))
    if header:
        h = re.search(r">=\s*(\d+)", header[0])
        if h and int(h.group(1)) != ones:
            return False, f"cabecalho diz {h.group(1)}, contei {ones}"
    # por linhas: quaisquer 3 linhas com <= 2 colunas em comum
    rows = [{c for c in range(n) if A[r][c]} for r in range(m)]
    for a, b, c in combinations(range(m), 3):
        if len(rows[a] & rows[b] & rows[c]) >= 3:
            return False, f"K33 nas linhas {a},{b},{c}"
    # checagem cruzada por colunas
    cols = [{r for r in range(m) if A[r][c]} for c in range(n)]
    for a, b, c in combinations(range(n), 3):
        if len(cols[a] & cols[b] & cols[c]) >= 3:
            return False, f"K33 nas colunas {a},{b},{c}"
    return True, ones


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        ok, info = check(p)
        print(f"{'OK  ' if ok else 'FAIL'} {p}: {info}")
        bad += not ok
    sys.exit(1 if bad else 0)
