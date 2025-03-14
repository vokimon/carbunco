#!/usr/bin/env python
import requests
from pathlib import Path
from yamlns import ns
import geopy.distance
from geopy.geocoders import Nominatim as Geocoder
import click
from consolemsg import step, warn, error



def float_es(x):
    if not x: return 0
    x = x.replace(',','.')
    return float(x)


class Carbunco:
    def __init__(self):
        self._stations = None

    def reloadPrices(self):
        response = requests.get('https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/')
        data = response.json()
        print(data['Nota'])
        print(data['Fecha'])
        print(data['ResultadoConsulta'])
        self._stations = data['ListaEESSPrecio']
        self.updateProducts()

    def updateProducts(self):
        lastStation = self._stations[-1]
        price_prefix = 'Precio '
        self.products = [
            key[len(price_prefix):]
            for key in lastStation.keys()
            if key.startswith(price_prefix)
        ]

    @property
    def stations(self):
        if self._stations:
            return self._stations

        import datetime
        import appdirs
        author = 'vokimon'
        appname = 'carbunco'
        datadir = Path(appdirs.user_data_dir(appname, author))
        today=datetime.date.today()
        datafile = datadir / f'stations-{today}.yaml'
        datadir.mkdir(exist_ok=True, parents=True)
        if datafile.exists():
            #step(f"Usando datos de {datafile}")
            self._stations = ns.load(datafile).data
            self.updateProducts()
            #step(f"Cache cargada")
            return self._stations
        #step("Descargando datos del Ministerio")
        self.reloadPrices()
        ns(data=self._stations).dump(datafile)
        return self._stations

    def locate(self, place):
        geocode = Geocoder(user_agent=__name__).geocode(place)
        #step(f"Buscando estaciones de servicio baratas cerca de {geocode.address}")
        return geocode.latitude, geocode.longitude

    def route(self, from_, to):
        url = f'http://router.project-osrm.org/route/v1/driving/{from_[0]},{from_[1]};{to[0]},{to[1]}?steps=true&overview=simplified'
        response = requests.get(url)
        travel = ns(response.json())
        route = travel.routes[0]
        return [from_] + [
            step['maneuver']['location'] for step in route['legs'][0]['steps']
        ] + [to]


    def cheapQuest(self, locations, product):
        if type(locations[0]) == float:
            locations=[locations]

        priceField = 'Precio '+product
        stations_by_price = sorted(
            self.stations,
            key=lambda x: float_es(x[priceField]),
        )

        def distanceTo(location, station):
            station_location = (
                float_es(station['Latitud']),
                float_es(station['Longitud (WGS84)'])
            )
            return geopy.distance.distance(location, station_location).km

        currentDistance = 2000

        for station in stations_by_price:
            if not station[priceField]:
                continue
            distance = min(distanceTo(location, station) for location in locations)
            station['Distancia'] = distance
            if distance > currentDistance*1.2:
                continue
            currentDistance = distance
            yield station

    def pricesByBrand(self, product):
        prices = {}
        for station in self.stations:
            if not station['Precio '+product]:
                continue
            prices.setdefault(station['Rótulo'].strip(), []).append(
                float_es(station['Precio '+product])
            )
        return [[
            'Marca', 'Gasolineras', 'Min', 'Max', 'Diff %', 'Media'
        ]] + [
            [
                brand,
                "{}".format(len(prices)),
                "{:.03f}".format(min(prices)),
                "{:.03f}".format(max(prices)),
                "{:2.02f}".format((max(prices)-min(prices))/max(prices)*100),
                "{:.03f}".format(sum(prices)/len(prices)),
            ] for brand, prices in prices.items()
        ]


def search(place):
    location = 37.166667, -3.15 # Lanteira
    location = 41.69, 2.49 # Sant Celoni
    location = 41.984444, 2.821111 # Girona
    location = 41.368056, 2.058056 # Sant Joan Despí
    location = 39.466667, -0.375 # Valencia

    product = 'Gasoleo A'
    product = 'Gasolina 95 E5'


    c = Carbunco()
    c.reloadPrices()
    location = c.locate(place)
    for station in c.cheapQuest(location, product):
        print(
            f"{station['Distancia']:.0f} km\t"
            f"{station['Precio '+product]} €/l\t"
            f"{station['Rótulo']}\t"
            f"{station['Provincia']}\t"
            f"{station['Localidad']}\t"
            f"{station['Dirección']}"
        )


