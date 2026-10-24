#!/usr/bin/env python3
"""Barra trivial: max(LO do artigo, regras de adicionar/remover linha/coluna),
aplicadas ate ponto fixo sobre a tabela inteira. Gera bars.csv."""
import csv
from table import MS, NS, up, lo

bar = {(m, n): lo(m, n) for m in MS for n in NS}
rule = {(m, n): "artigo" for m in MS for n in NS}


def push(key, val, why):
    if key in bar and val > bar[key]:
        bar[key] = val
        rule[key] = why
        return True
    return False


changed = True
while changed:
    changed = False
    for (m, n), z in list(bar.items()):
        # adicionar coluna/linha com 2 uns
        changed |= push((m, n + 1), z + 2, f"Z({m},{n})+2 [add col]")
        changed |= push((m + 1, n), z + 2, f"Z({m},{n})+2 [add lin]")
        # remover a coluna/linha mais vazia
        changed |= push((m, n - 1), z - z // n, f"Z({m},{n})-floor({z}/{n}) [rem col]")
        changed |= push((m - 1, n), z - z // m, f"Z({m},{n})-floor({z}/{m}) [rem lin]")

with open("bars.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["m", "n", "UP", "LO_artigo", "BARRA_trivial", "regra", "aberto"])
    for m in MS:
        for n in NS:
            b = bar[(m, n)]
            assert b <= up(m, n), (m, n, b, up(m, n))
            w.writerow([m, n, up(m, n), lo(m, n), b, rule[(m, n)],
                        int(up(m, n) > lo(m, n))])

opens = [(m, n) for m in MS for n in NS if up(m, n) > lo(m, n)]
better = [(m, n) for (m, n) in opens if bar[(m, n)] > lo(m, n)]
print(f"{len(opens)} casos abertos; barra trivial supera o artigo em {len(better)}:")
for m, n in better:
    print(f"  Z({m},{n}): artigo {lo(m, n)}, barra {bar[(m, n)]}, UP {up(m, n)}  <- {rule[(m, n)]}")
