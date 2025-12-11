import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, cairo

import math, os, threading, time, sqlite3, requests, json
from websocket import create_connection

TILE_URL = "https://ltak.drcat.fun/tiles/{z}/{x}/{y}.png"
TILE_CACHE_DB = "tilecache.db"

# --- Tile cache (SQLite) ---
class TileCache:
    def __init__(self, path=TILE_CACHE_DB):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init()

    def _init(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS tiles (zoom INTEGER, x INTEGER, y INTEGER, data BLOB, last_accessed INTEGER, PRIMARY KEY (zoom,x,y))''')
        self.conn.commit()

    def get(self, z, x, y):
        cur = self.conn.cursor()
        cur.execute("SELECT data FROM tiles WHERE zoom=? AND x=? AND y=?", (z,x,y))
        r = cur.fetchone()
        if not r: return None
        return r[0]

    def set(self, z, x, y, data):
        cur = self.conn.cursor()
        cur.execute("REPLACE INTO tiles (zoom,x,y,data,last_accessed) VALUES (?,?,?,?,?)",
                    (z,x,y,data,int(time.time())))
        self.conn.commit()

tile_cache = TileCache()

# --- Tile fetcher thread ---
def fetch_tile_background(z, x, y):
    cached = tile_cache.get(z,x,y)
    if cached:
        return
    url = TILE_URL.format(z=z,x=x,y=y)
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            tile_cache.set(z,x,y,r.content)
            GLib.idle_add(app.redraw)  # trigger redraw in main thread
    except Exception as e:
        print("tile fetch error", e)

# --- Map widget ---
class MapView(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.zoom = 14
        self.center_lat = 34.05
        self.center_lon = -118.25
        self.connect("draw", self.on_draw)
        self.set_content_width(800)
        self.set_content_height(600)

    def on_draw(self, area, ctx, width, height):
        tiles = self.compute_tiles(width, height)
        for tx, ty, px, py, z in tiles:
            data = tile_cache.get(z, tx, ty)
            if data:
                loader = GdkPixbuf.PixbufLoader.new()
                loader.write(data)
                loader.close()
                pix = loader.get_pixbuf()
                Gdk.cairo_set_source_pixbuf(ctx, pix, px, py)
                ctx.paint()
            else:
                # placeholder
                ctx.set_source_rgb(0.12,0.12,0.12)
                ctx.rectangle(px,py,256,256)
                ctx.fill()
                # spawn fetch
                threading.Thread(target=fetch_tile_background, args=(z,tx,ty), daemon=True).start()

    def compute_tiles(self, width, height):
        # compute center tile & visible tiles. This is placeholder logic.
        center_x = lon2tilex(self.center_lon, self.zoom)
        center_y = lat2tiley(self.center_lat, self.zoom)
        tiles = []
        n = int(max(width, height) / 256) + 2
        for dx in range(-n, n+1):
            for dy in range(-n, n+1):
                tx = center_x + dx
                ty = center_y + dy
                px = (dx + n) * 256
                py = (dy + n) * 256
                tiles.append((tx, ty, px, py, self.zoom))
        return tiles

# --- helper tile math ---
def lon2tilex(lon, z):
    return int((lon + 180.0) / 360.0 * (1 << z))
def lat2tiley(lat, z):
    lat_rad = math.radians(lat)
    return int((1.0 - math.log(math.tan(lat_rad) + 1.0/math.cos(lat_rad)) / math.pi) / 2.0 * (1 << z))

# --- Position uploader (GPSD or simulated) ---
def position_loop(server_url, user_id="pyclient", interval=2):
    while True:
        # read actual GPS here; simulate for now
        pos = {"user_id": user_id, "lat": 34.05, "lon": -118.25, "timestamp": int(time.time())}
        try:
            requests.post(server_url + "/users/position", json=pos, timeout=3)
        except Exception as e:
            print("position post failed", e)
        time.sleep(interval)

# --- WebSocket client for real-time positions/markers ---
def ws_loop(ws_url):
    while True:
        try:
            ws = create_connection(ws_url)
            while True:
                msg = ws.recv()
                if not msg:
                    break
                on_ws_message(msg)
        except Exception as e:
            print("ws error", e)
            time.sleep(2)

def on_ws_message(msg):
    j = json.loads(msg)
    # process position/marker events and call GLib.idle_add to update UI.
    print("ws:", j)

# --- Main app skeleton ---
class App:
    def __init__(self):
        self.win = Gtk.Window(title="LTAK Client")
        self.win.set_default_size(1024, 768)
        self.map = MapView()
        self.win.set_child(self.map)
        self.win.connect("close-request", lambda w: Gtk.main_quit())

    def run(self):
        self.win.show()
        Gtk.main()

    def redraw(self):
        self.map.queue_draw()
        return False

app = App()

if __name__ == "__main__":
    threading.Thread(target=position_loop, args=("https://ltak.drcat.fun", "pyclient01"), daemon=True).start()
    threading.Thread(target=ws_loop, args=("wss://ltak.drcat.fun/ws",), daemon=True).start()
    app.run()
