#!/usr/bin/env python

from yamlns import ns
import re
from pathlib import Path

print('loading')
"""
info = ns.load('stations-2022-06-11.yaml')
rotulos = [x['Rótulo' ] for x in info.data]
"""
rotulos = [
    line[len('  Rótulo: '):].strip(' \'')
    for line in Path("stations-2022-06-11.yaml").read_text(encoding='utf8').splitlines()
    if line.startswith('  Rótulo: ')
]


def split(items, regex):
    matcher = re.compile('.*'+regex+'.*')
    yes = [x for x in items if matcher.match(x)]
    no  = [x for x in items if not matcher.match(x)]
    return yes, no


filters = [
	('REPSOL', '(REPSOL|PETRONOR|CAMPSA)'),
	('BP', 'BP'), # UK Refino en españa
	('CEPSA', 'CEPSA'), # ES
	('TAMOIL', 'TAMOIL'), # NL
	('SHELL', 'SHELL'), # US
	('BONAREA', 'BONAREA'), # Super CAT Cooperativa
	('ALCAMPO', 'ALCAMPO'), # Super FR
	('ESCLAT', 'ESCLAT'), # Super CAT
	('CARREFOUR', '(CARREFOUR|CARRREFOUR)'), # Super FR
	('GALP', 'GALP'), # PT
	('AN ENERGETICOS', 'A\.*N\.* *ENERG.TICOS'),
	('PETROPRIX', 'PETROPRIX'),
	('MEROIL', 'MEROIL'),
	('PETROCAT', 'PETROCAT '),
	('PLENOIL', 'PLENOIL'),
	('BALLENOIL', 'BALLENOIL'),
	('AVIA', 'AVIA'), # Suiza
	('Q8', 'Q8'), # Kuwait
	('AGLA', 'AGLA'), # Associacion de independientes (Andalucia/Extremadura) (En su web son 92)
	('BEROIL', 'BEROIL'),
	('EROSKI', 'EROSKI'),
	('NATURGY', 'NATURGY'),
	('VALCARCE', 'VALCARCE\\b'),
	('DISA', '\\bDISA\\b'),
	('COOPERATIVAS', '(COOP'
	    '|S[. ]*C[. ]*A[. ]*'
	    '|S[. ]*C[. ]*L[. ]*'
	    '|S[. ]*C[. ]*C[. ]*L[. ]*'
	    '|S[.]C[.]G[.]'
        #'|AGRICOLA'
        '|CEREALES TERUEL' # Coope agricola
        ')'
    ),
    ('LECLERC', 'LECLERC'),
    ('ASOCIACIONES', '(ASOC|ASSOC)'),
    ('TGAS', 'TGAS'),
    ('STAROIL', 'STAROIL'),
    ('XPO', '\\bXPO'),
    ('VCC', 'VCC'),
    ('SUPECO', 'SUPECO'),
    ('V2', 'V2'),
    ('SEROIL', 'SEROIL'),
    ('REPOSTAR', 'REPOSTAR'),
    ('PETROMIRALLES', 'PETROMIRALLES'),
    ('PETROCAT', 'PETROCAT'),
    ('PETRO7', '(PETRO7|PETROLIS INDEPENDENTS)'),
    ('OILPRIX', '(OILPRIX|PRIX)'),
    ('SARAS', 'SARAS'),
    ('NIEVES', '^NIEVES'),
    ('ANEU OIL', 'ANEU'),
    ('ANDAMUR', 'ANDAMUR'),
    ('ALDI', 'ALDI'),
    ('ALIARA', 'ALIARA'),
    ('AUTONET', 'AUTONET'),
    ('ASC CARBURANTES', 'ASC CAR'),
    ('BDMED', 'BDMED'),
    ('BURAN ENERGY', '\\bBURAN'),
    ('CAMPOASTUR', 'CAMPOASTUR'),
    ('GASOLEOS TERUEL', 'GASOLEOS TERUEL'),
    ('CONFORT AUTO', 'CONFORT AUTO'),
    ('CALIDAD LOW COST', 'CLC'),
    ('EASYGAS', 'EASYGAS'),
    ('ENI', '\\bENI\\b'),
    ('GASEXPRESS', 'GASEXPRESS'),
    ('FAMILY ENERGY', 'FAMILY'),
    ('FARRUCO', 'FARRUCO'),
    ('GACOSUR', 'GACOSUR'),
]


def countBrandedStations(remaining):
    for company, matcher in filters:
        matches, remaining = split(remaining, matcher)
        yield company, len(matches)

    print(ns(remaining=sorted(remaining)[1100:1400]).dump())
    print(ns(lastmatch=matches).dump())
    print("Last", len(matches))
    print("Remaining", len(remaining))
    yield "otros", len(remaining)

sortedCompanies = [
    (company, number)
    for company, number in sorted(
        countBrandedStations(rotulos),
        key = lambda x: -x[1]
    )
]
for company, number in sortedCompanies:
    print(number, company)

def groupOthers(items, limit):
    others = 0
    supers = 0
    coops = 0
    for label, number in items:
        if label in ('CARREFOUR', 'ALDI', 'BONAREA', 'ESCLAT', 'ALCAMPO'):
            supers += number
        elif label == "COOPERATIVAS":
            coops += number
        elif number < limit or label=='otros':
            others += number
        else:
            yield label, number, number*100./len(rotulos)

    yield 'Supermercados', supers, supers*100/len(rotulos)
    yield 'Cooperativas', coops, coops*100/len(rotulos)
    yield 'Otros', others, others*100/len(rotulos)



labels, values, percents = zip(*groupOthers(sortedCompanies, 100))

import plotly.graph_objects as go

# pull is given as a fraction of the pie radius
fig = go.Figure(data=[
    go.Pie(
        labels=labels,
        values=values,
        rotation=-40,
        sort=False,
        showlegend=False,
    )
    ],
)
fig.update_layout(
    width=700,
    height=700,
)
fig.update_traces(
    hoverinfo='label+percent',
    textinfo='value+label',
    #textfont_size=20,
    #marker=dict(line=dict(color='#000000', width=2))
)
fig.show()
fig.write_image("gasstations-share.svg")

"""
import matplotlib.pyplot as plt

fig1, ax1 = plt.subplots()
wedges, texts, autotexts = ax1.pie(
    values, labels=labels,
    pctdistance = 1.3,
    labeldistance = 1.2,
    autopct=lambda pct: '' if pct < 3 else '{:.1f}%'.format(pct),
    shadow=True, startangle=90
)
ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
#fig1.savefig("gasstations-share.svg")
plt.show()
"""

