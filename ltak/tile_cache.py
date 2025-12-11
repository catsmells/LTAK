import os
import requests

class TileCache:
    def __init__(self, base_url, cache_dir="tile_cache"):
        self.base_url = base_url.rstrip("/")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_tile(self, z, x, y):
        path = f"{self.cache_dir}/{z}_{x}_{y}.png"
        if os.path.exists(path):
            return path

        # Fetch from LTAK server
        url = f"{self.base_url}/{z}/{x}/{y}.png"
        print(f"Fetching tile: {url}")

        r = requests.get(url)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            return path

        return None
