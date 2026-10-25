#!/usr/bin/env python3
"""Resumo dos perfis de grau de coluna para um caso m x n.
Uso: profile_info.py m n total [arquivo_matriz]"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from profile_sat import profiles  # noqa: E402

m, n, total = map(int, sys.argv[1:4])
P = profiles(m, n, total)
print(f"{m}x{n} com {total} uns: {len(P)} perfis")
for p in P[:5]:
    print("  ", " ".join(map(str, p)))
if len(sys.argv) > 4:
    rows = [l.strip() for l in open(sys.argv[4]) if l.strip() and not l.startswith("#")]
    d = sorted((sum(r[c] == "1" for r in rows) for c in range(n)), reverse=True)
    print(f"perfil da matriz {sys.argv[4]} ({sum(d)} uns): {' '.join(map(str, d))}")
