#!/bin/bash
# SAT por perfil (indicio): codifica com ../../sat/profile_sat.py e roda kissat com limite.
cd /work/approaches/lp_profiles/sat
enc() { python3 /work/sat/profile_sat.py encode $1 $2 "$3" $4 --pair; }
enc 14 21 "7 7 7 7 7 7 7 7 7 7 7 7 7 7 7 7 6 6 6 6 6" p14_21.cnf
enc 16 21 "8 8 8 8 8 8 8 8 8 8 8 8 8 7 7 7 7 7 7 7 7" p16_21.cnf
(timeout 2700 nice kissat -q p14_21.cnf > p14_21.out 2>&1; echo "exit $?" >> p14_21.out) &
(timeout 2700 nice kissat -q p16_21.cnf > p16_21.out 2>&1; echo "exit $?" >> p16_21.out) &
wait
