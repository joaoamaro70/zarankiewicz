import csv
for r in csv.DictReader(open('/work/literature.csv')):
    lb = max(int(r['LB_lit']), int(r['nosso']))
    if int(r['UB_lit']) > lb:
        print(r['m'], r['n'], r['LB_lit'], r['nosso'], r['UB_lit'])
