/* brute.c -- contagem ROTULADA (sem simetria) de matrizes F x N sem 3x3 de uns com
 * >= T uns, para validar orderly.c em casos pequenos.  uso: brute N F T */
#include <stdio.h>
#include <stdlib.h>
typedef unsigned int u32;
static int N, F, T; static u32 R[32]; static long long cnt = 0;
static void rec(int k, int e) {
    if (e + (F - k) * N < T) return;
    if (k == F) { cnt++; return; }
    for (u32 r = 0; r < (1u << N); r++) {
        int ok = 1;
        for (int i = 0; i < k && ok; i++)
            for (int j = i + 1; j < k; j++)
                if (__builtin_popcount(R[i] & R[j] & r) >= 3) { ok = 0; break; }
        if (!ok) continue;
        R[k] = r; rec(k + 1, e + __builtin_popcount(r));
    }
}
int main(int c, char **v) { N = atoi(v[1]); F = atoi(v[2]); T = atoi(v[3]); rec(0, 0); printf("labeled %lld\n", cnt); return 0; }
