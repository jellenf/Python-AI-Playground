# Map Reference Development Notes

## Goal and design

The application turns a city or country name into a compact geographic reference: one overview map, a place label, coordinates, and a small feature key. The map image is generated from OpenStreetMap data and includes its standard coastline and rail detail where mapped.

The project uses Python's standard library for its HTTP server and upstream requests, with plain HTML, CSS, and JavaScript in the browser. This keeps local setup small and avoids a framework dependency for a single-page lookup tool. The layout is responsive and keeps search, map status, place details, and map attribution in one view.

## Lookup flow

1. Submitting the place form sends one request to the local `/api/map` endpoint. The page does not load a map on startup and prevents overlapping submissions.
2. The Python server geocodes the place with the OpenStreetMap Nominatim search endpoint, requesting one result.
3. The server uses those coordinates to request one static map image from the OpenStreetMap static-map service. The image is returned to the page as a data URL, so the browser does not fetch map tiles.
4. Successful results are held in a six-entry in-memory cache. A repeat search for the same normalized place reuses its result instead of contacting either upstream service again.
5. The map panel shows a readable error if the place is unknown or either upstream service is unavailable. OpenStreetMap attribution remains visible beside the map.

The local server handles requests sequentially, so only one map lookup runs at a time. Geocoding and map rendering each have request timeouts. The image response is limited to 8 MiB.

## Run locally

Use Python 3.10 or newer; no third-party packages are required.

```sh
python app.py
```

Open <http://127.0.0.1:8000>. Set `HOST` or `PORT` before starting the server to change its bind address or port. Place searches require an internet connection to reach the OpenStreetMap services.

## Verify

Run the offline unit tests with:

```sh
python -m unittest discover -s tests -v
```

The tests mock upstream map services and cover a successful lookup, request caching, unknown places, and invalid coordinates. A live search additionally depends on network access and availability of the public OpenStreetMap endpoints.