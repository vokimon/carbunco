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
        self.products =  [
            key[len('Precio '):]
            for key in self._stations[-1].keys()
            if key.startswith('Precio ')
        ]

    @property
    def stations(self):
        import datetime
        today=datetime.date.today()
        if self._stations:
            return self._stations
        cachefile = Path(f'stations-{today}.yaml')
        if cachefile.exists():
            step(f"Usando datos de {cachefile}")
            self._stations = ns.load(cachefile).data
            self.updateProducts()
            step(f"Cache cargada")
            return self._stations
        step("Descargando datos del Ministerio")
        self.reloadPrices()
        ns(data=self._stations).dump(cachefile)
        return self._stations




    def locate(self, place):
        geocode = Geocoder(user_agent=__name__).geocode(place)
        step(f"Buscando estaciones de servicio baratas cerca de {geocode.address}")
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



    #print(products)
    #print(stations[-1])


def application(engine):
    from PySide6 import QtWidgets
    from qgmap import QGoogleMap
    
    w = QtWidgets.QDialog()
    h = QtWidgets.QVBoxLayout(w)
    l = QtWidgets.QFormLayout()
    h.addLayout(l)



    def goCoords() :
        def resetError() :
            coordsEdit.setStyleSheet('')
        try : latitude, longitude = coordsEdit.text().split(",")
        except ValueError :
            coordsEdit.setStyleSheet("color: red;")
            QtCore.QTimer.singleShot(500, resetError)
        else :
            gmap.centerAt(latitude, longitude)
            gmap.moveMarker("MyDragableMark", latitude, longitude)

    def goAddress() :
        def resetError() :
            addressEdit.setStyleSheet('')
        coords = gmap.centerAtAddress(addressEdit.text())
        if coords is None :
            addressEdit.setStyleSheet("color: red;")
            QtCore.QTimer.singleShot(500, resetError)
            return
        gmap.moveMarker("MyDragableMark", *coords)
        coordsEdit.setText("{}, {}".format(*coords))

    def onMarkerMoved(key, latitude, longitude) :
        print("Moved!!", key, latitude, longitude)
        coordsEdit.setText("{}, {}".format(latitude, longitude))
    def onMarkerRClick(key) :
        print("RClick on ", key)
        gmap.setMarkerOptions(key, draggable=False)
    def onMarkerLClick(key) :
        print("LClick on ", key)
    def onMarkerDClick(key) :
        print("DClick on ", key)
        gmap.setMarkerOptions(key, draggable=True)

    def onMapMoved(latitude, longitude) :
        print("Moved to ", latitude, longitude)
    def onMapRClick(latitude, longitude) :
        print("RClick on ", latitude, longitude)
    def onMapLClick(latitude, longitude) :
        print("LClick on ", latitude, longitude)
    def onMapDClick(latitude, longitude) :
        print("DClick on ", latitude, longitude)

    def onSearchPressed():
        product = productChooser.currentText()
        place = addressEdit.text()
        location = engine.locate(place)
        stationList.clear()
        for station in engine.cheapQuest(
            locations = [location],
            product = product,
        ):
            stationList.addTopLevelItem(QtWidgets.QTreeWidgetItem([
                f"{station['Distancia']:.0f} km",
                f"{station['Precio '+product]} €/l",
                f"{station['Rótulo']}",
                f"{station['Provincia']}",
                f"{station['Localidad']}",
                f"{station['Dirección']}",
            ]))

    addressEdit = QtWidgets.QLineEdit()
    l.addRow('Address:', addressEdit)
    addressEdit.editingFinished.connect(goAddress)

    productChooser = QtWidgets.QComboBox()
    l.addRow('Product:', productChooser)
    for product in sorted(engine.products):
        productChooser.addItem(product)

    coordsEdit = QtWidgets.QLineEdit()
    l.addRow('Coords:', coordsEdit)
    coordsEdit.editingFinished.connect(goCoords)

    button = QtWidgets.QPushButton("Search")
    l.addRow(button)
    button.clicked.connect(onSearchPressed)

    stationList = QtWidgets.QTreeWidget()
    stationList.setHeaderItem(QtWidgets.QTreeWidgetItem([
        "Distancia",
        "Precio",
        "Rótulo",
        "Provincia",
        "Localidad",
        "Dirección",
    ]))
    h.addWidget(stationList)

    """
    gmap = QGoogleMap(w)
    gmap.mapMoved.connect(onMapMoved)
    gmap.markerMoved.connect(onMarkerMoved)
    gmap.mapClicked.connect(onMapLClick)
    gmap.mapDoubleClicked.connect(onMapDClick)
    gmap.mapRightClicked.connect(onMapRClick)
    gmap.markerClicked.connect(onMarkerLClick)
    gmap.markerDoubleClicked.connect(onMarkerDClick)
    gmap.markerRightClicked.connect(onMarkerRClick)
    h.addWidget(gmap)
    gmap.setSizePolicy(
        QtWidgets.QSizePolicy.MinimumExpanding,
        QtWidgets.QSizePolicy.MinimumExpanding,
    )
    """
    return w


@click.command()
@click.option('--brands', is_flag=True)
@click.option('--target')
@click.argument('query', nargs=-1)
def carbunco(query, brands, target=None):
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

    import sys
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QLabel
    from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

    engine = Carbunco()
    engine.stations # force load
    QQuickWindow.setGraphicsApi(QSGRendererInterface.OpenGLRhi)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    label = application(engine)
    label.show()
    sys.exit(app.exec())



if __name__ == "__main__":
    carbunco()

