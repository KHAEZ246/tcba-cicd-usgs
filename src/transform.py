"""
transform.py
Modul untuk membersihkan, menstrukturkan, dan mentransformasikan raw data GeoJSON USGS
menjadi format data tabular yang siap dianalisis dan disimpan ke Azure Data Lake / Blob Storage.
"""

import csv
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def classify_magnitude(mag: Optional[float]) -> str:
    """Mengklasifikasikan skala kekuatan gempa bumi."""
    if mag is None:
        return "Unknown"
    if mag < 3.0:
        return "Micro"
    elif mag < 4.0:
        return "Minor"
    elif mag < 5.0:
        return "Light"
    elif mag < 6.0:
        return "Moderate"
    elif mag < 7.0:
        return "Strong"
    elif mag < 8.0:
        return "Major"
    else:
        return "Great"


def classify_depth(depth_km: Optional[float]) -> str:
    """Mengklasifikasikan kedalaman pusat gempa (hiposentrum)."""
    if depth_km is None:
        return "Unknown"
    if depth_km <= 70.0:
        return "Shallow"
    elif depth_km <= 300.0:
        return "Intermediate"
    else:
        return "Deep"


def epoch_to_iso(epoch_ms: Optional[int]) -> Optional[str]:
    """Mengonversi epoch milliseconds ke format ISO-8601 UTC."""
    if epoch_ms is None:
        return None
    try:
        dt = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def transform_geojson_to_records(raw_geojson: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Mengekstrak dan merapikan feature GeoJSON menjadi list of dictionary tabular.
    """
    features = raw_geojson.get("features", [])
    transformed_records: List[Dict[str, Any]] = []
    extraction_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for feat in features:
        feat_id = feat.get("id")
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates", [None, None, None])

        lon = coords[0] if len(coords) > 0 else None
        lat = coords[1] if len(coords) > 1 else None
        depth = coords[2] if len(coords) > 2 else None

        mag = props.get("mag")
        if mag is not None:
            mag = round(float(mag), 2)

        record = {
            "event_id": str(feat_id),
            "title": props.get("title", ""),
            "place": props.get("place", "Unknown Location"),
            "magnitude": mag,
            "magnitude_type": props.get("magType", "unknown"),
            "magnitude_class": classify_magnitude(mag),
            "event_time_epoch": props.get("time"),
            "event_time_utc": epoch_to_iso(props.get("time")),
            "updated_time_utc": epoch_to_iso(props.get("updated")),
            "latitude": lat,
            "longitude": lon,
            "depth_km": depth,
            "depth_class": classify_depth(depth),
            "significance": props.get("sig", 0),
            "tsunami_alert": bool(props.get("tsunami", 0)),
            "alert_level": props.get("alert") or "none",
            "status": props.get("status", "automatic"),
            "usgs_url": props.get("url", ""),
            "location_tag_id": props.get("_location_id", "global"),
            "location_tag_name": props.get("_location_name", "Global Search"),
            "transformed_at_utc": extraction_time
        }
        transformed_records.append(record)

    logger.info("Berhasil mentransformasi %d record dari GeoJSON", len(transformed_records))
    return transformed_records


def save_processed_data(records: List[Dict[str, Any]], output_basepath: str) -> Dict[str, str]:
    """
    Menyimpan hasil data transformasi ke CSV dan JSON di data/processed/.
    """
    os.makedirs(os.path.dirname(output_basepath), exist_ok=True)
    csv_path = f"{output_basepath}.csv"
    json_path = f"{output_basepath}.json"

    # Simpan ke JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Simpan ke CSV
    if records:
        fieldnames = list(records[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
    else:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            f.write("")

    logger.info("Data processed disimpan ke:\n  - CSV: %s\n  - JSON: %s", csv_path, json_path)
    return {"csv": csv_path, "json": json_path}

