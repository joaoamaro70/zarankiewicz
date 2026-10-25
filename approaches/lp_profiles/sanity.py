#!/usr/bin/env python3
"""Teste de sanidade: para cada matriz conhecida em results/, (1) seu perfil de colunas
NAO pode ser eliminado pelas estrategias; (2) para escolhas concretas dos blocos fixos na
matriz real, o vetor y da matriz satisfaz exatamente as restricoes do modelo do caso.

  sanity.py ../../results [--level 1]
"""
import glob
import os
import re
import sys
from collections import Counter
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import build  # noqa: E402
from search import try_profile  # noqa: E402


def load(path):
    mat = [l.strip() for l in open(path) if l.strip() and not l.startswith("#")]
    m, n = len(mat), len(mat[0])
    return m, n, [frozenset(r for r in range(m) if mat[r][c] == "1") for c in range(n)]


def primal_ok(m, cols, fixed_idx, excl):
    fixed = [cols[j] for j in fixed_idx]
    s = len(fixed)
    reg = [sum(1 << i for i in range(s) if r in fixed[i]) for r in range(m)]
    sz = [reg.count(a) for a in range(1 << s)]
    p = Counter(len(c) for c in cols)
    model = build(m, p, s, sz, excl)
    assert model is not None
    y = Counter()
    for j, c in enumerate(cols):
        if j in fixed_idx:
            continue
        b = [0] * (1 << s)
        for r in c:
            b[reg[r]] += 1
        y[(len(c), tuple(b))] += 1
    colset = {(d, b): coef for d, b, coef in model["cols"]}
    for key in y:
        if key not in colset:
            return f"tipo {key} excluido mas presente"
    for k, cap in enumerate(model["cap"]):
        if sum(v * colset[key][k] for key, v in y.items()) > cap:
            return f"tripla {model['T'][k]} viola"
    for d in model["degs"]:
        if sum(v for (dd, _), v in y.items() if dd == d) != model["e"][d]:
            return f"grau {d} conta errada"
    return None


def main():
    root = sys.argv[1]
    level = int(sys.argv[sys.argv.index("--level") + 1]) if "--level" in sys.argv else 1
    bad = 0
    for path in sorted(glob.glob(os.path.join(root, "Z_*_*.txt"))):
        m, n, cols = load(path)
        p = dict(Counter(len(c) for c in cols))
        r = try_profile((m, p, level))
        msg = []
        if r["strategy"] is not None:
            msg.append(f"ERRO: perfil real eliminado por {r['strategy']}")
        # casos concretos: L0 com cada coluna; L1 maxpair/minpair no grau mais comum
        for j in range(n):
            e = primal_ok(m, cols, [j], [])
            if e:
                msg.append(f"L0 col {j}: {e}")
        f = max(p, key=lambda d: p[d])
        idx = [j for j in range(n) if len(cols[j]) == f]
        pairs = [(len(cols[a] & cols[b]), a, b) for a, b in combinations(idx, 2)]
        for sel, op in ((max(pairs), "<="), (min(pairs), ">=")):
            i, a, b = sel
            e = primal_ok(m, cols, [a, b], [([f], 0, op, i), ([f], 1, op, i)])
            if e:
                msg.append(f"L1 pair {op}: {e}")
        print(os.path.basename(path), "ok" if not msg else "; ".join(msg), flush=True)
        bad += bool(msg)
    print("FALHAS:", bad)


if __name__ == "__main__":
    main()
