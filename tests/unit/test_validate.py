import unittest
from src.validate import validate_raw_geojson, validate_transformed_records
from src.ingest import load_fixture_data
from src.transform import transform_geojson_to_records


class TestValidate(unittest.TestCase):
    def test_validate_raw_geojson_success(self):
        fixture_data = load_fixture_data("data/sample/usgs_sample.json")
        is_valid, errors = validate_raw_geojson(fixture_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_raw_geojson_invalid(self):
        invalid_data = {
            "type": "NotFeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "",
                    "geometry": {"type": "Point", "coordinates": [999.0, 999.0]},
                    "properties": {"time": "not-a-number"}
                }
            ]
        }
        is_valid, errors = validate_raw_geojson(invalid_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_validate_transformed_records_success(self):
        fixture_data = load_fixture_data("data/sample/usgs_sample.json")
        records = transform_geojson_to_records(fixture_data)
        is_valid, errors = validate_transformed_records(records)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
