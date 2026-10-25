#!/usr/bin/env python3
"""Junta os resultados das pastas de trabalho em certificates/:
  certificates/proofs/  : por celula, o menor k com todos os perfis eliminados (+ validacao)
  certificates/partial/ : por celula, o k da fronteira (logo abaixo da prova, ou o UB)
                          com o melhor resultado parcial (menos sobreviventes)
Imprime a tabela-resumo. Nao confere nada (para isso: check_cert.py)."""
import glob
import json
import os
import shutil

SRC = ["work/l1", "certs2", "certs3", "certs4"]
best = {}  # (m,n,k) -> (sobram, total, path)
for d in SRC:
    for path in glob.glob(os.path.join(d, "z*_k*.json")):
        D = json.load(open(path))
        key = (D["m"], D["n"], D["k"])
        left = sum(1 for r in D["results"] if not r["strategy"])
        if key not in best or left < best[key][0]:
            best[key] = (left, len(D["results"]), path)
cells = [tuple(map(int, l.split())) for l in open("cells_all.txt")]
os.makedirs("certificates/proofs", exist_ok=True)
os.makedirs("certificates/partial", exist_ok=True)
rows = []
for m, n, lb, ub in cells:
    ks = sorted(k for (a, b, k) in best if (a, b) == (m, n))
    proved = [k for k in ks if best[(m, n, k)][0] == 0]
    kp = min(proved) if proved else None
    front = (kp - 1) if kp else ub
    if kp:
        shutil.copy(best[(m, n, kp)][2], f"certificates/proofs/z{m}_{n}_k{kp}.json")
    fr = best.get((m, n, front))
    if fr and front > lb:
        shutil.copy(fr[2], f"certificates/partial/z{m}_{n}_k{front}.json")
    rows.append((m, n, lb, ub, kp, front, fr))
for key in [(10, 22, 111), (13, 22, 138)]:
    if key in best:
        dst = "proofs" if best[key][0] == 0 else "partial"
        shutil.copy(best[key][2], f"certificates/{dst}/z{key[0]}_{key[1]}_k{key[2]}.json")
print("| celula | LB | UB antigo | UB novo (provado) | fronteira k | perfis | eliminados | sobram |")
print("|---|---|---|---|---|---|---|---|")
for m, n, lb, ub, kp, front, fr in rows:
    new = f"**{kp - 1}**" if kp else "—"
    if fr and front > lb:
        print(f"| ({m},{n}) | {lb} | {ub} | {new} | {front} | {fr[1]} | {fr[1] - fr[0]} | {fr[0]} |")
    else:
        print(f"| ({m},{n}) | {lb} | {ub} | {new} | — | | | |")
