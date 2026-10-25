#!/usr/bin/env python3
"""Enumera perfis para (m,n,k) e tenta elimina-los com certificados de Farkas.

  search.py m n k [--level L] [--jobs J] [--out certificates/]

Estrategias (cada uma e uma divisao completa em casos; o perfil e eliminado se todos os
casos tem certificado):
  L0 f            : fixa um bloco F de grau f.                      (1 caso)
  L1 f g any      : fixa F (grau f) e outro bloco G (grau g); ramifica em i=|F cap G|.
  L1 f g maxG     : G = bloco de grau g (!= F) com |G cap F| maximo; os outros blocos de
                    grau g tem |B cap F| <= i.
  L1 f g minG     : idem com minimo (>= i).
  L1 f f maxpair  : (F,G) = par de blocos de grau f com |F cap G| maximo; os outros
                    blocos de grau f tem |B cap F| <= i e |B cap G| <= i.
  L1 f f minpair  : idem com minimo.
"""
import json
import os
import sys
import time
from math import comb
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bnb import bnb  # noqa: E402
from lp import farkas  # noqa: E402
from model import build  # noqa: E402

BNB_NODES = int(os.environ.get("BNB_NODES", "400"))
BNB_NODES_REFINE = int(os.environ.get("BNB_NODES_REFINE", "30"))
REFINE_BUDGET = int(os.environ.get("REFINE_BUDGET", "30000"))  # nos de LP por perfil
from refine import prove  # noqa: E402


def profiles(m, n, total):
    cap = 2 * comb(m, 3)
    out = []

    def rec(d, cols_left, ones_left, cap_left, cur):
        if d < 0:
            if cols_left == 0 and ones_left == 0:
                out.append(dict(cur))
            return
        for k in range(cols_left + 1):
            if k * d > ones_left or k * comb(d, 3) > cap_left:
                break
            rest = cols_left - k
            if rest * max(d - 1, 0) < ones_left - k * d:
                continue
            if k:
                cur[d] = k
            rec(d - 1, rest, ones_left - k * d, cap_left - k * comb(d, 3), cur)
            cur.pop(d, None)

    rec(m, n, total, cap, {})
    return out


def pname(p):
    return " ".join(f"{d}^{c}" for d, c in sorted(p.items()))


def l1_cases(m, f, g, mode):
    cases = []
    for i in range(max(0, f + g - m), min(f, g) + 1):
        sz = [m - f - g + i, f - i, g - i, i]
        if mode == "any":
            ex = []
        elif mode == "maxG":
            ex = [([g], 0, "<=", i)]
        elif mode == "minG":
            ex = [([g], 0, ">=", i)]
        elif mode == "maxpair":
            ex = [([f], 0, "<=", i), ([f], 1, "<=", i)]
        elif mode == "minpair":
            ex = [([f], 0, ">=", i), ([f], 1, ">=", i)]
        cases.append(dict(s=2, sz=sz, excl=ex))
    return cases


def strategies(p, level):
    degs = sorted(p)
    for f in degs:
        yield ("L0", f), [dict(s=1, sz=None, excl=[], f=f)]
    if level < 1:
        return
    for f in sorted(degs, key=lambda d: -p[d]):
        if p[f] >= 2:
            for mode in ("maxpair", "minpair"):
                yield ("L1", f, f, mode), None
    for f in degs:
        for g in degs:
            if g == f and p[f] < 2:
                continue
            for mode in ("maxG", "minG"):
                yield ("L1", f, g, mode), None


def try_profile(args):
    m, p, level = args[:3]
    nk = args[3:5] if len(args) > 3 else None
    r = _try(m, p, min(level, 1), use_bnb=False)
    if r["strategy"] is None and level >= 2:
        r2 = _try(m, p, 1, use_bnb=True)
        r2["tried"] += r["tried"]
        r2["sec"] = round(r2["sec"] + r["sec"], 2)
        if r2["strategy"] is None and level >= 3:
            r3 = _try(m, p, 1, use_bnb=True, depth=level - 2, nk=nk)
            r3["tried"] += r2["tried"]
            r3["sec"] = round(r3["sec"] + r2["sec"], 2)
            return r3
        return r2
    return r


def _try(m, p, level, use_bnb, depth=0, nk=None):
    t0 = time.time()
    tried = 0
    budget = [REFINE_BUDGET]
    for strat, cases in strategies(p, level):
        if strat[0] == "L0":
            f = strat[1]
            cases = [dict(s=1, sz=[m - f, f], excl=[])]
        else:
            cases = l1_cases(m, strat[1], strat[2], strat[3])
        tried += 1
        proof = []
        ok = True
        for c in cases:
            if depth > 0:
                node = prove(m, p, c, depth, BNB_NODES_REFINE, budget, nk)
                if node is None:
                    ok = False
                    break
                proof.append(node)
                continue
            model = build(m, p, c["s"], c["sz"], c["excl"])
            if model is None:
                proof.append(dict(case=c, kind="invalid_config"))
                continue
            a = farkas(model)
            if a is None or a == "ROUNDING_FAILED":
                if use_bnb:
                    tree, _ = bnb(model, max_nodes=BNB_NODES)
                    if tree is not None:
                        proof.append(dict(case=c, kind="bnb", tree=tree,
                                          T=[list(t) for t in model["T"]]))
                        continue
                ok = False
                break
            proof.append(dict(case=c, kind="farkas", alpha=a,
                              T=[list(t) for t in model["T"]]))
        if ok:
            return dict(profile=p, strategy=list(strat), cases=proof, tried=tried,
                        sec=round(time.time() - t0, 2))
    return dict(profile=p, strategy=None, tried=tried, sec=round(time.time() - t0, 2))


def main():
    a = sys.argv
    m, n, k = int(a[1]), int(a[2]), int(a[3])
    level = int(a[a.index("--level") + 1]) if "--level" in a else 1
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 4
    out = a[a.index("--out") + 1] if "--out" in a else None
    P = profiles(m, n, k)
    print(f"z({m},{n}) k={k}: {len(P)} perfis", flush=True)
    # --reuse arquivo.json: perfis ja eliminados nesse arquivo sao copiados (o
    # check_cert.py confere tudo de novo); so os sobreviventes sao recalculados.
    old = {}
    if "--reuse" in a:
        R = json.load(open(a[a.index("--reuse") + 1]))
        assert (R["m"], R["n"], R["k"]) == (m, n, k)
        for r in R["results"]:
            if r["strategy"]:
                p = {int(d): c for d, c in r["profile"].items()}
                old[tuple(sorted(p.items()))] = dict(r, profile=p)
    todo = [p for p in P if tuple(sorted(p.items())) not in old]
    with Pool(jobs) as pool:
        new = pool.map(try_profile, [(m, p, level, n, k) for p in todo], chunksize=1)
    newd = {tuple(sorted(r["profile"].items())): r for r in new}
    res = [old.get(tuple(sorted(p.items()))) or newd[tuple(sorted(p.items()))] for p in P]
    left = [r for r in res if r["strategy"] is None]
    for r in res:
        st = " ".join(map(str, r["strategy"])) if r["strategy"] else "SOBREVIVE"
        print(f"  {pname(r['profile']):40s} {st:22s} ({r['tried']} estrat., {r['sec']}s)")
    print(f"eliminados {len(P) - len(left)} de {len(P)}; sobram {len(left)}", flush=True)
    if out:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, f"z{m}_{n}_k{k}.json"), "w") as fh:
            json.dump(dict(m=m, n=n, k=k, nprofiles=len(P), level=level,
                           results=[dict(r, profile={str(d): c for d, c in r["profile"].items()})
                                    for r in res]), fh)


if __name__ == "__main__":
    main()
