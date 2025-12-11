import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from .main_window import MainWindow

class LTAKApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="fun.drcat.ltak")

    def do_activate(self, *args):
        win = MainWindow(self)
        win.present()
