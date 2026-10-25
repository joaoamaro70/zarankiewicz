#!/usr/bin/env python3
"""Sanidade do v2: para cada matriz de results/, casos concretos com linha fixada
(grau maximo/minimo) e com um terceiro bloco: o vetor y da matriz real satisfaz o sistema.
Opcional --level3 N: roda o nivel 3 completo no perfil real das N primeiras matrizes
(nao pode eliminar).
  sanity2.py ../../../results [--level3 N]"""
import glob
import os
import sys
from collections import Counter
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import build, allowed  # noqa: E402
from search import try_profile  # noqa: E402


def load(path):
    mat = [l.strip() for l in open(path) if l.strip() and not l.startswith("#")]
    m, n = len(mat), len(mat[0])
    return m, n, [frozenset(r for r in range(m) if mat[r][c] == "1") for c in range(n)]


def check_case(m, cols, fixed_idx, row=None, op=None, excl=()):
    """row: indice da linha fixada (regiao propria). Regioes: por mascara de fixos, e a
    linha fixada como regiao extra ao final."""
    fixed = [cols[j] for j in fixed_idx]
    s = len(fixed)
    mask = [sum(1 << i for i in range(s) if r in fixed[i]) for r in range(m)]
    N = 1 << s
    reg = list(mask)
    rm = list(range(N))
    rows = ()
    if row is not None:
        reg[row] = N
        rm.append(mask[row])
        deg = sum(1 for c in cols if row in c)
        rows = [[N, deg, op]]
    sz = [reg.count(a) for a in range(len(rm))]
    p = Counter(len(c) for c in cols)
    model = build(m, p, s, sz, excl, rm, rows)
    y = Counter()
    for j, c in enumerate(cols):
        if j in fixed_idx:
            continue
        b = [0] * len(rm)
        for r in c:
            b[reg[r]] += 1
        y[(len(c), tuple(b))] += 1
    colset = {(d, b): coef for d, b, coef in model["cols"]}
    for key in y:
        if key not in colset:
            return f"tipo {key} excluido mas presente"
    for kk, (cap, se) in enumerate(zip(model["cap"], model["sense"])):
        lhs = sum(v * colset[key][kk] for key, v in y.items())
        if (se == "<=" and lhs > cap) or (se == "=" and lhs != cap):
            return f"linha {model['T'][kk]} viola ({lhs} {se} {cap})"
    for d in model["degs"]:
        if sum(v for (dd, _), v in y.items() if dd == d) != model["e"][d]:
            return f"grau {d} conta errada"
    return None


def main():
    root = sys.argv[1]
    nl3 = int(sys.argv[sys.argv.index("--level3") + 1]) if "--level3" in sys.argv else 0
    bad = 0
    for idx, path in enumerate(sorted(glob.glob(os.path.join(root, "Z_*_*.txt")))):
        m, n, cols = load(path)
        rdeg = [sum(1 for c in cols if r in c) for r in range(m)]
        rmax, rmin = rdeg.index(max(rdeg)), rdeg.index(min(rdeg))
        msg = []
        for j in range(n):
            for row, op in ((rmax, "max"), (rmin, "min")):
                e = check_case(m, cols, [j], row, op)
                if e:
                    msg.append(f"col {j} linha {op}: {e}")
        p = Counter(len(c) for c in cols)
        f = max(p, key=lambda d: p[d])
        idxs = [j for j in range(n) if len(cols[j]) == f]
        i, a, b = max((len(cols[x] & cols[y]), x, y) for x, y in combinations(idxs, 2))
        ex = [([f], 0, "<=", i), ([f], 1, "<=", i)]
        for row, op in ((rmax, "max"), (rmin, "min")):
            e = check_case(m, cols, [a, b], row, op, ex)
            if e:
                msg.append(f"par+linha {op}: {e}")
        # terceiro bloco: H = bloco de grau f (fora a,b) com |H cap F| maximo
        others = [x for x in idxs if x not in (a, b)]
        if others:
            hh = max(others, key=lambda x: len(cols[x] & cols[a]))
            jj = len(cols[hh] & cols[a])
            ex3 = [([f], 0, "<=", i), ([f], 1, "<=", i),
                   ([f], 0, "<=", jj)]
            e = check_case(m, cols, [a, b, hh], rmax, "max", ex3)
            if e:
                msg.append(f"3 blocos+linha: {e}")
        if idx < nl3:
            r = try_profile((m, dict(p), 3, n, sum(len(c) for c in cols)))
            if r["strategy"] is not None:
                msg.append(f"ERRO: perfil real eliminado por {r['strategy']}")
        print(os.path.basename(path), "ok" if not msg else "; ".join(msg[:3]), flush=True)
        bad += bool(msg)
    print("FALHAS:", bad)


if __name__ == "__main__":
    main()
