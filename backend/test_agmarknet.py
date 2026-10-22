import requests
from datetime import datetime
from functools import lru_cache
from typing import Any


BASE_URL = "https://api.agmarknet.gov.in/v1"

STATE_ID = 32
STATE_NAME = "Telangana"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://agmarknet.gov.in",
    "Referer": "https://agmarknet.gov.in/",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
}

TIMEOUT = 20


class AgmarknetError(Exception):
    pass


def _get(path: str, params: dict | None = None) -> Any:
    url = f"{BASE_URL}{path}"

    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout as error:
        raise AgmarknetError(
            f"Agmarknet request timed out: {url}"
        ) from error

    except requests.exceptions.RequestException as error:
        raise AgmarknetError(
            f"Agmarknet request failed: {error}"
        ) from error

    except ValueError as error:
        raise AgmarknetError(
            "Agmarknet returned invalid JSON."
        ) from error


# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------

@lru_cache(maxsize=1)
def get_filters() -> dict:
    return _get("/daily-price-arrival/filters")


def _filter_data(key: str) -> list:
    data = get_filters()

    return data.get("data", {}).get(key, []) or []


# ---------------------------------------------------------
# COMMODITIES
# ---------------------------------------------------------

@lru_cache(maxsize=100)
def get_commodity_id(crop_name: str) -> int | None:
    """
    Dynamically finds the Agmarknet commodity ID.

    This removes the old CROP_IDS problem completely.
    """

    wanted = crop_name.strip().lower()

    commodities = _filter_data("cmdt_data")

    # Exact match first
    for commodity in commodities:
        name = str(
            commodity.get("cmdt_name", "")
        ).strip().lower()

        if name == wanted:
            return int(commodity["cmdt_id"])

    # Common aliases
    aliases = {
        "maize": [
            "maize",
            "maize(corn)",
            "corn",
        ],
        "rice": [
            "rice",
        ],
        "cotton": [
            "cotton",
            "cotton seed",
        ],
        "groundnut": [
            "groundnut",
            "ground nut",
            "groundnut pods",
        ],
    }

    possible_names = aliases.get(wanted, [wanted])

    for commodity in commodities:
        name = str(
            commodity.get("cmdt_name", "")
        ).strip().lower()

        if name in possible_names:
            return int(commodity["cmdt_id"])

    # Partial match as final fallback
    for commodity in commodities:
        name = str(
            commodity.get("cmdt_name", "")
        ).strip().lower()

        if wanted in name or name in wanted:
            try:
                return int(commodity["cmdt_id"])
            except Exception:
                pass

    return None


# ---------------------------------------------------------
# COMMODITY LIST
# ---------------------------------------------------------

def get_commodities() -> list:
    return _filter_data("cmdt_data")


# ---------------------------------------------------------
# STATES
# ---------------------------------------------------------

def get_states() -> list:
    return _filter_data("state_data")


# ---------------------------------------------------------
# DISTRICTS
# ---------------------------------------------------------

def get_districts(state_name: str = STATE_NAME) -> list:
    states = get_states()

    state_id = None

    for state in states:
        name = str(
            state.get("state_name", "")
        ).strip().lower()

        if name == state_name.strip().lower():
            state_id = state.get("state_id")
            break

    if state_id is None:
        return []

    districts = _filter_data("district_data")

    result = []

    for district in districts:
        try:
            district_state_id = int(
                district.get("state_id")
            )
        except (TypeError, ValueError):
            continue

        if district_state_id == int(state_id):
            result.append({
                "district_id": district.get("id"),
                "district_name": district.get("district_name"),
                "state_id": district_state_id,
            })

    # Remove duplicates
    unique = {}

    for item in result:
        unique[item["district_id"]] = item

    return sorted(
        unique.values(),
        key=lambda x: x["district_name"] or ""
    )


# ---------------------------------------------------------
# MARKETS
# ---------------------------------------------------------

def get_markets(state_name: str = STATE_NAME) -> list:
    states = get_states()

    state_id = None

    for state in states:
        if (
            str(state.get("state_name", "")).strip().lower()
            == state_name.strip().lower()
        ):
            state_id = state.get("state_id")
            break

    if state_id is None:
        return []

    markets = _filter_data("market_data")

    result = []

    for market in markets:
        try:
            market_state_id = int(
                market.get("state_id")
            )
        except (TypeError, ValueError):
            continue

        if market_state_id == int(state_id):
            result.append({
                "market_id": market.get("id"),
                "market_name": market.get("mkt_name"),
                "state_id": market_state_id,
                "district_id": market.get("district_id"),
            })

    return result


# ---------------------------------------------------------
# DATE-WISE COMMODITY REPORT
# ---------------------------------------------------------

def get_month_prices(
    crop_name: str,
    year: int | None = None,
    month: int | None = None,
) -> dict:

    if year is None or month is None:
        now = datetime.now()

        year = now.year
        month = now.month

    commodity_id = get_commodity_id(crop_name)

    if commodity_id is None:
        raise AgmarknetError(
            f"Commodity '{crop_name}' was not found in Agmarknet."
        )

    params = {
        "year": year,
        "month": month,
        "stateId": STATE_ID,
        "commodityId": commodity_id,
        "includeExcel": "false",
    }

    return _get(
        "/prices-and-arrivals/date-wise/specific-commodity",
        params=params,
    )


# ---------------------------------------------------------
# PARSE MARKET DATA
# ---------------------------------------------------------

def parse_market_records(
    crop_name: str,
    raw_response: dict,
) -> list[dict]:

    markets = raw_response.get("markets", [])

    records = []

    for market in markets:

        market_name = (
            market.get("marketName")
            or market.get("mkt_name")
            or market.get("market")
            or "Unknown Market"
        )

        dates = market.get("dates", [])

        for date_block in dates:

            arrival_date = (
                date_block.get("arrivalDate")
                or date_block.get("date")
            )

            data_rows = date_block.get("data", [])

            for row in data_rows:

                try:
                    min_price = float(
                        row.get("minimumPrice")
                    )
                except (TypeError, ValueError):
                    min_price = None

                try:
                    max_price = float(
                        row.get("maximumPrice")
                    )
                except (TypeError, ValueError):
                    max_price = None

                try:
                    modal_price = float(
                        row.get("modalPrice")
                    )
                except (TypeError, ValueError):
                    modal_price = None

                try:
                    arrivals = float(
                        row.get("arrivals", 0)
                    )
                except (TypeError, ValueError):
                    arrivals = 0

                if modal_price is None:
                    continue

                records.append({
                    "market": market_name,
                    "date": arrival_date,
                    "variety": row.get(
                        "variety",
                        "Unknown"
                    ),
                    "arrivals": arrivals,
                    "min_price": min_price,
                    "max_price": max_price,
                    "modal_price": modal_price,
                })

    return records


# ---------------------------------------------------------
# LATEST RECORD PER MARKET
# ---------------------------------------------------------

def latest_per_market(
    records: list[dict],
) -> list[dict]:

    grouped = {}

    for record in records:

        market = record["market"]

        if market not in grouped:
            grouped[market] = record
            continue

        old_date = grouped[market].get("date")
        new_date = record.get("date")

        if not old_date:
            grouped[market] = record
            continue

        if not new_date:
            continue

        try:
            old_dt = datetime.strptime(
                old_date,
                "%d/%m/%Y"
            )

            new_dt = datetime.strptime(
                new_date,
                "%d/%m/%Y"
            )

            if new_dt > old_dt:
                grouped[market] = record

        except ValueError:

            if str(new_date) > str(old_date):
                grouped[market] = record

    return list(grouped.values())


# ---------------------------------------------------------
# GENERAL PRICING
# ---------------------------------------------------------

def general_pricing(
    crop_names: list[str] | None = None,
) -> list[dict]:

    if crop_names is None:
        crop_names = [
            "maize",
            "rice",
            "cotton",
            "groundnut",
        ]

    results = []

    for crop in crop_names:

        try:
            raw = get_month_prices(crop)

            records = parse_market_records(
                crop,
                raw,
            )

            latest = latest_per_market(records)

            if not latest:
                results.append({
                    "crop": crop.title(),
                    "average_price": None,
                    "highest_price": None,
                    "highest_market": None,
                    "highest_date": None,
                    "record_count": 0,
                    "status": "No current data",
                })

                continue

            prices = [
                x["modal_price"]
                for x in latest
                if x["modal_price"] is not None
            ]

            if not prices:
                results.append({
                    "crop": crop.title(),
                    "average_price": None,
                    "highest_price": None,
                    "highest_market": None,
                    "highest_date": None,
                    "record_count": 0,
                    "status": "No current prices",
                })

                continue

            highest = max(
                latest,
                key=lambda x: (
                    x["modal_price"] or 0
                ),
            )

            average = sum(prices) / len(prices)

            results.append({
                "crop": crop.title(),
                "average_price": round(
                    average,
                    2,
                ),
                "highest_price": highest[
                    "modal_price"
                ],
                "highest_market": highest[
                    "market"
                ],
                "highest_date": highest[
                    "date"
                ],
                "record_count": len(latest),
                "status": "Available",
            })

        except Exception as error:

            results.append({
                "crop": crop.title(),
                "average_price": None,
                "highest_price": None,
                "highest_market": None,
                "highest_date": None,
                "record_count": 0,
                "status": "Unavailable",
                "error": str(error),
            })

    return results