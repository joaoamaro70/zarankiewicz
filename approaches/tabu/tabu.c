// tabu.c — busca tabu com conflitos para limites inferiores de Z(m,n,3,3).
//
// Estado: matriz m x n com exatamente k uns (k fixo). Custo: soma, sobre as
// triplas de linhas {a,b,c}, de f(t), t = |colunas comuns|; f(t)=max(0,t-2)
// (modo "excess", padrao) ou f(t)=C(t,3) (modo "k33", numero de 3x3 cheias).
// Movimento: mover um 1 de (r,c) para um 0 em (r2,c2). Em cada passo avalia-se
// a vizinhanca inteira (uns x zeros) com deltas exatos: delta = rem(r,c) +
// add(r2,c2) + correcao para as triplas atingidas pelas duas metades.
// Tabu: depois do movimento, recolocar 1 em (r,c) fica proibido por tt_add
// passos e retirar o 1 de (r2,c2) por tt_rem passos (tenure + aleatorio).
// Aspiracao: movimento tabu e aceito se leva a custo < melhor custo.
// Perturbacao: sem melhora do melhor custo em `stall` passos, aplica `kick`
// movimentos aleatorios (a partir do estado atual).
// Pesos (-w P): com prob. P% em cada passo sem movimento melhorante, soma 1 ao
// peso das triplas violadas (breakout); a busca minimiza o custo ponderado.
// Custo 0 = matriz valida com k uns: grava o arquivo e (com -c) sobe k+1.
//
// Compilar: gcc -O3 -march=native -o tabu tabu.c
// Uso: tabu -m M -n N -k K [-s seed] [-t segundos] [-i inicial.txt] [-o saida.txt]
//           [-c (subir k ao achar)] [-T tenure] [-R aleatorio_tenure]
//           [-S stall] [-K kick] [-f excess|k33] [-v intervalo_log_s] [-w P]

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define MAXM 16
#define MAXN 32

static int M, N, K;
static uint32_t row[MAXM];   // bits = colunas
static uint32_t col[MAXN];   // bits = linhas
static int wadd[MAXN + 2], wrem[MAXN + 2];  // f(t+1)-f(t), f(t-1)-f(t)
static int rd[MAXM][MAXN], ad[MAXM][MAXN];
static long tabuA[MAXM][MAXN], tabuR[MAXM][MAXN];
static int W[MAXM][MAXM][MAXM];  // pesos das triplas (modo -w), simetricos
static uint64_t rng = 88172645463325252ULL;

static inline uint64_t xr(void) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return rng; }
static inline int rnd(int k) { return (int)(xr() % (uint64_t)k); }
static inline int pc(uint32_t x) { return __builtin_popcount(x); }
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + 1e-9 * t.tv_nsec; }

static int F(int t, int mode) {
    if (mode == 0) return t > 2 ? t - 2 : 0;
    return t >= 3 ? t * (t - 1) * (t - 2) / 6 : 0;
}

static inline void setbit(int r, int c, int v) {
    if (v) { row[r] |= 1u << c; col[c] |= 1u << r; }
    else { row[r] &= ~(1u << c); col[c] &= ~(1u << r); }
}

static long total_cost(int mode) {
    long s = 0;
    for (int a = 0; a < M; a++)
        for (int b = a + 1; b < M; b++)
            for (int c = b + 1; c < M; c++) s += F(pc(row[a] & row[b] & row[c]), mode);
    return s;
}

static long weighted_cost(int mode) {
    long s = 0;
    for (int a = 0; a < M; a++)
        for (int b = a + 1; b < M; b++)
            for (int c = b + 1; c < M; c++) s += (long)W[a][b][c] * F(pc(row[a] & row[b] & row[c]), mode);
    return s;
}

// +1 no peso das triplas violadas; se algum passar de 1000, divide todos por 2
static void bump_weights(void) {
    int big = 0;
    for (int a = 0; a < M; a++)
        for (int b = a + 1; b < M; b++)
            for (int c = b + 1; c < M; c++)
                if (pc(row[a] & row[b] & row[c]) >= 3) {
                    int v = ++W[a][b][c];
                    W[a][c][b] = W[b][a][c] = W[b][c][a] = W[c][a][b] = W[c][b][a] = v;
                    if (v > 1000) big = 1;
                }
    if (big)
        for (int a = 0; a < M; a++)
            for (int b = 0; b < M; b++)
                for (int c = 0; c < M; c++) W[a][b][c] = W[a][b][c] / 2 > 1 ? W[a][b][c] / 2 : 1;
}

// soma de w[t] sobre os pares {a,b} de S, tripla {r,a,b}
static inline int pairsum(int r, uint32_t S, const int *w) {
    int s = 0;
    uint32_t rr = row[r];
    while (S) {
        int a = __builtin_ctz(S); S &= S - 1;
        uint32_t ra = rr & row[a];
        if (pc(ra) < 2) continue;    // w[t]=0 para t<2 nos dois modos
        uint32_t T = S;
        while (T) { int b = __builtin_ctz(T); T &= T - 1; s += W[r][a][b] * w[pc(ra & row[b])]; }
    }
    return s;
}

static void compute_deltas(void) {
    for (int r = 0; r < M; r++)
        for (int c = 0; c < N; c++) {
            uint32_t S = col[c] & ~(1u << r);
            if (row[r] >> c & 1) rd[r][c] = pairsum(r, S, wrem);
            else ad[r][c] = pairsum(r, S, wadd);
        }
}

// delta exato do movimento (r,c)->(r2,c2)
static inline int move_delta(int r, int c, int r2, int c2) {
    int d = rd[r][c] + ad[r2][c2];
    if (r == r2) {
        uint32_t S = col[c] & col[c2] & ~(1u << r);
        uint32_t rr = row[r];
        while (S) {
            int a = __builtin_ctz(S); S &= S - 1;
            uint32_t T = S;
            while (T) { int b = __builtin_ctz(T); T &= T - 1; int t = pc(rr & row[a] & row[b]); d -= W[r][a][b] * (wadd[t] + wrem[t]); }
        }
    } else if (c == c2) {
        uint32_t S = col[c] & ~(1u << r);
        uint32_t x = row[r] & row[r2];
        while (S) { int z = __builtin_ctz(S); S &= S - 1; d -= W[r][r2][z] * wadd[pc(x & row[z])]; }
    } else if ((col[c] >> r2 & 1) && (col[c2] >> r & 1)) {
        uint32_t S = col[c] & col[c2] & ~(1u << r) & ~(1u << r2);
        uint32_t x = row[r] & row[r2];
        while (S) { int z = __builtin_ctz(S); S &= S - 1; int t = pc(x & row[z]); d -= W[r][r2][z] * (wadd[t] + wrem[t]); }
    }
    return d;
}

static void write_matrix(const char *path, int k) {
    char tmp[1024];
    snprintf(tmp, sizeof tmp, "%s.tmp", path);
    FILE *f = fopen(tmp, "w");
    if (!f) { perror(tmp); return; }
    fprintf(f, "# Z(%d,%d,3,3) >= %d\n", M, N, k);
    for (int r = 0; r < M; r++) {
        for (int c = 0; c < N; c++) fputc(row[r] >> c & 1 ? '1' : '0', f);
        fputc('\n', f);
    }
    fclose(f);
    rename(tmp, path);
}

static int count_ones(void) { int s = 0; for (int r = 0; r < M; r++) s += pc(row[r]); return s; }

static int load(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); exit(1); }
    char line[256]; int r = 0;
    while (fgets(line, sizeof line, f) && r < M) {
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r') continue;
        for (int c = 0; c < N; c++) setbit(r, c, line[c] == '1');
        r++;
    }
    fclose(f);
    return r == M;
}

// ajusta o numero de uns para k: adiciona com menor ad / remove com menor rd
static void adjust_to(int k) {
    while (count_ones() != k) {
        compute_deltas();
        int add = count_ones() < k, best = 1 << 30, br = -1, bc = -1, cnt = 0;
        for (int r = 0; r < M; r++)
            for (int c = 0; c < N; c++) {
                if ((row[r] >> c & 1) == add) continue;
                int v = add ? ad[r][c] : rd[r][c];
                if (v < best) { best = v; br = r; bc = c; cnt = 1; }
                else if (v == best && rnd(++cnt) == 0) { br = r; bc = c; }
            }
        setbit(br, bc, add);
    }
}

int main(int argc, char **argv) {
    long seed = 1, stall = 20000, kick = 3, tenure = 10, trand = 10;
    double tlim = 60, logint = 10;
    const char *init = NULL, *out = NULL;
    int climb = 0, mode = 0, weighted = 0, wprob = 100;
    for (int i = 1; i < argc; i++) {
        const char *a = argv[i];
#define NEXT (i + 1 < argc ? argv[++i] : (fprintf(stderr, "falta valor para %s\n", a), exit(1), ""))
        if (!strcmp(a, "-m")) M = atoi(NEXT);
        else if (!strcmp(a, "-n")) N = atoi(NEXT);
        else if (!strcmp(a, "-k")) K = atoi(NEXT);
        else if (!strcmp(a, "-s")) seed = atol(NEXT);
        else if (!strcmp(a, "-t")) tlim = atof(NEXT);
        else if (!strcmp(a, "-i")) init = NEXT;
        else if (!strcmp(a, "-o")) out = NEXT;
        else if (!strcmp(a, "-c")) climb = 1;
        else if (!strcmp(a, "-T")) tenure = atol(NEXT);
        else if (!strcmp(a, "-R")) trand = atol(NEXT);
        else if (!strcmp(a, "-S")) stall = atol(NEXT);
        else if (!strcmp(a, "-K")) kick = atol(NEXT);
        else if (!strcmp(a, "-f")) { const char *v = NEXT; mode = !strcmp(v, "k33"); }
        else if (!strcmp(a, "-v")) logint = atof(NEXT);
        else if (!strcmp(a, "-w")) { weighted = 1; wprob = atoi(NEXT); }
        else { fprintf(stderr, "opcao desconhecida %s\n", a); return 1; }
    }
    if (M < 3 || M > MAXM || N < 3 || N > MAXN || K <= 0 || K >= M * N) { fprintf(stderr, "parametros invalidos\n"); return 1; }
    rng ^= (uint64_t)seed * 0x9E3779B97F4A7C15ULL; for (int i = 0; i < 20; i++) xr();
    for (int t = 0; t <= MAXN; t++) { wadd[t] = F(t + 1, mode) - F(t, mode); wrem[t] = t > 0 ? F(t - 1, mode) - F(t, mode) : 0; }

    for (int a = 0; a < M; a++) for (int b = 0; b < M; b++) for (int c = 0; c < M; c++) W[a][b][c] = 1;
    if (init) load(init);
    else {  // aleatoria com k uns
        int placed = 0;
        while (placed < K) { int r = rnd(M), c = rnd(N); if (!(row[r] >> c & 1)) { setbit(r, c, 1); placed++; } }
    }
    adjust_to(K);

    double t0 = now(), tlog = t0;
    // com -w: cost = custo ponderado (guia a busca), tcost = custo verdadeiro
    long cost = total_cost(mode), tcost = cost, best = cost, gbest = cost, it = 0, lastimp = 0, kicks = 0, bumps = 0;
    int ones[MAXM * MAXN][2], zeros[MAXM * MAXN][2];
    fprintf(stderr, "inicio m=%d n=%d k=%d custo=%ld\n", M, N, K, cost);
    for (;;) {
        if (tcost == 0) {
            double el = now() - t0;
            printf("ACHOU m=%d n=%d k=%d t=%.2fs it=%ld\n", M, N, K, el, it);
            fflush(stdout);
            if (out) write_matrix(out, K);
            if (!climb) return 0;
            for (int a = 0; a < M; a++) for (int b = 0; b < M; b++) for (int c = 0; c < M; c++) W[a][b][c] = 1;
            K++; adjust_to(K); tcost = best = gbest = total_cost(mode); lastimp = it;
            cost = tcost;
            memset(tabuA, 0, sizeof tabuA); memset(tabuR, 0, sizeof tabuR);
            continue;
        }
        if ((it & 63) == 0) {
            double tn = now();
            if (tn - t0 > tlim) break;
            if (tn - tlog > logint) {
                if (cost != weighted_cost(mode)) { fprintf(stderr, "ERRO: custo incremental %ld != %ld\n", cost, weighted_cost(mode)); return 3; }
                fprintf(stderr, "t=%.0f it=%ld k=%d custo=%ld pond=%ld global=%ld kicks=%ld bumps=%ld\n", tn - t0, it, K, tcost, cost, gbest, kicks, bumps);
                tlog = tn;
            }
        }
        compute_deltas();
        int no = 0, nz = 0;
        for (int r = 0; r < M; r++)
            for (int c = 0; c < N; c++) {
                if (row[r] >> c & 1) { ones[no][0] = r; ones[no][1] = c; no++; }
                else { zeros[nz][0] = r; zeros[nz][1] = c; nz++; }
            }
        int bd = 1 << 30, cnt = 0, bi = -1, bj = -1;
        for (int i = 0; i < no; i++) {
            int r = ones[i][0], c = ones[i][1];
            int trem = tabuR[r][c] > it;
            for (int j = 0; j < nz; j++) {
                int r2 = zeros[j][0], c2 = zeros[j][1];
                int d = move_delta(r, c, r2, c2);
                if ((trem || tabuA[r2][c2] > it) && cost + d >= best) continue;
                if (d < bd) { bd = d; bi = i; bj = j; cnt = 1; }
                else if (d == bd && rnd(++cnt) == 0) { bi = i; bj = j; }
            }
        }
        if (bi < 0) { bi = rnd(no); bj = rnd(nz); }  // tudo tabu
        int r = ones[bi][0], c = ones[bi][1], r2 = zeros[bj][0], c2 = zeros[bj][1];
        setbit(r, c, 0); setbit(r2, c2, 1);
        cost += (bd == 1 << 30) ? 0 : bd;
        if (bd == 1 << 30) cost = weighted_cost(mode);
        tabuA[r][c] = it + tenure + rnd((int)trand + 1);
        tabuR[r2][c2] = it + tenure + rnd((int)trand + 1);
        it++;
        if (!weighted) tcost = cost;
        else {
            tcost = total_cost(mode);
            if (tcost < gbest) { gbest = tcost; lastimp = it; }
            if (bd >= 0 && rnd(100) < wprob) { bump_weights(); cost = weighted_cost(mode); best = cost; bumps++; }
            else if (cost < best) best = cost;
            continue;
        }
        if (cost < best) { best = cost; lastimp = it; if (cost < gbest) gbest = cost; }
        else if (it - lastimp > stall) {
            for (int q = 0; q < kick; q++) {
                int a, b, x, y;
                do { a = rnd(M); b = rnd(N); } while (!(row[a] >> b & 1));
                do { x = rnd(M); y = rnd(N); } while (row[x] >> y & 1);
                setbit(a, b, 0); setbit(x, y, 1);
            }
            cost = total_cost(mode); best = cost; lastimp = it; kicks++;
        }
    }
    printf("FALHOU m=%d n=%d k=%d melhor_custo=%ld it=%ld t=%.0fs\n", M, N, K, gbest, it, now() - t0);
    return 2;
}
