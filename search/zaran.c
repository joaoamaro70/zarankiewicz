// zaran.c — busca local para limites inferiores de Z(m,n,3,3).
// Matriz binaria m x n sem submatriz 3x3 toda de uns <=> quaisquer 3 linhas
// compartilham no maximo 2 colunas com 1.
//
// Ingredientes (ver a nota em paper/, Algoritmo 1):
//   - rip-up and repair e recozimento simulado (adicionar + reparar conflitos);
//   - semeadura entre vizinhos: toda melhora em (m,n) gera sementes para
//     (m,n+-1) e (m+-1,n) (adicionar/remover linha/coluna + completamento guloso);
//   - casos que atingiram o limite superior saem da fila; fatias sorteadas com
//     peso 1+(UB-melhor);
//   - fatias "simetricas": busca sobre orbitas de Z_p agindo em blocos circulantes
//     (m = a*p + r0, n = b*p + c0), completadas gulosamente e usadas como sementes;
//   - casos ja fechados tambem rodam (ate atingir o UB) e servem de semente.
//
// Compilar:  gcc -O3 -march=native -fopenmp -o zaran zaran.c -lm   (ou search/run.sh)
// Rodar:     ./zaran [-t horas] [-m mmin] [-M mmax] [-n nmin] [-N nmax]
//                    [-s fatia_seg] [-e rr|sa|mix] [-d dir_resultados]
//                    [-S (sem semeadura)] [-C (sem simetricas)] [-P (sem prioridade)]
//                    [-q (so casos abertos)]
// Retoma a partir de dir_resultados/Z_m_n.txt e salva cada melhora ali.

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <unistd.h>
#include <omp.h>
#include <sys/stat.h>

#define MAXM 32
#define MAXCASES 512
#define POOL 8
#define MAXORB 1024
#define MAXSYM 16

enum { SRC_RR, SRC_SA, SRC_SYM, SRC_SEED, SRC_LOAD, NSRC };
static const char *SRC_NAME[NSRC] = {"rr", "sa", "sym", "seed", "load"};

typedef struct {
    int m, n;
    int best, start_best;
    int up, lo, bar;
    uint32_t rows[MAXM];
    double t_improved;
    long long iters, slices;
    long long it_e[3];       // iteracoes por motor: rr (rip-up), sa (passos), sym (rip-up de orbitas)
    double sec_e[3];         // segundos-thread por motor
    int improv_src[NSRC];
    int npool;
    int pool_cnt[POOL];
    uint32_t pool[POOL][MAXM];
    int nsym;
    int sym_p[MAXSYM], sym_a[MAXSYM], sym_b[MAXSYM], sym_r0[MAXSYM], sym_c0[MAXSYM];
} Case;

static Case cases[MAXCASES];
static int ncases = 0;
static int cidx[MAXM + 1][33];

static const char *resdir = "results";
static int opt_seed = 1, opt_sym = 1, opt_prio = 1, opt_open_only = 0;
static int engine = 2;  // 0 rr, 1 sa, 2 mix
static double t0, deadline, next_report;

// ---------- RNG ----------
static inline uint64_t rng_next(uint64_t *s) {
    uint64_t z = (*s += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
static inline uint32_t rnd(uint64_t *s, uint32_t k) {
    return (uint32_t)(((rng_next(s) >> 32) * (uint64_t)k) >> 32);
}
static inline double rnd01(uint64_t *s) { return (rng_next(s) >> 11) * 0x1.0p-53; }

// ---------- verificacao ----------
static int count_ones(const uint32_t *rows, int m) {
    int c = 0;
    for (int i = 0; i < m; i++) c += __builtin_popcount(rows[i]);
    return c;
}

static int valid_full(const uint32_t *rows, int m, int n) {
    uint32_t mask = (n == 32) ? 0xFFFFFFFFu : ((1u << n) - 1);
    for (int i = 0; i < m; i++) if (rows[i] & ~mask) return 0;
    for (int i = 0; i < m; i++)
        for (int j = i + 1; j < m; j++) {
            uint32_t a = rows[i] & rows[j];
            if (__builtin_popcount(a) < 3) continue;
            for (int k = j + 1; k < m; k++)
                if (__builtin_popcount(a & rows[k]) >= 3) return 0;
        }
    return 1;
}

static inline int can_add(const uint32_t *rows, int m, int r, int c) {
    uint32_t b = 1u << c, rr = rows[r];
    for (int i = 0; i < m; i++) {
        if (i == r || !(rows[i] & b)) continue;
        uint32_t x = rr & rows[i];
        if (__builtin_popcount(x) < 2) continue;
        for (int j = i + 1; j < m; j++) {
            if (j == r || !(rows[j] & b)) continue;
            if (__builtin_popcount(x & rows[j]) >= 2) return 0;
        }
    }
    return 1;
}

static void greedy_fill(uint32_t *rows, int m, int n, uint64_t *s) {
    int cells[MAXM * 32];
    int nc = m * n;
    for (int i = 0; i < nc; i++) cells[i] = i;
    for (int i = nc - 1; i > 0; i--) {
        int j = rnd(s, i + 1);
        int t = cells[i]; cells[i] = cells[j]; cells[j] = t;
    }
    for (int t = 0; t < nc; t++) {
        int r = cells[t] / n, c = cells[t] % n;
        if (rows[r] & (1u << c)) continue;
        if (can_add(rows, m, r, c)) rows[r] |= (1u << c);
    }
}

static inline uint32_t kth_bit(uint32_t x, int k) {
    while (k--) x &= x - 1;
    return x & -x;
}

static void perturb(uint32_t *rows, int m, int n, uint64_t *s, int k) {
    int type = rnd(s, 10);
    if (type < 7) {
        for (int t = 0; t < k; t++) {
            int tot = count_ones(rows, m);
            if (tot == 0) return;
            int target = rnd(s, tot);
            for (int r = 0; r < m; r++) {
                int pc = __builtin_popcount(rows[r]);
                if (target < pc) { rows[r] &= ~kth_bit(rows[r], target); break; }
                target -= pc;
            }
        }
    } else if (type < 9) {
        int r = rnd(s, m);
        for (int t = 0; t < k && rows[r]; t++)
            rows[r] &= ~kth_bit(rows[r], rnd(s, __builtin_popcount(rows[r])));
    } else {
        uint32_t b = 1u << rnd(s, n);
        for (int t = 0; t < k; t++) rows[rnd(s, m)] &= ~b;
    }
}

// ---------- tabela ----------
static const int UP[9][8] = {
    { 70, 74, 77, 81, 84, 87, 90, 94},
    { 77, 81, 85, 89, 93, 96,100,104},
    { 85, 90, 94, 98,102,108,111,115},
    { 92, 96,101,108,112,116,121,125},
    { 99,108,113,118,122,127,132,136},
    {107,116,121,125,130,135,140,145},
    {115,124,129,135,140,145,150,155},
    {123,132,138,143,149,154,160,165},
    {128,141,146,152,158,164,169,175}};
static const int LO[9][8] = {
    { 70, 74, 77, 81, 84, 87, 90, 94},
    { 77, 81, 85, 89, 93, 96,100,103},
    { 85, 90, 94, 98, 99,106,110,112},
    { 92, 96, 97,102,111,116,121,118},
    { 99,102,108,110,113,116,132,125},
    {107,106,115,114,119,127,137,135},
    {115,118,124,121,125,131,137,138},
    {123,125,132,132,138,139,143,149},
    {128,128,130,132,146,147,149,158}};
static int in_table(int m, int n) { return m >= 8 && m <= 16 && n >= 16 && n <= 23; }

// Limites superiores mais fortes da literatura (Collins et al. 2016, Tan 2022, Afrasyab 2026,
// Hou 2026; ver literature.py). Usados so para tirar da fila casos ja fechados.
static int up_lit(int m, int n) {
    static const int T[][3] = {
        {12,17,103},{12,18,108},{13,17,110},{13,18,116},{14,17,118},{14,18,124},
        {15,17,126},{15,18,132},{16,17,133},{16,18,140},{12,19,114},{12,20,120},
        {12,21,126},{13,22,137}};
    int u = in_table(m, n) ? UP[m - 8][n - 16] : 0;
    for (unsigned i = 0; i < sizeof T / sizeof T[0]; i++)
        if (T[i][0] == m && T[i][1] == n && T[i][2] < u) u = T[i][2];
    return u;
}


// ---------- arquivos ----------
static void save_case(Case *cs) {
    char p[512], tmp[600];
    snprintf(p, sizeof p, "%s/Z_%d_%d.txt", resdir, cs->m, cs->n);
    snprintf(tmp, sizeof tmp, "%s.tmp", p);
    FILE *f = fopen(tmp, "w");
    if (!f) return;
    fprintf(f, "# Z(%d,%d,3,3) >= %d\n", cs->m, cs->n, cs->best);
    for (int r = 0; r < cs->m; r++) {
        for (int c = 0; c < cs->n; c++) fputc((cs->rows[r] >> c) & 1 ? '1' : '0', f);
        fputc('\n', f);
    }
    fclose(f);
    rename(tmp, p);
}

static void load_case(Case *cs) {
    char p[512], line[256];
    snprintf(p, sizeof p, "%s/Z_%d_%d.txt", resdir, cs->m, cs->n);
    FILE *f = fopen(p, "r");
    if (!f) return;
    uint32_t rows[MAXM] = {0};
    int r = 0;
    while (fgets(line, sizeof line, f) && r < cs->m) {
        if (line[0] == '#') continue;
        int len = (int)strcspn(line, "\r\n");
        if (len != cs->n) continue;
        for (int c = 0; c < cs->n; c++) if (line[c] == '1') rows[r] |= 1u << c;
        r++;
    }
    fclose(f);
    if (r == cs->m && valid_full(rows, cs->m, cs->n)) {
        memcpy(cs->rows, rows, sizeof rows);
        cs->best = count_ones(rows, cs->m);
    }
}

static const char *status_of(const Case *c) {
    if (!c->up) return "fora_da_tabela";
    if (c->lo == c->up) return c->best >= c->up ? "ja_conhecido" : "conhecido_nao_atingido";
    if (c->best >= c->up) return "FECHADO";
    if (c->best > c->bar) return "SUPERA_BARRA";
    if (c->best > c->lo) return "supera_so_artigo";
    if (c->best == c->lo) return "igual_artigo";
    return "abaixo_artigo";
}

static void write_summary(void) {
    char p[512], tmp[600];
    snprintf(p, sizeof p, "%s/summary.csv", resdir);
    snprintf(tmp, sizeof tmp, "%s.tmp", p);
    FILE *f = fopen(tmp, "w");
    if (!f) return;
    fprintf(f, "m,n,UP,LO_artigo,BARRA,best,status,iterations,slices,last_improvement_s,"
               "src_rr,src_sa,src_sym,src_seed,it_rr,it_sa,it_sym,sec_rr,sec_sa,sec_sym\n");
    for (int i = 0; i < ncases; i++) {
        Case *c = &cases[i];
        fprintf(f, "%d,%d,%d,%d,%d,%d,%s,%lld,%lld,%.0f,%d,%d,%d,%d,%lld,%lld,%lld,%.0f,%.0f,%.0f\n",
                c->m, c->n, c->up, c->lo,
                c->bar, c->best, status_of(c), c->iters, c->slices, c->t_improved,
                c->improv_src[SRC_RR], c->improv_src[SRC_SA], c->improv_src[SRC_SYM],
                c->improv_src[SRC_SEED], c->it_e[0], c->it_e[1], c->it_e[2],
                c->sec_e[0], c->sec_e[1], c->sec_e[2]);
    }
    fclose(f);
    rename(tmp, p);
}

static void print_table(double elapsed) {
    int nmin = 99, nmax = 0, mmin = 99, mmax = 0;
    for (int i = 0; i < ncases; i++) {
        if (cases[i].n < nmin) nmin = cases[i].n;
        if (cases[i].n > nmax) nmax = cases[i].n;
        if (cases[i].m < mmin) mmin = cases[i].m;
        if (cases[i].m > mmax) mmax = cases[i].m;
    }
    printf("\n=== %.1f min ===\n  m\\n", elapsed / 60.0);
    for (int n = nmin; n <= nmax; n++) printf("%6d", n);
    printf("\n");
    for (int m = mmin; m <= mmax; m++) {
        printf("%4d", m);
        for (int n = nmin; n <= nmax; n++) {
            int i = (m <= n) ? cidx[m][n] : -1;
            if (i < 0) { printf("%6s", "-"); continue; }
            Case *c = &cases[i];
            char mark = ' ';
            if (c->up && c->best >= c->up) mark = '*';
            else if (c->best > c->bar) mark = '+';
            else if (c->best > c->lo) mark = '!';
            else if (c->best == c->lo) mark = '=';
            printf("%5d%c", c->best, mark);
        }
        printf("\n");
    }
    printf("(* = atingiu UP; + = supera a barra trivial; ! = supera so o artigo; = = iguala o artigo)\n");
    fflush(stdout);
}

static void maybe_report(void) {
    double now = omp_get_wtime();
    if (now < next_report) return;
    #pragma omp critical(report)
    {
        if (now >= next_report) {
            next_report = now + 60.0;
            print_table(now - t0);
            write_summary();
        }
    }
}

// ---------- vizinhos e sementes ----------
static Case *find_case(int m, int n, int *tr) {
    *tr = 0;
    if (m > n) { int t = m; m = n; n = t; *tr = 1; }
    if (m < 1 || m > MAXM || n > 32) return NULL;
    int i = cidx[m][n];
    return i < 0 ? NULL : &cases[i];
}

static void transpose(const uint32_t *src, int m, int n, uint32_t *dst) {
    memset(dst, 0, sizeof(uint32_t) * MAXM);
    for (int r = 0; r < m; r++)
        for (int c = 0; c < n; c++)
            if ((src[r] >> c) & 1) dst[c] |= 1u << r;
}

static void pool_push(Case *cs, const uint32_t *rows, int cnt) {
    #pragma omp critical(pool)
    {
        if (cs->npool < POOL) {
            memcpy(cs->pool[cs->npool], rows, sizeof(uint32_t) * MAXM);
            cs->pool_cnt[cs->npool++] = cnt;
        } else {
            int w = 0;
            for (int i = 1; i < POOL; i++) if (cs->pool_cnt[i] < cs->pool_cnt[w]) w = i;
            if (cnt >= cs->pool_cnt[w]) {
                memcpy(cs->pool[w], rows, sizeof(uint32_t) * MAXM);
                cs->pool_cnt[w] = cnt;
            }
        }
    }
}

static void seed_neighbors(Case *cs, const uint32_t *A, uint64_t *s);

// candidato a solucao de cs (validado aqui); sementes que nao melhoram vao ao pool
static void offer(Case *cs, const uint32_t *rows, int src, uint64_t *s) {
    int cnt = count_ones(rows, cs->m);
    if (cnt > cs->best && valid_full(rows, cs->m, cs->n)) {
        int did = 0;
        #pragma omp critical(best)
        {
            if (cnt > cs->best) {
                cs->best = cnt;
                memcpy(cs->rows, rows, sizeof cs->rows);
                cs->t_improved = omp_get_wtime() - t0;
                cs->improv_src[src]++;
                save_case(cs);
                did = 1;
            }
        }
        if (did) {
            if (cs->best > cs->lo && cs->lo) {
                #pragma omp critical(report)
                printf("[%7.1f s] Z(%d,%d) >= %d  (%s; artigo %d, barra %d, UP %d)\n",
                       omp_get_wtime() - t0, cs->m, cs->n, cnt, SRC_NAME[src], cs->lo, cs->bar, cs->up);
            }
            if (opt_seed) seed_neighbors(cs, rows, s);
        }
    } else if ((src == SRC_SEED || src == SRC_SYM) && cnt >= cs->best - 4) {
        pool_push(cs, rows, cnt);
    }
}

static void send_seed(int M, int N, uint32_t *B, uint64_t *s) {
    int tr;
    Case *tc = find_case(M, N, &tr);
    if (!tc || (tc->up && tc->best >= tc->up)) return;
    if (tr) {
        uint32_t T[MAXM];
        transpose(B, M, N, T);
        greedy_fill(T, tc->m, tc->n, s);
        offer(tc, T, SRC_SEED, s);
    } else {
        greedy_fill(B, M, N, s);
        offer(tc, B, SRC_SEED, s);
    }
}

static void seed_neighbors(Case *cs, const uint32_t *A, uint64_t *s) {
    int m = cs->m, n = cs->n;
    uint32_t B[MAXM];
    // (m, n+1): coluna vazia
    if (n + 1 <= 32) { memcpy(B, A, sizeof B); send_seed(m, n + 1, B, s); }
    // (m+1, n): linha vazia
    if (m + 1 <= MAXM) { memcpy(B, A, sizeof B); B[m] = 0; send_seed(m + 1, n, B, s); }
    // (m, n-1): remove a coluna mais vazia e uma aleatoria
    for (int v = 0; v < 2 && n > 1; v++) {
        int col = 0;
        if (v == 0) {
            int bestc = 99;
            for (int c = 0; c < n; c++) {
                int k = 0;
                for (int r = 0; r < m; r++) k += (A[r] >> c) & 1;
                if (k < bestc) { bestc = k; col = c; }
            }
        } else col = rnd(s, n);
        memset(B, 0, sizeof B);
        for (int r = 0; r < m; r++) {
            uint32_t lowm = (1u << col) - 1;
            B[r] = (A[r] & lowm) | ((A[r] >> (col + 1)) << col);
        }
        send_seed(m, n - 1, B, s);
    }
    // (m-1, n): remove a linha mais vazia e uma aleatoria
    for (int v = 0; v < 2 && m > 1; v++) {
        int row = 0;
        if (v == 0) {
            for (int r = 1; r < m; r++)
                if (__builtin_popcount(A[r]) < __builtin_popcount(A[row])) row = r;
        } else row = rnd(s, m);
        memset(B, 0, sizeof B);
        for (int r = 0, q = 0; r < m; r++) if (r != row) B[q++] = A[r];
        send_seed(m - 1, n, B, s);
    }
}

// ---------- motores ----------
// rip-up and repair (prototipo)
static long long rr_slice(Case *cs, uint32_t *cur, uint64_t *s, double slice_end) {
    int m = cs->m, n = cs->n;
    uint32_t cand[MAXM];
    greedy_fill(cur, m, n, s);
    int curc = count_ones(cur, m), localbest = curc;
    int kmax = 2 + (m * n) / 40;
    long long it = 0;
    for (;;) {
        memcpy(cand, cur, sizeof cand);
        perturb(cand, m, n, s, 1 + rnd(s, kmax));
        greedy_fill(cand, m, n, s);
        int cc = count_ones(cand, m);
        if (cc >= curc || (cc == curc - 1 && rnd(s, 1000) < 3)) {
            memcpy(cur, cand, sizeof cand);
            curc = cc;
        }
        if (curc > localbest) {
            localbest = curc;
            if (curc > cs->best) offer(cs, cur, SRC_RR, s);
        }
        if ((++it & 255) == 0) {
            if (omp_get_wtime() >= slice_end) break;
            maybe_report();
        }
    }
    return it;
}

// recozimento simulado: adicionar um 1 e reparar os K33 criados
static long long sa_slice(Case *cs, uint32_t *cur, uint64_t *s, double slice_end) {
    int m = cs->m, n = cs->n;
    greedy_fill(cur, m, n, s);
    int curc = count_ones(cur, m);
    uint32_t best[MAXM], cand[MAXM];
    memcpy(best, cur, sizeof best);
    int bestc = curc;
    const double T0 = 0.6, T1 = 0.05;
    const long long EPOCH = 200000;
    const double decay = pow(T1 / T0, 1.0 / EPOCH);
    double T = T0;
    long long it = 0;
    for (;;) {
        int r = rnd(s, m), c = rnd(s, n);
        uint32_t b = 1u << c;
        if (cur[r] & b) {
            if (rnd01(s) < exp(-1.0 / T)) { cur[r] &= ~b; curc--; }
        } else {
            memcpy(cand, cur, sizeof cand);
            cand[r] |= b;
            int removed = 0;
            for (int i = 0; i < m; i++) {
                if (i == r || !(cand[i] & b)) continue;
                for (int j = i + 1; j < m; j++) {
                    if (!(cand[i] & b)) break;
                    if (j == r || !(cand[j] & b)) continue;
                    uint32_t S;
                    while (__builtin_popcount(S = cand[r] & cand[i] & cand[j]) >= 3) {
                        int who = rnd(s, 3);
                        int row = who == 0 ? r : (who == 1 ? i : j);
                        uint32_t opts = (row == r) ? (S & ~b) : S;
                        cand[row] &= ~kth_bit(opts, rnd(s, __builtin_popcount(opts)));
                        removed++;
                    }
                }
            }
            int d = 1 - removed;
            if (d >= 0 || rnd01(s) < exp(d / T)) { memcpy(cur, cand, sizeof cand); curc += d; }
        }
        if (curc > bestc) {
            bestc = curc;
            memcpy(best, cur, sizeof best);
            if (bestc > cs->best) offer(cs, best, SRC_SA, s);
        }
        T *= decay;
        if (++it % EPOCH == 0) {
            T = T0;
            if (rnd(s, 2)) { memcpy(cur, best, sizeof best); curc = bestc; }
        }
        if ((it & 4095) == 0) {
            if (omp_get_wtime() >= slice_end) break;
            maybe_report();
        }
    }
    return it;
}

// busca sobre orbitas de Z_p (blocos circulantes)
typedef struct {
    int norb;
    int ost[MAXORB + 1];
    short cell[MAXM * 32];
} Orbits;

static void build_orbits(Orbits *O, int p, int a, int b, int r0, int c0) {
    int no = 0, nc = 0;
    #define CELL(r, c) (short)(((r) << 5) | (c))
    for (int i = 0; i < a; i++)
        for (int j = 0; j < b; j++)
            for (int d = 0; d < p; d++) {
                O->ost[no++] = nc;
                for (int x = 0; x < p; x++) O->cell[nc++] = CELL(i * p + x, j * p + (x + d) % p);
            }
    for (int f = 0; f < r0; f++)
        for (int j = 0; j < b; j++) {
            O->ost[no++] = nc;
            for (int y = 0; y < p; y++) O->cell[nc++] = CELL(a * p + f, j * p + y);
        }
    for (int i = 0; i < a; i++)
        for (int g = 0; g < c0; g++) {
            O->ost[no++] = nc;
            for (int x = 0; x < p; x++) O->cell[nc++] = CELL(i * p + x, b * p + g);
        }
    for (int f = 0; f < r0; f++)
        for (int g = 0; g < c0; g++) {
            O->ost[no++] = nc;
            O->cell[nc++] = CELL(a * p + f, b * p + g);
        }
    O->ost[no] = nc;
    O->norb = no;
    #undef CELL
}

static void orbit_fill(uint32_t *rows, int m, const Orbits *O, unsigned char *on, uint64_t *s) {
    int order[MAXORB];
    for (int i = 0; i < O->norb; i++) order[i] = i;
    for (int i = O->norb - 1; i > 0; i--) {
        int j = rnd(s, i + 1);
        int t = order[i]; order[i] = order[j]; order[j] = t;
    }
    uint32_t save[MAXM];
    for (int t = 0; t < O->norb; t++) {
        int o = order[t];
        if (on[o]) continue;
        memcpy(save, rows, sizeof save);
        int k;
        for (k = O->ost[o]; k < O->ost[o + 1]; k++) {
            int r = O->cell[k] >> 5, c = O->cell[k] & 31;
            if (!can_add(rows, m, r, c)) break;
            rows[r] |= 1u << c;
        }
        if (k < O->ost[o + 1]) memcpy(rows, save, sizeof save);
        else on[o] = 1;
    }
}

static void complete_and_offer(Case *cs, const uint32_t *sym, uint64_t *s) {
    uint32_t t[MAXM], bestt[MAXM];
    int bc = -1;
    for (int q = 0; q < 4; q++) {
        memcpy(t, sym, sizeof t);
        greedy_fill(t, cs->m, cs->n, s);
        int c = count_ones(t, cs->m);
        if (c > bc) { bc = c; memcpy(bestt, t, sizeof t); }
    }
    offer(cs, bestt, SRC_SYM, s);
}

static long long sym_slice(Case *cs, uint64_t *s, double slice_end) {
    static __thread Orbits O;
    int m = cs->m;
    int q = rnd(s, cs->nsym);
    build_orbits(&O, cs->sym_p[q], cs->sym_a[q], cs->sym_b[q], cs->sym_r0[q], cs->sym_c0[q]);
    uint32_t cur[MAXM] = {0}, cand[MAXM], symbest[MAXM];
    unsigned char on[MAXORB] = {0}, con[MAXORB];
    orbit_fill(cur, m, &O, on, s);
    int curc = count_ones(cur, m), bestc = curc;
    memcpy(symbest, cur, sizeof cur);
    complete_and_offer(cs, symbest, s);
    int kmax = 2 + O.norb / 8;
    long long it = 0;
    for (;;) {
        memcpy(cand, cur, sizeof cand);
        memcpy(con, on, O.norb);
        int k = 1 + rnd(s, kmax);
        for (int t = 0, tries = 0; t < k && tries < 4 * O.norb; tries++) {
            int o = rnd(s, O.norb);
            if (!con[o]) continue;
            con[o] = 0;
            for (int e = O.ost[o]; e < O.ost[o + 1]; e++)
                cand[O.cell[e] >> 5] &= ~(1u << (O.cell[e] & 31));
            t++;
        }
        orbit_fill(cand, m, &O, con, s);
        int cc = count_ones(cand, m);
        if (cc >= curc || (cc == curc - 1 && rnd(s, 1000) < 3)) {
            memcpy(cur, cand, sizeof cand);
            memcpy(on, con, O.norb);
            curc = cc;
        }
        if (curc > bestc) {
            bestc = curc;
            memcpy(symbest, cur, sizeof cur);
            complete_and_offer(cs, symbest, s);
        }
        if ((++it & 255) == 0) {
            if (omp_get_wtime() >= slice_end) break;
            maybe_report();
        }
    }
    complete_and_offer(cs, symbest, s);
    return it;
}

// ---------- escalonamento ----------
static int is_done(const Case *c) { return c->up && c->best >= c->up; }

static int pick_case(uint64_t *s) {
    double w[MAXCASES], tot = 0;
    for (int i = 0; i < ncases; i++) {
        Case *c = &cases[i];
        w[i] = 0;
        if (is_done(c)) continue;
        w[i] = !opt_prio ? 1.0 : (c->up ? 1.0 + (c->up - c->best) : 5.0);
        tot += w[i];
    }
    if (tot <= 0) return -1;
    double x = rnd01(s) * tot;
    for (int i = 0; i < ncases; i++) {
        x -= w[i];
        if (w[i] > 0 && x <= 0) return i;
    }
    for (int i = ncases - 1; i >= 0; i--) if (w[i] > 0) return i;
    return -1;
}

static void setup_sym(Case *c) {
    c->nsym = 0;
    for (int p = 4; p <= c->m && c->nsym < MAXSYM; p++) {
        int a = c->m / p, r0 = c->m % p, b = c->n / p, c0 = c->n % p;
        if (a < 1 || b < 1 || r0 > 3 || c0 > 3) continue;
        c->sym_p[c->nsym] = p; c->sym_a[c->nsym] = a; c->sym_b[c->nsym] = b;
        c->sym_r0[c->nsym] = r0; c->sym_c0[c->nsym] = c0;
        c->nsym++;
    }
}

int main(int argc, char **argv) {
    double hours = 8.0, slice = 20.0;
    int mmin = 8, mmax = 16, nmin = 16, nmax = 23, opt;
    while ((opt = getopt(argc, argv, "t:m:M:n:N:s:e:d:SCPq")) != -1) {
        switch (opt) {
        case 't': hours = atof(optarg); break;
        case 'm': mmin = atoi(optarg); break;
        case 'M': mmax = atoi(optarg); break;
        case 'n': nmin = atoi(optarg); break;
        case 'N': nmax = atoi(optarg); break;
        case 's': slice = atof(optarg); break;
        case 'e': engine = !strcmp(optarg, "rr") ? 0 : !strcmp(optarg, "sa") ? 1 : 2; break;
        case 'd': resdir = optarg; break;
        case 'S': opt_seed = 0; break;
        case 'C': opt_sym = 0; break;
        case 'P': opt_prio = 0; break;
        case 'q': opt_open_only = 1; break;
        default: fprintf(stderr, "opcao invalida\n"); return 1;
        }
    }
    if (mmax > MAXM || nmax > 32) { fprintf(stderr, "m <= 32 e n <= 32\n"); return 1; }
    {   // mkdir -p
        char p[512];
        snprintf(p, sizeof p, "%s", resdir);
        for (char *q = p + 1; *q; q++)
            if (*q == '/') { *q = 0; mkdir(p, 0755); *q = '/'; }
        mkdir(p, 0755);
    }
    memset(cidx, -1, sizeof cidx);

    for (int m = mmin; m <= mmax; m++)
        for (int n = nmin; n <= nmax; n++) {
            if (m > n || ncases >= MAXCASES) continue;
            int up = up_lit(m, n);
            int lo = in_table(m, n) ? LO[m - 8][n - 16] : 0;
            if (opt_open_only && up && up == lo) continue;
            Case *c = &cases[ncases];
            memset(c, 0, sizeof *c);
            c->m = m; c->n = n; c->up = up; c->lo = lo; c->bar = lo;
            setup_sym(c);
            load_case(c);
            c->start_best = c->best;
            cidx[m][n] = ncases++;
        }
    if (ncases == 0) { fprintf(stderr, "nenhum caso\n"); return 1; }

    int nthreads = omp_get_max_threads();
    printf("Z(m,n,3,3) v2: %d casos, %d threads, %.2f h, fatias de %.0f s, motor %s, "
           "semeadura %d, simetricas %d, prioridade %d, dir %s\n",
           ncases, nthreads, hours, slice, engine == 0 ? "rr" : engine == 1 ? "sa" : "mix",
           opt_seed, opt_sym, opt_prio, resdir);

    t0 = omp_get_wtime();
    deadline = t0 + hours * 3600.0;
    next_report = t0 + 60.0;

    // retomada: semeia vizinhos a partir do que foi carregado
    if (opt_seed) {
        uint64_t s0 = 42;
        for (int i = 0; i < ncases; i++)
            if (cases[i].best > 0) {
                uint32_t A[MAXM];
                memcpy(A, cases[i].rows, sizeof A);
                seed_neighbors(&cases[i], A, &s0);
            }
    }

    #pragma omp parallel
    {
        uint64_t seed = 0x1234567ULL + 1000003ULL * (uint64_t)omp_get_thread_num()
                        + (uint64_t)(omp_get_wtime() * 1e6);
        uint32_t cur[MAXM];
        while (omp_get_wtime() < deadline) {
            int ci = pick_case(&seed);
            if (ci < 0) break;
            Case *cs = &cases[ci];
            double slice_end = omp_get_wtime() + slice;
            if (slice_end > deadline) slice_end = deadline;
            long long it;
            int e;
            double ts = omp_get_wtime();

            if (opt_sym && cs->nsym && rnd(&seed, 5) == 0) {
                e = 2;
                it = sym_slice(cs, &seed, slice_end);
            } else {
                // ponto de partida: pool de sementes, melhor global ou do zero
                memset(cur, 0, sizeof cur);
                int u = rnd(&seed, 100);
                if (cs->npool && u < 25) {
                    #pragma omp critical(pool)
                    memcpy(cur, cs->pool[rnd(&seed, cs->npool)], sizeof cur);
                } else if (cs->best > 0 && u < 80) {
                    #pragma omp critical(best)
                    memcpy(cur, cs->rows, sizeof cur);
                }
                e = engine == 2 ? (int)rnd(&seed, 2) : engine;
                it = e == 0 ? rr_slice(cs, cur, &seed, slice_end) : sa_slice(cs, cur, &seed, slice_end);
            }
            double dt = omp_get_wtime() - ts;
            #pragma omp atomic
            cs->iters += it;
            #pragma omp atomic
            cs->it_e[e] += it;
            #pragma omp atomic
            cs->sec_e[e] += dt;
            #pragma omp atomic
            cs->slices++;
        }
    }

    print_table(omp_get_wtime() - t0);
    write_summary();
    printf("Fim. Resultados em %s/\n", resdir);
    return 0;
}
