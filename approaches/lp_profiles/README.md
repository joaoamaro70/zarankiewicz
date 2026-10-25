# Abordagem 4: eliminação de perfis de grau por programação linear com certificado

Objetivo: limites superiores para z(m,n;3,3). Para mostrar z(m,n) ≤ k−1 basta mostrar que
nenhuma matriz m×n sem K₃,₃ tem exatamente k uns (de uma com mais uns apagam-se uns até
sobrarem k, sem criar K₃,₃). Enumeram-se os perfis de grau de coluna possíveis com k uns e
elimina-se cada um com um sistema linear inviável, certificado por um vetor de Farkas
inteiro conferido em aritmética exata.

## Modelo

Colunas = blocos E_j ⊆ [m], d_j = |E_j|. Sem K₃,₃ ⇔ cada tripla de linhas T está em
λ_T ≤ 2 blocos.

**Perfis.** Multiconjuntos (d_1..d_n) com Σd_j = k e Σ C(d_j,3) ≤ 2·C(m,3) (contagem de
pares tripla–bloco). Mesma enumeração de `sat/profile_sat.py`; o verificador reenumera por
outro caminho e exige a mesma lista.

**Caso.** Fixam-se s blocos F_0..F_{s−1} (s = 1, 2, 3, ...) pela sua configuração de Venn:
para cada máscara a, sz[a] = número de linhas que estão exatamente nos F_i com bit i em a.
Os n−s blocos restantes ("livres") são agrupados por tipo b = (|B ∩ região a|)_a, e
y_b ≥ 0 inteiro é o número de blocos livres do tipo b. Restrições, todas somas de
restrições válidas de qualquer matriz com esse perfil e essa configuração:

* (T_t) para cada tipo de tripla t = (t_a), Σt_a = 3 (quantas linhas da tripla em cada
  região), somando λ_T ≤ 2 sobre as N_t = Π C(sz_a, t_a) triplas do tipo:
  `Σ_b y_b · Π_a C(b_a, t_a) ≤ (2 − f_t) · N_t`, f_t = nº de blocos fixos que contêm as
  triplas do tipo t (se f_t ≥ 3 a configuração é impossível);
* (S_d) `Σ_{|b|=d} y_b = n_d − #{fixos de grau d}`;
* (X) regras de exclusão vindas de escolhas extremais (abaixo): certos tipos b têm y_b = 0.

Com s = 1 isso é exatamente o "block polytope" de Afrasyab (arXiv 2608.08154, §3)
simetrizado: as restrições por linha e por par dele são somas de restrições de triplas, e a
média sobre o estabilizador de F mostra que o LP completo é viável ⇔ o agregado é viável.
As restrições de par-déficit de dfield (D_P ≥ 0) também são somas de (T_t).

**Estratégias (divisões em casos).** Um perfil é eliminado se todos os casos de uma
estratégia são inviáveis:

* `L0 f`: fixa um bloco qualquer de grau f (1 caso).
* `L1 f g maxG|minG`: F de grau f qualquer, G = bloco de grau g (≠F) com |G∩F| máximo
  (mínimo) = i; ramifica em todos os i possíveis; os demais blocos de grau g têm
  |B∩F| ≤ i (≥ i).
* `L1 f f maxpair|minpair`: (F,G) = par de blocos de grau f com |F∩G| máximo (mínimo) = i;
  os demais blocos de grau f têm |B∩F|, |B∩G| ≤ i (≥ i).
* refinamento (`split`, nível 3): um caso que falha é dividido fixando mais um bloco livre H
  de grau h que maximiza/minimiza |H ∩ U| (U = união de regiões), um filho por tipo
  possível de H, com a nova regra para os demais blocos livres de grau h.
* refinamento por linha (`rowsplit`, nível 3): a linha de grau máximo (≥ ⌈k/m⌉) ou mínimo
  (≤ ⌊k/m⌋) fica numa região própria; ramifica na região e no grau v; acrescenta a
  igualdade do grau dessa linha e "cada região R tem ≤ |R|·v incidências" (ou ≥).

**Certificados.** Para um caso, um vetor α ≥ 0 inteiro (um por tipo de tripla) e
β_d = max_b(−Σ_t α_t c_t(b)) (calculado exatamente, deixa toda coluna dual ≥ 0) com
Σ α_t cap_t + Σ β_d e_d < 0 prova a inviabilidade:
0 ≤ Σ_b y_b(Aᵀα + Eᵀβ)_b ≤ αᵀcap + βᵀe < 0. Nível 2 usa a integralidade de y: árvore de
branch-and-bound (y_b ≤ v | y_b ≥ v+1) com um certificado de Farkas (com multiplicadores
dos limites) em cada folha.

Os α vêm do HiGHS (scipy) em ponto flutuante, são racionalizados e escalados para inteiros;
o solver nunca é usado como prova.

**Formato dos certificados** (`certificates/*/z{m}_{n}_k{k}.json`): `m, n, k`, e em
`results` um item por perfil: `profile` (grau → quantidade), `strategy` (ex.
`["L1", 7, 7, "maxpair"]`, ou `null` se o perfil sobreviveu) e `cases`, um nó de prova por
caso da estratégia. Nó: `case` (`s` blocos fixos, `sz` tamanhos das regiões, `rm` máscaras,
`excl` regras, `rows` linha fixada) e `kind`: `farkas` (`T` rótulos das linhas, `alpha`
inteiros), `bnb` (`tree` com `var`/`v`/`le`/`ge` e folhas `alpha`/`up`/`lo`), `split`
(`h`, `U`, `op`, `children`), `rowsplit` (`op`, `children`) ou `invalid_config`.
β_d não é guardado: o verificador o recalcula.

## Arquivos

| arquivo | papel |
|---|---|
| `Dockerfile` | imagem `zaran-lp` = `zaran` + python3-scipy |
| `model.py` | sistema agregado de um caso |
| `lp.py`, `bnb.py`, `refine.py` | busca de certificados (LP, B&B, refinamento) |
| `search.py m n k --level L --out DIR [--reuse JSON]` | enumera perfis e tenta eliminar cada um |
| `check_cert.py` | **verificador independente**: não importa nada acima, não usa solver; int/`Fraction` |
| `sanity.py` | teste de sanidade com as 72 matrizes de `results/` |
| `descend.sh` | desce k a partir do UB enquanto tudo é eliminado |
| `organize.py`, `summarize.py` | juntam os resultados em `certificates/` e fazem tabelas |
| `certificates/proofs/` | um JSON por prova (todos os perfis eliminados) |
| `certificates/partial/` | o melhor resultado na fronteira de cada célula |
| `work/l1`, `certs2..4`, `logs*` | resultados brutos dos níveis 1, 2, 3 (v1) e 3 (v2) |

Rodar (no PowerShell, pasta do repositório):

```
docker build -t zaran-lp approaches/lp_profiles
docker run --rm -v "${PWD}:/work" zaran-lp bash -c "cd /work/approaches/lp_profiles && python3 check_cert.py certificates/proofs/*.json"
```

## Validação

* **Sanidade**: para cada uma das 72 matrizes de `results/`, o perfil de colunas real nunca é
  eliminado (níveis 1 e 2), e o vetor y da própria matriz satisfaz o sistema de casos
  concretos (L0 com cada coluna; L1 maxpair/minpair no grau mais frequente). 0 falhas
  (`sanity.log`, `sanity2.log`). Para o v2 (regiões com máscara explícita, linha fixada,
  três blocos fixos), `sanity2.py`: casos com a coluna j fixa e a linha de grau máximo ou
  mínimo, par extremal + linha, e três blocos + linha, todos satisfeitos pela matriz real
  (`sanity2_v2.log`, 72/72).
* **z(10,22) ≤ 110** (dfield): k=111 tem 4 perfis; todos eliminados (2 por L0, 2 por
  L1 minpair), certificado verificado. Aqui o LP substitui os argumentos de resíduo da prova
  em Lean.
* **z(13,22) ≤ 137** (Afrasyab): k=138 tem 83 perfis (igual ao artigo). Só com L0 (que é o LP
  do artigo) eliminamos exatamente **77**, como no artigo; com L1 eliminamos 80. Sobram
  6¹⁶7⁶, 5¹6¹⁴7⁷, 5²6¹²7⁸ (três dos seis que o artigo trata à mão). Não reproduz a prova
  completa.

## Resultados nas células abertas

Para cada uma das 21 células abertas, começamos em k = UB atual e descemos k enquanto
todos os perfis eram eliminados (nível 1: LP; nível 2: + B&B inteiro; nível 3: +
refinamento por um terceiro bloco extremal ou pela linha de grau máximo/mínimo, só nos
sobreviventes). "UB novo" = k−1 para o menor k com todos os perfis eliminados.
"Fronteira" = o k seguinte (k−1, ou o UB se nada caiu), com quantos perfis sobraram.

| célula | LB | UB antigo | UB novo (provado) | nível da prova (nº de perfis em k = UB novo + 1) | fronteira k | perfis | eliminados | sobram |
|---|---|---|---|---|---|---|---|---|
| (13,19) | 120 | 122 | — | | 122 | 413 | 391 | 22 |
| (13,20) | 125 | 128 | — | | 128 | 159 | 156 | 3 |
| (13,21) | 131 | 134 | **133** | 1 (43 perfis) | 133 | 117 | 115 | 2 |
| (13,23) | 140 | 143 | **142** | 2 (54) | 142 | 143 | 138 | 5 |
| (14,19) | 128 | 130 | — | | 130 | 979 | 938 | 41 |
| (14,20) | 131 | 136 | — | | 136 | 531 | 511 | 20 |
| (14,21) | 136 | 142 | — | | 142 | 251 | 250 | 1 |
| (14,22) | 142 | 147 | — | | 147 | 239 | 238 | 1 |
| (14,23) | 146 | 153 | **152** | 2 (85) | 152 | 212 | 211 | 1 |
| (15,19) | 136 | 139 | — | | 139 | 1241 | 1219 | 22 |
| (15,20) | 139 | 145 | — | | 145 | 823 | 811 | 12 |
| (15,21) | 144 | 152 | **151** | 2 (215) | 151 | 490 | 487 | 3 |
| (15,22) | 150 | 157 | **156** | 2 (263) | 156 | 584 | 571 | 13 |
| (15,23) | 156 | 163 | **161** | 3 (305) | 161 | 663 | 651 | 12 |
| (16,17) | 132 | 133 | — | | 133 | 8932 | 8875 | 57 |
| (16,18) | 137 | 140 | — | | 140 | 5410 | 5379 | 31 |
| (16,19) | 142 | 147 | — | | 147 | 2837 | 2822 | 15 |
| (16,20) | 147 | 154 | — | | 154 | 1262 | 1260 | 2 |
| (16,21) | 152 | 161 | **160** | 1 (442) | 160 | 966 | 965 | 1 |
| (16,22) | 158 | 167 | **165** | 3 (686) | 165 | 1402 | 1395 | 7 |
| (16,23) | 163 | 173 | **171** | 2 (440) | 171 | 961 | 959 | 2 |

LB = max(literatura, nosso) e UB antigo = `UB_lit` de `literature.csv` (não procurei se
alguém já publicou limites melhores que esses depois). Em (15,23),
(16,22) e (16,23) caíram dois valores de k (por exemplo, (16,22): k=167 no nível 1 e
k=166 no nível 3). O nível usado na fronteira é o maior tentado ali (3 onde há "split"
na tabela de `summary.out`, senão 2). O refinamento por linha extremal (`rowsplit`) está
implementado e conferido pelo verificador, mas nenhuma eliminação final precisou dele.

### O que é prova e o que é indício

* **Prova verificada** (certificados em `certificates/proofs/`, todos reconferidos por
  `check_cert.py`, que reconstrói cada sistema a partir do perfil e do caso, regenera as
  divisões em casos e reenumera os perfis, em aritmética exata sem solver):
  **z(13,21) ≤ 133, z(13,23) ≤ 142, z(14,23) ≤ 152, z(15,21) ≤ 151, z(15,22) ≤ 156,
  z(15,23) ≤ 161, z(16,21) ≤ 160, z(16,22) ≤ 165, z(16,23) ≤ 171**, além da reprodução
  de z(10,22) ≤ 110. Resultado do verificador: `final_A.log` a `final_C.log` (os parciais
  das células m ≤ 14 e de várias m = 15, 16 também foram reconferidos: `final_D.log`).
  O argumento depende só de: (i) a enumeração de perfis (condição necessária
  Σ C(d_j,3) ≤ 2C(m,3)); (ii) a validade das restrições agregadas (somas de λ_T ≤ 2) e
  das escolhas extremais; (iii) o lema de Farkas. Não houve revisão humana do código do
  verificador além da minha; os testes de sanidade (as 72 matrizes conhecidas satisfazem
  todos os sistemas dos seus casos e nunca são eliminadas) são a principal checagem de
  que nenhuma restrição é forte demais.
* **Só indício / resultado parcial**: os números de perfis restantes nas fronteiras
  (`certificates/partial/`, os perfis eliminados lá também têm certificado; os que sobram
  não estão refutados). Que um perfil sobreviva não indica que ele seja realizável: o
  modelo agregado inteiro com 2 blocos fixos tem solução para os perfis quase regulares
  (teste com `scipy.milp` em `explore_ilp.py`), então é preciso outra ideia (resíduos
  como em Afrasyab/dfield, ou SAT por perfil) para eles.
* Tentativas sem resultado: modelo de "momentos" (tipos de linha, tipos de par, distribuição
  de interseções entre blocos, inteiro) — viável até em perfis que o LP mata, descartado;
  LP na transposta — 298 mil perfis de linha para (13,21), inviável no tempo;
  refinamento a profundidade 2 em (13,21) k=133 e (13,19) k=122 — estoura o tempo;
  SAT por perfil (Kissat + `sat/profile_sat.py --pair`, `sat/run_sat.sh`) nos perfis únicos
  6⁵7¹⁶ de (14,21) k=142 e 7⁸8¹³ de (16,21) k=160 — sem resposta em 45 min cada.

### Perfis que sobram nas fronteiras pequenas

Quase todos os sobreviventes são perfis quase regulares com dois graus consecutivos
(a lista completa por célula sai de `summarize.py certificates/partial/*.json`):

* (13,21) k=133: 6¹⁴7⁷, 5¹6¹²7⁸
* (13,20) k=128: 6¹²7⁸, 5¹6¹⁰7⁹, 5²6⁸7¹⁰
* (13,22) k=138 (Afrasyab): 6¹⁶7⁶, 5¹6¹⁴7⁷, 5²6¹²7⁸
* (13,23) k=142: 6¹⁹7⁴, 5¹6¹⁷7⁵, 5²6¹⁵7⁶, 5³6¹³7⁷, 6²⁰7²8¹
* (14,21) k=142: 6⁵7¹⁶ · (14,22) k=147: 6⁷7¹⁵ · (14,23) k=152: 6⁹7¹⁴
* (15,21) k=151: 7¹⁷8⁴, 6¹7¹⁵8⁵, 6²7¹³8⁶
* (16,20) k=154: 7⁶8¹⁴, 6¹7⁴8¹⁵ · (16,21) k=160: 7⁸8¹³ · (16,23) k=171: 7¹³8¹⁰, 6¹7¹¹8¹¹

Uma única célula com 1 perfil sobrando, por exemplo (16,21) k=160 com 7⁸8¹³, (14,21)
k=142 com 6⁵7¹⁶ ou (14,23) k=152 com 6⁹7¹⁴, viraria prova nova se esse perfil fosse
refutado de outro modo (por exemplo, SAT com graus de coluna fixos, `sat/profile_sat.py`).

## Reproduzir

```
docker build -t zaran-lp approaches/lp_profiles
# sanidade
docker run --rm -v "${PWD}:/work" zaran-lp bash -c "cd /work/approaches/lp_profiles && python3 sanity.py ../../results --level 2 && python3 sanity2.py ../../results"
# busca (exemplo): nivel 1 = LP, 2 = + B&B, 3 = + refinamento
docker run --rm -v "${PWD}:/work" zaran-lp bash -c "cd /work/approaches/lp_profiles && python3 search.py 13 21 134 --level 1 --jobs 4 --out /tmp/c"
# conferir as provas
docker run --rm -v "${PWD}:/work" zaran-lp bash -c "cd /work/approaches/lp_profiles && python3 check_cert.py certificates/proofs/*.json"
```
