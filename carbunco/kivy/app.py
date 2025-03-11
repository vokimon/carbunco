from kivymd.app import MDApp as App
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivy.uix.behaviors.knspace import KNSpaceBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ListProperty
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.metrics import dp

columnLabels = dict(
    distance = "Distancia",
    price = "Precio",
    title = "Rótulo",
    state = "Provincia",
    city = "Localidad",
    address = "Dirección",
)

class StationList(MDDataTable):
    stations = ListProperty([])
    def __init__(self, **kwds):
        super().__init__(
            use_pagination=True,
            check=True,
            column_data=[
                ("No.", dp(30)),
                ("Status", dp(30)),
                ("Signal Name", dp(60)),
                ("Severity", dp(30)),
                ("Stage", dp(30)),
                ("Schedule", dp(30)),
                ("Team Lead", dp(30),),
            ],
            row_data=[
                (
                    "1",
                    ("alert", [255 / 256, 165 / 256, 0, 1], "No Signal"),
                    "Astrid: NE shared managed",
                    "Medium",
                    "Triaged",
                    "0:33",
                    "Chase Nguyen",
                ),
            ],
            sorted_on="Schedule",
            sorted_order="ASC",
            elevation=2,
            #column_data = [
            #    (label, dp(6))
            #    for col, label in columnLabels.items()
            #],
            **kwds)

    def fed_station_data(self, stations):
        ""

class Tab(MDFloatLayout, MDTabsBase):
    pass

class CarbuncoApp(App):
    products = ListProperty(["Gasofa","Gasoil"])

    def __init__(self, engine, **kwds):
        super().__init__(
            kv_file='carbunco/kivy/carbunco.kv',
            title="Carbunco",
            **kwds
        )
        self.engine = engine
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.engine.stations # trigger load

    def search_stations(self):
        
        from kivymd.uix.label import MDLabel
        from kivymd.uix.list import ThreeLineListItem
        search = self.root.ids.address.text
        location = self.engine.locate(search)
        product = self.root.ids.product_selector.text
        print(dir(self.root))
        print(self.root.ids)
        self.root.ids.stationlist.clear_widgets()
        for station in self.engine.cheapQuest(
            locations = [location],
            product = product,
        ):
            item = ThreeLineListItem(
                text=f"[color=ffff88]{station['Precio '+product]} €/l[/color] [color=44ff33]{station['Distancia']:.2f} km[/color] {station['Rótulo']}",
                secondary_text=f"{station['Dirección']}",
                tertiary_text=f"{station['Localidad']} ({station['Provincia']})",
            )
            self.root.ids.stationlist.add_widget(item)

    def product_selected(self, i, product):
        self.root.ids.product_selector.text = product

    def open_product_dropdown(self):
        from kivymd.uix.menu import MDDropdownMenu
        from functools import partial
        self.menu = MDDropdownMenu(
            caller=self.root.ids.product_selector,
            items=[
                dict(
                    text = product,
                    on_release = partial(self.product_selected, i, product),
                )
                for i, product in enumerate(self.engine.products)
            ],
        )
        self.menu.open()


    def show_products(self):
        print("showing products")

def app(engine):
    CarbuncoApp(engine=engine).run()
 


