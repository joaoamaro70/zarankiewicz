# The note

Build (from the repository root):

```bash
docker run --rm -v "$PWD:/work" zaran ./paper/build.sh
```

`build.sh` runs `literature.py` and `make_tables.py`, which regenerate the table, the
figure, the drawn matrices (`gen/`) and the ancillary files (`anc/`) from `results/`,
and then compiles `main.pdf`.

To prepare the arXiv upload:

```bash
docker run --rm -v "$PWD:/work" zaran bash -c "bash paper/pack.sh && bash paper/testpack.sh"
```

`pack.sh` writes `arxiv.tar.gz`; arXiv treats its `anc/` folder (the matrices and the
verifier) as ancillary files. `testpack.sh` unpacks it in a clean folder and compiles it.
