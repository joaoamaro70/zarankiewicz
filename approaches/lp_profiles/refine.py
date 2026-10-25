"""Refinamento recursivo de casos.

split (bloco): dado um grau h com blocos livres, um conjunto de regioes U e op in
{max, min}: H = bloco livre de grau h (entre os que obedecem as regras do caso) que
maximiza (minimiza) |H cap U|. Um filho por tipo b possivel de H, com s+1 fixos:
    regioes antigas a: tamanho sz[a] - b[a], mascara rm[a];
    regioes novas a + N (N = numero de regioes): tamanho b[a], mascara rm[a] | 2^s;
    regras antigas com listas R traduzidas para R + {a + N}; nova regra:
    blocos livres de grau h tem |B cap U'| <= j (max) ou >= j (min), j = |H cap U|.
    Linhas fixadas: a linha rho vai para rho (se b[rho] = 0) ou rho + N (se b[rho] = 1).

rowsplit: (so se ainda nao ha linha fixada) a linha de grau maximo (op max) ou minimo
(op min) esta em alguma regiao a e tem algum grau v; um filho por (a, v) com sz[a] >= 1 e
v em [ceil(k/m), n] (max) ou [0, floor(k/m)] (min): a regiao a perde uma linha, que vira
uma regiao nova de tamanho 1 com a mesma mascara (listas de regras que contem a ganham a
regiao nova); rows = [[nova, v, op]].
"""
from bnb import bnb
from lp import farkas
import os

from model import build, compositions, rule_masks, allowed, regmasks

ROWFIRST = os.environ.get("ROWFIRST", "1") == "1"


def children(m, p, case, h, U, op):
    s, sz, excl = case["s"], case["sz"], case["excl"]
    rm = regmasks(case)
    N = len(sz)
    out = []
    for b in compositions(h, list(sz)):
        if not allowed(b, h, excl, rm):
            continue
        j = sum(b[a] for a in U)
        sz2 = [sz[a] - b[a] for a in range(N)] + [b[a] for a in range(N)]
        rm2 = list(rm) + [rm[a] | (1 << s) for a in range(N)]
        ex2 = []
        for degs, Rr, o, bound in excl:
            ms = rule_masks(Rr, N, rm)
            ex2.append([list(degs), sorted(ms + [a + N for a in ms]), o, bound])
        U2 = sorted(list(U) + [a + N for a in U])
        ex2.append([[h], U2, "<=" if op == "max" else ">=", j])
        rows2 = [[r + N * b[r], v, o] for r, v, o in case.get("rows", [])]
        c = dict(s=s + 1, sz=sz2, excl=ex2, rm=rm2)
        if rows2:
            c["rows"] = rows2
        out.append(c)
    return out


def row_children(m, n, k, case, op):
    sz, excl = case["sz"], case["excl"]
    rm = regmasks(case)
    N = len(sz)
    vs = range(-(-k // m), n + 1) if op == "max" else range(0, k // m + 1)
    out = []
    for a in range(N):
        if sz[a] < 1:
            continue
        sz2 = list(sz) + [1]
        sz2[a] -= 1
        rm2 = list(rm) + [rm[a]]
        ex2 = []
        for degs, Rr, o, bound in excl:
            ms = rule_masks(Rr, N, rm)
            ex2.append([list(degs), sorted(ms + ([N] if a in ms else [])), o, bound])
        for v in vs:
            out.append(dict(s=case["s"], sz=sz2, excl=ex2, rm=rm2, rows=[[N, v, op]]))
    return out


def options(case, p, m):
    """(h, U, op) candidatos para refinar com um bloco."""
    s, sz = case["s"], case["sz"]
    rm = regmasks(case)
    N = len(sz)
    rem = dict(p)
    for i in range(s):
        d = sum(sz[a] for a in range(N) if rm[a] >> i & 1)
        rem[d] -= 1
    hs = sorted((d for d, c in rem.items() if c > 0), key=lambda d: -rem[d])
    Us = [[a for a in range(N) if rm[a] >> i & 1] for i in range(s)]
    Us.append([a for a in range(N) if rm[a] == (1 << s) - 1])  # intersecao de todos
    Us.append([a for a in range(N) if rm[a] != 0])  # uniao
    for r, _, _ in case.get("rows", []):
        Us.append([r])  # contem a linha fixada
    seen = []
    for U in Us:
        U = [a for a in U if sz[a] > 0]
        if U and U not in seen:
            seen.append(U)
    for h in hs:
        for U in seen:
            for op in ("max", "min"):
                yield h, U, op


def mk(m, p, case):
    return build(m, p, case["s"], case["sz"], case["excl"], case.get("rm"), case.get("rows", ()))


def prove(m, p, case, depth, bnb_nodes=0, budget=None, nk=None, rowfirst=ROWFIRST):
    """Retorna no de prova ou None. nk = (n, k) habilita rowsplit."""
    if budget is not None:
        budget[0] -= 1
        if budget[0] < 0:
            return None
    model = mk(m, p, case)
    if model is None:
        return dict(case=case, kind="invalid_config")
    a = farkas(model)
    if isinstance(a, list):
        return dict(case=case, kind="farkas", alpha=a, T=model["T"])
    if bnb_nodes:
        tree, _ = bnb(model, max_nodes=bnb_nodes)
        if tree is not None:
            return dict(case=case, kind="bnb", tree=tree, T=model["T"])
    if depth <= 0:
        return None
    opts = []
    if nk and not case.get("rows"):
        opts += [("row", op) for op in ("max", "min")]
    opts += [("blk",) + o for o in options(case, p, m)]
    if not rowfirst:
        opts = opts[2:] + opts[:2] if opts and opts[0][0] == "row" else opts
    for o in opts:
        kids = []
        cs = row_children(m, nk[0], nk[1], case, o[1]) if o[0] == "row" else \
            children(m, p, case, o[1], o[2], o[3])
        for c in cs:
            kd = prove(m, p, c, depth - 1, bnb_nodes, budget, nk, rowfirst)
            if kd is None:
                break
            kids.append(kd)
        else:
            if o[0] == "row":
                return dict(case=case, kind="rowsplit", op=o[1], children=kids)
            return dict(case=case, kind="split", h=o[1], U=o[2], op=o[3], children=kids)
        if budget is not None and budget[0] < 0:
            return None
    return None
