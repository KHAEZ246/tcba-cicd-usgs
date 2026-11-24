"""
locations.py
Konfigurasi lokasi pemantauan gempa (USGS Earthquake Monitoring).
Mendefinisikan 6 zona seismik aktif dunia untuk batch ingestion.
"""

from typing import List, Dict, Any

# 6 Lokasi Pemantauan Gempa Bumi (Ring of Fire & Zona Seismik Utama)
MONITORED_LOCATIONS: List[Dict[str, Any]] = [
    {
        "id": "indonesia_sumatra",
        "name": "Indonesia (Sumatra & Java)",
        "latitude": -0.7893,
        "longitude": 102.8451,
        "maxradiuskm": 1000,
        "minmagnitude": 2.5
    },
    {
        "id": "japan_honshu",
        "name": "Japan (Honshu Region)",
        "latitude": 36.2048,
        "longitude": 138.2529,
        "maxradiuskm": 800,
        "minmagnitude": 2.5
    },
    {
        "id": "us_california",
        "name": "United States (California San Andreas)",
        "latitude": 36.7783,
        "longitude": -119.4179,
        "maxradiuskm": 600,
        "minmagnitude": 2.0
    },
    {
        "id": "chile_coast",
        "name": "Chile (Subduction Zone)",
        "latitude": -35.6751,
        "longitude": -71.5430,
        "maxradiuskm": 900,
        "minmagnitude": 3.0
    },
    {
        "id": "philippines_trench",
        "name": "Philippines (Trench Region)",
        "latitude": 12.8797,
        "longitude": 121.7740,
        "maxradiuskm": 700,
        "minmagnitude": 2.5
    },
    {
        "id": "turkey_fault",
        "name": "Turkey (Anatolian Fault)",
        "latitude": 38.9637,
        "longitude": 35.2433,
        "maxradiuskm": 600,
        "minmagnitude": 2.5
    }
]


def get_monitored_locations() -> List[Dict[str, Any]]:
    """Mengembalikan daftar 6 lokasi yang dipantau."""
    return MONITORED_LOCATIONS

