#!/usr/bin/env python3
"""Verificador independente dos certificados em certificates/z{m}_{n}_k{k}.json.
Nao importa model.py, lp.py, bnb.py, refine.py nem search.py, e nao usa solver: so
aritmetica exata (int e fractions.Fraction).

  check_cert.py certificates/z13_21_k134.json [...]

Para cada arquivo confere:
  1. a lista de perfis (multiconjuntos de n graus em 0..m, soma k, sum C(d,3) <= 2 C(m,3))
     e reenumerada aqui por um metodo diferente e coincide com a do arquivo;
  2. para cada perfil marcado como eliminado, a estrategia gera exatamente a lista de
     casos do arquivo (a divisao em casos cobre todas as possibilidades);
  3. cada caso e um no de prova, conferido recursivamente:
       farkas : sistema agregado reconstruido aqui a partir de (perfil, caso); alpha >= 0,
                beta_d := max_b(-sum_t alpha_t c_t(b)) e sum alpha cap + sum beta e < 0;
       bnb    : arvore y_b <= v | y_b >= v+1 com Farkas (com limites) em cada folha;
       split  : fixa mais um bloco H extremal; os filhos sao regenerados aqui e comparados;
       rowsplit : fixa a linha de grau maximo/minimo (regiao e grau); filhos regenerados;
       invalid_config : algum tipo de tripla esta em >= 3 blocos fixos (K_{3,3}).
Se todos os perfis tiverem eliminacao verificada, imprime PROVA: z(m,n) <= k-1
(basta k: de uma matriz com mais de k uns apagam-se uns ate sobrarem k, sem criar K_{3,3}).
"""
import json
import sys
from fractions import Fraction
from math import comb


def C(a, b):
    return comb(a, b) if 0 <= b <= a else 0


# ---------- 1. perfis ----------
def all_profiles(m, n, k):
    """graus em ordem crescente; poda so por soma e pela capacidade de triplas."""
    cap = 2 * C(m, 3)
    res = []

    def go(d, left_cols, left_ones, left_cap, cur):
        if d > m:
            if left_cols == 0 and left_ones == 0:
                res.append(tuple(sorted(cur.items())))
            return
        for c in range(left_cols + 1):
            if c * d > left_ones or c * C(d, 3) > left_cap:
                break
            if c:
                cur[d] = c
            if left_ones - c * d <= (left_cols - c) * m:
                go(d + 1, left_cols - c, left_ones - c * d, left_cap - c * C(d, 3), cur)
            cur.pop(d, None)

    go(0, n, k, cap, {})
    return set(res)


def vectors(total, caps):
    if not caps:
        return [()] if total == 0 else []
    out = []
    for v in range(min(total, caps[0]) + 1):
        for rest in vectors(total - v, caps[1:]):
            out.append((v,) + rest)
    return out


# ---------- 2. estrategias ----------
def expected_cases(m, p, strat):
    kind = strat[0]
    if kind == "L0":
        f = strat[1]
        assert p.get(f, 0) >= 1
        return [dict(s=1, sz=[m - f, f], excl=[])]
    assert kind == "L1"
    f, g, mode = strat[1], strat[2], strat[3]
    if f == g:
        assert p.get(f, 0) >= 2
    else:
        assert p.get(f, 0) >= 1 and p.get(g, 0) >= 1
    if mode in ("maxpair", "minpair"):
        assert f == g
    out = []
    for i in range(max(0, f + g - m), min(f, g) + 1):
        # regioes: 0 = fora de F e G, 1 = so F, 2 = so G, 3 = F e G
        ex = {"any": [], "maxG": [[[g], 0, "<=", i]], "minG": [[[g], 0, ">=", i]],
              "maxpair": [[[f], 0, "<=", i], [[f], 1, "<=", i]],
              "minpair": [[[f], 0, ">=", i], [[f], 1, ">=", i]]}[mode]
        out.append(dict(s=2, sz=[m - f - g + i, f - i, g - i, i], excl=ex))
    return out


def rmasks(case):
    """mascara de cada regiao (bit i: regiao dentro de F_i); por omissao rm[a] = a."""
    return list(case.get("rm") or range(1 << case["s"]))


def masks_of(R, rm):
    """regra cita um bloco fixo (int i -> regioes dentro de F_i) ou lista de regioes."""
    if isinstance(R, int):
        return [a for a in range(len(rm)) if rm[a] >> R & 1]
    return sorted(R)


def obeys(b, d, excl, rm):
    for degs, R, op, bound in excl:
        if d in degs:
            x = sum(b[a] for a in masks_of(R, rm))
            if op == "<=" and x > bound:
                return False
            if op == ">=" and x < bound:
                return False
    return True


def canon(case):
    rm = rmasks(case)
    ex = sorted((tuple(sorted(r[0])), tuple(masks_of(r[1], rm)), r[2], r[3])
                for r in case["excl"])
    rows = tuple(sorted(tuple(r) for r in case.get("rows", [])))
    return (case["s"], tuple(case["sz"]), tuple(rm), ex and tuple(ex) or (), rows)


def split_children(case, h, U, op):
    """H = bloco livre de grau h obedecendo as regras do caso que maximiza (op=max) ou
    minimiza (op=min) |H cap U|. Um filho por tipo possivel de H."""
    s, sz, excl = case["s"], case["sz"], case["excl"]
    rm = rmasks(case)
    N = len(sz)
    out = []
    for b in vectors(h, list(sz)):
        if not obeys(b, h, excl, rm):
            continue
        j = sum(b[a] for a in U)
        sz2 = [sz[a] - b[a] for a in range(N)] + [b[a] for a in range(N)]
        rm2 = rm + [rm[a] | (1 << s) for a in range(N)]
        ex2 = []
        for degs, Rr, o, bound in excl:
            ms = masks_of(Rr, rm)
            ex2.append([list(degs), ms + [a + N for a in ms], o, bound])
        ex2.append([[h], sorted(list(U) + [a + N for a in U]), "<=" if op == "max" else ">=", j])
        # linha fixada rho (regiao de tamanho 1) vai para rho ou rho + N
        rows2 = [[r + N * b[r], v, o] for r, v, o in case.get("rows", [])]
        out.append(dict(s=s + 1, sz=sz2, excl=ex2, rm=rm2, rows=rows2))
    return out


def row_children(m, n, k, case, op):
    """a linha de grau maximo (op=max; grau >= ceil(k/m)) ou minimo (op=min; grau <=
    floor(k/m)) esta em alguma regiao a e tem algum grau v. Um filho por (a, v)."""
    assert not case.get("rows")
    sz, excl = case["sz"], case["excl"]
    rm = rmasks(case)
    N = len(sz)
    vs = range(-(-k // m), n + 1) if op == "max" else range(0, k // m + 1)
    out = []
    for a in range(N):
        if sz[a] < 1:
            continue
        sz2 = list(sz) + [1]
        sz2[a] -= 1
        ex2 = []
        for degs, Rr, o, bound in excl:
            ms = masks_of(Rr, rm)
            ex2.append([list(degs), ms + ([N] if a in ms else []), o, bound])
        for v in vs:
            out.append(dict(s=case["s"], sz=sz2, excl=ex2, rm=rm + [rm[a]], rows=[[N, v, op]]))
    return out


# ---------- 3. sistema agregado e certificados ----------
def nfix(mask, s):
    return sum(1 for i in range(s) if mask >> i & 1)


def remaining(p, case):
    s, sz = case["s"], case["sz"]
    rm = rmasks(case)
    rem = dict(p)
    for i in range(s):
        d = sum(sz[a] for a in range(len(sz)) if rm[a] >> i & 1)
        rem[d] = rem.get(d, 0) - 1
        assert rem[d] >= 0, "blocos fixos incompativeis com o perfil"
    return rem


def triple_types(case):
    """[(t, N_t, f_t)] com N_t > 0; f_t = numero de fixos que contem as triplas do tipo t."""
    s, sz = case["s"], case["sz"]
    rm = rmasks(case)
    N = len(sz)
    out = []
    for t in vectors(3, list(sz)):
        Nt = 1
        for a in range(N):
            Nt *= C(sz[a], t[a])
        if Nt == 0:
            continue
        f = sum(1 for i in range(s) if all(t[a] == 0 or rm[a] >> i & 1 for a in range(N)))
        out.append((t, Nt, f))
    return out


def system(m, p, case):
    """linhas: [(rotulo, sentido, rhs, funcao b -> coeficiente)], colunas, e_d."""
    s, sz, excl = case["s"], case["sz"], case["excl"]
    rm = rmasks(case)
    N = len(sz)
    assert len(rm) == N and sum(sz) == m and min(sz) >= 0
    rem = remaining(p, case)
    TT = triple_types(case)
    assert all(f <= 2 for _, _, f in TT)
    lines = []
    for t, Nt, f in TT:  # sum_{T de tipo t} lambda_T <= (2 - f) N_t
        def co(b, t=t):
            c = 1
            for a in range(N):
                c *= C(b[a], t[a])
            return c  # triplas do tipo t dentro de um bloco do tipo b
        lines.append((tuple(t), "<=", (2 - f) * Nt, co))
    for rho, v, op in case.get("rows", []):
        assert sz[rho] == 1 and op in ("max", "min")
        # grau da linha rho = fixos que a contem + blocos livres que a contem = v
        lines.append((("G", rho), "=", v - nfix(rm[rho], s), lambda b, r=rho: b[r]))
        for R in range(N):
            if R == rho or sz[R] == 0:
                continue
            cap = sz[R] * (v - nfix(rm[R], s))  # incidencias na regiao R, cada linha <= v
            if op == "max":
                lines.append((("L", R), "<=", cap, lambda b, r=R: b[r]))
            else:
                lines.append((("L", R), "<=", -cap, lambda b, r=R: -b[r]))
    e = {d: c for d, c in rem.items() if c > 0}  # sum_{b de grau d} y_b = e_d
    cols = []
    for d in e:
        for b in vectors(d, list(sz)):
            if obeys(b, d, excl, rm):
                cols.append((d, b, {lab: fn(b) for lab, _, _, fn in lines}))
    return lines, cols, e


def label(x):
    return tuple(x) if isinstance(x[0], int) else (x[0], x[1])


def leaf_ok(sysm, mult, up, lo, bounds):
    """Farkas (Fraction) para: y >= 0, lo <= y_b <= hi, linhas '<=' e '=', E y = e."""
    lines, cols, e = sysm
    sense = {lab: se for lab, se, _, _ in lines}
    assert set(mult) <= set(sense)
    for lab, v in mult.items():
        assert isinstance(v, int) and (v >= 0 or sense[lab] == "=")
    for D in (up, lo):
        assert all(isinstance(v, int) and v >= 0 for v in D.values())
    al = {lab: Fraction(v) for lab, v in mult.items()}
    total = sum((al.get(lab, Fraction(0)) * rhs for lab, _, rhs, _ in lines), Fraction(0))
    for key, mu in up.items():
        assert bounds[key][1] is not None
        total += Fraction(mu) * bounds[key][1]
    for key, mu in lo.items():
        total -= Fraction(mu) * bounds.get(key, (0, None))[0]
    for d, ed in e.items():
        vals = [sum((a * co[lab] for lab, a in al.items()), Fraction(0)) + up.get((d, b), 0)
                - lo.get((d, b), 0) for dd, b, co in cols if dd == d]
        if not vals:
            return True  # nenhum tipo permitido de grau d, mas e_d > 0 blocos sao exigidos
        total += -min(vals) * ed  # beta_d = -min(...) torna a coluna dual >= 0
    return total < 0


def tree_ok(sysm, T, node, bounds):
    if "leaf" in node:
        L = node["leaf"]
        mult = {label(t): a for t, a in zip(T, L["alpha"]) if a}
        up = {(d, tuple(b)): v for d, b, v in L["up"]}
        lo = {(d, tuple(b)): v for d, b, v in L["lo"]}
        return leaf_ok(sysm, mult, up, lo, bounds)
    key = (node["var"][0], tuple(node["var"][1]))
    lo0, hi0 = bounds.get(key, (0, None))
    v = node["v"]
    b1 = dict(bounds)
    b1[key] = (lo0, v)
    b2 = dict(bounds)
    b2[key] = (v + 1, hi0)
    return tree_ok(sysm, T, node["le"], b1) and tree_ok(sysm, T, node["ge"], b2)


STATS = {}


def node_ok(m, n, k, p, node):
    case, kind = node["case"], node["kind"]
    STATS[kind] = STATS.get(kind, 0) + 1
    if kind == "invalid_config":
        remaining(p, case)
        return any(f >= 3 for _, _, f in triple_types(case))
    if kind == "farkas":
        sysm = system(m, p, case)
        mult = {label(t): a for t, a in zip(node["T"], node["alpha"]) if a}
        return leaf_ok(sysm, mult, {}, {}, {})
    if kind == "bnb":
        sysm = system(m, p, case)
        return tree_ok(sysm, node["T"], node["tree"], {})
    if kind == "split":
        h, U, op = node["h"], list(node["U"]), node["op"]
        assert op in ("max", "min")
        assert remaining(p, case).get(h, 0) >= 1, "nao ha bloco livre de grau h"
        exp = [canon(c) for c in split_children(case, h, U, op)]
    elif kind == "rowsplit":
        exp = [canon(c) for c in row_children(m, n, k, case, node["op"])]
    else:
        raise AssertionError(f"tipo de no desconhecido {kind}")
    got = [canon(c["case"]) for c in node["children"]]
    assert exp == got, "filhos do refinamento nao conferem"
    return all(node_ok(m, n, k, p, c) for c in node["children"])


def main():
    for path in sys.argv[1:]:
        STATS.clear()
        D = json.load(open(path))
        m, n, k = D["m"], D["n"], D["k"]
        P = all_profiles(m, n, k)
        filep = {tuple(sorted((int(d), c) for d, c in r["profile"].items())) for r in D["results"]}
        assert P == filep, "lista de perfis difere da reenumeracao"
        assert len(D["results"]) == len(P)
        done = 0
        for r in D["results"]:
            if not r["strategy"]:
                continue
            p = {int(d): c for d, c in r["profile"].items()}
            exp = [canon(c) for c in expected_cases(m, p, r["strategy"])]
            got = [canon(c["case"]) for c in r["cases"]]
            assert exp == got, f"casos nao cobrem a estrategia {r['strategy']}"
            for c in r["cases"]:
                assert node_ok(m, n, k, p, c), f"certificado invalido em {r['profile']}"
            done += 1
        print(f"{path}: z({m},{n}) k={k}: {len(P)} perfis, {done} eliminados com certificado "
              f"verificado, {len(P) - done} sobram; nos: {dict(sorted(STATS.items()))}", flush=True)
        if done == len(P):
            print(f"  PROVA: z({m},{n};3,3) <= {k - 1}", flush=True)


if __name__ == "__main__":
    main()
