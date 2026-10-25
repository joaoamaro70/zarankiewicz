#!/usr/bin/env python3
"""Consolida a literatura para Z(m,n,3,3) na faixa 8 <= m <= 16, 16 <= n <= 23, aplica as
regras elementares (adicionar/remover linha/coluna) ate ponto fixo, nas duas direcoes, e
compara com nossos resultados. Gera literature.csv com as 72 celulas.
Uso: literature.py [dir_resultados]"""
import csv
import os
import sys
from verify import check

MS = range(8, 17)
NS = range(16, 24)

# Bhan, Nobili, Raghuraman, Langer (arXiv 2605.01120v3), Figura 2, conferida contra a
# pagina 6 do PDF. Linhas m = 8..16, colunas n = 16..23. Onde Davies-Gill-Horsley 2026
# (Tabela 2) tem limite superior nessa faixa, ele coincide com UP_FIG2.
UP_FIG2 = [
    [70, 74, 77, 81, 84, 87, 90, 94],
    [77, 81, 85, 89, 93, 96, 100, 104],
    [85, 90, 94, 98, 102, 108, 111, 115],
    [92, 96, 101, 108, 112, 116, 121, 125],
    [99, 108, 113, 118, 122, 127, 132, 136],
    [107, 116, 121, 125, 130, 135, 140, 145],
    [115, 124, 129, 135, 140, 145, 150, 155],
    [123, 132, 138, 143, 149, 154, 160, 165],
    [128, 141, 146, 152, 158, 164, 169, 175],
]
LO_FIG2 = [
    [70, 74, 77, 81, 84, 87, 90, 94],
    [77, 81, 85, 89, 93, 96, 100, 103],
    [85, 90, 94, 98, 99, 106, 110, 112],
    [92, 96, 97, 102, 111, 116, 121, 118],
    [99, 102, 108, 110, 113, 116, 132, 125],
    [107, 106, 115, 114, 119, 127, 137, 135],
    [115, 118, 124, 121, 125, 131, 137, 138],
    [123, 125, 132, 132, 138, 139, 143, 149],
    [128, 128, 130, 132, 146, 147, 149, 158],
]


def up(m, n):
    return UP_FIG2[m - 8][n - 16]


def lo(m, n):
    return LO_FIG2[m - 8][n - 16]


# Limites superiores de outras fontes (ficam os menores)
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
    # repositorio github.com/dfield/finite-zarankiewicz-closures (ultimo commit 15/07/2026),
    # valores exatos com certificados; nao revisado por pares
    (9, 23): (103, "dfield26"), (10, 21): (106, "dfield26"), (10, 22): (110, "dfield26"),
    (10, 23): (112, "dfield26"), (11, 19): (106, "dfield26"), (11, 20): (111, "dfield26"),
    (11, 23): (123, "dfield26"), (12, 23): (134, "dfield26"),
}
# Limites inferiores de outras fontes, todos com matriz explicita (ficam os maiores)
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
    # repositorio dfield (matrizes explicitas dos valores exatos)
    (9, 23): (103, "dfield26"), (10, 21): (106, "dfield26"), (10, 22): (110, "dfield26"),
    (10, 23): (112, "dfield26"), (11, 19): (106, "dfield26"), (11, 20): (111, "dfield26"),
    (11, 23): (123, "dfield26"), (12, 23): (134, "dfield26"),
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


# Limites superiores novos deste trabalho, provados por computador (approaches/):
#   LP: eliminacao de todos os perfis de grau com certificados de Farkas exatos
#       (approaches/lp_profiles/certificates/proofs/); nao usa valores externos.
#   orderly: enumeracao exaustiva por geracao ordenada (approaches/orderly/); usa na poda
#       z(12,19) <= 114 e z(12,20) <= 120 de Afrasyab (preprint).
OUR_UB = {
    (13, 21): (133, "LP"), (13, 23): (142, "LP"), (14, 23): (152, "LP"),
    (15, 21): (151, "LP"), (15, 22): (156, "LP"), (15, 23): (161, "LP"),
    (16, 21): (160, "LP"), (16, 22): (165, "LP"), (16, 23): (171, "LP"),
    (13, 19): (121, "orderly"), (13, 20): (125, "orderly"),
}
for k, (v, s) in OUR_UB.items():
    if v < ub[k][0]:
        ub[k] = (v, s)

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


def is_open_in_bhan(k):
    return up(*k) > lo(*k)


opens = [k for k in cells if is_open_in_bhan(k)]
with open("literature.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["m", "n", "aberto_BNRL26", "UP_fig2", "LO_artigo", "UB_lit", "fonte_UB",
                "LB_lit", "fonte_LB", "nosso", "status", "UB_publicado", "fonte_UB_publicado"])
    for k in cells:
        w.writerow([*k, int(is_open_in_bhan(k)), up(*k), lo(*k), ub[k][0], ub[k][1],
                    lb[k][0], lb[k][1], ours.get(k, ""), status(k), ub_pub[k][0], ub_pub[k][1]])

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
