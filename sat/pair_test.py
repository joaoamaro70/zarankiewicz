#!/usr/bin/env python3
"""Teste rapido da restricao de capacidade por par (--pair) no metodo por perfil.
1) correcao: z(9,10)=54 e z(10,11)=64 (Tan 2022);  2) velocidade: 10x14 e 10x15.
Uso: pair_test.py workers limite_por_perfil_s"""
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from profile_sat import encode, profiles  # noqa: E402

OUT = os.path.join(HERE, "pairtest")
os.makedirs(OUT, exist_ok=True)


def run(args):
    m, n, k, i, prof, limit = args
    cnf = os.path.join(OUT, f"p_{m}_{n}_{k}_{i}.cnf")
    encode(m, n, prof, cnf, pair=True)
    t0 = time.time()
    try:
        p = subprocess.run(["kissat", "-q", cnf], capture_output=True, text=True, timeout=limit)
        line = next((l for l in p.stdout.splitlines() if l.startswith("s ")), "s ?")
        res = {"s SATISFIABLE": "SAT", "s UNSATISFIABLE": "UNSAT"}.get(line, "?")
    except subprocess.TimeoutExpired:
        res = "timeout"
    os.remove(cnf)
    return m, n, k, res, time.time() - t0


def batch(cases, workers, limit):
    jobs = [(m, n, k, i, p, limit) for (m, n, k) in cases for i, p in enumerate(profiles(m, n, k))]
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(run, jobs))
    for (m, n, k) in cases:
        rs = [r for r in res if r[:3] == (m, n, k)]
        c = {x: sum(r[3] == x for r in rs) for x in ("SAT", "UNSAT", "timeout", "?")}
        print(f"  {m}x{n} com {k}: {len(rs)} perfis -> SAT {c['SAT']}, UNSAT {c['UNSAT']}, "
              f"timeout {c['timeout']}  | mais lento {max(r[4] for r in rs):.1f}s, "
              f"soma {sum(r[4] for r in rs):.1f}s", flush=True)


workers, limit = int(sys.argv[1]), int(sys.argv[2])
t0 = time.time()
print("1) correcao (esperado: valor exato -> algum SAT; +1 -> todos UNSAT)", flush=True)
batch([(9, 10, 54), (9, 10, 55), (10, 11, 64), (10, 11, 65)], workers, 60)
print(f"   ({time.time() - t0:.0f}s)", flush=True)
print(f"2) velocidade, limite {limit}s por perfil", flush=True)
batch([(10, 14, 77), (10, 14, 78), (10, 15, 81), (10, 15, 82)], workers, limit)
print(f"total {time.time() - t0:.0f}s", flush=True)
