FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential python3 poppler-utils git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Kissat (SAT, para o M6 opcional)
RUN git clone --depth 1 https://github.com/arminbiere/kissat.git /opt/kissat \
    && cd /opt/kissat && ./configure && make -j"$(nproc)" \
    && cp build/kissat /usr/local/bin/ && rm -rf /opt/kissat
# LaTeX para a nota (paper/)
RUN apt-get update && apt-get install -y --no-install-recommends \
        texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended \
        texlive-bibtex-extra texlive-science latexmk lmodern \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
# O codigo e montado em /work; a compilacao (-march=native) acontece no run.
CMD ["bash"]
