"""Modelo linear agregado para eliminar perfis de grau de coluna em z(m,n;3,3).

Uma matriz m x n sem K_{3,3} e uma familia de n blocos (suportes das colunas) E_j em [m]
tal que cada tripla de linhas T esta em no maximo 2 blocos (lambda_T <= 2).

Caso: s blocos fixos F_0..F_{s-1} e uma particao das linhas em regioes; a regiao a tem
sz[a] linhas e mascara rm[a] (bit i ligado se a regiao esta dentro de F_i; por omissao
rm[a] = a, uma regiao por mascara). Os demais blocos ("livres") sao classificados pelo
tipo b = (b[a])_a, b[a] = |B cap regiao a|; y_b = numero de blocos livres do tipo b
(inteiro >= 0). Opcionalmente, linhas fixadas: rows = [[rho, v, op]] com sz[rho] = 1:
a linha da regiao rho tem grau v e e a de grau maximo (op 'max') ou minimo ('min').

Linhas do sistema (todas validas para qualquer matriz com esse perfil e esse caso):
  (T_t) para cada tipo de tripla t = (t[a]), sum t = 3:
        sum_b y_b * prod_a C(b[a], t[a])  <=  (2 - f_t) * prod_a C(sz[a], t[a])
        (soma de lambda_T <= 2 sobre as triplas do tipo t; f_t = fixos que as contem)
  (G_rho) grau da linha fixada:  sum_b y_b b[rho] = v - fix(rho)            (igualdade)
  (L_R)  demais regioes, op max: sum_b y_b b[R] <= sz[R] (v - fix(R));  op min: >=.
  (S_d) para cada grau d: sum_{|b|=d} y_b = n_d - #{fixos de grau d}.
  (X)   regras de exclusao (escolhas extremais): tipos b proibidos.

Certificado de Farkas (inteiro): multiplicador >= 0 para cada linha '<=' e livre para '=';
beta_d = max_b(-(A^T alpha)_b) calculado exatamente; prova se alpha.rhs + beta.e < 0.
"""
from math import comb, prod


def compositions(total, caps):
    """vetores v com 0 <= v[i] <= caps[i], soma total."""
    out = []
    k = len(caps)

    def rec(i, left, cur):
        if i == k - 1:
            if left <= caps[i]:
                out.append(tuple(cur + [left]))
            return
        rest = sum(caps[i + 1:])
        for v in range(max(0, left - rest), min(caps[i], left) + 1):
            rec(i + 1, left - v, cur + [v])

    if total <= sum(caps):
        rec(0, total, [])
    return out


def regmasks(case):
    return case.get("rm") or list(range(1 << case["s"]))


def fixed_degrees(s, sz, rm=None):
    rm = rm or list(range(1 << s))
    return [sum(sz[a] for a in range(len(sz)) if rm[a] >> i & 1) for i in range(s)]


def popcount_fixed(mask, s):
    return sum(1 for i in range(s) if mask >> i & 1)


def triple_types(s, sz, rm=None):
    """lista de (t, N_t, f_t)."""
    rm = rm or list(range(1 << s))
    out = []
    for t in compositions(3, list(sz)):
        N = prod(comb(sz[a], t[a]) for a in range(len(sz)))
        if N == 0:
            continue
        f = sum(1 for i in range(s) if all(t[a] == 0 or rm[a] >> i & 1 for a in range(len(sz))))
        out.append((t, N, f))
    return out


def rule_masks(R, nreg, rm=None):
    """regra cita um bloco fixo i (int: regioes dentro de F_i) ou lista explicita de regioes."""
    if isinstance(R, int):
        rm = rm or list(range(nreg))
        return [a for a in range(nreg) if rm[a] >> R & 1]
    return list(R)


def allowed(b, d, excl, rm=None):
    """excl: regras (degs, R, op, bound): blocos livres com grau em degs tem |B cap U| op bound."""
    for degs, R, op, bound in excl:
        if d in degs:
            x = sum(b[a] for a in rule_masks(R, len(b), rm))
            if op == "<=" and x > bound:
                return False
            if op == ">=" and x < bound:
                return False
    return True


def build(m, counts, s, sz, excl=(), rm=None, rows=()):
    """Retorna dict do modelo, ou None se a configuracao dos fixos viola K_{3,3}
    (algum tipo de tripla em >= 3 fixos)."""
    rm = rm or list(range(1 << s))
    assert sum(sz) == m and len(sz) == len(rm)
    fd = fixed_degrees(s, sz, rm)
    rem = dict(counts)
    for d in fd:
        rem[d] = rem.get(d, 0) - 1
        if rem[d] < 0:
            raise ValueError("fixos incompativeis com o perfil")
    T = triple_types(s, sz, rm)
    if any(f > 2 for _, _, f in T):
        return None
    nreg = len(sz)
    # linhas extras: (rotulo, funcao coeficiente de b, rhs, sentido)
    extra = []
    for rho, v, op in rows:
        assert sz[rho] == 1
        fx = popcount_fixed(rm[rho], s)
        extra.append((["G", rho], (lambda b, r=rho: b[r]), v - fx, "="))
        for R in range(nreg):
            if R == rho or sz[R] == 0:
                continue
            fR = popcount_fixed(rm[R], s)
            if op == "max":
                extra.append((["L", R], (lambda b, r=R: b[r]), sz[R] * (v - fR), "<="))
            else:
                extra.append((["L", R], (lambda b, r=R: -b[r]), -sz[R] * (v - fR), "<="))
    cols = []
    degs = sorted(d for d, c in rem.items() if c > 0)
    for d in degs:
        for b in compositions(d, list(sz)):
            if not allowed(b, d, excl, rm):
                continue
            coef = [prod(comb(b[a], t[a]) for a in range(nreg)) for t, _, _ in T]
            coef += [fn(b) for _, fn, _, _ in extra]
            cols.append((d, b, coef))
    cap = [(2 - f) * N for _, N, f in T] + [r for _, _, r, _ in extra]
    sense = ["<="] * len(T) + [se for _, _, _, se in extra]
    labels = [list(t) for t, _, _ in T] + [lab for lab, _, _, _ in extra]
    return dict(T=labels, cap=cap, sense=sense, cols=cols, degs=degs,
                e={d: rem[d] for d in degs})


def check(model, alpha):
    """Confere em inteiros (exato). alpha: inteiros, >= 0 nas linhas '<='.
    Calcula beta_d otimo = max_b(-A^T alpha) e retorna (ok, valor, beta)."""
    for a, se in zip(alpha, model["sense"]):
        if not isinstance(a, int) or (se == "<=" and a < 0):
            return False, None, None
    beta = {}
    for d in model["degs"]:
        vals = [sum(a * c for a, c in zip(alpha, coef)) for dd, _, coef in model["cols"] if dd == d]
        beta[d] = -min(vals) if vals else None
    val = sum(a * c for a, c in zip(alpha, model["cap"]))
    for d in model["degs"]:
        if beta[d] is None:  # nenhum tipo permitido de grau d mas e_d > 0: inviavel trivial
            return True, None, beta
        val += beta[d] * model["e"][d]
    return val < 0, val, beta
