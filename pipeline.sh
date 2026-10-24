#!/bin/bash
# M3 (benchmarks) seguido de M4 (execucao longa). Roda dentro do container.
# Uso: ./pipeline.sh [horas_execucao_longa]
HOURS=${1:-8}
set -e
cd /work
gcc -O3 -march=native -fopenmp -Wall -o zaran2 zaran2.c -lm
gcc -O3 -march=native -fopenmp -o zaran zaran.c
python3 bars.py > /dev/null
echo "nproc = $(nproc)"

B=bench
rm -rf $B/proto $B/v2 $B/rr $B/sa
mkdir -p $B/proto

echo "== [1/4] prototipo, 10 min =="
(cd $B/proto && nice -n 10 ../../zaran 0.1667 8 16 16 23 > log.txt)
echo "== [2/4] v2 (mix + semeadura + simetricas + prioridade), 10 min =="
nice -n 10 ./zaran2 -t 0.1667 -d $B/v2 > $B/v2.log
echo "== [3/4] v2 so rip-up, sem extras, 4 min =="
nice -n 10 ./zaran2 -t 0.0667 -q -e rr -S -C -P -d $B/rr > $B/rr.log
echo "== [4/4] v2 so recozimento, sem extras, 4 min =="
nice -n 10 ./zaran2 -t 0.0667 -q -e sa -S -C -P -d $B/sa > $B/sa.log

python3 compare.py $B/proto/results $B/v2 $B/rr $B/sa | tee $B/compare.txt
python3 - <<'EOF' | tee -a $B/compare.txt
import csv
def rate(path, col_it, col_sec):
    it = sec = 0
    for r in csv.DictReader(open(path)):
        it += int(r[col_it]); sec += float(r[col_sec])
    return it / sec if sec else 0
p = sum(int(r["iterations"]) for r in csv.DictReader(open("bench/proto/results/summary.csv")))
print(f"prototipo: {p/(600*32):.0f} iter/s/thread (rip-up)")
print(f"v2 rr:     {rate('bench/rr/summary.csv','it_rr','sec_rr'):.0f} iter/s/thread (rip-up)")
print(f"v2 sa:     {rate('bench/sa/summary.csv','it_sa','sec_sa'):.0f} passos/s/thread (SA)")
EOF

echo "== mesclando em results/ e iniciando execucao de $HOURS h =="
python3 merge.py results bench/m1 $B/proto/results $B/v2 $B/rr $B/sa
nice -n 10 ./zaran2 -t "$HOURS" -d results > results/run.log
python3 verify.py results/Z_*.txt > results/verify.txt && echo "verify OK" || echo "verify FALHOU"
