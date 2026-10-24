// zaran.c — busca local para limites inferiores de Z(m,n,3,3)
// Matriz binaria m x n sem submatriz 3x3 toda de uns <=> quaisquer 3 linhas
// compartilham no maximo 2 colunas com 1.
//
// Compilar:  gcc -O3 -march=native -fopenmp -o zaran zaran.c
// Rodar:     ./zaran HORAS [mmin mmax nmin nmax] [fatia_seg]
// Ex.:       ./zaran 8                 (8 horas, m=8..16, n=16..23)
//            ./zaran 0.05 13 16 17 23  (teste de 3 minutos)
//
// Marca '!' quando supera o limite inferior publicado no artigo arXiv 2605.01120.
//
// Resultados em results/Z_m_n.txt (retoma automaticamente na proxima execucao)
// e resumo em results/summary.csv.

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <omp.h>
#include <sys/stat.h>

#define MAXM 32
#define MAXCASES 1024

typedef struct {
    int m, n;
    int best;
    uint32_t rows[MAXM];
    int start_best;      // valor ao iniciar esta execucao
    double t_improved;   // momento da ultima melhora
    long long iters;
    int up, lo;          // limites da Figura 2 do artigo (0 se fora da tabela)
} Case;

static Case cases[MAXCASES];
static int ncases = 0;

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

// ---------- verificacao ----------
static int count_ones(const uint32_t *rows, int m) {
    int c = 0;
    for (int i = 0; i < m; i++) c += __builtin_popcount(rows[i]);
    return c;
}

// verificacao completa e independente: todas as triplas de linhas
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

// pode colocar 1 em (r,c) sem criar K_{3,3}?
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

// preenche gulosamente em ordem aleatoria (uma passada ja deixa a matriz maximal)
static void greedy_fill(uint32_t *rows, int m, int n, uint64_t *s, int *cells) {
    int nc = m * n;
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

// remove k uns: aleatorios, de uma linha ou de uma coluna
static void perturb(uint32_t *rows, int m, int n, uint64_t *s, int k) {
    int type = rnd(s, 10);
    if (type < 7) {
        for (int t = 0; t < k; t++) {
            int tot = count_ones(rows, m);
            if (tot == 0) return;
            int target = rnd(s, tot);
            for (int r = 0; r < m; r++) {
                int pc = __builtin_popcount(rows[r]);
                if (target < pc) {
                    uint32_t x = rows[r];
                    for (int q = 0; q < target; q++) x &= x - 1;
                    rows[r] &= ~(x & -x);
                    break;
                }
                target -= pc;
            }
        }
    } else if (type < 9) {
        int r = rnd(s, m);
        for (int t = 0; t < k && rows[r]; t++) {
            int pc = __builtin_popcount(rows[r]);
            int target = rnd(s, pc);
            uint32_t x = rows[r];
            for (int q = 0; q < target; q++) x &= x - 1;
            rows[r] &= ~(x & -x);
        }
    } else {
        int c = rnd(s, n);
        uint32_t b = 1u << c;
        for (int t = 0; t < k; t++) {
            int r = rnd(s, m);
            rows[r] &= ~b;
        }
    }
}

// ---------- arquivos ----------
static void case_path(char *buf, int m, int n) {
    sprintf(buf, "results/Z_%d_%d.txt", m, n);
}

static void save_case(Case *cs) {
    char p[256], tmp[300];
    case_path(p, cs->m, cs->n);
    sprintf(tmp, "%s.tmp", p);
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
    char p[256], line[256];
    case_path(p, cs->m, cs->n);
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

// Figura 2 do artigo (arXiv 2605.01120v3): limite superior conhecido e limite
// inferior publicado, para m=8..16 e n=16..23. Casos ja fechados tem UP == LO.
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
static int up_value(int m, int n) { return in_table(m, n) ? UP[m - 8][n - 16] : 0; }
static int lo_value(int m, int n) { return in_table(m, n) ? LO[m - 8][n - 16] : 0; }

static void write_summary(double now) {
    FILE *f = fopen("results/summary.csv.tmp", "w");
    if (!f) return;
    fprintf(f, "m,n,best,paper_lower,paper_upper,status,iterations,last_improvement_s\n");
    for (int i = 0; i < ncases; i++) {
        Case *c = &cases[i];
        const char *st = !c->lo ? "fora_da_tabela" : (c->best > c->lo ? (c->best >= c->up ? "NOVO_EXATO" : "NOVO_RECORDE")
                         : (c->best == c->lo ? "igual_artigo" : "abaixo_artigo"));
        if (c->lo && c->lo == c->up && c->best >= c->up) st = "ja_conhecido";
        fprintf(f, "%d,%d,%d,%d,%d,%s,%lld,%.0f\n", c->m, c->n, c->best, c->lo, c->up, st,
                c->iters, c->t_improved);
    }
    fclose(f);
    rename("results/summary.csv.tmp", "results/summary.csv");
}

static void print_table(double elapsed) {
    printf("\n=== %.1f min ===\n", elapsed / 60.0);
    printf("  m\\n");
    int nmin = cases[0].n, nmax = cases[0].n, mmin = cases[0].m, mmax = cases[0].m;
    for (int i = 0; i < ncases; i++) {
        if (cases[i].n < nmin) nmin = cases[i].n;
        if (cases[i].n > nmax) nmax = cases[i].n;
        if (cases[i].m < mmin) mmin = cases[i].m;
        if (cases[i].m > mmax) mmax = cases[i].m;
    }
    for (int n = nmin; n <= nmax; n++) printf("%6d", n);
    printf("\n");
    for (int m = mmin; m <= mmax; m++) {
        printf("%4d", m);
        for (int n = nmin; n <= nmax; n++) {
            int found = 0;
            for (int i = 0; i < ncases; i++)
                if (cases[i].m == m && cases[i].n == n) {
                    char mark = ' ';
                    Case *c = &cases[i];
                    if (c->lo && c->best > c->lo) mark = '!';
                    else if (c->lo && c->best == c->lo) mark = '=';
                    printf("%5d%c", cases[i].best, mark);
                    found = 1;
                }
            if (!found) printf("%6s", "-");
        }
        printf("\n");
    }
    printf("(! = supera o limite inferior do artigo; = = iguala; sem marca = abaixo)\n");
    fflush(stdout);
}

int main(int argc, char **argv) {
    double hours = argc > 1 ? atof(argv[1]) : 8.0;
    int mmin = argc > 2 ? atoi(argv[2]) : 8;
    int mmax = argc > 3 ? atoi(argv[3]) : 16;
    int nmin = argc > 4 ? atoi(argv[4]) : 16;
    int nmax = argc > 5 ? atoi(argv[5]) : 23;
    double slice = argc > 6 ? atof(argv[6]) : 30.0;

    if (mmax > MAXM || nmax > 32) { fprintf(stderr, "m <= 32 e n <= 32\n"); return 1; }
    mkdir("results", 0755);

    for (int m = mmin; m <= mmax; m++)
        for (int n = nmin; n <= nmax; n++) {
            if (m > n) continue;              // Z(m,n) = Z(n,m)
            if (in_table(m, n) && UP[m-8][n-16] == LO[m-8][n-16]) continue; // ja fechado
            if (ncases >= MAXCASES) break;
            Case *c = &cases[ncases++];
            memset(c, 0, sizeof *c);
            c->m = m; c->n = n; c->up = up_value(m, n); c->lo = lo_value(m, n);
            load_case(c);
            c->start_best = c->best;
        }
    if (ncases == 0) { fprintf(stderr, "nenhum caso\n"); return 1; }

    int nthreads = omp_get_max_threads();
    printf("Z(m,n,3,3): %d casos, %d threads, %.2f h, fatias de %.0f s\n",
           ncases, nthreads, hours, slice);

    double t0 = omp_get_wtime();
    double deadline = t0 + hours * 3600.0;
    double next_report = t0 + 60.0;
    long long slice_counter = 0;

    #pragma omp parallel
    {
        uint64_t seed = 0x1234567ULL + 1000003ULL * (uint64_t)omp_get_thread_num()
                        + (uint64_t)(omp_get_wtime() * 1e6);
        int cells[MAXM * 32];
        uint32_t cur[MAXM], cand[MAXM];

        while (omp_get_wtime() < deadline) {
            long long idx;
            #pragma omp atomic capture
            idx = slice_counter++;
            Case *cs = &cases[idx % ncases];
            if (cs->up && cs->best >= cs->up) {          // ja otimo: nao gasta CPU
                int all = 1;
                for (int q = 0; q < ncases; q++) if (!cases[q].up || cases[q].best < cases[q].up) { all = 0; break; }
                if (all) break;
                continue;
            }
            int m = cs->m, n = cs->n;
            for (int i = 0; i < m * n; i++) cells[i] = i;

            // ponto de partida: melhor global (60%) ou do zero (40%)
            memset(cur, 0, sizeof cur);
            if (cs->best > 0 && rnd(&seed, 10) < 6) {
                #pragma omp critical(best)
                memcpy(cur, cs->rows, sizeof cur);
            }
            greedy_fill(cur, m, n, &seed, cells);
            int curc = count_ones(cur, m);
            int localbest = curc;
            long long it = 0;
            double slice_end = omp_get_wtime() + slice;
            if (slice_end > deadline) slice_end = deadline;
            int kmax = 2 + (m * n) / 40;

            for (;;) {
                memcpy(cand, cur, sizeof cand);
                int k = 1 + rnd(&seed, kmax);
                perturb(cand, m, n, &seed, k);
                greedy_fill(cand, m, n, &seed, cells);
                int cc = count_ones(cand, m);
                // aceita igual (plato) e, raramente, pior por 1
                if (cc >= curc || (cc == curc - 1 && rnd(&seed, 1000) < 3)) {
                    memcpy(cur, cand, sizeof cur);
                    curc = cc;
                }
                if (curc > localbest) {
                    localbest = curc;
                    if (curc > cs->best && valid_full(cur, m, n)) {
                        #pragma omp critical(best)
                        {
                            if (curc > cs->best) {
                                cs->best = curc;
                                memcpy(cs->rows, cur, sizeof cs->rows);
                                cs->t_improved = omp_get_wtime() - t0;
                                save_case(cs);
                            }
                        }
                    }
                }
                if ((++it & 1023) == 0) {
                    double now = omp_get_wtime();
                    if (now >= slice_end) break;
                    if (now >= next_report) {
                        #pragma omp critical(report)
                        {
                            if (now >= next_report) {
                                next_report = now + 60.0;
                                print_table(now - t0);
                                write_summary(now - t0);
                            }
                        }
                    }
                }
            }
            #pragma omp atomic
            cs->iters += it;
        }
    }

    double el = omp_get_wtime() - t0;
    print_table(el);
    write_summary(el);
    printf("Fim. Resultados em results/\n");
    return 0;
}
