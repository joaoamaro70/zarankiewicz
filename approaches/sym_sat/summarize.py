#!/usr/bin/env python3
"""Resume logs/results.jsonl: escreve logs/results.csv (uma linha por instancia, melhor
tentativa) e imprime uma tabela markdown por celula e por k."""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
rank = {"SAT": 3, "UNSAT": 2, "TIMEOUT": 1, "ERROR": 0}
best = {}
with open(os.path.join(HERE, "logs", "results.jsonl")) as f:
    for line in f:
        r = json.loads(line)
        key = (r["m"], r["n"], r["k"], r["rows"], r["cols"])
        old = best.get(key)
        if old is None or (rank[r["status"]], r.get("timeout", 0)) > (rank[old["status"]], old.get("timeout", 0)):
            best[key] = r

with open(os.path.join(HERE, "logs", "results.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["m", "n", "k", "row_cycles", "col_cycles", "orbits", "status", "timeout_s",
                "solve_s", "sat_ones", "greedy_ones"])
    for key in sorted(best):
        r = best[key]
        w.writerow([*key, r.get("orbits"), r["status"], r.get("timeout"), r.get("solve_s"),
                    r.get("sat_ones", ""), r.get("greedy_ones", "")])

agg = defaultdict(lambda: defaultdict(int))
tsum = defaultdict(float)
sats = defaultdict(list)
for (m, n, k, rs, cs), r in best.items():
    agg[(m, n, k)][r["status"]] += 1
    tsum[(m, n, k)] += r.get("wall_s", 0) or 0
    if r["status"] == "SAT":
        sats[(m, n, k)].append(f"{rs}/{cs}->{r.get('greedy_ones')}")
print("| m | n | k | instancias | SAT | UNSAT | TIMEOUT | tempo total (min) | SAT (linhas/colunas->uns) |")
print("|---|---|---|---|---|---|---|---|---|")
for key in sorted(agg):
    a = agg[key]
    print(f"| {key[0]} | {key[1]} | {key[2]} | {sum(a.values())} | {a['SAT']} | {a['UNSAT']} | "
          f"{a['TIMEOUT']} | {tsum[key]/60:.0f} | {', '.join(sats[key][:4])} |")
print(f"\ntotal de tempo de parede somado: {sum(tsum.values())/3600:.1f} h-thread")
