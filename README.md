# Improved bounds and two exact values for the Zarankiewicz numbers z(m,n;3,3)

The Zarankiewicz number z(m,n;3,3) is the maximum number of ones in an m×n binary
matrix with no 3×3 all-ones submatrix. This repository contains:

- explicit matrices that improve the best known **lower bounds** for 18 of these
  numbers, with 13 ≤ m ≤ 16 and 18 ≤ n ≤ 23, by up to 7;
- improved **upper bounds** in 19 cells and two new exact values,
  **z(13,20) = 125** and **z(13,21) = 131**, from three methods: the density lemma of
  Collins et al. applied to known exact values, the elimination of column-degree
  profiles by linear programming with exactly checked Farkas certificates
  (`approaches/lp_profiles/`), and an exhaustive orderly generation
  (`approaches/orderly/`). The density argument also gives z(10,21) = 106,
  z(11,19) = 106 and z(11,20) = 111, but these three values had already been
  obtained in
  [dfield/finite-zarankiewicz-closures](https://github.com/dfield/finite-zarankiewicz-closures);
- the search code, an independent verifier, the consolidated bounds from the
  literature with their sources, and the LaTeX note describing everything.

**Paper:** [paper/main.pdf](paper/main.pdf)

## Results

![Bounds for z(m,n;3,3)](paper/figures/bounds.png)

Beige cells are values known exactly. In the other
cells the top number is the best known upper bound, the bottom number the best lower
bound, and the colour the gap between them; "a → **b**" marks an improvement from the
previous best bound a to b.

| (m,n) | previous lower bound | new lower bound | upper bound |
|---|---|---|---|
| (13,19) | 119 | 120 | 121 |
| (13,23) | 139 | 140 | 142 |
| (14,19) | 126 | 128 | 130 |
| (14,20) | 129 | 131 | 134 |
| (14,21) | 133 | 136 | 140 |
| (14,22) | 139 | 142 | 146 |
| (14,23) | 141 | 146 | 152 |
| (15,19) | 134 | 136 | 139 |
| (15,20) | 138 | 139 | 143 |
| (15,21) | 140 | 144 | 150 |
| (15,22) | 143 | 150 | 156 |
| (15,23) | 149 | 156 | 161 |
| (16,18) | 136 | 137 | 140 |
| (16,19) | 139 | 142 | 147 |
| (16,20) | 146 | 147 | 152 |
| (16,21) | 148 | 152 | 159 |
| (16,22) | 152 | 158 | 165 |
| (16,23) | 158 | 163 | 171 |

The source of every bound is listed in `literature.csv` and in Table 1 of the note.
Some upper bounds, including the two new exact values, depend on computer-assisted
proofs that are not yet peer reviewed (arXiv:2608.08154, arXiv:2608.08549, and the
dfield repository above); they are marked in the note. The linear-programming bounds
use no outside values.

## The matrices

The 18 matrices with improved lower bounds (black = 1, white = 0):

![The 18 matrices](paper/figures/matrices.png)

## Verify the matrices

Each matrix is in `results/Z_m_n.txt`, one row per line. The checker is plain Python
and shares no code with the search:

```bash
python3 verify.py results/Z_*.txt
```

It tests every triple of rows and, independently, every triple of columns.

## Found a better matrix?

If you find a matrix that beats any lower bound here, or a better upper bound, please
share it. Open an [issue](https://github.com/joaoamaro70/zarankiewicz/issues) or a pull
request with the matrix in the same format as `results/Z_m_n.txt` (one row per line,
`0`/`1`), after checking it with `python3 verify.py your_file.txt`. New results from the
literature that are missing here are just as welcome. Every confirmed improvement will
be added to the tables with credit to its author.

## Layout

| Path | Contents |
|---|---|
| `results/` | best matrices found for every cell 8 ≤ m ≤ 16, 16 ≤ n ≤ 23 |
| `verify.py` | independent verifier |
| `search/` | the local search (C + OpenMP) and a script to build and run it |
| `literature.py` | bounds from the literature (with sources), closed under the elementary rules; writes `literature.csv` for all 72 cells |
| `approaches/` | five further approaches run in parallel, each with its own README: `lp_profiles/` (upper bounds by LP with exact certificates, and their checker), `orderly/` (exhaustive orderly generation with nauty), and three lower-bound searches that found no improvement (`sym_sat/`, `lns_sat/`, `tabu/`) |
| `sat/` | SAT encodings (Kissat) and their self-tests; also an attempted independent per-profile check of z(13,22) ≤ 137, which did not finish (see below) |
| `paper/` | the LaTeX note; `paper/build.sh` regenerates its tables, figures and the README images from `results/` |
| `Dockerfile` | Ubuntu 24.04 with gcc, Python, TeX Live and Kissat |

## Reproduce

```bash
docker build -t zaran .
docker run --rm -v "$PWD:/work" zaran bash search/run.sh -t 1     # 1 hour of search
docker run --rm -v "$PWD:/work" zaran ./paper/build.sh            # rebuild the note
```

The search compiles inside the container with `-march=native`, resumes from
`results/`, and saves every improvement there.

## Attempted check of z(13,22) ≤ 137

Some of the new upper bounds depend on values from a computer-assisted proof in a
preprint (arXiv:2608.08154): z(13,22) = 137, and z(12,19) ≤ 114 and z(12,20) ≤ 120,
which the orderly generation uses for pruning. We tried to check z(13,22) ≤ 137
independently. A counting argument (`sat/afr_step1.py`) leaves 83 column-degree profiles
for a 13×22 matrix with 138 ones, as stated in the preprint. We then asked Kissat, profile
by profile, whether a valid matrix exists (`sat/profile_sat.py`, rows in lexicographic
order, columns sorted by degree). The method is correct on small known cases
(`sat/profile_test.sh`, e.g. z(10,11) = 64), but at 13×22 each of the 30 profiles that
ran for the full 2-hour limit timed out, including a control profile that is known to be
satisfiable; we then stopped the remaining runs. A stronger encoding would be needed.
