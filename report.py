#!/usr/bin/env python3
"""Gera REPORT.md a partir de results/ (so entram matrizes que passam no verify.py)."""
import csv
import os
import sys
from table import MS, NS, up, lo
from verify import check

RES = sys.argv[1] if len(sys.argv) > 1 else "results"
bars, rules = {}, {}
with open("bars.csv") as f:
    for r in csv.DictReader(f):
        k = (int(r["m"]), int(r["n"]))
        bars[k], rules[k] = int(r["BARRA_trivial"]), r["regra"]

summ = {}
if os.path.exists(f"{RES}/summary.csv"):
    with open(f"{RES}/summary.csv") as f:
        for r in csv.DictReader(f):
            summ[(int(r["m"]), int(r["n"]))] = r

best, mats = {}, {}
for m in MS:
    for n in NS:
        p = f"{RES}/Z_{m}_{n}.txt"
        if os.path.exists(p):
            ok, v = check(p)
            if ok:
                best[(m, n)] = v
                mats[(m, n)] = [l.strip() for l in open(p) if l.strip() and not l.startswith("#")]


def status(k):
    b = best.get(k, 0)
    if b >= up(*k):
        return "fechado"
    if b > bars[k]:
        return "supera a barra"
    if b > lo(*k):
        return "supera só o artigo"
    if b == lo(*k):
        return "igual ao artigo"
    return "abaixo do artigo"


opens = [(m, n) for m in MS for n in NS if up(m, n) > lo(m, n)]
cnt = {}
for k in opens:
    cnt[status(k)] = cnt.get(status(k), 0) + 1

out = ["# Relatório: limites inferiores para Z(m,n,3,3)", ""]
out.append(f"Casos abertos no artigo: {len(opens)}. " +
           ", ".join(f"{v} {s}" for s, v in sorted(cnt.items(), key=lambda x: -x[1])) + ".")
out.append("")
out.append("Todas as matrizes abaixo passaram no `verify.py` (todas as triplas de linhas e de colunas).")
out.append("\"Supera a barra\" = supera max(LO do artigo, barra trivial). Antes de chamar de novo, "
           "conferir a literatura (seção 8 do handoff).")
out.append("")
out.append("| m | n | UP | LO artigo | barra trivial | nosso | status | iterações | fonte da melhora |")
out.append("|---|---|---|---|---|---|---|---|---|")
for k in opens:
    s = summ.get(k, {})
    src = ",".join(f"{x}:{s.get('src_' + x)}" for x in ("rr", "sa", "sym", "seed")
                   if s.get("src_" + x, "0") != "0")
    it = s.get("iterations", "")
    out.append(f"| {k[0]} | {k[1]} | {up(*k)} | {lo(*k)} | {bars[k]} | **{best.get(k, '-')}** | "
               f"{status(k)} | {it} | {src} |")
out.append("")
out.append("Casos já fechados na tabela (reproduzidos como sementes): " +
           ", ".join(f"Z({m},{n})={best.get((m, n), '-')}{'' if best.get((m, n), 0) >= up(m, n) else ' (não atingido, UP ' + str(up(m, n)) + ')'}"
                     for m in MS for n in NS if up(m, n) == lo(m, n)))
out.append("")
if os.path.exists("literature.csv"):
    out += ["## Comparação com a literatura (gerada por `literature.py`)", "",
            "Fontes: Bhan et al. 2026 (Fig. 2), Davies–Gill–Horsley 2026 (UB, = UP da Fig. 2), "
            "Collins et al. 2016 (Tab. 4), Tan 2022 (Tab. 3, negrito = exato), "
            "Afrasyab 2026 (arXiv 2608.08154), Hou 2026 (arXiv 2608.08549), Saurabh 2026 (arXiv 2608.26603). "
            "LB_lit inclui as regras triviais aplicadas às bases da literatura.", "",
            "| m | n | UB lit | fonte UB | LB lit | fonte LB | nosso | status |",
            "|---|---|---|---|---|---|---|---|"]
    with open("literature.csv") as f:
        for r in csv.DictReader(f):
            out.append(f"| {r['m']} | {r['n']} | {r['UB_lit']} | {r['fonte_UB']} | {r['LB_lit']} | "
                       f"{r['fonte_LB']} | **{r['nosso']}** | {r['status']} |")
    out.append("")
if os.path.exists("bench/compare.txt"):
    out += ["## Benchmark (M3)", "", "```", open("bench/compare.txt").read().rstrip(), "```", ""]
out += ["## Matrizes dos casos que superam a barra ou fecham", ""]
for k in opens:
    if status(k) in ("fechado", "supera a barra"):
        out += [f"### Z({k[0]},{k[1]}) ≥ {best[k]}", "", "```", *mats[k], "```", ""]
open("REPORT.md", "w").write("\n".join(out) + "\n")
print("REPORT.md gerado:", cnt)
