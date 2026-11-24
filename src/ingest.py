"""
ingest.py
Modul untuk melakukan pengambilan data gempa dari USGS API (Batch Ingestion).
Mendukung pengambilan data live (HTTP) dan fixture mode (offline untuk CI/testing).
"""

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def fetch_usgs_events(
    latitude: float,
    longitude: float,
    maxradiuskm: float,
    starttime: str,
    endtime: str,
    minmagnitude: float = 2.0,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Mengambil data gempa bumi dari API USGS berdasarkan lokasi koordinat & radius.
    Format waktu ISO-8601 (misal: 2026-11-24T00:00:00).
    """
    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "latitude": latitude,
        "longitude": longitude,
        "maxradiuskm": maxradiuskm,
        "minmagnitude": minmagnitude,
        "orderby": "time"
    }

    logger.info("Mengirim request ke USGS API: lat=%s, lon=%s, radius=%skm", latitude, longitude, maxradiuskm)
    response = requests.get(USGS_API_URL, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    logger.info("Berhasil mengambil %d event dari USGS", len(data.get("features", [])))
    return data


def fetch_batch_all_locations(
    locations: List[Dict[str, Any]],
    hours_ago: int = 6,
    output_dir: str = "data/raw"
) -> Dict[str, Any]:
    """
    Melakukan batch ingestion untuk seluruh lokasi terdaftar untuk window waktu tertentu (default 6 jam).
    Menghasilkan dictionary gabungan dan menyimpan payload raw ke disk.
    """
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours_ago)
    starttime_str = start.strftime("%Y-%m-%dT%H:%M:%S")
    endtime_str = now.strftime("%Y-%m-%dT%H:%M:%S")

    all_features = []
    location_summaries = []

    for loc in locations:
        try:
            raw_result = fetch_usgs_events(
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                maxradiuskm=loc["maxradiuskm"],
                starttime=starttime_str,
                endtime=endtime_str,
                minmagnitude=loc.get("minmagnitude", 2.0)
            )
            features = raw_result.get("features", [])
            # Tandai metadata lokasi asal pada tiap feature properties
            for feat in features:
                if "properties" in feat:
                    feat["properties"]["_location_id"] = loc["id"]
                    feat["properties"]["_location_name"] = loc["name"]
            all_features.extend(features)
            location_summaries.append({"location_id": loc["id"], "count": len(features)})
        except Exception as e:
            logger.error("Gagal mengambil data untuk lokasi %s: %s", loc["name"], e)

    # Hilangkan duplikasi event jika ada event yang masuk dalam 2 radius
    unique_features = {}
    for feat in all_features:
        feat_id = feat.get("id")
        if feat_id and feat_id not in unique_features:
            unique_features[feat_id] = feat

    combined_payload = {
        "type": "FeatureCollection",
        "metadata": {
            "generated": int(now.timestamp() * 1000),
            "url": USGS_API_URL,
            "title": f"USGS Batch Ingestion (Past {hours_ago} Hours)",
            "status": 200,
            "api": "1.14.1",
            "count": len(unique_features),
            "window_start": starttime_str,
            "window_end": endtime_str,
            "locations_queried": location_summaries
        },
        "features": list(unique_features.values())
    }

    return combined_payload


def save_raw_data(data: Dict[str, Any], filepath: str) -> str:
    """Menyimpan data raw JSON ke file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Data raw tersimpan di: %s", filepath)
    return filepath


def load_fixture_data(fixture_path: str = "data/sample/usgs_sample.json") -> Dict[str, Any]:
    """Memuat data sample/fixture untuk keperluan testing offline & CI."""
    if not os.path.exists(fixture_path):
        raise FileNotFoundError(f"Fixture data tidak ditemukan di: {fixture_path}")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)

