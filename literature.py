#!/usr/bin/env python3
"""Consolida a literatura para Z(m,n,3,3) na faixa da Figura 2, aplica as regras triviais
(adicionar/remover linha/coluna) ate ponto fixo e compara com nossos resultados.
Gera literature.csv. Uso: literature.py [dir_resultados]"""
import csv
import os
import sys
from table import MS, NS, up, lo
from verify import check

# Limites superiores (min com a Figura 2, que ja e a Tabela 2 de Davies-Gill-Horsley 2026)
UB_LIT = {
    # Collins, Riasanovsky, Wallace, Radziszowski (2016), Tabela 4; (12,17)=103 e exato
    (10, 18): (94, "Collins16"), (11, 18): (101, "Collins16"), (12, 17): (103, "Collins16"),
    (12, 18): (109, "Collins16"), (13, 17): (110, "Collins16"), (13, 18): (116, "Collins16"),
    (14, 17): (118, "Collins16"), (14, 18): (124, "Collins16"), (15, 17): (126, "Collins16"),
    (15, 18): (132, "Collins16"), (16, 17): (133, "Collins16"), (16, 18): (140, "Collins16"),
    # Afrasyab (arXiv 2608.08154) e Hou (arXiv 2608.08549): valores exatos
    (12, 18): (108, "Afrasyab26/Hou26"), (12, 19): (114, "Afrasyab26"), (12, 20): (120, "Afrasyab26"),
    (12, 21): (126, "Afrasyab26"), (13, 22): (137, "Afrasyab26"),
    # Tan (2022, arXiv 2203.02283), Tabela 3, valores em negrito (exatos)
    (10, 20): (102, "Tan22"), (11, 18): (101, "Tan22"),
}
# Limites inferiores com matriz explicita
LB_LIT = {
    (10, 20): (102, "Tan22"), (11, 18): (101, "Tan22"),
    (12, 17): (103, "Collins16"),
    (12, 18): (108, "Afrasyab26/Hou26"), (13, 17): (110, "Hou26"), (13, 18): (116, "Hou26"),
    (14, 17): (118, "Hou26"), (14, 18): (124, "Hou26"), (15, 17): (126, "Hou26"),
    (15, 18): (132, "Hou26"), (12, 19): (114, "Afrasyab26"), (12, 20): (120, "Afrasyab26"),
    (12, 21): (126, "Afrasyab26"), (16, 17): (132, "Afrasyab26"),
    # Saurabh (arXiv 2608.26603)
    (13, 19): (118, "Saurabh26"), (14, 19): (126, "Saurabh26"), (16, 18): (136, "Saurabh26"),
    (14, 20): (126, "Saurabh26"), (16, 19): (136, "Saurabh26"),
}

cells = [(m, n) for m in MS for n in NS]
ub = {k: (up(*k), "Fig2/Davies26") for k in cells}
for k, (v, s) in UB_LIT.items():
    if v < ub[k][0]:
        ub[k] = (v, s)
lb = {k: (lo(*k), "Bhan26") for k in cells}
for k, (v, s) in LB_LIT.items():
    if v > lb[k][0]:
        lb[k] = (v, s)


def push(key, val, why):
    if key in lb and val > lb[key][0]:
        lb[key] = (val, why)
        return True
    return False


changed = True
while changed:
    changed = False
    for (m, n), (z, _) in list(lb.items()):
        changed |= push((m, n + 1), z + 2, f"Z({m},{n})+2")
        changed |= push((m + 1, n), z + 2, f"Z({m},{n})+2")
        changed |= push((m, n - 1), z - z // n, f"Z({m},{n})-floor({z}/{n})")
        changed |= push((m - 1, n), z - z // m, f"Z({m},{n})-floor({z}/{m})")
# Limites superiores: as mesmas regras na direcao oposta.
#   densidade (Collins et al., Lema 3): z(m,n+1) <= max{W : W - floor(W/(n+1)) <= z(m,n)}
#   coluna com dois uns:                 z(m,n)   <= z(m,n+1) - 2
ub_pub = dict(ub)


def dens(prev, k):
    W = prev
    while (W + 1) - (W + 1) // k <= prev:
        W += 1
    return W


def push_ub(key, val, why):
    if key in ub and val < ub[key][0]:
        ub[key] = (val, why)
        return True
    return False


changed = True
while changed:
    changed = False
    for (m, n), (u, _) in list(ub.items()):
        changed |= push_ub((m, n + 1), dens(u, n + 1), f"Z({m},{n}) [densidade]")
        changed |= push_ub((m + 1, n), dens(u, m + 1), f"Z({m},{n}) [densidade]")
        changed |= push_ub((m, n - 1), u - 2, f"Z({m},{n})-2")
        changed |= push_ub((m - 1, n), u - 2, f"Z({m},{n})-2")
for k in cells:
    assert lb[k][0] <= ub[k][0], (k, lb[k], ub[k])

RES = sys.argv[1] if len(sys.argv) > 1 else "results"
ours = {}
for k in cells:
    p = f"{RES}/Z_{k[0]}_{k[1]}.txt"
    if os.path.exists(p):
        ok, v = check(p)
        if ok:
            ours[k] = v


def status(k):
    o, l, u = ours.get(k, 0), lb[k][0], ub[k][0]
    if l >= ub_pub[k][0]:
        return "já fechado na literatura" if o >= u else "fechado na literatura (não atingido)"
    if max(o, l) >= u:
        return "NOVO: fecha o caso"
    if o > l:
        return "NOVO: supera a literatura"
    if o == l:
        return "igual à literatura"
    return "abaixo da literatura"


opens = [k for k in cells if up(*k) > lo(*k)]
with open("literature.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["m", "n", "UP_fig2", "LO_artigo", "UB_lit", "fonte_UB", "LB_lit", "fonte_LB",
                "nosso", "status", "UB_publicado", "fonte_UB_publicado"])
    for k in opens:
        w.writerow([*k, up(*k), lo(*k), ub[k][0], ub[k][1], lb[k][0], lb[k][1],
                    ours.get(k, ""), status(k), ub_pub[k][0], ub_pub[k][1]])

cnt = {}
for k in opens:
    cnt[status(k)] = cnt.get(status(k), 0) + 1
print(cnt)
for k in opens:
    if ub[k][0] < ub_pub[k][0]:
        print(f"  UB Z({k[0]},{k[1]}): {ub_pub[k][0]} -> {ub[k][0]} via {ub[k][1]}")
for k in opens:
    if status(k).startswith("NOVO") or "abaixo" in status(k) or "não atingido" in status(k):
        print(f"  Z({k[0]},{k[1]}): nosso {ours.get(k, '-')}, LB lit {lb[k][0]} ({lb[k][1]}), "
              f"UB {ub[k][0]} ({ub[k][1]}) -> {status(k)}")
