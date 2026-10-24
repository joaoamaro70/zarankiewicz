# New bounds and three exact values for the Zarankiewicz numbers z(m,n;3,3)

Explicit K_{3,3}-free binary matrices that improve the best known lower bounds for
18 Zarankiewicz numbers z(m,n;3,3) with 13 ≤ m ≤ 16 and 18 ≤ n ≤ 23, together with
the search code and an independent verifier. Applying the density lemma of Collins et al.
to known exact values also improves 22 upper bounds and settles three cells:
z(10,21) = 106, z(11,19) = 106 and z(11,20) = 111.

| (m,n) | previous best | new | upper bound |
|---|---|---|---|
| (13,19) | 119 | 120 | 122 |
| (13,23) | 139 | 140 | 143 |
| (14,19) | 126 | 128 | 130 |
| (14,20) | 129 | 131 | 136 |
| (14,21) | 133 | 136 | 142 |
| (14,22) | 139 | 142 | 147 |
| (14,23) | 141 | 146 | 153 |
| (15,19) | 134 | 136 | 139 |
| (15,20) | 138 | 139 | 145 |
| (15,21) | 140 | 144 | 152 |
| (15,22) | 143 | 150 | 157 |
| (15,23) | 149 | 156 | 163 |
| (16,18) | 136 | 137 | 140 |
| (16,19) | 139 | 142 | 147 |
| (16,20) | 146 | 147 | 154 |
| (16,21) | 148 | 152 | 161 |
| (16,22) | 152 | 158 | 167 |
| (16,23) | 158 | 163 | 173 |

"Previous best" is the largest lower bound found in the literature up to October 2026
(see `literature.py` and the note in `paper/`), closed under the elementary
add/remove-a-row-or-column bounds. Upper bounds are the published ones closed under the
same rules in the other direction; `literature.csv` lists the source of every bound.

## Verify

Each matrix is in `results/Z_m_n.txt` (one row per line). The checker is plain Python
and shares no code with the search:

```bash
python3 verify.py results/Z_*.txt
```

It tests every triple of rows and, independently, every triple of columns.

## Contents

| File | What it is |
|---|---|
| `results/` | best matrices for every cell 8 ≤ m ≤ 16, 16 ≤ n ≤ 23 |
| `verify.py` | independent verifier |
| `zaran2.c` | search (rip-up and repair, simulated annealing, neighbour seeding, cyclic orbits; C + OpenMP) |
| `zaran.c` | original prototype, kept as a baseline |
| `table.py`, `bars.py` | bounds from Figure 2 of arXiv:2605.01120 and the elementary bar |
| `literature.py` | consolidated literature bounds and comparison |
| `sat/` | CNF encoding (Kissat) and its self-test |
| `paper/` | LaTeX note; `paper/build.sh` regenerates tables from `results/` |
| `Dockerfile`, `run.sh`, `pipeline.sh`, `longrun.sh` | container and run scripts |

## Reproduce

```bash
docker build -t zaran .
docker run --rm -v "$PWD:/work" zaran ./run.sh ./zaran2 -t 1 -d results
```

The program compiles inside the container with `-march=native` and resumes from `results/`.
