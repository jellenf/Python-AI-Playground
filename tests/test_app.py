import unittest
from unittest.mock import patch

from app import MapLookupError, _lookup_cached


class MapLookupTests(unittest.TestCase):
    def setUp(self):
        _lookup_cached.cache_clear()

    def tearDown(self):
        _lookup_cached.cache_clear()

    @patch("app.fetch_map_image", return_value=("image/png", b"map-bytes"))
    @patch("app.fetch_json", return_value=[{"lat": "55.6761", "lon": "12.5683", "display_name": "Copenhagen, Denmark"}])
    def test_lookup_geocodes_once_and_returns_a_map(self, fetch_json, fetch_map_image):
        result = _lookup_cached("copenhagen, denmark")

        self.assertEqual(result["name"], "Copenhagen")
        self.assertEqual(result["region"], "Denmark")
        self.assertEqual(result["coordinates"], {"lat": 55.6761, "lon": 12.5683})
        self.assertTrue(result["image"].startswith("data:image/png;base64,"))
        fetch_json.assert_called_once()
        fetch_map_image.assert_called_once()

    @patch("app.fetch_map_image", return_value=("image/png", b"map-bytes"))
    @patch("app.fetch_json", return_value=[{"lat": "55.6761", "lon": "12.5683", "display_name": "Copenhagen, Denmark"}])
    def test_repeated_lookup_uses_cached_result(self, fetch_json, fetch_map_image):
        first = _lookup_cached("copenhagen, denmark")
        second = _lookup_cached("copenhagen, denmark")

        self.assertEqual(first, second)
        fetch_json.assert_called_once()
        fetch_map_image.assert_called_once()

    @patch("app.fetch_json", return_value=[])
    def test_unknown_place_returns_a_clear_error(self, fetch_json):
        with self.assertRaisesRegex(MapLookupError, "No place found"):
            _lookup_cached("somewhere unknown")

    @patch("app.fetch_json", return_value=[{"lat": "999", "lon": "12", "display_name": "Invalid"}])
    def test_invalid_coordinates_are_rejected(self, fetch_json):
        with self.assertRaisesRegex(MapLookupError, "invalid location"):
            _lookup_cached("invalid coordinates")


if __name__ == "__main__":
    unittest.main()