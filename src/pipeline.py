"""
pipeline.py
Main Orchestrator untuk batch data pipeline USGS Earthquake.
Mengorkestrasikan:
1. Ingest (6 Lokasi Seismik atau Fixture Sample)
2. Validasi Data Contract (Raw GeoJSON)
3. Transformasi ke format terstruktur (CSV & JSON)
4. Validasi Data Contract (Transformed Records)
5. Simpan ke direktori data/
6. Upload ke Azure Blob Storage

Mendukung eksekusi:
- Fixture Mode (Offline / CI test): python -m src.pipeline fixture
- Live Mode:                       python -m src.pipeline
- Live + Upload Azure:             python -m src.pipeline --upload --hours 6
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List

from src.locations import get_monitored_locations
from src.ingest import fetch_batch_all_locations, load_fixture_data, save_raw_data
from src.validate import validate_raw_geojson, validate_transformed_records, DataContractValidationError
from src.transform import transform_geojson_to_records, save_processed_data
from src.upload_blob import upload_file_to_blob

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline(
    mode: str = "live",
    hours_ago: int = 6,
    upload: bool = False,
    fixture_path: str = "data/sample/usgs_sample.json"
) -> Dict[str, Any]:
    """
    Menjalankan seluruh alur end-to-end data pipeline.
    """
    logger.info("=== Memulai Pipeline USGS Earthquake (Mode: %s) ===", mode.upper())
    timestamp_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # 1. Ingestion Stage
    if mode == "fixture":
        logger.info("[Tahap 1/5] Ingest: Memuat data dari fixture sample '%s'", fixture_path)
        raw_data = load_fixture_data(fixture_path)
        raw_filepath = f"data/raw/usgs_fixture_raw_{timestamp_tag}.json"
    else:
        locations = get_monitored_locations()
        logger.info("[Tahap 1/5] Ingest: Menarik data batch dari %d lokasi pemantauan USGS (Window: %d jam terakhir)", len(locations), hours_ago)
        raw_data = fetch_batch_all_locations(locations=locations, hours_ago=hours_ago)
        raw_filepath = f"data/raw/usgs_batch_raw_{timestamp_tag}.json"

    # Simpan raw data
    save_raw_data(raw_data, raw_filepath)

    # 2. Validation Stage (Raw Data Contract)
    logger.info("[Tahap 2/5] Validasi: Memeriksa Data Contract pada Raw GeoJSON")
    raw_valid, raw_errors = validate_raw_geojson(raw_data)
    if not raw_valid:
        error_msg = f"Data Contract Violation pada Raw GeoJSON ({len(raw_errors)} error):\n" + "\n".join(raw_errors[:5])
        logger.error(error_msg)
        raise DataContractValidationError(error_msg)
    logger.info("Raw GeoJSON valid. Lulus data contract.")

    # 3. Transformation Stage
    logger.info("[Tahap 3/5] Transformasi: Mengonversi GeoJSON ke structured tabular records")
    transformed_records = transform_geojson_to_records(raw_data)

    # 4. Validation Stage (Transformed Data Contract)
    logger.info("[Tahap 4/5] Validasi: Memeriksa Data Contract pada Transformed Records")
    trans_valid, trans_errors = validate_transformed_records(transformed_records)
    if not trans_valid:
        error_msg = f"Data Contract Violation pada Transformed Records ({len(trans_errors)} error):\n" + "\n".join(trans_errors[:5])
        logger.error(error_msg)
        raise DataContractValidationError(error_msg)
    logger.info("Transformed records valid. Lulus data contract.")

    # Simpan data hasil transformasi
    processed_basepath = f"data/processed/usgs_processed_{timestamp_tag}"
    processed_files = save_processed_data(transformed_records, processed_basepath)

    # 5. Azure Storage Upload Stage
    upload_results = []
    if upload or mode == "live":
        logger.info("[Tahap 5/5] Storage: Mengunggah data ke Azure Blob Storage")
        files_to_upload = [raw_filepath, processed_files["csv"], processed_files["json"]]
        for fpath in files_to_upload:
            res = upload_file_to_blob(fpath)
            upload_results.append(res)
    else:
        logger.info("[Tahap 5/5] Storage: Upload dilewati (bisa diaktifkan dengan opsi --upload)")

    summary = {
        "status": "success",
        "mode": mode,
        "raw_file": raw_filepath,
        "processed_files": processed_files,
        "total_events": len(transformed_records),
        "uploads": upload_results
    }

    logger.info("=== Pipeline Selesai Sukses! Total Gempa Diproses: %d ===", len(transformed_records))
    return summary


def main():
    parser = argparse.ArgumentParser(description="USGS Earthquake Batch Data Pipeline")
    parser.add_argument(
        "action",
        nargs="?",
        default="run",
        choices=["run", "fixture"],
        help="Mode eksekusi: 'run' untuk live batch query, 'fixture' untuk validasi fixture CI"
    )
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="Flag alternatif untuk menjalankan mode fixture"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=6,
        help="Window waktu dalam jam untuk data batch USGS (default: 6 jam)"
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Mengunggah hasil ke Azure Blob Storage"
    )
    parser.add_argument(
        "--fixture-path",
        type=str,
        default="data/sample/usgs_sample.json",
        help="Path ke file sample fixture"
    )

    args = parser.parse_args()
    mode = "fixture" if (args.action == "fixture" or args.fixture) else "live"

    try:
        run_pipeline(
            mode=mode,
            hours_ago=args.hours,
            upload=args.upload,
            fixture_path=args.fixture_path
        )
    except Exception as e:
        logger.error("Pipeline gagal dieksekusi: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

