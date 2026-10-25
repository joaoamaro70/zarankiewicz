#!/usr/bin/env python3
"""LNS com SAT exato para limites inferiores de z(m,n;3,3).

Parte da matriz atual X (|X| uns), escolhe uma janela de celulas livres, congela o
resto e pergunta ao Kissat se existe preenchimento da janela com >= |X|+1 uns no
total sem K_{3,3}. Clausulas 3x3 so onde ha variavel livre; constantes simplificadas.

Janelas (mode, a, b):
  rows  a linhas inteiras livres (lex entre as linhas livres: sao intercambiaveis)
  cols  a colunas inteiras livres (lex entre as colunas livres)
  cross a linhas inteiras + b colunas inteiras
  block a linhas x b colunas

  lns.py run m n segundos [semente]   roda LNS na celula, estado em state/, saida em found/
  lns.py one m n mode a b [timeout]   resolve uma janela aleatoria (calibracao)
"""
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from itertools import combinations
from math import comb

sys.path.insert(0, "/work/sat")
from zsat import CNF  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.gettempdir()


def load(path):
    rows = [l.strip() for l in open(path) if l.strip() and not l.startswith("#")]
    return [[int(ch) for ch in l] for l in rows]


def ones(A):
    return sum(map(sum, A))


def save(A, path, note=""):
    m, n = len(A), len(A[0])
    with open(path + ".tmp", "w") as f:
        f.write(f"# Z({m},{n},3,3) >= {ones(A)}  (LNS-SAT{note})\n")
        f.write("\n".join("".join(map(str, r)) for r in A) + "\n")
    os.replace(path + ".tmp", path)


def is_valid(A):
    m, n = len(A), len(A[0])
    masks = [sum(1 << c for c in range(n) if A[r][c]) for r in range(m)]
    for a, b, c in combinations(range(m), 3):
        if bin(masks[a] & masks[b] & masks[c]).count("1") >= 3:
            return False
    return True


def window_cells(m, n, mode, R, C):
    if mode == "rows":
        return {(r, c) for r in R for c in range(n)}
    if mode == "cols":
        return {(r, c) for r in range(m) for c in C}
    if mode == "cross":
        return {(r, c) for r in R for c in range(n)} | {(r, c) for r in range(m) for c in C}
    if mode == "block":
        return {(r, c) for r in R for c in C}
    raise ValueError(mode)


def build(A, free, target, mode, R, C, forbid_current=False):
    """CNF: preenchimento das celulas livres com >= target uns no total."""
    m, n = len(A), len(A[0])
    cells = sorted(free)
    vid = {rc: i + 1 for i, rc in enumerate(cells)}
    F = CNF(len(cells))
    fixed_ones = ones(A) - sum(A[r][c] for r, c in cells)
    need = target - fixed_ones
    if need > len(cells):
        return None, vid
    one_mask = [0] * m
    free_mask = [0] * m
    for r in range(m):
        for c in range(n):
            if (r, c) in free:
                free_mask[r] |= 1 << c
            elif A[r][c]:
                one_mask[r] |= 1 << c
    hasfree = [free_mask[r] != 0 for r in range(m)]
    for T in combinations(range(m), 3):
        if not (hasfree[T[0]] or hasfree[T[1]] or hasfree[T[2]]):
            continue
        cand = (one_mask[T[0]] | free_mask[T[0]]) & (one_mask[T[1]] | free_mask[T[1]]) \
            & (one_mask[T[2]] | free_mask[T[2]])
        cl = []
        c = 0
        while cand:
            if cand & 1:
                cl.append([-vid[(r, c)] for r in T if (r, c) in vid])
            cand >>= 1
            c += 1
        for a, b, d in combinations(cl, 3):
            lits = a + b + d
            if lits:
                F.add(lits)
    if need > 0:
        F.at_most([-vid[rc] for rc in cells], len(cells) - need)
    if mode == "rows" and not forbid_current:
        Rs = sorted(R)
        for i in range(len(Rs) - 1):
            F.lex_geq([vid[(Rs[i], c)] for c in range(n)], [vid[(Rs[i + 1], c)] for c in range(n)])
    if mode == "cols" and not forbid_current:
        Cs = sorted(C)
        for i in range(len(Cs) - 1):
            F.lex_geq([vid[(r, Cs[i])] for r in range(m)], [vid[(r, Cs[i + 1])] for r in range(m)])
    if forbid_current:
        F.add([(-vid[rc] if A[rc[0]][rc[1]] else vid[rc]) for rc in cells])
    return F, vid


def solve(F, timeout, seed=0):
    """Retorna ('SAT', modelo) | ('UNSAT', None) | ('UNKNOWN', None)."""
    if F is None:
        return "UNSAT", None
    fd, path = tempfile.mkstemp(suffix=".cnf", dir=TMP)
    os.close(fd)
    try:
        F.write(path)
        p = subprocess.run(["kissat", "-q", f"--seed={seed}", f"--time={int(timeout)}", path],
                           capture_output=True, text=True, timeout=timeout + 30)
    except subprocess.TimeoutExpired:
        return "UNKNOWN", None
    finally:
        os.remove(path)
    if p.returncode == 20:
        return "UNSAT", None
    if p.returncode != 10:
        return "UNKNOWN", None
    val = set()
    for line in p.stdout.splitlines():
        if line.startswith("v "):
            val.update(int(t) for t in line.split()[1:] if int(t) > 0)
    return "SAT", val


def apply(A, vid, model):
    B = [row[:] for row in A]
    for (r, c), v in vid.items():
        B[r][c] = 1 if v in model else 0
    return B


def try_window(A, mode, R, C, target, timeout, seed=0, forbid_current=False):
    free = window_cells(len(A), len(A[0]), mode, R, C)
    t = time.time()
    F, vid = build(A, free, target, mode, R, C, forbid_current)
    st, model = solve(F, timeout, seed)
    B = apply(A, vid, model) if st == "SAT" else None
    return st, B, time.time() - t


def n_windows(m, n, mode, a, b):
    if mode == "rows":
        return comb(m, a)
    if mode == "cols":
        return comb(n, a)
    return comb(m, a) * comb(n, b)


def windows(m, n, mode, a, b, rng, limit):
    """Todas as janelas se forem <= limit, senao limit aleatorias distintas."""
    N = n_windows(m, n, mode, a, b)
    if N <= limit:
        if mode == "rows":
            out = [(R, ()) for R in combinations(range(m), a)]
        elif mode == "cols":
            out = [((), C) for C in combinations(range(n), a)]
        else:
            out = [(R, C) for R in combinations(range(m), a) for C in combinations(range(n), b)]
        rng.shuffle(out)
        return out, True
    seen = set()
    out = []
    while len(out) < limit:
        R = tuple(sorted(rng.sample(range(m), a))) if mode != "cols" else ()
        C = tuple(sorted(rng.sample(range(n), b if mode != "cols" else a))) if mode != "rows" else ()
        if (R, C) not in seen:
            seen.add((R, C))
            out.append((R, C))
    return out, False


# Fases em ordem crescente de tamanho; cada fase e (mode, a, b).
def phases(m, n):
    P = []
    for s in range(1, 9):
        P.append(("rows", s, 0))
        P.append(("cols", s, 0))
        if s >= 1:
            P.append(("cross", s, s))
    for f in (0.6, 0.7, 0.8, 0.9):
        P.append(("block", round(m * f), round(n * f)))
    return P


def key(ph):
    return f"{ph[0]}:{ph[1]}:{ph[2]}"


def run(m, n, budget, seed):
    rng = random.Random(seed * 1000 + m * 31 + n)
    sp = os.path.join(HERE, "state", f"{m}_{n}.json")
    fp = os.path.join(HERE, "found", f"Z_{m}_{n}.txt")
    cp = os.path.join(HERE, "state", f"cur_{m}_{n}.txt")
    if os.path.exists(sp):
        S = json.load(open(sp))
        A = load(cp)
    else:
        A = load(os.environ.get("LNS_START", f"/work/results/Z_{m}_{n}.txt"))
        S = {"start": ones(A), "best": ones(A), "stats": {}, "improvements": [],
             "plateau_moves": 0, "dead": [], "done": [], "elapsed": 0.0}
    assert is_valid(A)
    t0 = time.time()
    TO = 40          # timeout por instancia (s)
    LIMIT = 300      # janelas por fase (todas se houver menos que isso)
    PHASE_CAP = 900  # s por fase; o resto da fase fica para depois do plato
    log = open(os.path.join(HERE, "logs", f"{m}_{n}.log"), "a")

    def say(msg):
        log.write(f"[{time.strftime('%H:%M:%S')}] {m}x{n} |X|={ones(A)} {msg}\n")
        log.flush()

    def persist():
        S["elapsed"] += time.time() - persist.t
        persist.t = time.time()
        save(A, cp)
        json.dump(S, open(sp + ".tmp", "w"), indent=1)
        os.replace(sp + ".tmp", sp)
    persist.t = time.time()

    say(f"inicio (best={S['best']}, start={S['start']})")
    while time.time() - t0 < budget:
        improved = False
        for ph in phases(m, n):
            # fase morta mata as maiores do mesmo tipo
            bigger = any(d.split(":")[0] == ph[0] and int(d.split(":")[1]) <= ph[1]
                         and int(d.split(":")[2]) <= ph[2] for d in S["dead"])
            if bigger or key(ph) in S["done"]:
                continue
            k = key(ph)
            st = S["stats"].setdefault(k, {"unsat": 0, "sat": 0, "unknown": 0, "time": 0.0,
                                           "sweeps_full": 0})
            W, full = windows(m, n, *ph, rng, LIMIT)
            nunk = 0
            nproc = 0
            tph = time.time()
            capped = False
            for R, C in W:
                if time.time() - tph > PHASE_CAP:
                    capped = True
                    break
                if time.time() - t0 > budget:
                    break
                res, B, dt = try_window(A, ph[0], R, C, ones(A) + 1, TO, rng.randrange(1 << 20))
                st["time"] += dt
                nproc += 1
                if res == "UNSAT":
                    st["unsat"] += 1
                elif res == "UNKNOWN":
                    st["unknown"] += 1
                    nunk += 1
                else:
                    assert is_valid(B) and ones(B) > ones(A)
                    st["sat"] += 1
                    A = B
                    S["improvements"].append({"ones": ones(A), "phase": k, "R": R, "C": C,
                                              "t": S["elapsed"] + time.time() - persist.t})
                    if ones(A) > S["best"]:
                        S["best"] = ones(A)
                        save(A, fp)
                    say(f"MELHORA -> {ones(A)} via {k} R={R} C={C}")
                    improved = True
                    S["done"] = []
                    persist()
                    break
                # muitas indecisoes: fase grande demais, marca como morta
                if nproc >= 10 and nunk > 0.3 * nproc:
                    S["dead"].append(k)
                    say(f"fase {k} abandonada ({nunk}/{nproc} timeouts)")
                    break
            if improved:
                break
            if k in S["dead"]:
                persist()
                continue
            if nproc < len(W) and not capped:
                break  # fim da fatia; retoma esta fase na proxima
            if full and nunk == 0 and not capped:
                st["sweeps_full"] += 1
            S["done"].append(k)
            say(f"fase {k}: {nproc} janelas, unsat={st['unsat']} unk={st['unknown']} "
                f"t_med={st['time'] / max(1, st['unsat'] + st['unknown'] + st['sat']):.2f}s")
            persist()
            if time.time() - t0 > budget:
                break
        if improved or time.time() - t0 > budget:
            continue
        # estagnou: movimentos de plato (outra matriz com o mesmo |X|) em janelas block/cross
        moved = 0
        for _ in range(40):
            if time.time() - t0 > budget:
                break
            mode = rng.choice(["block", "cross"])
            if mode == "block":
                a = rng.randint(m // 3, m // 2 + 1)
                b = rng.randint(n // 3, n // 2 + 1)
            else:
                a, b = rng.randint(1, 3), rng.randint(1, 3)
            R = tuple(sorted(rng.sample(range(m), a)))
            C = tuple(sorted(rng.sample(range(n), b)))
            res, B, dt = try_window(A, mode, R, C, ones(A), 20, rng.randrange(1 << 20),
                                    forbid_current=True)
            if res == "SAT":
                assert is_valid(B) and ones(B) >= ones(A)
                A = B
                moved += 1
                if ones(A) > S["best"]:
                    S["best"] = ones(A)
                    save(A, fp)
                    say(f"MELHORA (plato) -> {ones(A)}")
        S["plateau_moves"] += moved
        S["plateau_rounds"] = S.get("plateau_rounds", 0) + 1
        if moved:
            S["done"] = []
        say(f"plato: {moved} movimentos")
        persist()
    persist()
    say(f"fim da fatia; best={S['best']}")


def one(m, n, mode, a, b, timeout):
    A = load(f"/work/results/Z_{m}_{n}.txt")
    rng = random.Random()
    W, _ = windows(m, n, mode, a, b, rng, 1)
    R, C = W[0]
    free = window_cells(m, n, mode, R, C)
    t = time.time()
    F, vid = build(A, free, ones(A) + 1, mode, R, C)
    tb = time.time() - t
    nv, nc = (F.nv, len(F.clauses)) if F else (0, 0)
    st, model = solve(F, timeout)
    print(f"{m}x{n} {mode}:{a}:{b} livres={len(free)} vars={nv} cls={nc} "
          f"build={tb:.2f}s total={time.time() - t:.2f}s -> {st}", flush=True)


if __name__ == "__main__":
    a = sys.argv
    if a[1] == "run":
        os.makedirs(os.path.join(HERE, "state"), exist_ok=True)
        os.makedirs(os.path.join(HERE, "found"), exist_ok=True)
        os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
        run(int(a[2]), int(a[3]), float(a[4]), int(a[5]) if len(a) > 5 else 0)
    elif a[1] == "one":
        one(int(a[2]), int(a[3]), a[4], int(a[5]), int(a[6]), float(a[7]) if len(a) > 7 else 60)
