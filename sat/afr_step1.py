#!/usr/bin/env python3
"""Reproducao independente da etapa 1 de Afrasyab (arXiv 2608.08154) para z(13,22) <= 137.

Numa matriz 13x22 sem K_{3,3}, cada tripla de linhas esta contida em no maximo 2 colunas.
Contando pares (tripla de linhas, coluna que contem a tripla):
    sum_j C(d_j, 3) <= 2 * C(13, 3) = 572,
onde d_j e o numero de uns da coluna j. Com 138 uns, enumeramos todos os histogramas de
graus de coluna (multiconjuntos de 22 valores em 0..13 com soma 138) que satisfazem a
desigualdade. Afrasyab afirma que restam 83.
"""
from functools import lru_cache
from math import comb

M, N, TOTAL = 13, 22, 138
CAP = 2 * comb(M, 3)


def profiles():
    out = []

    def rec(d, cols_left, ones_left, cap_left, cur):
        # escolhe quantas colunas tem grau d (graus decrescentes, d = 13..0)
        if d < 0:
            if cols_left == 0 and ones_left == 0:
                out.append(dict(cur))
            return
        for k in range(cols_left + 1):
            if k * d > ones_left or k * comb(d, 3) > cap_left:
                break
            rest = cols_left - k
            if rest * (d - 1 if d > 0 else 0) < ones_left - k * d:
                continue  # colunas restantes (grau <= d-1) nao alcancam a soma
            if k:
                cur[d] = k
            rec(d - 1, rest, ones_left - k * d, cap_left - k * comb(d, 3), cur)
            cur.pop(d, None)

    rec(M, N, TOTAL, CAP, {})
    return out


P = profiles()
print(f"perfis de grau de coluna para 13x22 com 138 uns: {len(P)}")
for p in sorted(P, key=lambda p: sorted(p.items(), reverse=True), reverse=True)[:5]:
    print("  ", " ".join(f"{d}^{k}" for d, k in sorted(p.items(), reverse=True)))
# o perfil citado na Proposicao 6.1 do artigo
target = {6: 18, 7: 3, 9: 1}
print("perfil 6^18 7^3 9^1 presente:", target in P)
