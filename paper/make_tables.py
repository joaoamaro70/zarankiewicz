#!/usr/bin/env python3
"""Gera paper/gen/*.tex e paper/anc/ a partir de literature.csv e results/.
Rodar da raiz do projeto, depois de literature.py:  python3 paper/make_tables.py"""
import csv
import os
import re
import shutil
import sys

sys.path.insert(0, os.getcwd())
from verify import check  # noqa: E402

RES = "results"
GEN = "paper/gen"
ANC = "paper/anc"
os.makedirs(GEN, exist_ok=True)
os.makedirs(ANC, exist_ok=True)

CITE = {
    "Bhan26": r"\cite{BNRL26}",
    "Fig2/Davies26": r"\cite[Fig.~2]{BNRL26}",
    "Saurabh26": r"\cite{Sau26}",
    "Collins16": r"\cite{CRWR16}",
    "Tan22": r"\cite{Tan22}",
    "Afrasyab26": r"\cite{Afr26}",
    "Hou26": r"\cite{Hou26}",
    "Afrasyab26/Hou26": r"\cite{Afr26,Hou26}",
}


def src_tex(s):
    if s in CITE:
        return CITE[s]
    m = re.match(r"Z\((\d+),(\d+)\)", s)
    if m:
        return rf"via $({m.group(1)},{m.group(2)})$"
    return s


rows = list(csv.DictReader(open("literature.csv", encoding="utf-8")))
for r in rows:
    for k in ("m", "n", "UP_fig2", "LO_artigo", "UB_lit", "LB_lit"):
        r[k] = int(r[k])
    r["ours"] = int(r["nosso"]) if r["nosso"] else 0
    p = f"{RES}/Z_{r['m']}_{r['n']}.txt"
    ok, v = check(p) if os.path.exists(p) else (False, 0)
    assert ok and v == r["ours"], (p, ok, v, r["ours"])

for r in rows:
    r["UB_publicado"] = int(r["UB_publicado"])
improved = [r for r in rows if r["ours"] > r["LB_lit"]]
closed_new = [r for r in rows if r["status"] == "NOVO: fecha o caso"]
ub_improved = [r for r in rows if r["UB_lit"] < r["UB_publicado"]]
gains = [r["ours"] - r["LB_lit"] for r in improved]

WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
         "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
         "eighteen", "nineteen", "twenty", "twenty-one", "twenty-two", "twenty-three",
         "twenty-four", "twenty-five"]
with open(f"{GEN}/macros.tex", "w") as f:
    n = len(improved)
    word = WORDS[n] if n < len(WORDS) else str(n)
    f.write(f"\\newcommand{{\\NumImproved}}{{{n}}}\n")
    f.write(f"\\newcommand{{\\NumImprovedWord}}{{{word}}}\n")
    f.write(f"\\newcommand{{\\NumImprovedWordCap}}{{{word.capitalize()}}}\n")
    f.write(f"\\newcommand{{\\NumOpen}}{{{len(rows)}}}\n")
    f.write(f"\\newcommand{{\\NumClosedNew}}{{{len(closed_new)}}}\n")
    nu = len(ub_improved)
    f.write(f"\\newcommand{{\\NumUBImproved}}{{{nu}}}\n")
    f.write(f"\\newcommand{{\\NumUBImprovedWord}}{{{WORDS[nu] if nu < len(WORDS) else nu}}}\n")
    cl = [f"$z({r['m']},{r['n']})={r['UB_lit']}$" for r in closed_new]
    cl_txt = cl[0] if len(cl) == 1 else ", ".join(cl[:-1]) + " and " + cl[-1] if cl else ""
    f.write(f"\\newcommand{{\\ClosedList}}{{{cl_txt}}}\n")
    f.write(f"\\newcommand{{\\MaxGain}}{{{max(gains) if gains else 0}}}\n")
    f.write(f"\\newcommand{{\\TotalGain}}{{{sum(gains)}}}\n")
    byk = {(r["m"], r["n"]): r for r in rows}
    f.write(f"\\newcommand{{\\OursSixteenEighteen}}{{{byk[(16, 18)]['ours']}}}\n")
    f.write(f"\\newcommand{{\\UBSixteenEighteen}}{{{byk[(16, 18)]['UB_lit']}}}\n")
    ms, ns = [r["m"] for r in improved], [r["n"] for r in improved]
    f.write(f"\\newcommand{{\\Mmin}}{{{min(ms)}}}\\newcommand{{\\Mmax}}{{{max(ms)}}}\n")
    f.write(f"\\newcommand{{\\Nmin}}{{{min(ns)}}}\\newcommand{{\\Nmax}}{{{max(ns)}}}\n")

# Figura: mapa de calor no estilo da Figura 2 de [BNRL26], com "antigo -> novo"
from table import MS, NS, up as up_fig2, lo as lo_fig2  # noqa: E402

YLORRD = [(255, 255, 204), (255, 237, 160), (254, 217, 118), (254, 178, 76),
          (253, 141, 60), (252, 78, 42), (227, 26, 28), (189, 0, 38), (128, 0, 38)]
GMAX = 12
BEIGE = (240, 206, 186)


def cmap(gap):
    t = 1 - min(max(gap, 0), GMAX) / GMAX  # folga pequena = escuro
    x = t * (len(YLORRD) - 1)
    i = min(int(x), len(YLORRD) - 2)
    f = x - i
    return tuple(round(a + (b - a) * f) for a, b in zip(YLORRD[i], YLORRD[i + 1]))


def rgb(c):
    return f"{{rgb,255:red,{c[0]};green,{c[1]};blue,{c[2]}}}"


def dark(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] < 140


byk = {(r["m"], r["n"]): r for r in rows}
W, H = 1.6, 1.15
with open(f"{GEN}/heatmap.tex", "w") as f:
    f.write("\\begin{tikzpicture}[font=\\scriptsize]\n")
    for i, m in enumerate(MS):
        y = (len(MS) - 1 - i) * H
        f.write(f"\\node[anchor=east,font=\\small] at (-0.1,{y + H / 2:.3f}) {{{m}}};\n")
        for j, n in enumerate(NS):
            x = j * W
            r = byk.get((m, n))
            star = False
            ub_txt = None
            if r is not None and r["UB_lit"] < r["UB_publicado"]:
                ub_txt = f"{r['UB_publicado']}$\\,\\to\\,$\\textbf{{{r['UB_lit']}}}"
            if r is None:  # fechado em [BNRL26]
                col, top, bot = BEIGE, None, str(up_fig2(m, n))
            elif r["status"] == "NOVO: fecha o caso":  # fechado na Secao 2
                col, top, bot = BEIGE, ub_txt, f"\\textbf{{{r['UB_lit']}}}"
            elif max(r["ours"], r["LB_lit"]) >= r["UB_lit"]:  # fechado na literatura
                col, top, bot = BEIGE, None, str(r["UB_lit"])
            else:
                best = max(r["ours"], r["LB_lit"])
                col = cmap(r["UB_lit"] - best)
                top = ub_txt or str(r["UB_lit"])
                if r["ours"] > r["LB_lit"]:
                    bot = f"{r['LB_lit']}$\\,\\to\\,$\\textbf{{{r['ours']}}}"
                else:
                    bot = f"\\textbf{{{best}}}"
            tc = "white" if dark(col) else "black"
            f.write(f"\\fill[fill={rgb(col)}] ({x + 0.03:.3f},{y + 0.03:.3f}) rectangle "
                    f"({x + W - 0.03:.3f},{y + H - 0.03:.3f});\n")
            cx = x + W / 2
            if top is None:
                f.write(f"\\node[text=black!70] at ({cx:.3f},{y + H / 2:.3f}) {{\\itshape {bot}}};\n")
            else:
                f.write(f"\\node[text={tc}] at ({cx:.3f},{y + 0.73 * H:.3f}) {{{top}}};\n")
                f.write(f"\\draw[{tc},line width=0.3pt] ({cx - 0.3:.3f},{y + 0.5 * H:.3f}) -- "
                        f"({cx + 0.3:.3f},{y + 0.5 * H:.3f});\n")
                f.write(f"\\node[text={tc}] at ({cx:.3f},{y + 0.27 * H:.3f}) {{{bot}}};\n")
                if star:
                    f.write(f"\\node[text={tc}] at ({x + W - 0.15:.3f},{y + 0.18:.3f}) {{$\\ast$}};\n")
    for j, n in enumerate(NS):
        f.write(f"\\node[font=\\small] at ({j * W + W / 2:.3f},-0.3) {{{n}}};\n")
    f.write(f"\\node[font=\\small] at ({len(NS) * W / 2:.3f},-0.75) {{$n$}};\n")
    f.write(f"\\node[font=\\small,rotate=90] at (-0.95,{len(MS) * H / 2:.3f}) {{$m$}};\n")
    # barra de cores
    bx, bh = len(NS) * W + 0.4, len(MS) * H * 0.8
    by = (len(MS) * H - bh) / 2
    steps = 60
    for k in range(steps):
        g = k / steps * GMAX
        f.write(f"\\fill[fill={rgb(cmap(g))}] ({bx},{by + bh * k / steps:.3f}) rectangle "
                f"({bx + 0.35},{by + bh * (k + 1) / steps + 0.002:.3f});\n")
    f.write(f"\\draw[line width=0.3pt] ({bx},{by:.3f}) rectangle ({bx + 0.35},{by + bh:.3f});\n")
    for g in range(0, GMAX + 1, 4):
        yy = by + bh * g / GMAX
        f.write(f"\\draw ({bx + 0.35},{yy:.3f}) -- ({bx + 0.45},{yy:.3f}) "
                f"node[right,font=\\scriptsize] {{{g}}};\n")
    f.write(f"\\node[rotate=90,font=\\scriptsize] at ({bx + 1.05},{by + bh / 2:.3f}) "
            f"{{gap (upper $-$ lower)}};\n")
    f.write("\\end{tikzpicture}\n")

# Tabela unica: os casos abertos de [BNRL26, Fig. 2], antes e depois deste trabalho.
# Um limite superior recebe \dag se a sua cadeia de deducao chega a um preprint.
PREPRINT = {"Afrasyab26", "Hou26", "Afrasyab26/Hou26"}


def ub_depends_on_preprint(k, seen=()):
    r = byk.get(k)
    if r is None or k in seen:
        return False  # celula fechada em [BNRL26]: base publicada
    src = r["fonte_UB"]
    if src in PREPRINT:
        return True
    mm = re.match(r"Z\((\d+),(\d+)\)", src)
    return bool(mm) and ub_depends_on_preprint((int(mm.group(1)), int(mm.group(2))), seen + (k,))


n_dep = 0
with open(f"{GEN}/summary.tex", "w") as f:
    for r in rows:
        k = (r["m"], r["n"])
        dag = "$^\\dag$" if ub_depends_on_preprint(k) else ""
        ub_new = r["UB_lit"] < r["UB_publicado"]
        lb_new = r["ours"] > r["LB_lit"]
        n_dep += bool(dag and ub_new)
        if r["status"] == "NOVO: fecha o caso":
            st = "\\textbf{exact (new)}"
        elif r["status"].startswith("já fechado"):
            st = "exact"
        else:
            st = "open"
        ub_prev_src = src_tex(r["fonte_UB_publicado"])
        ub_prev = f"{r['UB_publicado']}{dag if not ub_new else ''}"
        f.write(
            f"$({r['m']},{r['n']})$ & {ub_prev} & {ub_prev_src} & "
            f"{('\\textbf{' + str(r['UB_lit']) + '}' + dag) if ub_new else ''} & "
            f"{r['LB_lit']} & {src_tex(r['fonte_LB'])} & "
            f"{('\\textbf{' + str(r['ours']) + '}') if lb_new else ''} & "
            f"{('$+' + str(r['ours'] - r['LB_lit']) + '$') if lb_new else ''} & {st} \\\\\n")
    f.write("\\bottomrule\n")
with open(f"{GEN}/macros.tex", "a") as f:
    f.write(f"\\newcommand{{\\NumPreprintDep}}{{{n_dep}}}\n")

# Apendice: matrizes desenhadas em grade (preto = 1), tres por linha
LETTERS = "abcdefghijklmnopqrstuvwxyz"
with open(f"{GEN}/matrices.tex", "w") as f:
    for i, r in enumerate(improved):
        p = f"{RES}/Z_{r['m']}_{r['n']}.txt"
        mat = [l.strip() for l in open(p) if l.strip() and not l.startswith("#")]
        m, n = len(mat), len(mat[0])
        f.write("\\begin{minipage}[b]{0.32\\textwidth}\\centering\n")
        f.write("\\begin{tikzpicture}[x=2mm,y=2mm]\n")
        for row, line in enumerate(mat):
            for col, ch in enumerate(line):
                if ch == "1":
                    f.write(f"\\fill ({col},{m - row - 1}) rectangle +(1,1);")
            f.write("\n")
        f.write(f"\\draw[black!30,line width=0.3pt,step=1] (0,0) grid ({n},{m});\n")
        f.write(f"\\draw[line width=0.4pt] (0,0) rectangle ({n},{m});\n")
        f.write("\\end{tikzpicture}\\\\[3pt]\n")
        f.write(f"{{\\small ({LETTERS[i]}) $z({r['m']},{r['n']};3,3)\\ge {r['ours']}$}}\n")
        f.write("\\end{minipage}" + ("\n\n\\bigskip\n" if i % 3 == 2 else "\\hfill\n"))
        shutil.copyfile(p, f"{ANC}/Z_{r['m']}_{r['n']}.txt")
shutil.copyfile("verify.py", f"{ANC}/verify.py")
print(f"{len(improved)} casos melhorados, ganho total {sum(gains)}, max {max(gains) if gains else 0}")
