# Abordagem 3: busca tabu com conflitos (limites inferiores)

**Resultado: nenhuma melhora.** Nas 21 células abertas a busca tabu nunca achou uma matriz válida
com k = nosso+1. Ela reproduz o `nosso` atual em todas as células, a partir de matrizes aleatórias,
e em geral leva de segundos a poucos minutos. `found/` está vazio.

## Método (`tabu.c`)

- **Estado:** uma matriz m×n com exatamente k uns. Linhas e colunas são guardadas como máscaras de bits.
- **Custo:** soma, sobre as triplas de linhas {a,b,c}, de max(0, t−2), onde t = |colunas comuns|.
  Com `-f k33` o custo passa a ser o número de submatrizes 3×3 cheias, C(t,3). Custo 0 equivale
  a uma matriz válida.
- **Movimento:** mover um 1 de (r,c) para um 0 em (r',c'). A cada passo, a vizinhança inteira
  (uns × zeros, ~20–25 mil movimentos) é avaliada com delta exato:
  `rem(r,c) + add(r',c') + correção`. A correção cobre as triplas atingidas pelas duas metades
  ({r,r',z}, o caso r=r' e o caso c=c'). Os deltas rem/add saem de popcounts sobre as máscaras.
  O custo incremental é conferido contra o recálculo completo a cada log.
- **Tabu:** depois do movimento, recolocar 1 em (r,c) e retirar o 1 de (r',c') ficam proibidos
  por `T + rand(0..R)` passos. **Aspiração:** um movimento tabu é aceito se levar a custo < melhor.
- **Perturbação** (modo padrão): sem melhora em `S` passos, aplica `K` trocas aleatórias.
- **Pesos** (`-w P`, estilo breakout): em cada passo sem movimento melhorante, com probabilidade P%,
  soma 1 ao peso de cada tripla violada; a busca minimiza o custo ponderado. Se algum peso passar
  de 1000, todos os pesos são divididos por 2.
- **Modo subida** (`-c`): ao chegar a custo 0, grava a matriz, acrescenta o 1 de menor custo e
  continua em k+1.
- **Partidas:** matriz aleatória (com subida a partir de nosso−12, ou direto em nosso+1) ou
  `results/Z_m_n.txt` com um 1 extra colocado de forma gulosa (k = nosso+1).

Velocidade: ~7 mil passos/s em 13×19 e ~4 mil passos/s em 16×23 (um núcleo).

## Parâmetros

O padrão é `T=10, R=10, S=20000, K=3`, custo `excess`. As campanhas usaram esse padrão (`d`) e
pesos `-w 10` (`w`). A rodada 3 também usou `-w 30`.

## Calibração (tempo para reproduzir valores conhecidos, modo subida a partir de aleatória com nosso−12)

| célula = valor | configuração | tempos (s) por semente |
|---|---|---|
| (13,19)=120 | padrão | 0,9 · 1,0 · 1,0 |
| (13,23)=140, (15,20)=139, (16,17)=132 | padrão | < 0,4 (3/3 sementes cada) |
| (14,19)=128 | padrão `T10 R10` | 5 · 17 · 18 · 29 · 36 · 37 |
| (14,19)=128 | `T5 R5` | 0/6 em 120 s |
| (14,19)=128 | `T20 R20` | 70 · 87 · 4 falhas (120 s) |
| (14,19)=128 | `S5000` | 9 · 38 · 45 · 66 · 67 · 1 falha |
| (14,19)=128 | `S100000 K5` | 3 · 28 · 36 · 37 · 55 · 1 falha |
| (14,19)=128 | `-f k33` | 11 · 17 · 24 · 39 · 49 · 67 |
| (14,19)=128 | `-w 100` / `-w 30` / `-w 10` / `-w 3` | 0/6 · 5/6 (20–37) · 6/6 (1,5–79) · 6/6 (6–64) |
| (16,23)=163 | padrão | 30 · 55 · 235 · 257 · 275 · 1 falha (300 s) |
| (16,23)=163 | `-w 10` | 11 · 16 · 21 · 38 · 60 · 81 |

Os arquivos brutos estão em `calib1.txt`, `tune1.txt`, `tune2.txt` e `tune3.txt`. Conclusão: tenure
em torno de 10–20 funciona e tenure 5 cicla. Pesos com P≈10% são a melhor configuração nas células
mais difíceis.

## Campanhas (7 processos, `nice`, container `zaran`)

- **Rodada 1** (`round1.txt` vazio): foi interrompida pela queda do Docker depois de ~3 min por job.
  Os logs `*_r1` ficaram registrados.
- **Rodada 2** (`campaign.sh 2 1200`): 21 células × {aleatória com subida, nossa melhor+1} ×
  {padrão, `-w 10`}, 20 min cada, ou seja, 84 jobs e ~28 h de CPU.
- **Rodada 3** (`campaign3.sh 1200`): 21 células × aleatória direto em k = nosso+1 × {`-w 10`, `-w 30`},
  20 min cada, ou seja, 42 jobs e ~14 h de CPU.

Cada job de 20 min faz 4–9 milhões de passos.

## Resultados por célula

O custo mínimo é o menor número de violações (excesso sobre 2 somado nas triplas de linhas) que
qualquer job atingiu em k = nosso+1.

| (m,n) | nosso | UB | maior k (tabu) | jobs | custo mínimo em nosso+1 |
|---|---|---|---|---|---|
| (13,19) | 120 | 122 | 120 | 8 | 5 |
| (13,20) | 125 | 128 | 125 | 8 | 3 |
| (13,21) | 131 | 134 | 131 | 8 | 3 |
| (13,23) | 140 | 143 | 140 | 7 | 1 |
| (14,19) | 128 | 130 | 128 | 6 | 5 |
| (14,20) | 131 | 136 | 131 | 6 | 1 |
| (14,21) | 136 | 142 | 136 | 6 | 1 |
| (14,22) | 142 | 147 | 142 | 6 | 1 |
| (14,23) | 146 | 153 | 146 | 6 | 1 |
| (15,19) | 136 | 139 | 136 | 6 | 5 |
| (15,20) | 139 | 145 | 139 | 6 | 1 |
| (15,21) | 144 | 152 | 144 | 6 | 2 |
| (15,22) | 150 | 157 | 150 | 6 | 2 |
| (15,23) | 156 | 163 | 156 | 6 | 5 |
| (16,17) | 132 | 133 | 132 | 6 | 2 |
| (16,18) | 137 | 140 | 137 | 6 | 2 |
| (16,19) | 142 | 147 | 142 | 6 | 1 |
| (16,20) | 147 | 154 | 147 | 6 | 2 |
| (16,21) | 152 | 161 | 152 | 6 | 1 |
| (16,22) | 158 | 167 | 158 | 6 | 3 |
| (16,23) | 163 | 173 | 163 | 6 | 1 |

Observações:

- **Os jobs aleatórios sempre chegam exatamente ao `nosso`.** Isso vale para 63 jobs com subida, em
  todas as células, e nenhum passa dele. Os valores atuais parecem ser o ponto onde a busca local
  satura, e não um artefato da busca anterior (`search/zaran.c`).
- **O custo mínimo em nosso+1 é idêntico em todos os jobs de uma célula,** seja qual for a partida
  (aleatória, com subida ou direta, ou nossa melhor+1) e o modo (padrão, `-w 10` ou `-w 30`). Esse
  mínimo é atingido no primeiro minuto e nunca melhora. Um piso tão estável sugere que nosso+1 pode
  ser inviável em várias dessas células (compare com as eliminações de perfis da abordagem 4), mas
  isso **não** é prova.
- Todas as 46 matrizes gravadas pela busca (`runs/`, com k ≤ nosso) passam no `verify.py`.

## Arquivos

- `tabu.c`: a busca. Compilar com `gcc -O3 -march=native -o tabu tabu.c`; a lista de opções está
  no cabeçalho.
- `calibrate.sh` e `tune.sh`: calibração. `campaign.sh` e `campaign3.sh`: campanhas.
  `summary.sh`: tabela, cópia para `found/` e `verify.py`. `watch.sh`: monitor de melhoras.
- `open.txt`: as 21 células abertas (m,n,nosso,UB), extraídas de `literature.csv`.
- `logs/`: saída de cada job (`.out` traz ACHOU/FALHOU, `.err` traz o progresso).
  `runs/`: as últimas matrizes válidas de cada job.
