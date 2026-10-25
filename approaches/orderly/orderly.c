/* orderly.c -- geracao ordenada (canonical augmentation, McKay) de matrizes 0/1
 * F x N sem submatriz 3x3 toda de uns, linha a linha, a menos de permutacoes de
 * linhas e de colunas.
 *
 * Caminho canonico: as linhas entram em ordem de grau nao crescente; o pai de uma
 * matriz e ela sem uma linha de grau minimo, escolhida canonicamente: entre as
 * linhas de grau minimo, as de maior chave invariante (soma de s^2 e de s^3 sobre
 * as intersecoes s com as outras linhas); empate decidido pelo rotulamento
 * canonico do nauty.  Um filho M+r e aceito sse r esta na orbita (em Aut(M+r)) da
 * linha canonica.  Irmaos isomorfos aceitos sao exatamente os r da mesma orbita de
 * Aut(M); guardamos so o r de mascara minima na orbita (ou, se |Aut(M)| e grande,
 * deduplicamos pela forma canonica do nauty).
 *
 * Toda matriz F x N com >= T uns tem um caminho desses partindo da matriz vazia,
 * e cada prefixo k x N satisfaz as podas abaixo (todas sao condicoes necessarias):
 *   B1: e_k + soma das proximas linhas >= T, com as proximas linhas de grau <= d_k
 *       (grau da ultima linha) e e_j <= Z[j] (limite superior valido de z(j,N)),
 *       e linhas depois do nivel j com grau <= floor(e_j / j);
 *   B2: orcamento de triplas por coluna: sum_c C(c_c,3) <= 2 C(F,3) no final.
 * Portanto, se a busca termina sem achar nenhuma matriz F x N com >= T uns, isso
 * prova z(F,N) <= T-1 (dado que os Z[j], j < F, sejam limites superiores validos;
 * Z[F] deve ser um limite valido ou um numero grande).
 *
 * Uso:
 *   orderly N F T Z1,Z2,...,ZF [opcoes]
 *     -c        conta classes no nivel F (senao: modo prova, so testa existencia
 *               no ultimo nivel, sem nauty)
 *     -s S W I  divide o trabalho: no nivel S, so a sub-arvore de indice = I mod W
 *     -e K seed estimativa de Knuth com K caminhos aleatorios
 *     -o file   grava as matrizes finais encontradas (no maximo 1000)
 *     -L lev    para no nivel lev (conta nos ate la)
 *     -x        (modo prova) para na primeira matriz encontrada
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include "nauty.h"

typedef unsigned int u32;
typedef unsigned long long u64;
#define MAXR 32
#define MAXC 32
#define MAXV (MAXR + MAXC + 1)
#define GMAX 2000  /* acima disso, deduplica irmaos pela forma canonica */

static int N, F, T, Z[MAXR + 1];
static int stopfirst = 0;
static int countmode = 0, splitS = -1, splitW = 1, splitI = 0, stopL = -1;
static long long splitctr = 0;
static FILE *outf = NULL;
static long long nout = 0;
static int C2[MAXR + 2], C3[MAXR + 2];

static u32 R[MAXR];
static int Dg[MAXR], colDeg[MAXC], K, E;

static long long nodes[MAXR + 1], ncand[MAXR + 1], nnauty[MAXR + 1], nfinal = 0;
static double labeled = 0.0;
static double fact[40];
static int ehist[1024];

/* ---- poda ---- */
static int bound_ok(int e, int d, int k, const int *cd)
{
    if (k == F) return e >= T;
    for (int j = k; j <= F; j++) {
        int Ej = e + (j - k) * d;
        if (Ej > Z[j]) Ej = Z[j];
        int da = d;
        if (j > 0 && Ej / j < da) da = Ej / j;
        if (Ej + (F - j) * da < T) return 0;
    }
    /* B2: maximo de uns adicionais com orcamento de triplas de linhas por coluna
       (custo marginal C(s,2) crescente: guloso e otimo) */
    long budget = 2L * C3[F];
    int s[MAXC], cap[MAXC];
    for (int c = 0; c < N; c++) {
        budget -= C3[cd[c]];
        s[c] = cd[c];
        cap[c] = cd[c] + (F - k);
        if (cap[c] > F) cap[c] = F;
    }
    if (budget < 0) return 0;
    int need = T - e, add = 0;
    for (int lev = 0; lev < F && add < need; lev++) {
        for (int c = 0; c < N && add < need; c++) {
            if (s[c] == lev && cap[c] > lev) {
                if (C2[lev] > budget) return add >= need;
                budget -= C2[lev];
                s[c]++;
                add++;
            }
        }
    }
    return add >= need;
}

/* ---- geracao das linhas candidatas ---- */
static u32 pairmask[MAXR * MAXR / 2];
static int npair;
static int plist[MAXC][MAXR * MAXR / 2], plen[MAXC];
static int twinPrev[MAXC];
static int g_dlo, g_dhi;
static u32 g_full;

typedef void (*emit_fn)(u32 r, int d);
static emit_fn g_emit;

/* enumera cada linha valida com grau em [g_dlo, g_dhi] uma vez.
   forb: colunas proibidas (a linha ja tem 2 colunas do conjunto comum de um par);
   twinPrev: entre colunas gemeas (iguais em M) so prefixos. */
static void rowdfs_f(int from, u32 cur, int cnt, u32 forb)
{
    u32 avail = ~forb & g_full & ~((1u << from) - 1);
    if (cnt + __builtin_popcount(avail) < g_dlo) return;
    if (cnt >= g_dlo) g_emit(cur, cnt);
    if (cnt == g_dhi) return;
    for (u32 rem = avail; rem; rem &= rem - 1) {
        if (cnt + __builtin_popcount(rem) < g_dlo) break;
        int c = __builtin_ctz(rem);
        if (twinPrev[c] >= 0 && !(cur >> twinPrev[c] & 1)) continue;
        u32 nc = cur | (1u << c), nf = forb;
        for (int i = 0; i < plen[c]; i++) {
            u32 p = pairmask[plist[c][i]];
            if (__builtin_popcount(nc & p) == 2) nf |= p;
        }
        rowdfs_f(c + 1, nc, cnt + 1, nf);
    }
}

static void rowdfs(void)
{
    g_full = (N == 32) ? 0xffffffffu : ((1u << N) - 1);
    if (g_dlo <= g_dhi) rowdfs_f(0, 0, 0, 0);
}

static void prep_rows(void)
{
    npair = 0;
    for (int c = 0; c < N; c++) plen[c] = 0;
    for (int i = 0; i < K; i++)
        for (int j = i + 1; j < K; j++) {
            u32 p = R[i] & R[j];
            if (__builtin_popcount(p) >= 3) {
                pairmask[npair] = p;
                for (int c = 0; c < N; c++)
                    if (p >> c & 1) plist[c][plen[c]++] = npair;
                npair++;
            }
        }
    u32 colv[MAXC];
    for (int c = 0; c < N; c++) {
        colv[c] = 0;
        for (int i = 0; i < K; i++)
            if (R[i] >> c & 1) colv[c] |= 1u << i;
        twinPrev[c] = -1;
        for (int c2 = c - 1; c2 >= 0; c2--)
            if (colv[c2] == colv[c]) { twinPrev[c] = c2; break; }
    }
}

/* ---- chaves invariantes das linhas ---- */
static u64 row_key(const u32 *rows, int nr, int i)
{
    u64 a = 0, b = 0;
    for (int j = 0; j < nr; j++)
        if (j != i) {
            u64 s = __builtin_popcount(rows[i] & rows[j]);
            a += s * s;
            b += s * s * s;
        }
    return a << 32 | b;
}

/* ---- nauty ---- */
static int nvmax;
typedef struct { setword g[MAXV]; u32 r; } child_t;

/* grafo da matriz rows[0..nr-1]: linhas 0..nr-1, colunas nr..nr+N-1.
   Particao: celula 0 = linhas em 'first' (mascara de indices), depois as demais
   linhas por grau, depois colunas por grau. */
static void build_graph(const u32 *rows, int nr, u32 first, graph *g, int *lab, int *ptn)
{
    int nv = nr + N, m = 1;
    EMPTYGRAPH(g, m, nv);
    int cd[MAXC] = {0}, rd[MAXR + 1];
    for (int i = 0; i < nr; i++) {
        rd[i] = __builtin_popcount(rows[i]);
        for (int c = 0; c < N; c++)
            if (rows[i] >> c & 1) { ADDONEEDGE(g, i, nr + c, m); cd[c]++; }
    }
    int p = 0;
    if (first) {
        for (int i = 0; i < nr; i++) if (first >> i & 1) { lab[p] = i; ptn[p] = 1; p++; }
        ptn[p - 1] = 0;
    }
    for (int deg = 0; deg <= N; deg++) {
        int st = p;
        for (int i = 0; i < nr; i++)
            if (!(first >> i & 1) && rd[i] == deg) { lab[p] = i; ptn[p] = 1; p++; }
        if (p > st) ptn[p - 1] = 0;
    }
    for (int deg = 0; deg <= nr; deg++) {
        int st = p;
        for (int c = 0; c < N; c++) if (cd[c] == deg) { lab[p] = nr + c; ptn[p] = 1; p++; }
        if (p > st) ptn[p - 1] = 0;
    }
}

/* teste de aceitacao do filho M+r (linha nova = indice K); 'first' = linhas de
   grau minimo com chave maxima.  Devolve 1 se aceito; canong recebe a forma
   canonica; grp (se != NULL) recebe |Aut(M+r)|. */
static int canon_child(u32 r, u32 first, setword *canong, double *grp)
{
    u32 rows[MAXR + 1];
    memcpy(rows, R, sizeof(u32) * K);
    rows[K] = r;
    int nv = K + 1 + N;
    graph g[MAXV];
    int lab[MAXV], ptn[MAXV], orbits[MAXV];
    static DEFAULTOPTIONS_GRAPH(options);
    statsblk stats;
    build_graph(rows, K + 1, first, g, lab, ptn);
    options.getcanon = TRUE;
    options.defaultptn = FALSE;
    options.userautomproc = NULL;
    densenauty(g, lab, ptn, orbits, &options, &stats, 1, nv, canong);
    nnauty[K + 1]++;
    if (grp) *grp = stats.grpsize1 * pow(10.0, stats.grpsize2);
    return orbits[K] == orbits[lab[0]];
}

/* geradores de Aut(M), como permutacoes das colunas */
static int ngen;
static int gcol[64][MAXC];
static void collect_gen(int count, int *perm, int *orbits, int numorbits, int stabvertex, int n)
{
    (void)count; (void)orbits; (void)numorbits; (void)stabvertex; (void)n;
    if (ngen >= 64) return;
    for (int c = 0; c < N; c++) gcol[ngen][c] = perm[K + c] - K;
    ngen++;
}

static double aut_parent(void)
{
    if (K == 0) { ngen = 0; return 1e300; }
    /* se as linhas tem (grau, chave) distintos, todo automorfismo fixa as linhas e
       so troca colunas gemeas; o rowdfs ja escolhe prefixos entre gemeas (= minimo
       da orbita), entao nao ha geradores a aplicar */
    u64 kk[MAXR];
    int distinct = 1;
    for (int i = 0; i < K && distinct; i++) {
        kk[i] = row_key(R, K, i);
        for (int j = 0; j < i; j++)
            if (Dg[j] == Dg[i] && kk[j] == kk[i]) { distinct = 0; break; }
    }
    if (distinct) { ngen = 0; return 1; }
    int nv = K + N;
    graph g[MAXV];
    int lab[MAXV], ptn[MAXV], orbits[MAXV];
    static DEFAULTOPTIONS_GRAPH(options);
    statsblk stats;
    build_graph(R, K, 0, g, lab, ptn);
    options.getcanon = FALSE;
    options.defaultptn = FALSE;
    options.userautomproc = collect_gen;
    ngen = 0;
    densenauty(g, lab, ptn, orbits, &options, &stats, 1, nv, NULL);
    nnauty[K]++;
    return stats.grpsize1 * pow(10.0, stats.grpsize2);
}

static inline u32 apply_gen(int gi, u32 r)
{
    u32 img = 0;
    for (u32 b = r; b; b &= b - 1) img |= 1u << gcol[gi][__builtin_ctz(b)];
    return img;
}

/* r e o minimo da sua orbita sob <geradores>? (BFS, orbita <= |Aut| <= GMAX) */
static int orbit_min(u32 r)
{
    static u32 orb[GMAX + 8];
    int n = 1, h = 0;
    orb[0] = r;
    while (h < n) {
        u32 x = orb[h++];
        for (int gi = 0; gi < ngen; gi++) {
            u32 y = apply_gen(gi, x);
            if (y < r) return 0;
            int seen = 0;
            for (int t = 0; t < n; t++) if (orb[t] == y) { seen = 1; break; }
            if (!seen && n < GMAX + 8) orb[n++] = y;
        }
    }
    return 1;
}

/* ---- busca ---- */
static child_t *cbuf[MAXR + 1];
static int ccap[MAXR + 1], clen[MAXR + 1];
static int g_e, g_orbitmode;

static void push_child(u32 r, int d)
{
    ncand[K + 1]++;
    int cd[MAXC];
    for (int c = 0; c < N; c++) cd[c] = colDeg[c] + (r >> c & 1);
    if (!bound_ok(g_e + d, d, K + 1, cd)) return;
    if (g_orbitmode && !orbit_min(r)) return;
    /* chave da linha nova contra as outras linhas de grau minimo (= d) */
    u32 rows[MAXR + 1];
    memcpy(rows, R, sizeof(u32) * K);
    rows[K] = r;
    u64 kn = row_key(rows, K + 1, K);
    u32 first = 1u << K;
    for (int i = K - 1; i >= 0 && Dg[i] == d; i--) {
        u64 ki = row_key(rows, K + 1, i);
        if (ki > kn) return;           /* outra linha tem chave maior: nao canonico */
        if (ki == kn) first |= 1u << i;
    }
    setword cg[MAXV];
    if (first != (1u << K) || !g_orbitmode) {
        if (!canon_child(r, first, cg, NULL)) return;
    }
    int L = K + 1;
    if (clen[L] == ccap[L]) {
        ccap[L] = ccap[L] ? 2 * ccap[L] : 1024;
        cbuf[L] = realloc(cbuf[L], sizeof(child_t) * ccap[L]);
    }
    child_t *ch = &cbuf[L][clen[L]++];
    if (!g_orbitmode) {
        memset(ch->g, 0, sizeof ch->g);
        memcpy(ch->g, cg, sizeof(setword) * (K + 1 + N));
    }
    ch->r = r;
}

static void print_matrix(FILE *f, int e)
{
    fprintf(f, "# Z(%d,%d,3,3) >= %d\n", F, N, e);
    for (int i = 0; i < F; i++) {
        for (int c = 0; c < N; c++) fputc((R[i] >> c & 1) ? '1' : '0', f);
        fputc('\n', f);
    }
    fputc('\n', f);
    fflush(f);
}

static void final_last(u32 r, int d)
{
    /* modo prova: qualquer linha valida fecha uma matriz com >= T uns */
    int cd[MAXC];
    for (int c = 0; c < N; c++) cd[c] = colDeg[c] + (r >> c & 1);
    ncand[K + 1]++;
    if (!bound_ok(g_e + d, d, K + 1, cd)) return;
    nfinal++;
    if ((outf && nout < 1000) || stopfirst) {
        R[K] = r; K++;
        if (outf) print_matrix(outf, g_e + d);
        if (stopfirst) { printf("FOUND\n"); print_matrix(stdout, g_e + d); exit(0); }
        K--;
        nout++;
    }
}

static int cmp_child(const void *a, const void *b)
{
    return memcmp(((const child_t *)a)->g, ((const child_t *)b)->g, sizeof(setword) * nvmax);
}

static void add_row(u32 r, int d)
{
    R[K] = r; Dg[K] = d; K++; E += d;
    for (int c = 0; c < N; c++) colDeg[c] += (r >> c & 1);
}
static void del_row(void)
{
    K--; E -= Dg[K];
    for (int c = 0; c < N; c++) colDeg[c] -= (R[K] >> c & 1);
}

static void gen_children(void)
{
    prep_rows();
    int dhi = (K == 0) ? N : Dg[K - 1];
    int rem = F - K;
    int dlo = (T - E + rem - 1) / rem;
    if (dlo < 0) dlo = 0;
    g_dlo = dlo; g_dhi = dhi; g_e = E;
    clen[K + 1] = 0;
    if (dlo > dhi) return;
    /* K = 0: linhas candidatas sao prefixos (todas as colunas gemeas), uma por grau */
    double grp = aut_parent();
    g_orbitmode = (K == 0) || grp <= GMAX;
    g_emit = push_child;
    rowdfs();
    if (g_orbitmode) return;
    nvmax = K + 1 + N;
    qsort(cbuf[K + 1], clen[K + 1], sizeof(child_t), cmp_child);
    int u = 0;
    for (int i = 0; i < clen[K + 1]; i++)
        if (u == 0 || cmp_child(&cbuf[K + 1][u - 1], &cbuf[K + 1][i]) != 0)
            cbuf[K + 1][u++] = cbuf[K + 1][i];
    clen[K + 1] = u;
}

static void search(void)
{
    nodes[K]++;
    if (K == splitS) {
        long long id = splitctr++;
        if (id % splitW != splitI) return;
    }
    if (K == stopL) return;
    if (K == F) {
        nfinal++;
        if (E < 1024) ehist[E]++;
        double grp;
        setword cg[MAXV];
        /* grupo de automorfismos da matriz final (para contagem rotulada) */
        K--;
        canon_child(R[K], 0, cg, &grp);
        K++;
        labeled += fact[F] * fact[N] / grp;
        if (outf && nout < 1000) { print_matrix(outf, E); nout++; }
        return;
    }
    if (!countmode && K == F - 1) {
        prep_rows();
        int dhi = (K == 0) ? N : Dg[K - 1], dlo = T - E;
        if (dlo < 0) dlo = 0;
        g_dlo = dlo; g_dhi = dhi; g_e = E;
        g_emit = final_last;
        rowdfs();
        return;
    }
    gen_children();
    int L = K + 1, cnt = clen[L];
    /* copia local: os buffers do nivel L sao reutilizados pelos irmaos */
    u32 *rows = malloc(sizeof(u32) * (cnt ? cnt : 1));
    for (int i = 0; i < cnt; i++) rows[i] = cbuf[L][i].r;
    for (int i = 0; i < cnt; i++) {
        add_row(rows[i], __builtin_popcount(rows[i]));
        search();
        del_row();
    }
    free(rows);
}

/* estimativa de Knuth do tamanho da arvore */
static double est[MAXR + 1], est2[MAXR + 1];
static void knuth(int samples, unsigned seed)
{
    srand(seed);
    for (int s = 0; s < samples; s++) {
        double w = 1.0;
        K = 0; E = 0; memset(colDeg, 0, sizeof colDeg);
        est[0] += 1;
        while (K < F) {
            gen_children();
            int cnt = clen[K + 1];
            if (cnt == 0) break;
            w *= cnt;
            est[K + 1] += w;
            est2[K + 1] += w * w;
            u32 r = cbuf[K + 1][rand() % cnt].r;
            add_row(r, __builtin_popcount(r));
        }
    }
    for (int k = 0; k <= F; k++) {
        double mu = est[k] / samples, var = est2[k] / samples - mu * mu;
        printf("est level %2d: %.4g  (rel.se %.2f)\n", k, mu,
               mu > 0 ? sqrt(var > 0 ? var : 0) / mu / sqrt((double)samples) : 0.0);
    }
}

int main(int argc, char **argv)
{
    if (argc < 5) { fprintf(stderr, "uso: orderly N F T Z1,..,ZF [-c] [-s S W I] [-e K seed] [-o f] [-L lev] [-x]\n"); return 2; }
    N = atoi(argv[1]); F = atoi(argv[2]); T = atoi(argv[3]);
    char *zs = argv[4];
    Z[0] = 0;
    for (int j = 1; j <= F; j++) {
        Z[j] = (int)strtol(zs, &zs, 10);
        if (*zs == ',') zs++;
    }
    int ksamples = 0; unsigned kseed = 1;
    for (int a = 5; a < argc; a++) {
        if (!strcmp(argv[a], "-c")) countmode = 1;
        else if (!strcmp(argv[a], "-x")) stopfirst = 1;
        else if (!strcmp(argv[a], "-s")) { splitS = atoi(argv[++a]); splitW = atoi(argv[++a]); splitI = atoi(argv[++a]); }
        else if (!strcmp(argv[a], "-e")) { ksamples = atoi(argv[++a]); kseed = atoi(argv[++a]); }
        else if (!strcmp(argv[a], "-o")) outf = fopen(argv[++a], "w");
        else if (!strcmp(argv[a], "-L")) stopL = atoi(argv[++a]);
    }
    for (int i = 0; i < MAXR + 2; i++) { C2[i] = i * (i - 1) / 2; C3[i] = i * (i - 1) * (i - 2) / 6; }
    fact[0] = 1; for (int i = 1; i < 40; i++) fact[i] = fact[i - 1] * i;
    if (N > MAXC || F > MAXR || F + N + 1 > WORDSIZE) { fprintf(stderr, "grande demais\n"); return 2; }
    nauty_check(WORDSIZE, 1, F + N + 1, NAUTYVERSIONID);
    printf("N=%d F=%d T=%d Z=", N, F, T);
    for (int j = 1; j <= F; j++) printf("%d%c", Z[j], j < F ? ',' : '\n');
    if (splitS >= 0) printf("split level %d: worker %d of %d\n", splitS, splitI, splitW);
    fflush(stdout);
    clock_t t0 = clock();
    if (ksamples) { knuth(ksamples, kseed); return 0; }
    K = 0; E = 0;
    search();
    double secs = (double)(clock() - t0) / CLOCKS_PER_SEC;
    for (int k = 0; k <= F; k++)
        printf("level %2d: nodes %lld  cand %lld  nauty %lld\n", k, nodes[k], ncand[k], nnauty[k]);
    printf("final (>= T=%d): %lld%s\n", T, nfinal, countmode ? " classes" : " raw (modo prova)");
    if (countmode) {
        printf("labeled count: %.0f\n", labeled);
        for (int e = 0; e < 1024; e++) if (ehist[e]) printf("  e=%d: %d classes\n", e, ehist[e]);
    }
    printf("time %.1fs\n", secs);
    return 0;
}
