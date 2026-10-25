#!/usr/bin/env python3
"""SAT com simetria ciclica imposta para limites inferiores de z(m,n;3,3).

Um gerador g de Z_N age nas linhas por sigma (ciclos de comprimento p, demais fixas) e
nas colunas por tau. Exigimos A[sigma r][tau c] = A[r][c], ou seja, A constante em cada
orbita de celulas {(sigma^t r, tau^t c)}. Uma variavel por orbita; clausulas 3x3
reescritas em termos de orbitas (so um representante por orbita de pares (R,C), sem
duplicatas); cardinalidade ponderada pelo tamanho da orbita (literal repetido no contador
sequencial). Resolve com Kissat e completa gulosamente sem a simetria.

  symsat.py solve m n k rowspec colspec [--timeout T] [--seed S] [--out arquivo]
     rowspec/colspec: comprimentos dos ciclos separados por '.', ex. "11" ou "6.6" ou "0"
     (sem ciclos). Linhas/colunas que sobram ficam fixas.
Imprime uma linha JSON com o resultado.
"""
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from itertools import combinations
from math import gcd


def perm_from_cycles(size, cycles):
    p = list(range(size))
    pos = 0
    for L in cycles:
        for i in range(L):
            p[pos + i] = pos + (i + 1) % L
        pos += L
    assert pos <= size, "ciclos maiores que a dimensao"
    return p


def lcm(xs):
    r = 1
    for x in xs:
        r = r * x // gcd(r, x)
    return r


def orbits(m, n, sig, tau, N):
    oid = [[-1] * n for _ in range(m)]
    weights = []
    for r in range(m):
        for c in range(n):
            if oid[r][c] >= 0:
                continue
            k = len(weights)
            rr, cc, w = r, c, 0
            while oid[rr][cc] < 0:
                oid[rr][cc] = k
                w += 1
                rr, cc = sig[rr], tau[cc]
            weights.append(w)
    return oid, weights


def build_cnf(m, n, k, rowcyc, colcyc):
    sig = perm_from_cycles(m, rowcyc)
    tau = perm_from_cycles(n, colcyc)
    N = lcm(rowcyc + colcyc)
    oid, w = orbits(m, n, sig, tau, N)
    nv = len(w)
    # potencias de sigma para canonizar o trio de linhas
    spow = [list(range(m))]
    for _ in range(N - 1):
        spow.append([sig[x] for x in spow[-1]])
    clauses = set()
    coltrip = list(combinations(range(n), 3))
    for R in combinations(range(m), 3):
        if any(tuple(sorted(P[x] for x in R)) < R for P in spow):
            continue  # outra imagem de R e representante da orbita de (R,C)
        o0, o1, o2 = oid[R[0]], oid[R[1]], oid[R[2]]
        for a, b, c in coltrip:
            clauses.add(frozenset((o0[a], o0[b], o0[c], o1[a], o1[b], o1[c],
                                   o2[a], o2[b], o2[c])))
    # remove clausulas subsumidas (apenas quando cabe: pares de tamanho pequeno raros)
    out = [[-(x + 1) for x in sorted(cl)] for cl in clauses]
    # cardinalidade: sum w_i x_i >= k  <=>  no maximo T-k dos literais negados (repetidos)
    lits = []
    for i, wi in enumerate(w):
        lits += [-(i + 1)] * wi
    T = len(lits)
    K = T - k
    if K < 0:
        return None, nv, w, oid
    cnt = nv

    def new():
        nonlocal cnt
        cnt += 1
        return cnt
    L = len(lits)
    if K == 0:
        for l in lits:
            out.append([-l])
    elif K < L:
        s = [[new() for _ in range(K)] for _ in range(L - 1)]
        out.append([-lits[0], s[0][0]])
        for j in range(1, K):
            out.append([-s[0][j]])
        for i in range(1, L - 1):
            out.append([-lits[i], s[i][0]])
            out.append([-s[i - 1][0], s[i][0]])
            for j in range(1, K):
                out.append([-lits[i], -s[i - 1][j - 1], s[i][j]])
                out.append([-s[i - 1][j], s[i][j]])
            out.append([-lits[i], -s[i - 1][K - 1]])
        out.append([-lits[L - 1], -s[L - 2][K - 1]])
    return (cnt, out), nv, w, oid


def run_kissat(cnf, timeout, seed):
    nvars, cls = cnf
    fd, path = tempfile.mkstemp(suffix=".cnf")
    with os.fdopen(fd, "w") as f:
        f.write(f"p cnf {nvars} {len(cls)}\n")
        for c in cls:
            f.write(" ".join(map(str, c)) + " 0\n")
    try:
        p = subprocess.run(["kissat", "-q", f"--seed={seed}", f"--time={timeout}", path],
                           capture_output=True, text=True, timeout=timeout + 30)
        txt = p.stdout
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None
    finally:
        os.unlink(path)
    if "s SATISFIABLE" in txt:
        val = set()
        for line in txt.splitlines():
            if line.startswith("v "):
                for t in line[2:].split():
                    v = int(t)
                    if v > 0:
                        val.add(v)
        return "SAT", val
    if "s UNSATISFIABLE" in txt:
        return "UNSAT", None
    return "TIMEOUT", None


def can_add(A, rows, m, r, c):
    # adicionar (r,c) cria K33 sse existem r1,r2 com 1 na coluna c e >=2 colunas
    # (alem de c) comuns a r, r1, r2
    others = [x for x in range(m) if x != r and A[x][c]]
    Rr = rows[r]
    for i in range(len(others)):
        a = rows[others[i]] & Rr
        if len(a) < 2:
            continue
        for j in range(i + 1, len(others)):
            if len(a & rows[others[j]]) >= 2:
                return False
    return True


def greedy_complete(A, m, n, tries=200, seed=0):
    rng = random.Random(seed)
    best = [row[:] for row in A]
    bestc = sum(map(sum, A))
    zeros = [(r, c) for r in range(m) for c in range(n) if not A[r][c]]
    for t in range(tries):
        B = [row[:] for row in A]
        rows = [{c for c in range(n) if B[r][c]} for r in range(m)]
        rng.shuffle(zeros)
        for r, c in zeros:
            if can_add(B, rows, m, r, c):
                B[r][c] = 1
                rows[r].add(c)
        cnt = sum(map(sum, B))
        if cnt > bestc:
            best, bestc = B, cnt
    return best, bestc


def has_k33(A, m, n):
    rows = [{c for c in range(n) if A[r][c]} for r in range(m)]
    return any(len(rows[a] & rows[b] & rows[c]) >= 3 for a, b, c in combinations(range(m), 3))


def parse_spec(s):
    return [] if s in ("0", "") else [int(x) for x in s.split(".")]


def main():
    args = sys.argv[1:]
    assert args[0] == "solve"
    m, n, k = int(args[1]), int(args[2]), int(args[3])
    rowcyc, colcyc = parse_spec(args[4]), parse_spec(args[5])
    timeout, seed, outp = 300, 0, None
    i = 6
    while i < len(args):
        if args[i] == "--timeout":
            timeout = int(args[i + 1]); i += 2
        elif args[i] == "--seed":
            seed = int(args[i + 1]); i += 2
        elif args[i] == "--out":
            outp = args[i + 1]; i += 2
        else:
            raise SystemExit("arg? " + args[i])
    t0 = time.time()
    cnf, nv, w, oid = build_cnf(m, n, k, rowcyc, colcyc)
    res = {"m": m, "n": n, "k": k, "rows": args[4], "cols": args[5], "orbits": nv}
    if cnf is None:
        res.update(status="UNSAT", note="k > m*n")
    else:
        res["clauses"] = len(cnf[1])
        tb = time.time()
        st, val = run_kissat(cnf, timeout, seed)
        res.update(status=st, build_s=round(tb - t0, 1), solve_s=round(time.time() - tb, 1))
        if st == "SAT":
            A = [[1 if (oid[r][c] + 1) in val else 0 for c in range(n)] for r in range(m)]
            ones = sum(map(sum, A))
            assert ones >= k and not has_k33(A, m, n), "modelo invalido"
            B, cnt = greedy_complete(A, m, n, seed=seed)
            assert not has_k33(B, m, n)
            res.update(sat_ones=ones, greedy_ones=cnt)
            if outp:
                with open(outp, "w") as f:
                    f.write(f"# Z({m},{n},3,3) >= {cnt}\n")
                    f.write(f"# sym_sat: linhas ciclos {args[4]}, colunas ciclos {args[5]},"
                            f" k={k}, SAT {ones} uns + completacao gulosa\n")
                    for row in B:
                        f.write("".join(map(str, row)) + "\n")
    print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
