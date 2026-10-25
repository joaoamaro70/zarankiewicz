"""Branch-and-bound com certificados: prova que o modelo agregado nao tem solucao inteira.

y_b conta colunas, logo e inteiro. Cada no da arvore acrescenta limites lo <= y_b <= hi;
num no com y_b fracionario v, os filhos sao y_b <= floor(v) e y_b >= floor(v)+1 (cobrem
todos os inteiros). Cada folha tem um certificado de Farkas para o LP com os limites:
  para toda coluna b de grau d: sum_t alpha_t c_t(b) + beta_d + up_b - lo_b >= 0
  sum_t alpha_t cap_t + sum_d beta_d e_d + sum up_b*hi_b - sum lo_b*lo_b' < 0
com alpha, up, lo >= 0 inteiros (beta_d calculado exatamente).
"""
from fractions import Fraction
from math import floor, gcd, lcm

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix


def leaf_check(model, alpha, up, lo, bounds):
    """up, lo: dict chave->(multiplicador inteiro >= 0). bounds: chave->(lo, hi)."""
    for a, se in zip(alpha, model.get("sense", ["<="] * len(alpha))):
        if (not isinstance(a, int)) or (se == "<=" and a < 0):
            return False
    for D in (up, lo):
        if any((not isinstance(v, int)) or v < 0 for v in D.values()):
            return False
    val = sum(a * c for a, c in zip(alpha, model["cap"]))
    for key, mu in up.items():
        hi = bounds[key][1]
        if hi is None:
            return False
        val += mu * hi
    for key, mu in lo.items():
        val -= mu * bounds[key][0]
    for d in model["degs"]:
        vals = []
        for dd, b, coef in model["cols"]:
            if dd != d:
                continue
            key = (d, b)
            vals.append(sum(a * c for a, c in zip(alpha, coef)) + up.get(key, 0) - lo.get(key, 0))
        if not vals:
            return True
        val += -min(vals) * model["e"][d]
    return val < 0


def _rat(xs, den, free):
    fr = [Fraction(float(v) if f else max(float(v), 0.0)).limit_denominator(den)
          for v, f in zip(xs, free)]
    L = 1
    for f in fr:
        L = lcm(L, f.denominator)
    return [int(f * L) for f in fr]


def lp_node(model, bounds):
    """Resolve o LP primal com limites. Retorna ('feas', y) ou ('infeas', cert) ou ('fail',)."""
    cols = model["cols"]
    nT = len(model["T"])
    degs = model["degs"]
    present = {d for d, _, _ in cols}
    if any(d not in present for d in degs):
        return ("infeas", dict(alpha=[0] * nT, up={}, lo={}))
    keys = [(d, b) for d, b, _ in cols]
    nc = len(cols)
    sense = model.get("sense", ["<="] * nT)
    free = [se == "=" for se in sense]
    ub = [k for k in range(nT) if not free[k]]
    eqr = [k for k in range(nT) if free[k]]
    A = np.array([[c[2][k] for c in cols] for k in ub], dtype=float)
    E = np.array([[1.0 if c[0] == d else 0.0 for c in cols] for d in degs]
                 + [[c[2][k] for c in cols] for k in eqr])
    e = np.array([model["e"][d] for d in degs] + [model["cap"][k] for k in eqr], dtype=float)
    bnd = [bounds.get(k, (0, None)) for k in keys]
    r = linprog(np.zeros(nc), A_ub=A, b_ub=np.array([model["cap"][k] for k in ub], float),
                A_eq=E, b_eq=e, bounds=bnd, method="highs")
    if r.status == 0:
        return ("feas", r.x)
    if r.status != 2:
        return ("fail",)
    # dual: variaveis alpha(nT), up(nU), lo(nL), beta(nD)
    U = [i for i, k in enumerate(keys) if bnd[i][1] is not None]
    Lw = [i for i, k in enumerate(keys) if bnd[i][0] > 0]
    nU, nL, nD = len(U), len(Lw), len(degs)
    nv = nT + nU + nL + nD
    di = {d: j for j, d in enumerate(degs)}
    M = lil_matrix((nc, nv))
    for i, (d, _, coef) in enumerate(cols):
        for k, c in enumerate(coef):
            if c:
                M[i, k] = -c
        M[i, nT + nU + nL + di[d]] = -1
    for j, i in enumerate(U):
        M[i, nT + j] = -1
    for j, i in enumerate(Lw):
        M[i, nT + nU + j] = 1
    Aeq = np.zeros((1, nv))
    Aeq[0, :nT] = model["cap"]
    for j, i in enumerate(U):
        Aeq[0, nT + j] = bnd[i][1]
    for j, i in enumerate(Lw):
        Aeq[0, nT + nU + j] = -bnd[i][0]
    for d in degs:
        Aeq[0, nT + nU + nL + di[d]] = model["e"][d]
    cobj = np.zeros(nv)
    cobj[:nT + nU + nL] = 1
    vb = ([(-1e6, 1e6) if f else (0, None) for f in free] + [(0, None)] * (nU + nL)
          + [(None, None)] * nD)
    for k in range(nT):
        if free[k]:
            cobj[k] = 0
    res = linprog(cobj, A_ub=M.tocsr(), b_ub=np.zeros(nc), A_eq=Aeq, b_eq=[-1.0],
                  bounds=vb, method="highs")
    if res.status != 0:
        return ("fail",)
    x = res.x[:nT + nU + nL]
    for den in (10**2, 10**3, 10**4, 10**6, 10**8, 10**10):
        z = _rat(x, den, free + [False] * (nU + nL))
        g = 0
        for v in z:
            g = gcd(g, abs(v))
        if g > 1:
            z = [v // g for v in z]
        alpha = z[:nT]
        up = {keys[i]: z[nT + j] for j, i in enumerate(U) if z[nT + j]}
        lo = {keys[i]: z[nT + nU + j] for j, i in enumerate(Lw) if z[nT + nU + j]}
        if leaf_check(model, alpha, up, lo, bounds):
            return ("infeas", dict(alpha=alpha, up=up, lo=lo))
    return ("fail",)


def bnb(model, max_nodes=3000, tol=1e-7):
    """Retorna arvore certificada (dict) se nao houver solucao inteira; None caso contrario
    (solucao inteira encontrada, falha numerica ou limite de nos)."""
    count = [0]
    keys = [(d, b) for d, b, _ in model["cols"]]

    def rec(bounds):
        count[0] += 1
        if count[0] > max_nodes:
            raise StopIteration
        st = lp_node(model, bounds)
        if st[0] == "infeas":
            c = st[1]
            return dict(leaf=dict(alpha=c["alpha"],
                                  up=[[k[0], list(k[1]), v] for k, v in c["up"].items()],
                                  lo=[[k[0], list(k[1]), v] for k, v in c["lo"].items()]))
        if st[0] == "fail":
            raise StopIteration
        y = st[1]
        frac = [(abs(v - round(v)), i) for i, v in enumerate(y) if abs(v - round(v)) > tol]
        if not frac:
            raise StopIteration  # solucao inteira: o modelo agregado nao refuta
        _, i = max(frac)
        v = floor(y[i])
        key = keys[i]
        lo0, hi0 = bounds.get(key, (0, None))
        b1 = dict(bounds)
        b1[key] = (lo0, v)
        b2 = dict(bounds)
        b2[key] = (v + 1, hi0)
        return dict(var=[key[0], list(key[1])], v=v, le=rec(b1), ge=rec(b2))

    try:
        t = rec({})
        return t, count[0]
    except StopIteration:
        return None, count[0]
