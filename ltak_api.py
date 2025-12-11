import requests

class LTAKApi:
    def __init__(self, server):
        self.server = server.rstrip("/")

    def get_markers(self):
        return requests.get(f"{self.server}/markers").json()

    def update_position(self, lat, lon):
        return requests.post(f"{self.server}/position", json={
            "lat": lat,
            "lon": lon,
        }).json()
