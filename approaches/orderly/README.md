# Abordagem 5: geração ordenada (canonical augmentation) linha a linha

Enumeração exaustiva, a menos de permutações de linhas e de colunas, de matrizes
F×N 0/1 sem submatriz 3×3 toda de uns e com pelo menos T uns. Se a enumeração
termina vazia, isso prova z(F,N) ≤ T−1; se acha uma matriz, ela é um limite inferior.

## Resultado

**Provas completas** (enumeração exaustiva terminada sem nenhuma matriz; todas as
partes da divisão terminaram; reproduzíveis com [proofs.sh](proofs.sh)):

| célula | prova | antes (UB_lit) | custo | consequência |
|---|---|---|---|---|
| z(13,19) | ≤ 121 (T=122) | 122 | 3,2 CPU-h | intervalo passa a [120, 121] |
| z(13,20) | ≤ 127, ≤ 126, ≤ 125 (T=128, 127, 126) | 128 | 0,66 + 0,76 + 1,33 CPU-h | **z(13,20) = 125** (matriz com 125 já em `results/Z_13_20.txt`) |

Por densidade (remover a coluna mais vazia), z(13,21) ≤ ⌊125·21/20⌋ = 131, e a
matriz de `results/Z_13_21.txt` tem 131: **z(13,21) = 131**. Propagando os dois
limites novos pela densidade (linhas e colunas, [derive.py](derive.py)):

| m,n | UB_lit | UB novo | LB | |
|---|---|---|---|---|
| 13,19 | 122 | 121 | 120 | aberto |
| 13,20 | 128 | 125 | 125 | **fechado** |
| 13,21 | 134 | 131 | 131 | **fechado** |
| 14,20 | 136 | 134 | 131 | aberto |
| 14,21 | 142 | 140 | 136 | aberto |
| 14,22 | 147 | 146 | 142 | aberto |
| 14,23 | 153 | 152 | 146 | aberto |
| 15,20 | 145 | 143 | 139 | aberto |
| 15,21 | 152 | 150 | 144 | aberto |
| 15,22 | 157 | 156 | 150 | aberto |
| 15,23 | 163 | 162 | 156 | aberto |
| 16,20 | 154 | 152 | 147 | aberto |
| 16,21 | 161 | 159 | 152 | aberto |
| 16,22 | 167 | 166 | 158 | aberto |
| 16,23 | 173 | 172 | 163 | aberto |

As provas dependem dos limites Z[j] usados na poda (tabela abaixo): j ≤ 9
calculados aqui, j = 10..12 valores exatos da literatura. Nenhuma matriz melhor que
o `nosso` apareceu (todas as rodadas de prova terminaram vazias), então não há
pasta `found/`.

**Enumerações parciais** (não são provas; retomáveis, pois `run_chunks.sh` pula os
pedaços já terminados):

| alvo | pedaços terminados (todos sem matriz) | CPU-h gastas | falta (estimativa) | se terminar |
|---|---|---|---|---|
| z(13,19), T=121 (`runs/C_13_19_T121`, W=240, S=4) | 93 / 240 | 19,9 | ≈ 31 (média 770 s por pedaço) | z(13,19) = 120 (fecha) e z(14,19) ≤ 129 |
| z(14,20), T=134 (`runs/F_14_20_T134`, W=120, S=4, Z[13]=125) | 9 / 120 | 3,2 | ≈ 40 (média 1290 s por pedaço) | z(14,20) ≤ 133 |

Os pedaços são uma partição dos nós do nível 4 por índice mod W. Os pedaços
terminados cobrem 93/240 e 9/120 desses nós, que não são amostras uniformes da
árvore, então isso não diz nada probabilístico sobre o resto. Para retomar (com P
processos):

```bash
docker run -d --name orderly_C121 -v "${PWD}:/work" zaran-orderly bash /work/approaches/orderly/run_chunks.sh C_13_19_T121 P 240 4 19 13 121 19,38,40,46,57,64,72,81,89,98,106,114,999
docker run -d --name orderly_F134 -v "${PWD}:/work" zaran-orderly bash /work/approaches/orderly/run_chunks.sh F_14_20_T134 P 120 4 20 14 134 20,40,42,48,60,66,75,84,93,102,111,120,125,999
```

(Se uma rodada for morta no meio, apague `runs/NOME/lock_*` e `*.tmp` antes de
retomar.) A prova completa vale quando todos os W logs `c*.log` têm `final (...): 0`
e o mesmo número de nós no nível 4.

## Método

Arquivos: [orderly.c](orderly.c) (busca, C + nauty), [Dockerfile](Dockerfile)
(imagem `zaran-orderly` = `zaran` + `libnauty-dev`), [build.sh](build.sh),
[run_chunks.sh](run_chunks.sh) (rodada dividida em pedaços, retomável),
[zcalc.sh](zcalc.sh) (z(j,N) pequenos), [brute.c](brute.c) + [validate.sh](validate.sh)
(validação), `runs/` (logs de todas as rodadas).

**Caminho canônico (estilo McKay / "backwards path" de Collins et al.).** Toda
matriz X F×N com ≥ T uns se reduz à matriz vazia removendo, a cada passo, uma linha
de grau mínimo. Lido ao contrário: as linhas entram em ordem de grau não crescente,
e o prefixo X_k (k linhas) é "a matriz sem as F−k linhas mais vazias". A busca
constrói esses prefixos linha a linha:

* **Filhos.** De um nó M (k linhas, última de grau d) saem as linhas r com
  grau ≤ d que não criam 3×3 (para todo par de linhas i,j de M,
  |r ∩ R_i ∩ R_j| ≤ 2). A enumeração usa uma máscara de colunas proibidas (quando r
  já tem 2 colunas do conjunto comum de um par, as outras desse conjunto ficam
  proibidas) e, entre colunas gêmeas de M (colunas iguais), só prefixos.
* **Rejeição de isomorfos (canonical augmentation).** A linha "canônica" de uma
  matriz é escolhida entre as de grau mínimo: primeiro pela maior chave invariante
  (Σ s², Σ s³ das interseções s com as outras linhas), depois pelo rotulamento
  canônico do nauty (grafo bipartido linhas/colunas, partição por grau). O filho
  M+r é aceito sse r está na órbita, em Aut(M+r), da linha canônica; quando r é a
  única linha de chave máxima, o nauty nem é chamado. Irmãos isomorfos aceitos são
  exatamente os r de uma mesma órbita de Aut(M): mantém-se só o r de máscara
  mínima na órbita (geradores de Aut(M) pelo nauty; se todas as linhas de M têm
  (grau, chave) distintos, Aut(M) só troca colunas gêmeas, o que o prefixo já
  resolve; se |Aut(M)| > 2000, deduplica pela forma canônica). Com isso cada classe
  de isomorfismo aparece uma vez em cada nível.
* **Podas** (todas são condições necessárias para que o nó tenha descendente com
  ≥ T uns, logo não perdem nada):
  * B1: com e = uns do prefixo e d = grau da última linha, as F−k linhas que
    faltam têm grau ≤ d; para todo j ≥ k, e_j ≤ min(Z[j], e + (j−k)d) e as linhas
    depois do nível j têm grau ≤ ⌊e_j/j⌋; exige-se e_j + (F−j)·min(d,⌊e_j/j⌋) ≥ T.
    Aqui Z[j] é um limite superior **válido** de z(j,N) (ver abaixo).
  * B2: Σ_c C(c_c,3) ≤ 2·C(F,3) no final (cada tripla de linhas cabe em ≤ 2
    colunas); o máximo de uns ainda adicionáveis sob esse orçamento é calculado
    pelo guloso de custo marginal C(c,2) (ótimo, custo convexo) e tem de ser ≥ T−e.
  * grau mínimo da próxima linha ⌈(T−e)/(F−k)⌉.
* **Último nível** (modo prova): basta existir uma linha válida com grau ≥ T−e;
  não precisa de nauty.
* **Paralelismo.** `-s S W I`: no nível S os nós são numerados na ordem (determinística)
  da busca e o processo I só desce nos de índice ≡ I (mod W). Em todas as rodadas
  conferimos que todos os pedaços veem o mesmo número de nós no nível S.

Uso: `orderly N F T Z1,...,ZF [-c] [-s S W I] [-o arq] [-x] [-e K seed]`
(N = comprimento das linhas, F = número de linhas, `-c` conta classes no nível F,
`-x` para na primeira matriz, `-e` estimativa de Knuth). Exemplo de rodada:

```bash
docker build -t zaran-orderly approaches/orderly
docker run --rm -v "${PWD}:/work" zaran-orderly bash /work/approaches/orderly/build.sh
docker run --rm -v "${PWD}:/work" zaran-orderly bash /work/approaches/orderly/run_chunks.sh C_13_19_T122 6 60 4 19 13 122 19,38,40,46,57,64,72,81,89,98,106,114,999
```

### Limites Z[j] usados nas podas

Z[F] nunca é usado como hipótese (passamos 999). Para j < F:

| N | j = 1..9 (calculados aqui com `zcalc.sh`) | j ≥ 10 (literatura, `literature.csv`) |
|---|---|---|
| 16 | 16,32,34,40,49,56,63,70,77 | 85,92,99,107,115,123,128 |
| 17 | 17,34,36,42,52,58,66,74,81 | 90,96,103,110,118,126 |
| 19 | 19,38,40,46,57,64,72,81,89 | 98,106,114 (+ z(13,19) ≤ 121, provado aqui) |
| 20 | 20,40,42,48,60,66,75,84,93 | 102,111,120 |
| 21 | 21,42,44,50,62,69,78,87,96 | 106,116,126 |

Os valores j ≤ 9 foram obtidos pelo próprio programa (achar matriz com T, provar
que não há com T+1, subindo em j); os de j = 8, 9 coincidem com a literatura. Os
de j ≥ 10 são valores exatos já fechados na literatura (`status` "já fechado"), e
as provas abaixo dependem deles (qualquer limite superior válido serve).

## Validação

1. **Contagem rotulada contra força bruta** ([validate.sh](validate.sh)): para cada
   caso, Σ F!·N!/|Aut| sobre as classes enumeradas (|Aut| pelo nauty) deve ser
   igual ao número de matrizes rotuladas contadas por [brute.c](brute.c) (sem
   simetria nenhuma). Isso testa ao mesmo tempo completude e ausência de
   duplicatas. Bateu exatamente nos 8 casos rodados:

   | N×F, T | classes | rotuladas (ambos) |
   |---|---|---|
   | 5×4, ≥14 | 30 | 26760 |
   | 6×4, ≥15 | 230 | 1419840 |
   | 6×5, ≥18 | 1406 | 68903910 |
   | 5×5, ≥17 | 60 | 374220 |
   | 6×5, ≥20 | 110 | 4508910 |
   | 6×6, ≥24 | 96 | 26302590 |
   | 6×6, ≥25 | 9 | 1747440 |
   | 7×5, ≥21 | 2801 | 990413550 |

   (7×6, ≥26: 2683 classes, 7480844910 rotuladas; a força bruta não terminou em 10 min.)
   Depois de cada otimização ([quickval.sh](quickval.sh)) as contagens de classes e
   rotuladas continuaram idênticas.
2. **Valores conhecidos.** z(8,9) = 45 (4 classes extremais), z(10,11) = 64 (1
   classe); z(j,N) para j = 8, 9 e N = 16, 17, 18, 19, 20, 21 iguais à literatura.
3. **Limites da literatura reproduzidos como provas**, com Z[F] = 999:
   z(11,17) ≤ 96 (9 s), z(11,19) ≤ 106 (7 s), z(12,17) ≤ 103 (Collins et al., 7 s).

## Estimativas por alvo e escolha

Primeiro tentei a estimativa de Knuth (`-e`, 2000 caminhos aleatórios). Ela
**subestimou muito**: para (13,19) T=121 previa ~5·10⁸ nós (~2 CPU-h), e a medição
direta deu ~110 CPU-h com a versão inicial. A árvore tem cauda pesada (poucas
sub-árvores enormes), e os caminhos aleatórios quase nunca passam por elas. Daí em
diante estimei rodando pedaços `-s 4 W I` de 1/1200 ou 1/2000 da árvore com I
aleatório (custo total ≈ média × W). Isso também subestima quando a amostra é
pequena: (14,20) T=134 dava ~6 CPU-h com 6 amostras, mas os pedaços reais de
1/120 levam ~1290 s (≈ 43 CPU-h). Custos em CPU-h de um núcleo, com a versão final:

| alvo (linhas×colunas da busca) | T | estimativa | medido |
|---|---|---|---|
| (13,19): 13 linhas de 19 | 122 | – | 3,2 (prova completa) |
| (13,19) | 121 (fecharia em 120) | ≈ 39 (6 amostras 1/1200: 26–358 s) | ≈ 51 (93/240 pedaços, média 770 s); parcial |
| (13,20): 13 linhas de 20 | 128 / 127 / 126 | ≈ 0,7 / 1,0 | 0,66 / 0,76 / 1,33 (provas completas) |
| (13,21): 13 linhas de 21 | 134 | ≈ 2 | ≥ 2,8 (45/60 pedaços); interrompida, ficou redundante com z(13,20)=125 |
| (14,20): 14 linhas de 20, Z[13]=125 | 136, 135 | 0 (cortada na raiz = limite de densidade 134) | – |
| (14,20) | 134 | ≈ 6 (amostras) | ≈ 43 (9/120 pedaços, média 1290 s); parcial |
| (14,20) | 133 | 4 de 6 amostras de 1/2000 passaram de 400 s | ≫ 100 |
| (14,19): 14 linhas de 19, Z[13]=121 | 130 | amostras de 1/2000: 13 s, 65 s, > 400 s | ≫ 100 |
| (16,17): 16 linhas de 17 | 133 (fecharia em 132) | amostras de 1/2000: 1, 13, 391 s | ≈ 90+ |
| (16,17) transposta: 17 linhas de 16 | 133 | 6 amostras: 0,2–192 s, média 48 s | ≈ 27+ (cauda pesada; provavelmente bem mais) |

O caminho sugerido "a partir de 15×17 com ≥ 125 uns" é o mesmo que a busca F=16
já faz: o prefixo de 15 linhas é exatamente essa matriz quase extremal, e as podas
B1 exigem e_15 ≥ 125 e d ≥ 8. A dificuldade está nos níveis do meio (7 a 9
linhas), onde há ~10⁹ a 10¹⁰ prefixos que ainda passam nas podas e morrem dois ou
três níveis depois.

Escolha: (13,19) T=122 e a sequência (13,20) T=128 → 126 eram baratas e deram
resultados novos; (13,19) T=121, (16,17) T=133 e (14,19) T=130 não cabiam nas ~35
CPU-h que restavam. Com o orçamento restante rodei (14,20) T=134 e depois (13,19) T=121 como enumerações parciais retomáveis. (13,23) T=143 e T=142 também passam de 150 CPU-h (3 de 6 amostras de 1/2000 passaram de 300 s).

### O que não funcionou (registrado para não repetir)

* Lookahead (calcular, antes do nauty, o maior grau de uma linha ainda possível no
  filho e refazer a poda B1): corta 2,7× os nós, mas fica mais lento no total.
* Modo "cru" nos níveis profundos (sem nauty, linhas em ordem lexicográfica): as
  duplicatas explodem (de 2× a 20× mais nós), mais lento.
* O que funcionou: máscara de colunas proibidas no gerador de linhas, um nauty por
  nó (Aut do pai) em vez de um por filho, chave invariante para decidir a aceitação
  sem nauty e o atalho "linhas com chaves distintas ⇒ Aut só troca gêmeas": juntos,
  ~2× no caso de referência z(12,17) ≤ 103 (13,6 s → 7,2 s).
