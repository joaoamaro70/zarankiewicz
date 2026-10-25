#!/usr/bin/env python3
"""Campanha: para cada celula aberta de literature.csv, tenta k = nosso+1 com varias acoes
de Z_N (a ciclos de N nas linhas, b ciclos de N nas colunas, resto fixo). Quando SAT,
tenta k+1 na mesma acao. Registro em logs/results.jsonl (retomavel).

  run.py --timeout T --maxorb O [--minorb o] [--nmin N] [--jobs J] [--cells 13x19,14x19]
"""
import argparse
import csv
import json
import os
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, FIRST_COMPLETED, wait

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "logs", "results.jsonl")


def open_cells():
    cells = {}
    with open(os.path.join(HERE, "..", "..", "literature.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m, n = int(row["m"]), int(row["n"])
            ub, lb, ours = int(row["UB_lit"]), int(row["LB_lit"]), int(row["nosso"])
            if ub > max(lb, ours):
                cells[(m, n)] = max(lb, ours)
    return cells


def mixed_configs(m, n, nmin):
    """Ciclos de comprimento p nas linhas e q != p nas colunas (grupo Z_lcm(p,q));
    orbitas bloco x bloco tem tamanho lcm(p,q), gcd(p,q) delas por par de blocos."""
    from math import gcd
    out = []
    for p in range(nmin, m + 1):
        for q in range(nmin, n + 1):
            if p == q:
                continue
            L = p * q // gcd(p, q)
            if L > 2 * max(p, q):
                continue  # grupo grande demais, simetria pouco natural
            for a in range(1, m // p + 1):
                for b in range(1, n // q + 1):
                    r0, c0 = m - a * p, n - b * q
                    orb = a * b * gcd(p, q) + a * c0 + r0 * b + r0 * c0
                    out.append((orb, ".".join([str(p)] * a), ".".join([str(q)] * b)))
    return out


def configs(m, n, nmin, mixed=False):
    if mixed:
        return mixed_configs(m, n, nmin)
    out = []
    for N in range(nmin, max(m, n) + 1):
        for a in range(0, m // N + 1):
            for b in range(0, n // N + 1):
                if a == 0 and b == 0:
                    continue
                r0, c0 = m - a * N, n - b * N
                orb = a * b * N + a * c0 + r0 * b + r0 * c0
                rs = ".".join([str(N)] * a) or "0"
                cs = ".".join([str(N)] * b) or "0"
                out.append((orb, rs, cs))
    return out


def job(m, n, k, rs, cs, timeout, seed):
    outp = os.path.join(HERE, "tmp", f"Z_{m}_{n}__{rs}__{cs}__{k}.txt")
    t = time.time()
    p = subprocess.run(["nice", "-n", "10", "python3", os.path.join(HERE, "symsat.py"), "solve",
                        str(m), str(n), str(k), rs, cs, "--timeout", str(timeout),
                        "--seed", str(seed), "--out", outp],
                       capture_output=True, text=True)
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        res = {"m": m, "n": n, "k": k, "rows": rs, "cols": cs, "status": "ERROR",
               "err": p.stderr[-500:]}
    res["timeout"] = timeout
    res["wall_s"] = round(time.time() - t, 1)
    if res.get("status") == "SAT":
        res["file"] = os.path.relpath(outp, HERE)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--maxorb", type=int, default=120)
    ap.add_argument("--minorb", type=int, default=0)
    ap.add_argument("--nmin", type=int, default=3)
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cells", default="")
    ap.add_argument("--mixed", action="store_true")
    ap.add_argument("--delta", type=int, default=1)
    a = ap.parse_args()
    cells = open_cells()
    if a.cells:
        want = {tuple(map(int, c.split("x"))) for c in a.cells.split(",")}
        cells = {c: v for c, v in cells.items() if c in want}
    done = set()
    if os.path.exists(LOG):
        with open(LOG) as f:
            for line in f:
                r = json.loads(line)
                if r.get("status") in ("SAT", "UNSAT") or r.get("timeout", 0) >= a.timeout:
                    done.add((r["m"], r["n"], r["k"], r["rows"], r["cols"]))
    tasks = []
    for (m, n), best in cells.items():
        for orb, rs, cs in configs(m, n, a.nmin, a.mixed):
            if a.minorb <= orb <= a.maxorb and (m, n, best + a.delta, rs, cs) not in done:
                tasks.append((orb, m, n, best + a.delta, rs, cs))
    tasks.sort()
    print(f"{len(cells)} celulas, {len(tasks)} instancias", flush=True)
    with ProcessPoolExecutor(a.jobs) as ex, open(LOG, "a") as log:
        pend = {}
        it = iter(tasks)

        def submit(t):
            _, m, n, k, rs, cs = t
            pend[ex.submit(job, m, n, k, rs, cs, a.timeout, a.seed)] = t

        for _ in range(a.jobs):
            t = next(it, None)
            if t:
                submit(t)
        while pend:
            fin, _ = wait(pend, return_when=FIRST_COMPLETED)
            for f in fin:
                t = pend.pop(f)
                r = f.result()
                log.write(json.dumps(r) + "\n")
                log.flush()
                if r["status"] == "SAT":
                    print("SAT", json.dumps(r), flush=True)
                    best = max(r["k"], r.get("greedy_ones", 0))
                    submit((t[0], t[1], t[2], best + 1, t[4], t[5]))
                nt = next(it, None)
                if nt:
                    submit(nt)


if __name__ == "__main__":
    main()
