#!/bin/bash
cd /work/approaches/sym_sat
echo "== pass1 resume $(date)"; python3 run.py --timeout 60 --maxorb 120 --jobs 7 >> logs/pass1.out 2>&1
echo "== mixed $(date)";  python3 run.py --mixed --timeout 60 --maxorb 120 --jobs 7 > logs/mixed.out 2>&1
echo "== diag k=nosso $(date)"; python3 run.py --delta 0 --timeout 30 --maxorb 100 --jobs 7 > logs/diag.out 2>&1
echo "== long $(date)"; python3 run.py --timeout 600 --maxorb 120 --jobs 7 > logs/long.out 2>&1
echo "== done $(date)"
