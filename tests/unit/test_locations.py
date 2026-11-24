import unittest
from src.locations import get_monitored_locations


class TestLocations(unittest.TestCase):
    def test_locations_count_and_keys(self):
        locations = get_monitored_locations()
        self.assertEqual(len(locations), 6, "Harus terdapat 6 lokasi pemantauan")
        for loc in locations:
            self.assertIn("id", loc)
            self.assertIn("name", loc)
            self.assertIn("latitude", loc)
            self.assertIn("longitude", loc)
            self.assertIn("maxradiuskm", loc)
            self.assertTrue(-90.0 <= loc["latitude"] <= 90.0)
            self.assertTrue(-180.0 <= loc["longitude"] <= 180.0)


if __name__ == "__main__":
    unittest.main()
