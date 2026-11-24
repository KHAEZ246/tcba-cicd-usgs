"""
validate.py
Modul Data Contract & Data Validation.
Memastikan integritas struktur skema GeoJSON USGS dan nilai batas (boundary checks)
sebelum dan sesudah transformasi.
"""

import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class DataContractValidationError(Exception):
    """Exception khusus jika data melanggar data contract."""
    pass


def validate_raw_geojson(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Memvalidasi data contract dari raw response USGS GeoJSON.
    Kriteria:
    - Root objek harus memiliki key 'type' dengan nilai 'FeatureCollection'
    - 'features' harus bertipe list
    - Setiap item feature harus memiliki:
      * type == 'Feature'
      * id (string tidak kosong)
      * geometry (Point) dengan koordinat [lon, lat, depth]
      * properties (dict dengan minimal field time, mag, place)
    """
    errors: List[str] = []

    if not isinstance(payload, dict):
        return False, ["Payload bukan bertipe dictionary/JSON object."]

    if payload.get("type") != "FeatureCollection":
        errors.append(f"Root 'type' harus 'FeatureCollection', ditemukan: {payload.get('type')}")

    features = payload.get("features")
    if not isinstance(features, list):
        errors.append("Field 'features' harus bertipe list.")
        return False, errors

    for idx, feat in enumerate(features):
        prefix = f"Feature[{idx}] (id={feat.get('id', 'N/A')}):"

        if feat.get("type") != "Feature":
            errors.append(f"{prefix} type harus 'Feature'.")

        if not feat.get("id"):
            errors.append(f"{prefix} id tidak boleh kosong.")

        # Validasi Geometry
        geom = feat.get("geometry")
        if not isinstance(geom, dict):
            errors.append(f"{prefix} geometry harus bertipe dict.")
        else:
            if geom.get("type") != "Point":
                errors.append(f"{prefix} geometry.type harus 'Point'.")

            coords = geom.get("coordinates")
            if not isinstance(coords, (list, tuple)) or len(coords) < 2:
                errors.append(f"{prefix} geometry.coordinates harus berisi minimal 2 elemen [lon, lat].")
            else:
                lon, lat = coords[0], coords[1]
                if not (-180.0 <= lon <= 180.0):
                    errors.append(f"{prefix} Longitude di luar batas [-180, 180]: {lon}")
                if not (-90.0 <= lat <= 90.0):
                    errors.append(f"{prefix} Latitude di luar batas [-90, 90]: {lat}")

        # Validasi Properties
        props = feat.get("properties")
        if not isinstance(props, dict):
            errors.append(f"{prefix} properties harus bertipe dict.")
        else:
            if "time" not in props or not isinstance(props["time"], (int, float)):
                errors.append(f"{prefix} properties.time harus berupa timestamp numerik.")

            mag = props.get("mag")
            if mag is not None:
                if not isinstance(mag, (int, float)):
                    errors.append(f"{prefix} properties.mag harus numerik jika ada.")
                elif not (-2.0 <= mag <= 10.5):
                    errors.append(f"{prefix} properties.mag di luar batas logis [-2.0, 10.5]: {mag}")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_transformed_records(records: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Memvalidasi data contract dari hasil transformasi data tabular.
    Memeriksa ketersediaan kolom penting, tipe data, dan konsistensi.
    """
    errors: List[str] = []
    required_fields = ["event_id", "magnitude", "place", "event_time_utc", "latitude", "longitude", "depth_km"]

    if not isinstance(records, list):
        return False, ["Hasil transformasi harus berupa list of dictionary."]

    for idx, rec in enumerate(records):
        prefix = f"Record[{idx}] (id={rec.get('event_id', 'N/A')}):"
        for field in required_fields:
            if field not in rec:
                errors.append(f"{prefix} field wajib '{field}' hilang.")

        # Pengecekan koordinat
        lat = rec.get("latitude")
        lon = rec.get("longitude")
        if lat is not None and not (-90.0 <= lat <= 90.0):
            errors.append(f"{prefix} latitude tidak valid: {lat}")
        if lon is not None and not (-180.0 <= lon <= 180.0):
            errors.append(f"{prefix} longitude tidak valid: {lon}")

    is_valid = len(errors) == 0
    return is_valid, errors

