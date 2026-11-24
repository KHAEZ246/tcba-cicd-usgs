import unittest
from src.transform import classify_magnitude, classify_depth, epoch_to_iso, transform_geojson_to_records
from src.ingest import load_fixture_data


class TestTransform(unittest.TestCase):
    def test_classify_magnitude(self):
        self.assertEqual(classify_magnitude(None), "Unknown")
        self.assertEqual(classify_magnitude(2.5), "Micro")
        self.assertEqual(classify_magnitude(3.5), "Minor")
        self.assertEqual(classify_magnitude(4.5), "Light")
        self.assertEqual(classify_magnitude(5.5), "Moderate")
        self.assertEqual(classify_magnitude(6.5), "Strong")
        self.assertEqual(classify_magnitude(7.5), "Major")
        self.assertEqual(classify_magnitude(8.5), "Great")

    def test_classify_depth(self):
        self.assertEqual(classify_depth(None), "Unknown")
        self.assertEqual(classify_depth(10.0), "Shallow")
        self.assertEqual(classify_depth(70.0), "Shallow")
        self.assertEqual(classify_depth(150.0), "Intermediate")
        self.assertEqual(classify_depth(350.0), "Deep")

    def test_epoch_to_iso(self):
        self.assertIsNone(epoch_to_iso(None))
        iso_time = epoch_to_iso(1732450000000)
        self.assertIsNotNone(iso_time)
        self.assertIn("T", iso_time)
        self.assertTrue(iso_time.endswith("Z"))

    def test_transform_fixture(self):
        fixture_data = load_fixture_data("data/sample/usgs_sample.json")
        records = transform_geojson_to_records(fixture_data)
        self.assertEqual(len(records), 6)
        first = records[0]
        self.assertIn("event_id", first)
        self.assertIn("magnitude", first)
        self.assertIn("depth_km", first)
        self.assertIn("latitude", first)
        self.assertIn("longitude", first)


if __name__ == "__main__":
    unittest.main()
