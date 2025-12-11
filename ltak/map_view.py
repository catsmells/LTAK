import gi
gi.require_version("Gtk", "4.0")
from gi.repository import cairo

import math

from .tile_cache import TileCache

class MapView:
    def __init__(self):
        self.zoom = 4
        self.center_lat = 39.0
        self.center_lon = -96.0

        self.cache = TileCache("https://ltak.drcat.fun/tiles")

    def on_draw(self, area, cr, width, height):

        tile_x, tile_y = self.latlon_to_tile(self.center_lat, self.center_lon, self.zoom)

        for dx in range(-2, 3):
            for dy in range(-2, 3):
                tx = tile_x + dx
                ty = tile_y + dy

                tile = self.cache.get_tile(self.zoom, tx, ty)
                if tile:
                    surface = cairo.ImageSurface.create_from_png(tile)
                    px = (dx + 2) * 256
                    py = (dy + 2) * 256
                    cr.set_source_surface(surface, px, py)
                    cr.paint()

    @staticmethod
    def latlon_to_tile(lat, lon, z):
        lat_rad = math.radians(lat)
        n = 2.0 ** z
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int(
            (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) 
            / 2.0 * n
        )
        return xtile, ytile
