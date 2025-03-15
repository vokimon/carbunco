#!/usr/bin/env python
from yamlns import ns
import click
from .engine import Carbunco



def float_es(x):
    if not x: return 0
    x = x.replace(',','.')
    return float(x)

@click.command()
@click.option('--brands', is_flag=True)
@click.option('--target')
@click.option('--qt', is_flag=True)
@click.argument('query', nargs=-1)
def carbunco(query, brands, target=None, qt=True):
    if query:
        product = 'Gasolina 95 E5'
        product = 'Gasoleo A'
        engine = Carbunco()
        first = engine.locate(' '.join(query))
        if target:
            last = engine.locate(target)
            route = engine.route(first, last)
        else:
            route = [ first ]
        print(ns(route=route).dump())
        engine.cheapQuest(route, 'Gasoleo A')
        for station in engine.cheapQuest(route, product):
            print(
                f"{station['Distancia']:.0f} km\t"
                f"{station['Precio '+product]} €/l\t"
                f"{station['Rótulo']}\t"
                f"{station['Provincia']}\t"
                f"{station['Localidad']}\t"
                f"{station['Dirección']}"
            )
        return

    if brands:
        engine = Carbunco()
        engine.reloadPrices()
        pricestable=engine.pricesByBrand('Gasoleo A')
        print('\n'.join(
            '\t'.join(x for x in l)
            for l in pricestable
        ))
        return

    engine = Carbunco()

    if qt:
        import sys
        sys.argv.remove('--qt')
        from .qt import qtapp
        qtapp(engine)
        return

    from .kivy.app import app
    app(engine)





if __name__ == "__main__":
    carbunco()

