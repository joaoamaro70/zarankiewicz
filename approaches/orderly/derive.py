#!/usr/bin/env python3
"""Propaga limites superiores pela densidade:
    z(m,n) <= floor(z(m-1,n) * m / (m-1))   (remover a linha mais vazia)
    z(m,n) <= floor(z(m,n-1) * n / (n-1))   (remover a coluna mais vazia)
partindo de UB_lit (literature.csv) com os limites provados aqui por cima.
Uso: derive.py [m,n,ub ...]   (ex.: derive.py 13,19,121 13,20,125)"""
import csv
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(here, "..", "..", "literature.csv"))))
ub, lb, lit = {}, {}, {}
for r in rows:
    k = (int(r["m"]), int(r["n"]))
    ub[k] = lit[k] = int(r["UB_lit"])
    lb[k] = max(int(r["LB_lit"]), int(r["nosso"]))
for a in sys.argv[1:]:
    m, n, u = map(int, a.split(","))
    ub[(m, n)] = min(ub[(m, n)], u)
changed = True
while changed:
    changed = False
    for (m, n) in sorted(ub):
        best = ub[(m, n)]
        if (m - 1, n) in ub:
            best = min(best, ub[(m - 1, n)] * m // (m - 1))
        if (m, n - 1) in ub:
            best = min(best, ub[(m, n - 1)] * n // (n - 1))
        if best < ub[(m, n)]:
            ub[(m, n)] = best
            changed = True
print("m,n,UB_lit,UB_novo,LB,status")
for k in sorted(ub):
    if ub[k] < lit[k]:
        st = "FECHADO" if ub[k] == lb[k] else "aberto"
        print(f"{k[0]},{k[1]},{lit[k]},{ub[k]},{lb[k]},{st}")
