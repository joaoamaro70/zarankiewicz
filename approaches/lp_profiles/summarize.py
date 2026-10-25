#!/usr/bin/env python3
"""Tabela-resumo dos arquivos de certificado (nao confere nada; para isso use check_cert.py).
  summarize.py certificates/*.json"""
import json
import sys


def kinds(node, acc):
    acc[node["kind"]] = acc.get(node["kind"], 0) + 1
    for c in node.get("children", []):
        kinds(c, acc)


rows = []
for path in sys.argv[1:]:
    D = json.load(open(path))
    left = [r for r in D["results"] if not r["strategy"]]
    acc = {}
    for r in D["results"]:
        for c in r.get("cases", []):
            kinds(c, acc)
    rows.append((D["m"], D["n"], D["k"], D["level"], len(D["results"]), len(left), acc,
                 [" ".join(f"{d}^{c}" for d, c in sorted(((int(a), b) for a, b in r["profile"].items())))
                  for r in left]))
for m, n, k, lev, tot, nl, acc, left in sorted(rows):
    print(f"| ({m},{n}) | {k} | {lev} | {tot} | {tot - nl} | {nl} | {acc} |")
    if 0 < nl <= 12:
        print("|  |  |  |  |  |  | sobram: " + "; ".join(left) + " |")
