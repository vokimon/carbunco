#!/usr/bin/env python
import requests
from pathlib import Path
import json
from yamlns import ns
import geopy.distance
from geopy.geocoders import Nominatim as Geocoder
import geocoder
import click
from consolemsg import step, warn, error


def default_reporter(*args):
    print("===", *args)

def float_es(x):
    if not x: return 0
    x = x.replace(',','.')
    return float(x)


class Carbunco:
    def __init__(self, reporter=default_reporter):
        self._stations = None
        self._reporter = reporter

    def report(self, *args):
        self._reporter(*args)

    def download_prices(self):
        try:
            self.report(f"Bajando datos de hoy")
            response = requests.get('https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/')
        except Exception as e:
            self.report("Error bajando datos", e)
            self._stations = []
            return
        data = response.json()
        self.report("Nota:", data['Nota'])
        self.report("Fecha:", data['Fecha'])
        self.report(data['ResultadoConsulta'])
        self._stations = data['ListaEESSPrecio']
        self.updateProducts()

    def updateProducts(self):
        if not self._stations:
            self.products = []
            return
        lastStation = self._stations[-1]
        price_prefix = 'Precio '
        self.products = [
            key[len(price_prefix):]
            for key in lastStation.keys()
            if key.startswith(price_prefix)
        ]

    def _load_cached_today_data(self):
        self.report(f"Cargando datos guardados de hoy")
        self._stations = []
        datafile = self.today_data_file
        if not datafile.exists():
            self.report(f"No hay datos guardados de hoy")
            return
        self._stations = ns(json.loads(datafile.read_text())).data
        self.report(f"Cache cargada")
        return self._stations

    def _load_last_data(self):
        self.report(f"Cargando cache vieja")
        self._stations = []
        datafile = self.last_data_file
        if not datafile:
            self.report(f"No hay datos antiguos")
            return
        self._stations = ns(json.loads(datafile.read_text())).data
        self.report(f"Cache cargada")
        return self._stations

    def _save_today_cache(self):
        self.data_dir.mkdir(exist_ok=True, parents=True)
        datafile = self.today_data_file
        datafile.write_text(json.dumps(ns(data=self._stations)))

    @property
    def today_data_file(self):
        import datetime
        today=datetime.date.today()
        return self.data_dir / f'stations-{today}.json'

    @property
    def last_data_file(self):
        availables = list(sorted(self.data_dir.glob('stations-*.json')))
        return availables[-1] if availables else None

    @property
    def data_dir(self):
        import platformdirs
        author = 'vokimon'
        appname = 'carbunco'
        return Path(platformdirs.user_data_dir(appname, author, ensure_exists=True))

    def _load_stations(self):
        self._load_cached_today_data()
        if self._stations:
            return
        self.download_prices()
        if self._stations:
            self._save_today_cache()
            return
        self._load_last_data()

    @property
    def stations(self):
        if not self._stations:
            self._load_stations()
        self.updateProducts()
        return self._stations

    def locate(self, place):
        location = None
        geo = Geocoder(user_agent=__name__)
        if not place:
            import geocoder
            self.report(f"Usando geolocalizacion del dispositivo")
            location = geocoder.ip('me')
            location = location and location.latlng
        else:
            self.report(f"Geolocalizando \"{place}\"")
            location = geo.geocode(place)
            location = location and (location.latitude, location.longitude)
        self.report("Location:", location)
        return location

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
    c.download_prices()
    print("searching", place)
    location = c.locate(place)
    if not location:
        print("Location not found")
        return

    for station in c.cheapQuest(location, product):
        print(
            f"{station['Distancia']:.0f} km\t"
            f"{station['Precio '+product]} €/l\t"
            f"{station['Rótulo']}\t"
            f"{station['Provincia']}\t"
            f"{station['Localidad']}\t"
            f"{station['Dirección']}"
        )


