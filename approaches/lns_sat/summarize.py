#!/usr/bin/env python3
"""Tabela markdown por celula a partir de state/*.json."""
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for p in glob.glob(os.path.join(HERE, "state", "*_*.json")):
    m, n = map(int, re.findall(r"(\d+)_(\d+)\.json", p)[0])
    S = json.load(open(p))
    st = S["stats"]
    unsat = sum(v["unsat"] for v in st.values())
    unk = sum(v["unknown"] for v in st.values())
    full = [k for k, v in st.items() if v["sweeps_full"]]
    biggest = {}
    for k, v in st.items():
        mode, a, b = k.split(":")
        if v["unsat"]:
            biggest[mode] = max(biggest.get(mode, (0, 0)), (int(a), int(b)))
    big = ", ".join(f"{md} {a}" + (f"x{b}" if md in ("cross", "block") else "")
                    for md, (a, b) in sorted(biggest.items()))
    rows.append((m, n, S["start"], S["best"], unsat, unk, S["plateau_moves"],
                 S.get("plateau_rounds", 0), len(full), big, S["elapsed"] / 60))
print("| célula | início | melhor | janelas UNSAT | timeouts | mov. platô (rodadas) "
      "| fases varridas por completo | maior janela UNSAT por tipo | min |")
print("|---|---|---|---|---|---|---|---|---|")
for r in sorted(rows):
    print(f"| {r[0]}×{r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} ({r[7]}) | {r[8]} "
          f"| {r[9]} | {r[10]:.0f} |")
