"""Busca de certificados de Farkas com HiGHS (scipy) e racionalizacao exata."""
from fractions import Fraction
from math import gcd, lcm

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

from model import check


def rationalize(x, free, den):
    """x: floats; free[i]: multiplicador livre (linha '='), senao corta em 0."""
    fr = [Fraction(float(v) if f else max(float(v), 0.0)).limit_denominator(den)
          for v, f in zip(x, free)]
    L = 1
    for f in fr:
        L = lcm(L, f.denominator)
    z = [int(f * L) for f in fr]
    g = 0
    for v in z:
        g = gcd(g, abs(v))
    return [v // g for v in z] if g > 1 else z


def farkas(model):
    """Retorna lista inteira alpha que certifica inviabilidade (conferida por check),
    None se o LP primal parece viavel, ou 'ROUNDING_FAILED'."""
    nT = len(model["T"])
    degs = model["degs"]
    nD = len(degs)
    di = {d: k for k, d in enumerate(degs)}
    free = [se == "=" for se in model["sense"]]
    present = {d for d, _, _ in model["cols"]}
    if any(d not in present for d in degs):
        alpha = [0] * nT
        ok, _, _ = check(model, alpha)
        return alpha if ok else None
    cols = model["cols"]
    A = lil_matrix((len(cols), nT + nD))
    for r, (d, _, coef) in enumerate(cols):
        for k, c in enumerate(coef):
            if c:
                A[r, k] = -c
        A[r, nT + di[d]] = -1
    Aeq = np.zeros((1, nT + nD))
    Aeq[0, :nT] = model["cap"]
    for d in degs:
        Aeq[0, nT + di[d]] = model["e"][d]
    cobj = np.zeros(nT + nD)
    cobj[:nT] = [0.0 if f else 1.0 for f in free]
    bounds = [(None, None) if f else (0, None) for f in free] + [(None, None)] * nD
    if any(free):  # multiplicadores livres: limita para o LP ficar limitado
        bounds = [(-1e6, 1e6) if f else (0, None) for f in free] + [(None, None)] * nD
    res = linprog(cobj, A_ub=A.tocsr(), b_ub=np.zeros(len(cols)), A_eq=Aeq, b_eq=[-1.0],
                  bounds=bounds, method="highs")
    if res.status != 0:
        return None
    x = res.x[:nT]
    for den in (10**2, 10**3, 10**4, 10**6, 10**8, 10**10):
        alpha = rationalize(x, free, den)
        ok, _, _ = check(model, alpha)
        if ok:
            return alpha
    return "ROUNDING_FAILED"
