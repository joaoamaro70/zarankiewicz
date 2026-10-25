#!/usr/bin/env python3
"""Indicio (nao prova): o modelo agregado com y inteiro e inviavel para os sobreviventes?
  explore_ilp.py m "d^c d^c ..." """
import os
import sys

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import build  # noqa: E402
from search import l1_cases  # noqa: E402


def ilp_feasible(model):
    cols = model["cols"]
    if not cols:
        return False
    nT = len(model["T"])
    A = np.array([[c[2][k] for c in cols] for k in range(nT)], dtype=float)
    E = np.array([[1.0 if c[0] == d else 0.0 for c in cols] for d in model["degs"]])
    e = np.array([model["e"][d] for d in model["degs"]], dtype=float)
    cons = [LinearConstraint(A, -np.inf, np.array(model["cap"], dtype=float)),
            LinearConstraint(E, e, e)]
    r = milp(np.zeros(len(cols)), constraints=cons, integrality=np.ones(len(cols)),
             bounds=Bounds(0, np.inf), options=dict(time_limit=60))
    return {0: True, 2: False}.get(r.status, "?")


def main():
    m = int(sys.argv[1])
    p = {int(x.split("^")[0]): int(x.split("^")[1]) for x in sys.argv[2].split()}
    for f in sorted(p):
        mod = build(m, p, 1, [m - f, f], [])
        print("L0", f, "ILP viavel?", ilp_feasible(mod), flush=True)
    for f in sorted(p):
        for g in sorted(p):
            if f == g and p[f] < 2:
                continue
            modes = ["maxG", "minG"] + (["maxpair", "minpair"] if f == g else [])
            for mode in modes:
                st = []
                for c in l1_cases(m, f, g, mode):
                    mod = build(m, p, 2, c["sz"], c["excl"])
                    st.append(ilp_feasible(mod) if mod else False)
                print("L1", f, g, mode, "ramos viaveis:",
                      [i for i, s in enumerate(st) if s is not False], flush=True)


if __name__ == "__main__":
    main()
