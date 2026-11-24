import os
import unittest
from src.pipeline import run_pipeline


class TestPipelineIntegration(unittest.TestCase):
    def test_pipeline_fixture_end_to_end(self):
        result = run_pipeline(mode="fixture", fixture_path="data/sample/usgs_sample.json", upload=False)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_events"], 6)
        self.assertTrue(os.path.exists(result["raw_file"]))
        self.assertTrue(os.path.exists(result["processed_files"]["csv"]))
        self.assertTrue(os.path.exists(result["processed_files"]["json"]))

        # Bersihkan file output pengujian
        if os.path.exists(result["raw_file"]):
            os.remove(result["raw_file"])
        if os.path.exists(result["processed_files"]["csv"]):
            os.remove(result["processed_files"]["csv"])
        if os.path.exists(result["processed_files"]["json"]):
            os.remove(result["processed_files"]["json"])


if __name__ == "__main__":
    unittest.main()
