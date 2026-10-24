# Nota: Improved lower bounds for z(m,n;3,3)

Compilar e empacotar (no container, da raiz do projeto):

```bash
docker run --rm -v "${PWD}:/work" zaran bash -c "./paper/build.sh && bash paper/pack.sh"
```

`build.sh` roda `literature.py` e `make_tables.py` (tabelas, macros, apêndice e `anc/`
a partir de `results/`) e compila `main.pdf`. `pack.sh` gera `arxiv.tar.gz`.

## Estado (2026-10-18)

- [x] Resultados finais: 18 casos acima da literatura, todos verificados.
- [x] Horas de execução, frase da semeadura e tentativa de SAT atualizadas no texto.
- [x] Última busca no arXiv (nada sobre z(m,n;3,3) depois de ago/2026).
- [x] Referências conferidas.
- [x] Autor, cidade e e-mail em `main.tex`.
- [ ] Leitura final pelo autor (e, de preferência, por um ex-professor).

## Submissão ao arXiv

Subir `arxiv.tar.gz` (o arXiv trata `anc/` como ancillary files). Categoria: math.CO.
