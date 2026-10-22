from __future__ import annotations

import json
import math
import os
import time

from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Optional

import certifi
import requests


NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)

HEADERS = {
    "User-Agent": "CropConn8t/1.0"
}

TIMEOUT = 20

CACHE_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "geocode_cache.json"
)

CACHE_LOCK = Lock()

LAST_REQUEST = 0.0


# =========================================================
# CACHE
# =========================================================

def _load_cache() -> dict:
    try:
        if not CACHE_FILE.exists():
            return {}

        with CACHE_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception as error:
        print(
            "Geocode cache read failed:",
            error,
        )

    return {}


def _save_cache(
    data: dict,
) -> None:
    try:
        CACHE_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = CACHE_FILE.with_suffix(
            ".tmp"
        )

        with temporary.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        temporary.replace(
            CACHE_FILE
        )

    except Exception as error:
        print(
            "Geocode cache save failed:",
            error,
        )


def _cache_key(
    query: str,
) -> str:
    return " ".join(
        query.strip()
        .lower()
        .split()
    )


# =========================================================
# REQUEST THROTTLE
# =========================================================

def _throttle() -> None:
    global LAST_REQUEST

    with CACHE_LOCK:
        now = time.monotonic()

        wait = (
            1.05
            - (now - LAST_REQUEST)
        )

        if wait > 0:
            time.sleep(wait)

        LAST_REQUEST = time.monotonic()


# =========================================================
# SSL / CERTIFICATE
# =========================================================

def _certificate_path():
    """
    Return a valid certifi bundle if available.

    If certifi is broken, fall back to True so requests
    uses the system/default certificate handling.
    """

    try:
        certificate = certifi.where()

        if (
            certificate
            and os.path.isfile(
                certificate
            )
        ):
            return certificate

    except Exception as error:
        print(
            "certifi lookup failed:",
            error,
        )

    return True


# =========================================================
# GEOCODING
# =========================================================

@lru_cache(maxsize=2000)
def geocode(
    query: str,
) -> Optional[dict]:

    clean_query = " ".join(
        query.strip().split()
    )

    if not clean_query:
        return None

    key = _cache_key(
        clean_query
    )

    cache = _load_cache()

    if key in cache:
        return cache[key]

    _throttle()

    verify = _certificate_path()

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1,
                "countrycodes": "in",
                "q": clean_query,
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=verify,
        )

        response.raise_for_status()

        results = response.json()

        if not results:
            cache[key] = None
            _save_cache(cache)
            return None

        item = results[0]

        result = {
            "latitude": float(
                item["lat"]
            ),
            "longitude": float(
                item["lon"]
            ),
            "display_name": item.get(
                "display_name"
            ),
            "address": item.get(
                "address",
                {},
            ),
        }

        cache[key] = result
        _save_cache(cache)

        return result

    except requests.exceptions.SSLError as error:

        print(
            f"SSL error while geocoding "
            f"'{clean_query}': {error}"
        )

        return None

    except requests.exceptions.RequestException as error:

        print(
            f"Geocoding request failed "
            f"for '{clean_query}': {error}"
        )

        return None

    except Exception as error:

        print(
            f"Geocoding failed "
            f"for '{clean_query}': {error}"
        )

        return None


# =========================================================
# DISTANCE
# =========================================================

def distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:

    earth_radius = 6371.0

    lat1_rad = math.radians(
        lat1
    )

    lat2_rad = math.radians(
        lat2
    )

    delta_lat = math.radians(
        lat2 - lat1
    )

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(
            delta_lat / 2
        ) ** 2
        +
        math.cos(
            lat1_rad
        )
        *
        math.cos(
            lat2_rad
        )
        *
        math.sin(
            delta_lon / 2
        ) ** 2
    )

    c = (
        2
        * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a),
        )
    )

    return round(
        earth_radius * c,
        1,
    )


# =========================================================
# MARKET LOCATION
# =========================================================

def market_location(
    market_name: str,
    district_name: Optional[str] = None,
) -> Optional[dict]:

    clean_market = (
        market_name or ""
    ).strip()

    for suffix in (
        " APMC",
        " Market",
    ):
        if clean_market.endswith(
            suffix
        ):
            clean_market = (
                clean_market[
                    :-len(suffix)
                ].strip()
            )

    pieces = [
        clean_market
    ]

    if district_name:
        pieces.append(
            district_name
        )

    pieces.extend(
        [
            "Telangana",
            "India",
        ]
    )

    return geocode(
        ", ".join(pieces)
    )