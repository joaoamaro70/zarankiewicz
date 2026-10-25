#!/usr/bin/env python3
"""Roda lns.py em todas as celulas abertas: 2 fatias por celula, 6 processos."""
import csv
import subprocess
import sys
from multiprocessing import Pool

SLICE = int(sys.argv[1]) if len(sys.argv) > 1 else 2400
ROUNDS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
OFFSET = int(sys.argv[3]) if len(sys.argv) > 3 else 0
WORKERS = int(sys.argv[4]) if len(sys.argv) > 4 else 6

cells = []
for r in csv.DictReader(open("/work/literature.csv")):
    if int(r["UB_lit"]) > max(int(r["LB_lit"]), int(r["nosso"])):
        cells.append((int(r["m"]), int(r["n"])))


def job(t):
    (m, n), rnd = t
    subprocess.run(["nice", "-n", "10", "python3", "/work/approaches/lns_sat/lns.py", "run",
                    str(m), str(n), str(SLICE), str(rnd)])
    return m, n, rnd


if __name__ == "__main__":
    tasks = [(c, rnd) for rnd in range(OFFSET, OFFSET + ROUNDS) for c in cells]
    with Pool(WORKERS) as p:
        for m, n, rnd in p.imap_unordered(job, tasks):
            print(f"concluido {m}x{n} rodada {rnd}", flush=True)
