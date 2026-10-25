# Abordagem 1: SAT com simetria cíclica imposta (limites inferiores)

**Resultado: nenhuma melhoria.** Nenhuma das 21 células abertas ganhou um 1 a mais que o
`nosso` atual. `found/` está vazio.

## Método (`symsat.py`)

- Um gerador g de Z_L age nas linhas por σ (a ciclos de comprimento p, as demais linhas
  fixas) e nas colunas por τ (b ciclos de comprimento q, as demais fixas), com L = lcm(p,q).
  Exigimos A[σr][τc] = A[r][c], então há uma variável por órbita de células.
- Cláusulas 3×3 reescritas em órbitas: só se enumeram os trios de linhas R que são o mínimo
  da sua órbita sob σ (um representante por órbita de pares (R,C)). As cláusulas viram
  conjuntos de órbitas, o que elimina duplicatas.
- Cardinalidade ponderada Σ |órbita|·x ≥ k: contador sequencial de Sinz em que o literal de
  cada órbita aparece |órbita| vezes.
- Resolução com Kissat (`--time`). Quando dá SAT, o modelo é conferido e completado
  gulosamente sem a simetria (200 ordens aleatórias das células zero, cada 1 só entra se não
  criar K_{3,3}).
- `run.py` é a campanha: lê as células abertas de `literature.csv` (UB_lit > max(LB_lit,
  nosso)) e roda em paralelo, sempre com `nice`, registrando em `logs/results.jsonl`. Quando
  dá SAT, tenta k+1 na mesma ação. `summarize.py` gera `logs/results.csv` (uma linha por
  instância) e `logs/summary.md`.

**Validação:** com p=q=11 (linhas "11", colunas "11.11") o método reproduz z(11,22)=121
(122 dá UNSAT com essa simetria) e z(12,22)=132 (1 linha fixa). As duas matrizes passam no
`verify.py` (`tmp/Z_11_22.txt`, `tmp/Z_12_22.txt`). Cada caso leva menos de 2 s.

## O que foi tentado

Todas as 21 células abertas, com k = nosso+1. A coluna `rows`/`cols` do CSV dá os ciclos,
por exemplo `5.5` = dois ciclos de 5 e o resto fixo, `0` = nenhum ciclo.

| fase | ações | filtro | timeout | instâncias | resultado |
|---|---|---|---|---|---|
| 1 | p=q=N, 3≤N≤23, a,b ≥ 0 quaisquer (inclui ação só nas linhas ou só nas colunas) | ≤120 órbitas | 60 s | 1535 | 0 SAT; 1265 UNSAT, 270 timeouts |
| 2 | mistas p≠q, lcm(p,q) ≤ 2·max(p,q) | ≤120 órbitas | 60 s | 3398 | 0 SAT; 12 timeouts |
| 3 (diagnóstico) | as da fase 1, com k = nosso | ≤100 órbitas | 30 s | 1115 | 3 SAT, ver abaixo |
| 4 | os 270 timeouts da fase 1 | ≤120 órbitas | 600 s | 270 | 0 SAT; 79 UNSAT, 191 timeouts |

O tempo de parede somado foi de 41,8 h-thread, com 6 a 7 threads; esse total já conta o
reinício depois da queda do Docker, autorizado com até 7 threads.

**Diagnóstico.** A simetria Z_5 com linhas `5.5` e colunas `5.5.5.5` alcança exatamente o
valor atual em 13×20 (125), 13×21 (131) e 13×23 (140). Nos três casos a completação gulosa
não acrescenta nenhum 1, e k+1 é UNSAT ou timeout nessa ação. Nas outras 18 células,
nenhuma ação com ≤100 órbitas chega sequer ao `nosso` em 30 s. As melhores matrizes atuais
(busca local) não parecem vir de uma estrutura cíclica simples.

**Lacuna.** Restaram 191 instâncias sem resposta após 600 s: 138 com N=3, 37 com N=4, 8 com
N=5 e 8 com N=7, de 42 a 120 órbitas. Também não foram rodadas ações com N=2 nem instâncias
com mais de 120 órbitas, que estão perto do SAT puro e já se sabe que não escalam. Para essas
ações, o UNSAT **não** está provado.

Resumo por célula (a linha com k = nosso é o diagnóstico; a com k = nosso+1 é a tentativa
de melhoria):

| m | n | k | instâncias | SAT | UNSAT | TIMEOUT | tempo (min) |
|---|---|---|---|---|---|---|---|
| 13 | 19 | 120 / 121 | 59 / 204 | 0 / 0 | 50 / 198 | 9 / 6 | 6 / 80 |
| 13 | 20 | 125 / 126 | 63 / 225 | 1 / 0 | 54 / 218 | 8 / 7 | 7 / 98 |
| 13 | 21 | 131 / 132 | 60 / 233 | 1 / 0 | 47 / 222 | 12 / 11 | 8 / 140 |
| 13 | 23 | 140 / 141 | 44 / 217 | 1 / 0 | 40 / 210 | 3 / 7 | 3 / 104 |
| 14 | 19 | 128 / 129 | 56 / 206 | 0 / 0 | 48 / 200 | 8 / 6 | 6 / 79 |
| 14 | 20 | 131 / 132 | 56 / 223 | 0 / 0 | 49 / 215 | 7 / 8 | 6 / 112 |
| 14 | 21 | 136 / 137 | 55 / 230 | 0 / 0 | 44 / 218 | 11 / 12 | 8 / 151 |
| 14 | 22 | 142 / 143 | 49 / 225 | 0 / 0 | 42 / 214 | 7 / 11 | 5 / 120 |
| 14 | 23 | 146 / 147 | 44 / 211 | 0 / 0 | 39 / 201 | 5 / 10 | 5 / 98 |
| 15 | 19 | 136 / 137 | 54 / 223 | 0 / 0 | 49 / 215 | 5 / 8 | 5 / 108 |
| 15 | 20 | 139 / 140 | 59 / 249 | 0 / 0 | 52 / 237 | 7 / 12 | 7 / 134 |
| 15 | 21 | 144 / 145 | 49 / 255 | 0 / 0 | 41 / 240 | 8 / 15 | 6 / 162 |
| 15 | 22 | 150 / 151 | 46 / 250 | 0 / 0 | 39 / 237 | 7 / 13 | 5 / 137 |
| 15 | 23 | 156 / 157 | 40 / 233 | 0 / 0 | 37 / 227 | 3 / 6 | 4 / 82 |
| 16 | 17 | 132 / 133 | 60 / 217 | 0 / 0 | 53 / 211 | 7 / 6 | 6 / 91 |
| 16 | 18 | 137 / 138 | 63 / 254 | 0 / 0 | 52 / 245 | 11 / 9 | 8 / 116 |
| 16 | 19 | 142 / 143 | 49 / 242 | 0 / 0 | 46 / 231 | 3 / 11 | 4 / 123 |
| 16 | 20 | 147 / 148 | 56 / 265 | 0 / 0 | 48 / 254 | 8 / 11 | 6 / 122 |
| 16 | 21 | 152 / 153 | 55 / 271 | 0 / 0 | 46 / 253 | 9 / 18 | 7 / 165 |
| 16 | 22 | 158 / 159 | 52 / 260 | 0 / 0 | 46 / 250 | 6 / 10 | 6 / 98 |
| 16 | 23 | 163 / 164 | 46 / 240 | 0 / 0 | 42 / 234 | 4 / 6 | 5 / 67 |

O detalhe por instância (célula, ciclos, k, órbitas, status, timeout, tempo) está em
`logs/results.csv`.

## Como rodar

```
docker run --rm -v "${PWD}:/work" zaran bash -c "cd /work/approaches/sym_sat && python3 symsat.py solve 11 22 121 11 11.11 --out tmp/Z_11_22.txt"
docker run --rm -v "${PWD}:/work" zaran bash -c "cd /work/approaches/sym_sat && python3 run.py --timeout 60 --maxorb 120 --jobs 6"
```
Opções do `run.py`: `--mixed` (p≠q), `--delta 0` (k = nosso), `--cells 13x19,...`.
