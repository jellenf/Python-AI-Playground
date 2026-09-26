import base64
import json
import os
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
USER_AGENT = "MapReferencePlayground/1.0 (local development app)"
MAX_IMAGE_BYTES = 8 * 1024 * 1024


class MapLookupError(Exception):
    """An expected issue while retrieving place or map data."""


def fetch_json(url):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=12) as response:
            return json.loads(response.read(2 * 1024 * 1024))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise MapLookupError("The place service could not be reached. Check your connection and try again.") from error


def fetch_map_image(url):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=20) as response:
            content_type = response.headers.get("Content-Type", "")
            image = response.read(MAX_IMAGE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as error:
        raise MapLookupError("The map image could not be reached. Check your connection and try again.") from error

    if not content_type.startswith("image/") or len(image) > MAX_IMAGE_BYTES:
        raise MapLookupError("The map service returned an invalid image. Please try another place.")
    return content_type.split(";", 1)[0], image


@lru_cache(maxsize=6)
def _lookup_cached(query):
    geocode_url = "https://nominatim.openstreetmap.org/search?" + urlencode(
        {"q": query, "format": "jsonv2", "limit": 1}
    )
    places = fetch_json(geocode_url)
    if not places:
        raise MapLookupError("No place found. Try a city or country name.")

    try:
        place = places[0]
        latitude = float(place["lat"])
        longitude = float(place["lon"])
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError
    except (IndexError, KeyError, TypeError, ValueError) as error:
        raise MapLookupError("The place service returned an invalid location. Please try again.") from error

    image_url = "https://staticmap.openstreetmap.de/staticmap.php?" + urlencode(
        {
            "center": f"{latitude},{longitude}",
            "zoom": 11,
            "size": "1000x650",
            "maptype": "mapnik",
            "markers": f"{latitude},{longitude},red-pushpin",
        }
    )
    content_type, image = fetch_map_image(image_url)
    display_name = place.get("display_name", query).split(",")

    return {
        "name": display_name[0].strip(),
        "region": ", ".join(part.strip() for part in display_name[1:3] if part.strip()),
        "coordinates": {"lat": latitude, "lon": longitude},
        "image": f"data:{content_type};base64,{base64.b64encode(image).decode('ascii')}",
    }


class MapRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path)
        if path.path == "/":
            return self.serve_file("templates/index.html", "text/html; charset=utf-8")
        if path.path == "/static/styles.css":
            return self.serve_file("static/styles.css", "text/css; charset=utf-8")
        if path.path == "/static/app.js":
            return self.serve_file("static/app.js", "text/javascript; charset=utf-8")
        if path.path == "/api/map":
            return self.serve_map(parse_qs(path.query).get("q", [""])[0])
        return self.send_json(404, {"error": "Not found."})

    def serve_file(self, relative_path, content_type):
        content = (ROOT / relative_path).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def serve_map(self, query):
        query = " ".join(query.split())
        if not query or len(query) > 120:
            return self.send_json(400, {"error": "Enter a place name up to 120 characters."})
        try:
            return self.send_json(200, _lookup_cached(query.casefold()))
        except MapLookupError as error:
            status = 404 if str(error).startswith("No place found") else 502
            return self.send_json(status, {"error": str(error)})

    def send_json(self, status, payload):
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string, *args):
        print(f"{self.log_date_time_string()} {format_string % args}")


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer((host, port), MapRequestHandler)
    print(f"Map reference running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMap reference stopped.")
    finally:
        server.server_close()