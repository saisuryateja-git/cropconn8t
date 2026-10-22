"""Agmarknet API integration."""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Optional
import requests

BASE_URL = "https://api.agmarknet.gov.in/v1"
STATE_ID = 32
STATE_NAME = "Telangana"
TIMEOUT = 45
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 CropConn8t/1.0",
    "Referer": "https://agmarknet.gov.in/",
    "Origin": "https://agmarknet.gov.in",
}

class AgmarknetError(Exception):
    pass


def _get(path, params=None):
    url = f"{BASE_URL}{path}"
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as exc:
        raise AgmarknetError(f"Agmarknet request timed out: {url}") from exc
    except requests.exceptions.RequestException as exc:
        raise AgmarknetError(f"Agmarknet request failed: {exc}") from exc
    except ValueError as exc:
        raise AgmarknetError("Agmarknet returned invalid JSON") from exc


@lru_cache(maxsize=1)
def get_filters():
    return _get("/daily-price-arrival/filters")


def _filter_list(key):
    data = get_filters().get("data", {})
    return data.get(key, []) if isinstance(data, dict) else []


def get_commodities():
    return _filter_list("cmdt_data")


def get_states():
    return _filter_list("state_data")


def get_districts(state_name="Telangana"):
    state_id = None
    for s in get_states():
        if str(s.get("state_name", "")).strip().lower() == state_name.strip().lower():
            state_id = s.get("state_id")
            break
    if state_id is None:
        return []
    result = []
    seen = set()
    for d in _filter_list("district_data"):
        try:
            sid = int(d.get("state_id"))
        except (TypeError, ValueError):
            continue
        if sid != int(state_id):
            continue
        did = d.get("id")
        if did in seen:
            continue
        seen.add(did)
        result.append({
            "district_id": did,
            "district_name": d.get("district_name"),
            "state_id": sid,
        })
    return sorted(result, key=lambda x: x.get("district_name") or "")


def get_markets(state_name="Telangana"):
    state_id = None
    for s in get_states():
        if str(s.get("state_name", "")).strip().lower() == state_name.strip().lower():
            state_id = s.get("state_id")
            break
    if state_id is None:
        return []
    out = []
    seen = set()
    for m in _filter_list("market_data"):
        try:
            sid = int(m.get("state_id"))
        except (TypeError, ValueError):
            continue
        if sid != int(state_id):
            continue
        mid = m.get("id")
        if mid in seen:
            continue
        seen.add(mid)
        out.append({
            "market_id": mid,
            "market_name": m.get("mkt_name"),
            "state_id": sid,
            "district_id": m.get("district_id"),
        })
    return out


# Verified IDs from the project testing data, used as fallbacks.
FALLBACK_COMMODITY_IDS = {
    "rice": 3,
    "groundnut": 10,
    "cotton": 15,
    "banana": 19,
    "maize": 4,
}

ALIASES = {
    "maize": ["maize", "maize(corn)", "corn"],
    "rice": ["rice"],
    "cotton": ["cotton", "cotton (unginned)", "cotton seed"],
    "groundnut": ["groundnut", "ground nut", "groundnut pods"],
    "banana": ["banana"],
}


def get_commodity_id(crop_name: str) -> Optional[int]:
    wanted = crop_name.strip().lower()
    aliases = ALIASES.get(wanted, [wanted])
    for item in get_commodities():
        name = str(item.get("cmdt_name", "")).strip().lower()
        if name in aliases:
            try:
                return int(item["cmdt_id"])
            except (TypeError, ValueError):
                pass
    for item in get_commodities():
        name = str(item.get("cmdt_name", "")).strip().lower()
        if wanted in name:
            try:
                return int(item["cmdt_id"])
            except (TypeError, ValueError):
                pass
    return FALLBACK_COMMODITY_IDS.get(wanted)


def get_month_prices(crop_name: str, year: Optional[int] = None, month: Optional[int] = None):
    if year is None or month is None:
        now = datetime.now()
        year, month = now.year, now.month
    commodity_id = get_commodity_id(crop_name)
    if commodity_id is None:
        raise AgmarknetError(f"Commodity '{crop_name}' was not found in Agmarknet")
    return _get(
        "/prices-and-arrivals/date-wise/specific-commodity",
        params={
            "year": year,
            "month": month,
            "stateId": STATE_ID,
            "commodityId": commodity_id,
            "includeExcel": "false",
        },
    )


def parse_market_records(crop_name: str, raw_response: dict):
    records = []
    for market in raw_response.get("markets", []) or []:
        market_name = market.get("marketName") or market.get("mkt_name") or market.get("market") or "Unknown Market"
        for date_block in market.get("dates", []) or []:
            arrival_date = date_block.get("arrivalDate") or date_block.get("date")
            for row in date_block.get("data", []) or []:
                def f(key):
                    try:
                        return float(row.get(key))
                    except (TypeError, ValueError):
                        return None
                modal = f("modalPrice")
                if modal is None:
                    continue
                records.append({
                    "market": market_name,
                    "date": arrival_date,
                    "variety": row.get("variety", "Unknown"),
                    "arrivals": f("arrivals") or 0,
                    "min_price": f("minimumPrice"),
                    "max_price": f("maximumPrice"),
                    "modal_price": modal,
                })
    return records


def latest_per_market(records):
    grouped = {}
    for record in records:
        key = record["market"]
        old = grouped.get(key)
        if old is None:
            grouped[key] = record
            continue
        try:
            old_dt = datetime.strptime(old.get("date", ""), "%d/%m/%Y")
            new_dt = datetime.strptime(record.get("date", ""), "%d/%m/%Y")
            if new_dt > old_dt:
                grouped[key] = record
        except ValueError:
            if str(record.get("date", "")) > str(old.get("date", "")):
                grouped[key] = record
    return list(grouped.values())


def general_pricing(crop_names=None):
    crop_names = crop_names or ["maize", "rice", "cotton", "groundnut", "banana"]
    results = []
    for crop in crop_names:
        try:
            latest = latest_per_market(parse_market_records(crop, get_month_prices(crop)))
            prices = [x["modal_price"] for x in latest if x.get("modal_price") is not None]
            if not prices:
                results.append({"crop": crop, "average_price": None, "highest_price": None, "highest_market": None, "highest_date": None, "record_count": 0, "status": "No current data"})
                continue
            highest = max(latest, key=lambda x: x.get("modal_price") or 0)
            results.append({
                "crop": crop,
                "average_price": round(sum(prices) / len(prices), 2),
                "highest_price": highest.get("modal_price"),
                "highest_market": highest.get("market"),
                "highest_date": highest.get("date"),
                "record_count": len(latest),
                "status": "Available",
            })
        except Exception as exc:
            results.append({"crop": crop, "average_price": None, "highest_price": None, "highest_market": None, "highest_date": None, "record_count": 0, "status": str(exc)})
    return results
