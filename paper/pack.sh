#!/bin/bash
# Monta paper/arxiv.tar.gz para submissao (rodar no container depois de build.sh).
# O arXiv trata a pasta anc/ do pacote como "ancillary files".
set -e
cd /work/paper
if grep -q "AUTHOR NAME\|TODO(autor)" main.tex; then
  echo "AVISO: preencha autor, cidade e e-mail em main.tex antes de submeter"
fi
rm -f arxiv.tar.gz
tar czf arxiv.tar.gz main.tex main.bbl refs.bib gen anc
tar tzf arxiv.tar.gz
