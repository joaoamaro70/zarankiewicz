#!/usr/bin/env python3
"""Calibracao do metodo por perfil em 10 x n, com valores exatos conhecidos (Tan 2022).

Para cada n: roda todos os perfis com v uns (algum e SAT: "achar") e com v+1 uns (todos
UNSAT: "provar"), em paralelo. Registra o tempo de cada perfil. Para quando um n passa
do limite de tempo (por perfil ou no total).
Uso: calib.py n_inicial n_final workers limite_s
Saida: sat/calib/calib.csv (uma linha por perfil) e um resumo por n na tela.
"""
import csv
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from profile_sat import encode, profiles  # noqa: E402

TAN_10 = {11: 64, 12: 68, 13: 73, 14: 77, 15: 81, 16: 85, 17: 90, 18: 94, 19: 98, 20: 102}
M = 10
OUT = os.path.join(HERE, "calib")
os.makedirs(OUT, exist_ok=True)


def run_profile(args):
    n, k, i, prof, limit = args
    cnf = os.path.join(OUT, f"c_{n}_{k}_{i}.cnf")
    encode(M, n, prof, cnf)
    t0 = time.time()
    try:
        p = subprocess.run(["kissat", "-q", cnf], capture_output=True, text=True, timeout=limit)
        line = next((l for l in p.stdout.splitlines() if l.startswith("s ")), "s ?")
        res = {"s SATISFIABLE": "SAT", "s UNSATISFIABLE": "UNSAT"}.get(line, "?")
    except subprocess.TimeoutExpired:
        res = "timeout"
    dt = time.time() - t0
    os.remove(cnf)
    return n, k, " ".join(map(str, prof)), res, dt


def main():
    n0, n1, workers, limit = map(int, sys.argv[1:5])
    path = os.path.join(OUT, "calib.csv")
    new = not os.path.exists(path)
    f = open(path, "a", newline="")
    w = csv.writer(f)
    if new:
        w.writerow(["n", "k", "tipo", "perfil", "resultado", "segundos"])
    # fila unica em ordem crescente de n: quando um n acaba, os nucleos ja pegam o proximo.
    # Cada resultado e gravado assim que sai. Se algum perfil estoura o limite em n, os
    # perfis ainda nao iniciados de n maiores sao cancelados.
    jobs = []
    for n in range(n0, n1 + 1):
        v = TAN_10[n]
        for k in (v, v + 1):
            for i, prof in enumerate(profiles(M, n, k)):
                jobs.append((n, k, i, prof, limit))
    t0 = time.time()
    results, n_fail = [], None
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(run_profile, j): j for j in jobs}
        for fu in as_completed(futs):
            if fu.cancelled():
                continue
            r = fu.result()
            results.append(r)
            n, k = r[0], r[1]
            tipo = "achar" if k == TAN_10[n] else "provar"
            w.writerow([n, k, tipo, r[2], r[3], f"{r[4]:.1f}"])
            f.flush()
            print(f"  [{time.time() - t0:6.0f}s] n={n} {tipo:6s} {r[3]:7s} {r[4]:7.1f}s", flush=True)
            if r[3] == "timeout" and (n_fail is None or n < n_fail):
                n_fail = n
                for g, j in futs.items():
                    if j[0] > n_fail:
                        g.cancel()
    print(f"{'n':>3} {'tipo':>7} {'perfis':>6} {'SAT':>4} {'UNSAT':>5} {'tout':>4} "
          f"{'max(s)':>8} {'soma(s)':>9}")
    for n in range(n0, n1 + 1):
        v = TAN_10[n]
        for k, tipo in ((v, "achar"), (v + 1, "provar")):
            rs = [r for r in results if r[0] == n and r[1] == k]
            if not rs:
                continue
            ts = [r[4] for r in rs]
            cnt = {x: sum(r[3] == x for r in rs) for x in ("SAT", "UNSAT", "timeout")}
            print(f"{n:>3} {tipo:>7} {len(rs):>6} {cnt['SAT']:>4} {cnt['UNSAT']:>5} "
                  f"{cnt['timeout']:>4} {max(ts):>8.1f} {sum(ts):>9.1f}", flush=True)
    print(f"tempo total: {time.time() - t0:.0f}s; primeiro n com timeout: {n_fail}")
    f.close()


if __name__ == "__main__":
    main()
