#!/bin/bash
# para cada celula, desce k a partir de UB enquanto todos os perfis forem eliminados
# uso: descend.sh arquivo_celulas jobs nivel pasta_cert pasta_log
cd /work/approaches/lp_profiles
mkdir -p $5 $4
while read m n lb ub; do
  k=$ub
  while [ $k -gt $lb ]; do
    log=$5/z${m}_${n}_k${k}.log
    [ -s $log ] || nice python3 search.py $m $n $k --level $3 --jobs $2 --out $4 > $log 2>&1
    echo "z($m,$n) k=$k: $(tail -1 $log)"
    grep -q "sobram 0$" $log || break
    k=$((k-1))
  done
done < $1
