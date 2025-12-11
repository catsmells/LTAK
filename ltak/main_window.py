import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

from .map_view import MapView
from .ltak_api import LTAKApi

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)

        builder = Gtk.Builder.new_from_file("data/ui/main_window.ui")
        self._window = builder.get_object("main_window")
        self.set_child(self._window.get_child())

        self.map_area = builder.get_object("map_area")
        self.refresh_button = builder.get_object("refresh_button")

        self.api = LTAKApi("https://ltak.drcat.fun")

        # Attach drawing area to custom MapView class
        self.map_view = MapView()
        self.map_area.set_draw_func(self.map_view.on_draw)

        # Signals
        self.refresh_button.connect("clicked", self.on_refresh_clicked)

    def on_refresh_clicked(self, btn):
        print("Refreshing remote data...")
