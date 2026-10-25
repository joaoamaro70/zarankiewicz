#!/usr/bin/env python3
"""SAT por perfil de grau de coluna: existe matriz m x n sem K_{3,3} cujas colunas tem
exatamente os graus dados?

  profile_sat.py encode m n "d1 d2 ... dn" saida.cnf
  profile_sat.py profiles m n total            (lista perfis que passam na contagem)

Quebra de simetria (correta para graus fixos):
  - colunas em ordem de grau nao crescente (permutacao de colunas, sempre possivel);
  - linhas em ordem lexicografica nao crescente (para qualquer ordem fixa de colunas,
    as linhas podem ser reordenadas assim).
Nao ordenamos colunas dentro de um mesmo grau: combinado com a ordem das linhas, isso
nem sempre e possivel, e um UNSAT deixaria de valer como prova.
"""
import sys
from itertools import combinations
from math import comb

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from zsat import CNF  # noqa: E402


def profiles(m, n, total):
    cap = 2 * comb(m, 3)
    out = []

    def rec(d, cols_left, ones_left, cap_left, cur):
        if d < 0:
            if cols_left == 0 and ones_left == 0:
                out.append(list(cur))
            return
        for k in range(cols_left + 1):
            if k * d > ones_left or k * comb(d, 3) > cap_left:
                break
            rest = cols_left - k
            if rest * max(d - 1, 0) < ones_left - k * d:
                continue
            rec(d - 1, rest, ones_left - k * d, cap_left - k * comb(d, 3), cur + [d] * k)

    rec(m, n, total, cap, [])
    return out


def encode(m, n, degs, path, pair=False):
    """pair=True acrescenta a restricao redundante de capacidade por par de linhas:
    para cada par {r1,r2}, sum_{colunas j com r1,r2} (d_j - 2) <= 2(m-2), pois cada
    coluna j com o par forma d_j-2 triplas com ele e cada tripla cabe em no maximo
    2 colunas. E consequencia da ausencia de K_{3,3}; so ajuda a propagacao."""
    degs = sorted(degs, reverse=True)
    assert len(degs) == n
    x = lambda r, c: 1 + r * n + c  # noqa: E731
    F = CNF(m * n)
    for R in combinations(range(m), 3):
        for C in combinations(range(n), 3):
            F.add([-x(r, c) for r in R for c in C])
    for c in range(n):
        col = [x(r, c) for r in range(m)]
        F.at_most(col, degs[c])
        F.at_most([-v for v in col], m - degs[c])
    for r in range(m - 1):
        F.lex_geq([x(r, c) for c in range(n)], [x(r + 1, c) for c in range(n)])
    if pair:
        cap = 2 * (m - 2)
        for r1, r2 in combinations(range(m), 2):
            lits = []
            for c in range(n):
                w = degs[c] - 2
                if w <= 0:
                    continue
                a = F.new()  # a -> (x(r1,c) e x(r2,c)) nao e preciso; basta (ambos) -> a
                F.add([-x(r1, c), -x(r2, c), a])
                lits += [a] * w  # peso w = literal repetido w vezes no contador
            F.at_most(lits, cap)
    F.write(path)
    return F.nv, len(F.clauses)


if __name__ == "__main__":
    a = sys.argv
    if a[1] == "profiles":
        for p in profiles(int(a[2]), int(a[3]), int(a[4])):
            print(" ".join(map(str, p)))
    elif a[1] == "encode":
        nv, nc = encode(int(a[2]), int(a[3]), list(map(int, a[4].split())), a[5],
                        pair="--pair" in a)
        print(f"{a[5]}: {nv} variaveis, {nc} clausulas")
