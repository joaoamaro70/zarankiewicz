# Abordagem 2: LNS com SAT exato (limites inferiores)

**Resultado: nenhuma melhora.** Em nenhuma das 21 células abertas a busca achou matriz com mais
uns que o `nosso` atual; `found/` está vazio. Cerca de 75 mil janelas foram provadas UNSAT
(nenhum preenchimento da janela atinge |X|+1), o que sugere que as matrizes atuais são
localmente ótimas para vizinhanças bem grandes (até 8 linhas inteiras de 16, 6 colunas
inteiras, cruz 3+3, blocos 11×13).

## Método (`lns.py`)
Parte de `results/Z_m_n.txt` (|X| = `nosso`). Escolhe uma janela de células livres, congela
o resto e gera um CNF: a cláusula 3×3 entra só quando o 3×3 tem célula livre e nenhum 0 congelado,
e os 1s congelados saem da cláusula. A contagem "uns livres ≥ |X|+1 − uns congelados" usa um
contador sequencial (`sat/zsat.py`, `CNF.at_most`). O Kissat roda com 40 s de limite por instância.
Tipos de janela:

- `rows a`: a linhas inteiras, com ordem lex entre as linhas livres (são intercambiáveis);
- `cols a`: a colunas inteiras, com ordem lex entre elas;
- `cross a×a`: a linhas inteiras + a colunas inteiras;
- `block a×b`: submatriz a linhas × b colunas (60–90% de m e de n).

Fases em ordem crescente de tamanho (rows/cols/cross s = 1..8, depois blocos). Cada fase usa
todas as combinações se forem ≤ 300; senão, 300 janelas aleatórias distintas. Uma fase é
abandonada com > 30% de timeouts (e as maiores do mesmo tipo também) e tem teto de 15 min.
Quando acha um SAT, adota a matriz nova e recomeça das fases pequenas. Quando todas as fases
acabam sem melhora, faz 40 tentativas de **movimento de platô**: em janela `block`/`cross`
aleatória, pede outra matriz com o mesmo |X| e preenchimento diferente do atual (cláusula de
bloqueio). Depois recomeça as fases. Execução: `runall.py` (pool de 7 processos, `nice`,
container `--cpus=7`), fatias de 40 min, cerca de 2 h por célula (cerca de 42 h-thread no total).

## Calibração (tempo por janela, 13×19 e 16×23)
rows ≤ 4 e cols ≤ 3: < 0,2 s; rows 5–6: 1–16 s; cols 5: 1–15 s; cols 7: ≥ 45 s / timeout;
cross 2+2: 0,2 s; cross 3+3: 8–22 s; cross 4+4: sempre timeout. Blocos de até ~60% são triviais
(resolvidos por propagação); blocos ~75–80% (10–11 × 13–15) começam a estourar.

## Janelas provadas UNSAT (somadas nas 21 células)
| tipo | tamanhos (UNSAT / timeouts) |
|---|---|
| rows | 1: 431, 2: 3005, 3: 8044, 4: 7494/4, 5: 6645/65, 6: 2872/100, 7: 800/65, 8: 124/28 |
| cols | 1: 597, 2: 5895, 3: 8100, 4: 7200, 5: 3167/35, 6: 150/158, 7: 0/12 |
| cross | 1+1: 8418, 2+2: 8435, 3+3: 2693/293, 4+4 e acima: 0/346 |
| block | 8×11..8×14: 973; 10×10..10×14: 1614/18; 11×12..11×13: 12/21; maiores: só timeouts |

Varreduras completas (todas as combinações, todas UNSAT): rows 1–2 e cols 1–2 em todas as
células; rows 3 para m=13; cross 1+1 para m=13 e para 14×19..21. As demais fases foram amostradas
(300 janelas aleatórias por passagem).

## Por célula
"Fases varridas" = fases em que todas as combinações couberam e todas deram UNSAT.
Os movimentos de platô só chegaram a rodar onde a lista de fases terminou dentro do orçamento.

| célula | início | melhor | janelas UNSAT | timeouts | mov. platô (rodadas) | fases varridas por completo | maior janela UNSAT por tipo | min |
|---|---|---|---|---|---|---|---|---|
| 13×19 | 120 | 120 | 2983 | 43 | 0 (0) | 6 | cols 6, cross 3x3, rows 6 | 122 |
| 13×20 | 125 | 125 | 2962 | 66 | 0 (0) | 6 | cols 6, cross 3x3, rows 6 | 123 |
| 13×21 | 131 | 131 | 3071 | 66 | 0 (0) | 6 | cols 6, cross 3x3, rows 6 | 123 |
| 13×23 | 140 | 140 | 2819 | 66 | 0 (0) | 6 | cols 6, cross 3x3, rows 6 | 123 |
| 14×19 | 128 | 128 | 3250 | 32 | 0 (0) | 5 | block 8x11, cols 6, cross 3x3, rows 7 | 122 |
| 14×20 | 131 | 131 | 2810 | 46 | 0 (0) | 5 | cols 6, cross 3x3, rows 6 | 122 |
| 14×21 | 136 | 136 | 4741 | 79 | 18 (1) | 5 | block 8x13, cols 5, cross 3x3, rows 6 | 137 |
| 14×22 | 142 | 142 | 5000 | 78 | 16 (1) | 4 | block 8x13, cols 6, cross 3x3, rows 6 | 121 |
| 14×23 | 146 | 146 | 4902 | 62 | 24 (1) | 4 | block 8x14, cols 6, cross 3x3, rows 6 | 121 |
| 15×19 | 136 | 136 | 3235 | 26 | 0 (0) | 5 | cols 6, cross 3x3, rows 7 | 120 |
| 15×20 | 139 | 139 | 2829 | 45 | 0 (0) | 5 | cols 6, cross 3x3, rows 7 | 120 |
| 15×21 | 144 | 144 | 2811 | 35 | 0 (0) | 4 | cols 6, cross 3x3, rows 6 | 121 |
| 15×22 | 150 | 150 | 2974 | 49 | 0 (0) | 4 | cols 5, cross 3x3, rows 6 | 121 |
| 15×23 | 156 | 156 | 2863 | 39 | 0 (0) | 4 | cols 6, cross 3x3, rows 7 | 120 |
| 16×17 | 132 | 132 | 5819 | 66 | 19 (1) | 5 | block 11x12, cols 5, cross 3x3, rows 8 | 121 |
| 16×18 | 137 | 137 | 4235 | 64 | 24 (1) | 5 | block 11x13, cols 5, cross 3x3, rows 8 | 121 |
| 16×19 | 142 | 142 | 4800 | 62 | 19 (1) | 4 | block 11x13, cols 5, cross 3x3, rows 8 | 120 |
| 16×20 | 147 | 147 | 3178 | 70 | 0 (0) | 4 | block 10x12, cols 6, cross 3x3, rows 7 | 120 |
| 16×21 | 152 | 152 | 4531 | 63 | 19 (1) | 4 | block 10x13, cols 5, cross 3x3, rows 7 | 120 |
| 16×22 | 158 | 158 | 3328 | 59 | 0 (0) | 4 | block 10x13, cols 5, cross 3x3, rows 7 | 120 |
| 16×23 | 163 | 163 | 3528 | 81 | 15 (1) | 4 | block 10x14, cols 5, cross 3x3, rows 6 | 121 |

(Tabela gerada por `summarize.py`. Cada UNSAT vale para a matriz corrente naquele momento; nas
células com platô, foram matrizes diferentes de mesmo |X|.)

## Arquivos
- `lns.py` (driver), `runall.py` (fila de células), `summarize.py` (tabela), `open_cells.py`.
- `state/m_n.json` (estatísticas por fase) e `state/cur_m_n.txt` (matriz corrente, com o mesmo
  |X| do `nosso`; nas 9 células com platô, é uma matriz diferente da de `results/`). Todas as 21
  passam no `verify.py` e podem servir de pontos de partida diversificados.
- `logs/m_n.log` (log por célula).
- `found/`: vazio (seria Z_m_n.txt para matrizes acima do `nosso`).

## Observações
- Tudo rodou cerca de 2 h por célula. Houve uma queda do Docker (de ~02:27 a 10:20) e o estado foi retomado.
- O gargalo são as fases grandes (cross ≥ 4+4, cols ≥ 7, blocos ≥ 80%), que estouram 40 s.
  Mais alcance pediria um limite maior por instância ou outro solver (CaDiCaL, que é incremental).
  Pelos números acima, é pouco provável que melhore: nem 8 linhas inteiras livres de 16 bastaram.
