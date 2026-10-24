#!/usr/bin/env python3
"""Codifica "existe matriz m x n sem K_{3,3} com >= k uns" em CNF (DIMACS) e decodifica
o modelo do solver para o formato results/Z_m_n.txt.

  zsat.py encode m n k saida.cnf [--nosym]
  zsat.py decode m n saida_do_solver.txt Z_m_n.txt

Variavel x(r,c) = 1 + r*n + c. Restricoes:
  - para cada 3 linhas e 3 colunas, nem todos os 9 sao 1 (clausula de 9 literais);
  - pelo menos k uns (contador sequencial de Sinz sobre os literais negados: no maximo
    m*n-k zeros... equivalentemente no maximo m*n-k literais ~x verdadeiros);
  - quebra de simetria: linhas e colunas em ordem lexicografica nao crescente
    (toda matriz admite uma ordenacao duplamente lexicografica, Lubiw 1987).
"""
import sys
from itertools import combinations


class CNF:
    def __init__(self, nv):
        self.nv = nv
        self.clauses = []

    def new(self):
        self.nv += 1
        return self.nv

    def add(self, c):
        self.clauses.append(c)

    def at_most(self, lits, k):
        """Contador sequencial (Sinz 2005): no maximo k de lits verdadeiros."""
        n = len(lits)
        if k >= n:
            return
        if k == 0:
            for l in lits:
                self.add([-l])
            return
        s = [[self.new() for _ in range(k)] for _ in range(n - 1)]
        self.add([-lits[0], s[0][0]])
        for j in range(1, k):
            self.add([-s[0][j]])
        for i in range(1, n - 1):
            self.add([-lits[i], s[i][0]])
            self.add([-s[i - 1][0], s[i][0]])
            for j in range(1, k):
                self.add([-lits[i], -s[i - 1][j - 1], s[i][j]])
                self.add([-s[i - 1][j], s[i][j]])
            self.add([-lits[i], -s[i - 1][k - 1]])
        self.add([-lits[n - 1], -s[n - 2][k - 1]])

    def lex_geq(self, a, b):
        """vetor a >= vetor b lexicograficamente (primeira posicao mais significativa)."""
        e = None  # "iguais ate aqui"; None = verdadeiro
        for j in range(len(a)):
            pre = [] if e is None else [-e]
            self.add(pre + [a[j], -b[j]])          # iguais ate j => a_j >= b_j
            if j == len(a) - 1:
                break
            e2 = self.new()
            self.add(pre + [-a[j], -b[j], e2])     # iguais ate j e a_j=b_j=1 => iguais ate j+1
            self.add(pre + [a[j], b[j], e2])       # iguais ate j e a_j=b_j=0 => iguais ate j+1
            e = e2

    def write(self, path):
        with open(path, "w") as f:
            f.write(f"p cnf {self.nv} {len(self.clauses)}\n")
            for c in self.clauses:
                f.write(" ".join(map(str, c)) + " 0\n")


def encode(m, n, k, path, sym=True):
    x = lambda r, c: 1 + r * n + c  # noqa: E731
    F = CNF(m * n)
    for R in combinations(range(m), 3):
        for C in combinations(range(n), 3):
            F.add([-x(r, c) for r in R for c in C])
    F.at_most([-x(r, c) for r in range(m) for c in range(n)], m * n - k)
    if sym:
        for r in range(m - 1):
            F.lex_geq([x(r, c) for c in range(n)], [x(r + 1, c) for c in range(n)])
        for c in range(n - 1):
            F.lex_geq([x(r, c) for r in range(m)], [x(r, c + 1) for r in range(m)])
    F.write(path)
    print(f"{path}: {F.nv} variaveis, {len(F.clauses)} clausulas")


def decode(m, n, model_path, out):
    val = set()
    sat = False
    for line in open(model_path):
        if line.startswith("s SATISFIABLE"):
            sat = True
        if line.startswith("v "):
            val.update(int(t) for t in line.split()[1:] if int(t) > 0)
    if not sat:
        print("sem modelo (UNSAT ou nao terminou)")
        return 1
    rows = ["".join("1" if 1 + r * n + c in val else "0" for c in range(n)) for r in range(m)]
    ones = sum(s.count("1") for s in rows)
    with open(out, "w") as f:
        f.write(f"# Z({m},{n},3,3) >= {ones}  (SAT)\n" + "\n".join(rows) + "\n")
    print(f"{out}: {ones} uns")
    return 0


if __name__ == "__main__":
    a = sys.argv
    if a[1] == "encode":
        encode(int(a[2]), int(a[3]), int(a[4]), a[5], sym="--nosym" not in a)
    elif a[1] == "decode":
        sys.exit(decode(int(a[2]), int(a[3]), a[4], a[5]))
