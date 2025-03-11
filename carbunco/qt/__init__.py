#!/usr/bin/env python

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
        gmap.setMarkerOptions(key, draggable=1)

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

        gmap.deleteMarker("MyDragableMark")
        gmap.addMarker("MyDragableMark", *location, draggable=1)
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

    tab = QtWidgets.QTabWidget()
    h.addWidget(tab)
    

    stationList = QtWidgets.QTreeWidget()
    stationList.setHeaderItem(QtWidgets.QTreeWidgetItem([
        "Distancia",
        "Precio",
        "Rótulo",
        "Provincia",
        "Localidad",
        "Dirección",
    ]))
    tab.addTab(stationList, "Estaciones")

    gmap = QGoogleMap(w)
    gmap.mapMoved.connect(onMapMoved)
    gmap.markerMoved.connect(onMarkerMoved)
    gmap.mapClicked.connect(onMapLClick)
    gmap.mapDoubleClicked.connect(onMapDClick)
    gmap.mapRightClicked.connect(onMapRClick)
    gmap.markerClicked.connect(onMarkerLClick)
    gmap.markerDoubleClicked.connect(onMarkerDClick)
    gmap.markerRightClicked.connect(onMarkerRClick)
    tab.addTab(gmap, "Mapa")
    gmap.setSizePolicy(
        QtWidgets.QSizePolicy.MinimumExpanding,
        QtWidgets.QSizePolicy.MinimumExpanding,
    )
    return w



def qtapp(engine):
    import sys
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QLabel
    from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

    engine.stations # force load
    QQuickWindow.setGraphicsApi(QSGRendererInterface.OpenGLRhi)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = application(engine)
    window.show()
    sys.exit(app.exec())


