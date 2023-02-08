import plotly.graph_objects as go

flows = [ # Millones de toneladas anuales
    ('Gasolina Importada', 'Gasolina', 0.5),
    ('Gasoil Importado', 'Gasoil', 6.0),
    ('Gasolina Refinada', 'Gasolina', 8.6),
    ('Gasoil Refinado', 'Gasoil', 26.55),
    ('Gasolina', 'Gasolina Consumida', 4.844),
    ('Gasoil', 'Gasoil Consumido', 29.96),
    ('Gasolina', 'Gasolina Exportada', 4.3),
    ('Gasoil', 'Gasoil Exportado', 7.3),
    ('Reservas', 'Gasoil', (
        11.122 # reserves diciembre 2011
        -9.380 # reservas diciembre 2021
        )/10 # años
    ),
]
print(6.+26.55-4.844-7.3)

fullnames = list(set(sum(( [source,target] for source, target, value in flows), [])))

def labelFor(fullname):
    label = fullname.split()[-1]
    if label in ('Gasoil', 'Gasolina'):
        return label
    for flow in flows:
        if fullname in flow:
            return f"{label} {flow[-1]:0.02f}"
    return f"{label} ??"

print(fullnames)
labels = [labelFor(fullname) for fullname in fullnames]
print(labels)
source = [fullnames.index(source) for source, target, value in flows]
target = [fullnames.index(target) for source, target, value in flows]
value = [value for source, target, value in flows]

print(source)
print(target)
print(value)

fig = go.Figure(data=[
    go.Sankey(
        valueformat = ".1f",
        arrangement = 'fixed',
        name="Koala",
        node = dict(
            pad = 100,
            #thickness = 20,
            #line = dict(color="black", width=0.5),
            label = labels,
        ),
        link = dict(
            source = [fullnames.index(source) for source, target, value in flows],
            target = [fullnames.index(target) for source, target, value in flows],
            value = [value for source, target, value in flows],
            label = [f"{value:.01f}" for source, target, value in flows],
        ),
        orientation= 'v',
    ),
])
fig.update_layout(
    title_text="Flujo comercial de Carburante refinado en España\n(media anual 2012-2021 en Millones de toneladas)",
    margin=dict(l=20, r=20, t=30, b=20),
    height = 300,
    width = 1000,
    title_xanchor = 'center',
    title_x = 0.5,
)
fig.show()
fig.write_image('flujos-refinados.svg')
fig.write_image('flujos-refinados.pdf')

