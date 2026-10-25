import csv
for r in csv.DictReader(open("/work/literature.csv", encoding="utf-8")):
    lb = max(int(r["LB_lit"]), int(r["nosso"] or 0)); ub = int(r["UB_lit"])
    if ub > lb:
        print(r["m"], r["n"], lb, ub)
