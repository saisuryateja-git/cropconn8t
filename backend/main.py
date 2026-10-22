from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from services.agmarknet import (
    AgmarknetError,
    get_commodities,
    get_markets,
    get_month_prices,
    parse_market_records,
    latest_per_market,
    general_pricing,
)

from services.geocoding import (
    geocode,
    distance_km,
    market_location,
)

from services.lgd import (
    district_list,
    subdistricts_for_lgd_district,
    villages_for_district,
    villages_for_subdistrict,
    find_district_by_name,
    search_locations,
)

from services.recommendation import analyze


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="CropConn8t API",
    description=(
        "Crop market comparison, location hierarchy, "
        "transport analysis and selling recommendation API"
    ),
    version="6.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://cropconn8t.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# AGMARKNET DISTRICT IDS
# =========================================================

AGMARKNET_DISTRICT_IDS = {
    "adilabad": 565,
    "asifabad": 729,
    "bhadradri kothagudem": 704,
    "bhupalapally": 703,
    "hanumakonda": 701,
    "hyderabad": 566,
    "jagtial": 567,
    "jangaon": 702,
    "jogulamba gadwal": 730,
    "kamareddy": 568,
    "karimnagar": 569,
    "khammam": 570,
    "mahabubabad": 731,
    "mahbubnagar": 571,
    "mancherial": 706,
    "medak": 572,
    "medchal malkajgiri": 732,
    "mulugu": 733,
    "nagarkurnool": 734,
    "nalgonda": 573,
    "narayanpet": 735,
    "nirmal": 736,
    "nizamabad": 574,
    "peddapalli": 737,
    "rajanna siricilla": 705,
    "ranga reddy": 575,
    "sangareddy": 700,
    "siddipet": 576,
    "suryapet": 738,
    "vikarabad": 708,
    "wanaparthy": 707,
    "warangal": 577,
    "yadadri bhuvanagiri": 739,
}


# =========================================================
# DISTRICT ALIASES
# =========================================================

DISTRICT_ALIASES = {
    "adilabad": [
        "adilabad",
    ],

    "asifabad": [
        "asifabad",
        "kumuram bheem asifabad",
        "kumaram bheem asifabad",
        "komaram bheem asifabad",
        "kumaram bheem",
        "komaram bheem",
    ],

    "bhadradri kothagudem": [
        "bhadradri kothagudem",
    ],

    "bhupalapally": [
        "bhupalapally",
        "jayashankar bhupalapally",
        "jayashankar bhupalpally",
    ],

    "hanumakonda": [
        "hanumakonda",
        "warangal urban",
        "warangal city",
    ],

    "hyderabad": [
        "hyderabad",
    ],

    "jagtial": [
        "jagtial",
    ],

    "jangaon": [
        "jangaon",
    ],

    "jogulamba gadwal": [
        "jogulamba gadwal",
        "gadwal",
    ],

    "kamareddy": [
        "kamareddy",
    ],

    "karimnagar": [
        "karimnagar",
    ],

    "khammam": [
        "khammam",
    ],

    "mahabubabad": [
        "mahabubabad",
    ],

    "mahbubnagar": [
        "mahbubnagar",
    ],

    "mancherial": [
        "mancherial",
    ],

    "medak": [
        "medak",
    ],

    "medchal malkajgiri": [
        "medchal malkajgiri",
        "medchal",
    ],

    "mulugu": [
        "mulugu",
    ],

    "nagarkurnool": [
        "nagarkurnool",
        "nagar kurnool",
    ],

    "nalgonda": [
        "nalgonda",
    ],

    "narayanpet": [
        "narayanpet",
    ],

    "nirmal": [
        "nirmal",
    ],

    "nizamabad": [
        "nizamabad",
    ],

    "peddapalli": [
        "peddapalli",
    ],

    "rajanna siricilla": [
        "rajanna siricilla",
        "rajanna sircilla",
        "sircilla",
        "siricilla",
    ],

    "ranga reddy": [
        "ranga reddy",
        "rangareddy",
    ],

    "sangareddy": [
        "sangareddy",
    ],

    "siddipet": [
        "siddipet",
    ],

    "suryapet": [
        "suryapet",
    ],

    "vikarabad": [
        "vikarabad",
    ],

    "wanaparthy": [
        "wanaparthy",
    ],

    "warangal": [
        "warangal",
        "warangal rural",
    ],

    "yadadri bhuvanagiri": [
        "yadadri bhuvanagiri",
        "yadadri",
        "bhuvanagiri",
        "yadadri bhongir",
    ],
}


# =========================================================
# SETTINGS
# =========================================================

MAX_NEARBY_DISTANCE_KM = 100.0


# =========================================================
# BASIC HELPERS
# =========================================================

def norm_name(value: str) -> str:
    return " ".join(
        (value or "")
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .split()
    )


def norm_market_name(value: str) -> str:
    text = (
        value or ""
    ).strip().lower()

    for token in (
        "(f&v)",
        "apmc",
        "market",
    ):
        text = text.replace(
            token,
            " ",
        )

    return " ".join(
        text
        .replace("/", " ")
        .split()
    )


def safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None

        number = float(value)

        if number != number:
            return None

        return number

    except (
        TypeError,
        ValueError,
    ):
        return None


# =========================================================
# DISTRICT MAPPING
# =========================================================

def district_mapping() -> dict[str, str]:
    """
    Map AGMARKNET district IDs to LGD district codes.
    Handles naming differences between datasets.
    """

    lgd_rows = district_list()

    lgd_by_name: dict[str, dict] = {}

    for row in lgd_rows:

        name = norm_name(
            row.get(
                "district_name",
                "",
            )
        )

        if name:
            lgd_by_name[name] = row

    mapping: dict[str, str] = {}

    for ag_name, ag_id in AGMARKNET_DISTRICT_IDS.items():

        aliases = DISTRICT_ALIASES.get(
            ag_name,
            [ag_name],
        )

        found = None

        # Exact alias matching.
        for alias in aliases:

            alias_name = norm_name(
                alias
            )

            if alias_name in lgd_by_name:

                found = lgd_by_name[
                    alias_name
                ]

                break

        # Conservative fuzzy matching.
        if found is None:

            normalized_ag = norm_name(
                ag_name
            )

            for (
                lgd_name,
                row,
            ) in lgd_by_name.items():

                if (
                    normalized_ag in lgd_name
                    or
                    lgd_name in normalized_ag
                ):

                    found = row
                    break

        if found:

            mapping[
                str(ag_id)
            ] = str(
                found["lgd_id"]
            )

    return mapping


def district_record_for_ag_id(
    district_id: Optional[int],
) -> Optional[dict]:

    if district_id is None:
        return None

    lgd_code = district_mapping().get(
        str(district_id)
    )

    if not lgd_code:
        return None

    for row in district_list():

        if str(
            row["lgd_id"]
        ) == str(
            lgd_code
        ):

            return row

    return None


def market_district_name(
    district_id: Optional[int],
) -> Optional[str]:

    if district_id is None:
        return None

    for (
        name,
        ag_id,
    ) in AGMARKNET_DISTRICT_IDS.items():

        if str(
            ag_id
        ) == str(
            district_id
        ):

            return name.title()

    return None


# =========================================================
# VILLAGE LOOKUP
# =========================================================

def find_village_by_code(
    village_code: str,
) -> Optional[dict]:
    """
    Find a village by its LGD village code.

    This intentionally searches the same LGD data source
    used by /locations/villages rather than relying on a
    separate helper that previously returned 404 for valid
    village codes such as 576092.
    """

    requested = str(
        village_code
    ).strip()

    if not requested:
        return None

    for district in district_list():

        lgd_id = district.get(
            "lgd_id"
        )

        if lgd_id is None:
            continue

        try:

            rows = villages_for_district(
                lgd_id
            )

        except Exception as error:

            print(
                "[LGD] District village lookup failed:",
                district.get(
                    "district_name"
                ),
                error,
            )

            continue

        for row in rows:

            code = str(
                row.get(
                    "village_code",
                    "",
                )
            ).strip()

            if code != requested:
                continue

            district_name = (
                row.get(
                    "district_name"
                )
                or
                district.get(
                    "district_name"
                )
                or
                ""
            )

            return {
                "village_code":
                    code,

                "village_name":
                    row.get(
                        "village_name",
                        "",
                    ),

                "subdistrict_code":
                    row.get(
                        "subdistrict_code",
                        "",
                    ),

                "subdistrict_name":
                    row.get(
                        "subdistrict_name",
                        "",
                    ),

                "district_name":
                    district_name,

                "pincode":
                    row.get(
                        "pincode"
                    ),
            }

    return None


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "name":
            "CropConn8t API",

        "status":
            "running",

        "version":
            "6.0.0",
    }


@app.get("/health")
def health():

    return {
        "status":
            "healthy",

        "version":
            "6.0.0",
    }


# =========================================================
# COMMODITIES
# =========================================================

@app.get("/commodities")
def commodities():

    try:

        data = get_commodities()

        return {
            "count":
                len(data),

            "commodities":
                data,
        }

    except Exception as error:

        raise HTTPException(
            status_code=502,
            detail=str(error),
        )


# =========================================================
# DISTRICTS
# =========================================================

@app.get("/locations/districts")
def districts(
    state: str = "Telangana",
):

    if (
        state.strip().lower()
        != "telangana"
    ):

        return {
            "state":
                state,

            "count":
                0,

            "districts":
                [],
        }

    result = []

    for row in district_list():

        lgd_name = row[
            "district_name"
        ]

        normalized_lgd = norm_name(
            lgd_name
        )

        ag_id = None

        # Alias match.
        for (
            ag_name,
            aliases,
        ) in DISTRICT_ALIASES.items():

            alias_names = {
                norm_name(alias)
                for alias in aliases
            }

            if (
                normalized_lgd
                in alias_names
            ):

                ag_id = (
                    AGMARKNET_DISTRICT_IDS.get(
                        ag_name
                    )
                )

                break

        # Fuzzy fallback.
        if ag_id is None:

            for (
                ag_name,
                candidate_id,
            ) in AGMARKNET_DISTRICT_IDS.items():

                normalized_ag = norm_name(
                    ag_name
                )

                if (
                    normalized_ag
                    in normalized_lgd
                    or
                    normalized_lgd
                    in normalized_ag
                ):

                    ag_id = candidate_id

                    break

        result.append(
            {
                "district_id":
                    ag_id,

                "district_name":
                    lgd_name,

                "state_id":
                    32,

                "name":
                    lgd_name,

                "lgd_id":
                    row[
                        "lgd_id"
                    ],
            }
        )

    result.sort(
        key=lambda item:
            item[
                "district_name"
            ].lower()
    )

    return {
        "state":
            "Telangana",

        "count":
            len(result),

        "districts":
            result,
    }


# =========================================================
# MANDALS / TOWNS
# =========================================================

@app.get("/locations/towns")
def towns(
    district_id: Optional[int] = None,
    district_name: Optional[str] = None,
    state: str = "Telangana",
):

    if (
        state.strip().lower()
        != "telangana"
    ):

        return {
            "state":
                state,

            "district_id":
                district_id,

            "count":
                0,

            "towns":
                [],
        }

    lgd_id = None
    resolved_name = district_name

    # Primary: AGMARKNET ID -> LGD ID.
    if district_id is not None:

        record = district_record_for_ag_id(
            district_id
        )

        if record:

            lgd_id = record[
                "lgd_id"
            ]

            resolved_name = record[
                "district_name"
            ]

    # Exact district name.
    if (
        lgd_id is None
        and district_name
    ):

        record = find_district_by_name(
            district_name
        )

        if record:

            lgd_id = record[
                "lgd_id"
            ]

            resolved_name = record[
                "district_name"
            ]

    # Alias district name.
    if (
        lgd_id is None
        and district_name
    ):

        requested = norm_name(
            district_name
        )

        for (
            ag_name,
            aliases,
        ) in DISTRICT_ALIASES.items():

            alias_names = {
                norm_name(alias)
                for alias in aliases
            }

            if (
                requested
                == norm_name(
                    ag_name
                )
                or
                requested
                in alias_names
            ):

                for row in district_list():

                    actual_name = norm_name(
                        row[
                            "district_name"
                        ]
                    )

                    if (
                        actual_name
                        in alias_names
                    ):

                        lgd_id = row[
                            "lgd_id"
                        ]

                        resolved_name = row[
                            "district_name"
                        ]

                        break

                if lgd_id:
                    break

    if not lgd_id:

        return {
            "state":
                "Telangana",

            "district_id":
                district_id,

            "district_name":
                resolved_name,

            "count":
                0,

            "towns":
                [],
        }

    subs = subdistricts_for_lgd_district(
        lgd_id
    )

    result = []

    for row in subs:

        result.append(
            {
                "id":
                    row[
                        "subdistrict_code"
                    ],

                "town_id":
                    row[
                        "subdistrict_code"
                    ],

                "name":
                    row[
                        "subdistrict_name"
                    ],

                "town_name":
                    row[
                        "subdistrict_name"
                    ],

                "subdistrict_code":
                    row[
                        "subdistrict_code"
                    ],

                "village_count":
                    row[
                        "village_count"
                    ],
            }
        )

    result.sort(
        key=lambda item:
            item[
                "town_name"
            ].lower()
    )

    return {
        "state":
            "Telangana",

        "district_id":
            district_id,

        "district_name":
            resolved_name,

        "lgd_id":
            lgd_id,

        "count":
            len(result),

        "towns":
            result,
    }


# =========================================================
# VILLAGES
# =========================================================

@app.get("/locations/villages")
def villages(
    district_id: Optional[int] = None,
    district_name: Optional[str] = None,
    subdistrict_code: Optional[str] = None,
):

    lgd_id = None

    if district_id is not None:

        record = district_record_for_ag_id(
            district_id
        )

        if record:
            lgd_id = record[
                "lgd_id"
            ]

    elif district_name:

        record = find_district_by_name(
            district_name
        )

        if record:
            lgd_id = record[
                "lgd_id"
            ]

    if subdistrict_code:

        rows = villages_for_subdistrict(
            subdistrict_code
        )

    elif lgd_id:

        rows = villages_for_district(
            lgd_id
        )

    else:

        rows = []

    result = []

    for row in rows:

        result.append(
            {
                "village_code":
                    row[
                        "village_code"
                    ],

                "village_name":
                    row[
                        "village_name"
                    ],

                "subdistrict_code":
                    row[
                        "subdistrict_code"
                    ],

                "subdistrict_name":
                    row[
                        "subdistrict_name"
                    ],

                "pincode":
                    row[
                        "pincode"
                    ],
            }
        )

    result.sort(
        key=lambda item:
            item[
                "village_name"
            ].lower()
    )

    return {
        "state":
            "Telangana",

        "district_id":
            district_id,

        "district_name":
            district_name,

        "subdistrict_code":
            subdistrict_code,

        "count":
            len(result),

        "villages":
            result,
    }


# =========================================================
# LOCATION SEARCH
# =========================================================

@app.get("/locations/search")
def location_search(
    q: str = Query(
        ...,
        min_length=2,
    ),

    limit: int = Query(
        20,
        ge=1,
        le=50,
    ),
):

    results = search_locations(
        q,
        limit,
    )

    return {
        "query":
            q,

        "count":
            len(results),

        "results":
            results,
    }


# =========================================================
# GENERAL GEOCODING
# =========================================================

@app.get("/locations/geocode")
def location_geocode(
    query: str = Query(
        ...,
        min_length=2,
    ),
):

    result = geocode(
        query
    )

    if result is None:

        raise HTTPException(
            status_code=502,
            detail=(
                f"Could not geocode "
                f"'{query}'."
            ),
        )

    address = (
        result.get(
            "address",
            {},
        )
        or {}
    )

    district_hint = (
        address.get(
            "state_district"
        )
        or
        address.get(
            "district"
        )
        or
        address.get(
            "county"
        )
        or
        address.get(
            "city_district"
        )
    )

    ag_district_id = None
    lgd_id = None

    if district_hint:

        hint = norm_name(
            district_hint
        )

        for (
            ag_name,
            ag_id,
        ) in AGMARKNET_DISTRICT_IDS.items():

            aliases = DISTRICT_ALIASES.get(
                ag_name,
                [ag_name],
            )

            if (
                hint
                in {
                    norm_name(alias)
                    for alias in aliases
                }
            ):

                ag_district_id = ag_id
                break

        if ag_district_id is not None:

            lgd_id = (
                district_mapping().get(
                    str(
                        ag_district_id
                    )
                )
            )

    return {
        "query":
            query,

        **result,

        "district_name":
            district_hint,

        "district_id":
            ag_district_id,

        "lgd_id":
            lgd_id,
    }


# =========================================================
# HIERARCHY GEOCODING
#
# FIXED:
# We no longer use find_village().
# We search the LGD village data directly.
#
# Fallback:
#   1. village
#   2. mandal
#   3. district
# =========================================================

@app.get(
    "/locations/hierarchy/geocode"
)
def hierarchy_geocode(
    village_code: str,
):

    requested_code = str(
        village_code
    ).strip()

    if not requested_code:

        raise HTTPException(
            status_code=400,
            detail="Village code is required.",
        )

    # -----------------------------------------------------
    # FIND VILLAGE DIRECTLY IN LGD DATA
    # -----------------------------------------------------

    village = find_village_by_code(
        requested_code
    )

    if village is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Village code "
                f"{requested_code} "
                "not found in the LGD dataset."
            ),
        )

    village_name = (
        village.get(
            "village_name",
            "",
        )
        .strip()
    )

    subdistrict_name = (
        village.get(
            "subdistrict_name",
            "",
        )
        .strip()
    )

    district_name = (
        village.get(
            "district_name",
            "",
        )
        .strip()
    )

    print(
        "[HIERARCHY]",
        requested_code,
        "=>",
        village_name,
        "=>",
        subdistrict_name,
        "=>",
        district_name,
    )

    # =====================================================
    # TRY 1: EXACT VILLAGE
    # =====================================================

    village_query = (
        f"{village_name}, "
        f"{subdistrict_name}, "
        f"{district_name}, "
        "Telangana, India"
    )

    print(
        "[GEOCODE] Trying village:",
        village_query,
    )

    result = geocode(
        village_query
    )

    if result is not None:

        return {
            "village_code":
                requested_code,

            "village_name":
                village_name,

            "subdistrict_name":
                subdistrict_name,

            "district_name":
                district_name,

            "query":
                village_query,

            "latitude":
                result[
                    "latitude"
                ],

            "longitude":
                result[
                    "longitude"
                ],

            "display_name":
                result.get(
                    "display_name"
                ),

            "accuracy":
                "village",

            "location_source":
                "Nominatim village",
        }

    # =====================================================
    # TRY 2: MANDAL
    # =====================================================

    mandal_query = (
        f"{subdistrict_name}, "
        f"{district_name}, "
        "Telangana, India"
    )

    print(
        "[GEOCODE] Village unavailable; "
        "trying mandal:",
        mandal_query,
    )

    result = geocode(
        mandal_query
    )

    if result is not None:

        return {
            "village_code":
                requested_code,

            "village_name":
                village_name,

            "subdistrict_name":
                subdistrict_name,

            "district_name":
                district_name,

            "query":
                mandal_query,

            "latitude":
                result[
                    "latitude"
                ],

            "longitude":
                result[
                    "longitude"
                ],

            "display_name":
                result.get(
                    "display_name"
                ),

            "accuracy":
                "mandal_fallback",

            "location_source":
                "Nominatim mandal fallback",
        }

    # =====================================================
    # TRY 3: DISTRICT
    # =====================================================

    district_query = (
        f"{district_name}, "
        "Telangana, India"
    )

    print(
        "[GEOCODE] Mandal unavailable; "
        "trying district:",
        district_query,
    )

    result = geocode(
        district_query
    )

    if result is not None:

        return {
            "village_code":
                requested_code,

            "village_name":
                village_name,

            "subdistrict_name":
                subdistrict_name,

            "district_name":
                district_name,

            "query":
                district_query,

            "latitude":
                result[
                    "latitude"
                ],

            "longitude":
                result[
                    "longitude"
                ],

            "display_name":
                result.get(
                    "display_name"
                ),

            "accuracy":
                "district_fallback",

            "location_source":
                "Nominatim district fallback",
        }

    # =====================================================
    # NOTHING WORKED
    # =====================================================

    raise HTTPException(
        status_code=502,
        detail=(
            "Could not determine coordinates for "
            f"{village_name}, "
            f"{subdistrict_name}, "
            f"{district_name}."
        ),
    )


# =========================================================
# MARKETS
# =========================================================

@app.get("/markets")
def market_directory():

    markets = get_markets(
        "Telangana"
    )

    return {
        "state":
            "Telangana",

        "count":
            len(markets),

        "markets":
            markets,
    }


# =========================================================
# PRICE HELPERS
# =========================================================

def _price_data(
    crop: str,
):

    raw = get_month_prices(
        crop
    )

    records = parse_market_records(
        crop,
        raw,
    )

    latest = latest_per_market(
        records
    )

    title = (
        raw.get(
            "title"
        )
        if isinstance(
            raw,
            dict,
        )
        else None
    )

    return latest, title


def calculate_statewide_average(
    latest: list,
) -> Optional[float]:

    values = []

    for row in latest:

        value = safe_float(
            row.get(
                "modal_price"
            )
        )

        if value is None:
            continue

        if value <= 0:
            continue

        values.append(
            value
        )

    if not values:
        return None

    return round(
        sum(values) / len(values),
        2,
    )


def build_unique_market_master(
    master: list,
) -> list:

    result = []
    seen = set()

    for market in master:

        market_id = market.get(
            "market_id"
        )

        market_name = (
            market.get(
                "market_name"
            )
            or
            market.get(
                "market"
            )
            or ""
        )

        if market_id is not None:

            key = (
                "id",
                str(
                    market_id
                ),
            )

        else:

            key = (
                "name",
                norm_market_name(
                    market_name
                ),
            )

        if key in seen:
            continue

        seen.add(
            key
        )

        result.append(
            market
        )

    return result


def build_price_map(
    latest: list,
) -> dict:

    result = {}

    for row in latest:

        key = norm_market_name(
            row.get(
                "market",
                "",
            )
        )

        if key:
            result[key] = row

    return result


def resolve_market_coordinates(
    market: dict,
):

    market_name = (
        market.get(
            "market_name"
        )
        or
        market.get(
            "market"
        )
        or ""
    )

    district_id = market.get(
        "district_id"
    )

    district_name = market_district_name(
        district_id
    )

    if not market_name:
        return None

    return market_location(
        market_name,
        district_name,
    )


# =========================================================
# PRICES
#
# IMPORTANT:
# ALL Telangana markets are evaluated.
# The farmer's district does NOT restrict destination markets.
# =========================================================

@app.get("/prices")
def prices(
    crop: str = Query(
        ...,
        min_length=2,
    ),

    latitude: Optional[float] = None,

    longitude: Optional[float] = None,

    quantity_quintals: float = Query(
        10.0,
        gt=0,
    ),

    district_id: Optional[int] = None,
):

    crop_name = (
        crop
        .strip()
        .lower()
    )

    # =====================================================
    # 1. CURRENT PRICE DATA
    # =====================================================

    try:

        latest, title = _price_data(
            crop_name
        )

    except AgmarknetError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error),
        )

    price_map = build_price_map(
        latest
    )

    # =====================================================
    # 2. TELANGANA FALLBACK AVERAGE
    # =====================================================

    statewide_average = (
        calculate_statewide_average(
            latest
        )
    )

    # =====================================================
    # 3. LOAD ALL TELANGANA MARKETS
    #
    # NO DISTRICT FILTER.
    # =====================================================

    raw_master = get_markets(
        "Telangana"
    )

    master = build_unique_market_master(
        raw_master
    )

    # Add price-only markets missing from directory.
    known_names = {
        norm_market_name(
            (
                market.get(
                    "market_name"
                )
                or
                market.get(
                    "market"
                )
                or ""
            )
        )
        for market in master
    }

    for row in latest:

        market_name = row.get(
            "market",
            "",
        )

        key = norm_market_name(
            market_name
        )

        if (
            key
            and key not in known_names
        ):

            master.append(
                {
                    "market_id":
                        None,

                    "market_name":
                        market_name,

                    "district_id":
                        None,
                }
            )

            known_names.add(
                key
            )

    # =====================================================
    # 4. EVALUATE EVERY MARKET
    # =====================================================

    market_results = []

    for market in master:

        market_name = (
            market.get(
                "market_name"
            )
            or
            market.get(
                "market"
            )
            or
            "Unknown Market"
        )

        market_key = norm_market_name(
            market_name
        )

        actual = price_map.get(
            market_key
        )

        market_lat = None
        market_lon = None
        market_distance = None

        # -------------------------------------------------
        # DISTANCE
        # -------------------------------------------------

        if (
            latitude is not None
            and longitude is not None
        ):

            try:

                coordinates = (
                    resolve_market_coordinates(
                        market
                    )
                )

                if coordinates:

                    market_lat = safe_float(
                        coordinates.get(
                            "latitude"
                        )
                    )

                    market_lon = safe_float(
                        coordinates.get(
                            "longitude"
                        )
                    )

                    if (
                        market_lat is not None
                        and
                        market_lon is not None
                    ):

                        market_distance = (
                            distance_km(
                                latitude,
                                longitude,
                                market_lat,
                                market_lon,
                            )
                        )

            except Exception as error:

                print(
                    "[MARKET GEOCODE]",
                    market_name,
                    error,
                )

        # -------------------------------------------------
        # CURRENT MARKET PRICE
        # -------------------------------------------------

        if actual:

            item = dict(
                actual
            )

            item.update(
                {
                    "market_id":
                        market.get(
                            "market_id"
                        ),

                    "market":
                        market_name,

                    "market_latitude":
                        market_lat,

                    "market_longitude":
                        market_lon,

                    "distance_km":
                        market_distance,

                    "current_price_available":
                        True,

                    "price_source":
                        "agmarknet_current",

                    "price_is_estimated":
                        False,

                    "price_status":
                        "Current AGMARKNET price",
                }
            )

            market_results.append(
                item
            )

            continue

        # -------------------------------------------------
        # TELANGANA AVERAGE ESTIMATE
        # -------------------------------------------------

        if statewide_average is not None:

            market_results.append(
                {
                    "market_id":
                        market.get(
                            "market_id"
                        ),

                    "market":
                        market_name,

                    "date":
                        None,

                    "variety":
                        "Telangana Average Estimate",

                    "arrivals":
                        None,

                    "min_price":
                        statewide_average,

                    "modal_price":
                        statewide_average,

                    "max_price":
                        statewide_average,

                    "market_latitude":
                        market_lat,

                    "market_longitude":
                        market_lon,

                    "distance_km":
                        market_distance,

                    "current_price_available":
                        False,

                    "price_source":
                        "telangana_average",

                    "price_is_estimated":
                        True,

                    "price_status":
                        "Estimated from Telangana average",

                    "price_reference":
                        (
                            "Telangana statewide average: "
                            f"₹{round(statewide_average):,}/quintal"
                        ),
                }
            )

            continue

        # -------------------------------------------------
        # NO PRICE
        # -------------------------------------------------

        market_results.append(
            {
                "market_id":
                    market.get(
                        "market_id"
                    ),

                "market":
                    market_name,

                "date":
                    None,

                "variety":
                    None,

                "arrivals":
                    None,

                "min_price":
                    None,

                "modal_price":
                    None,

                "max_price":
                    None,

                "market_latitude":
                    market_lat,

                "market_longitude":
                    market_lon,

                "distance_km":
                    market_distance,

                "current_price_available":
                    False,

                "price_source":
                    "unavailable",

                "price_is_estimated":
                    False,

                "price_status":
                    "No price data available",
            }
        )

    # =====================================================
    # 5. PRICE-CAPABLE MARKETS
    # =====================================================

    valued_markets = [
        item
        for item in market_results
        if safe_float(
            item.get(
                "modal_price"
            )
        ) is not None
    ]

    actual_markets = [
        item
        for item in market_results
        if item.get(
            "price_source"
        )
        == "agmarknet_current"
    ]

    estimated_markets = [
        item
        for item in market_results
        if item.get(
            "price_source"
        )
        == "telangana_average"
    ]

    # =====================================================
    # 6. OBSERVED AVERAGE
    # =====================================================

    actual_prices = []

    for item in actual_markets:

        value = safe_float(
            item.get(
                "modal_price"
            )
        )

        if value is not None:

            actual_prices.append(
                value
            )

    if actual_prices:

        observed_average = round(
            sum(actual_prices)
            / len(actual_prices),
            2,
        )

    else:

        observed_average = (
            statewide_average
        )

    # =====================================================
    # 7. ECONOMIC ANALYSIS
    # =====================================================

    economic = analyze(
        valued_markets,
        observed_average,
        quantity_quintals,
    )

    calculated_markets = (
        economic.get(
            "markets",
            []
        )
    )

    calculated_by_key = {}

    for item in calculated_markets:

        key = (
            norm_market_name(
                item.get(
                    "market",
                    "",
                )
            ),

            item.get(
                "date"
            ),
        )

        calculated_by_key[
            key
        ] = item

    merged = []

    for original in market_results:

        key = (
            norm_market_name(
                original.get(
                    "market",
                    "",
                )
            ),

            original.get(
                "date"
            ),
        )

        calculated = (
            calculated_by_key.get(
                key
            )
        )

        if calculated:

            result = dict(
                calculated
            )

            result.update(
                {
                    "market_id":
                        original.get(
                            "market_id"
                        ),

                    "market":
                        original.get(
                            "market"
                        ),

                    "market_latitude":
                        original.get(
                            "market_latitude"
                        ),

                    "market_longitude":
                        original.get(
                            "market_longitude"
                        ),

                    "distance_km":
                        original.get(
                            "distance_km"
                        ),

                    "price_source":
                        original.get(
                            "price_source"
                        ),

                    "price_is_estimated":
                        original.get(
                            "price_is_estimated",
                            False,
                        ),

                    "price_status":
                        original.get(
                            "price_status"
                        ),

                    "current_price_available":
                        original.get(
                            "current_price_available",
                            False,
                        ),
                }
            )

            if original.get(
                "price_reference"
            ):

                result[
                    "price_reference"
                ] = original.get(
                    "price_reference"
                )

            merged.append(
                result
            )

        else:

            item = dict(
                original
            )

            item[
                "is_best_option"
            ] = False

            merged.append(
                item
            )

    # =====================================================
    # 8. SORT
    # =====================================================

    alternatives = sorted(
        merged,

        key=lambda item: (

            # Markets without any price go last.
            item.get(
                "modal_price"
            ) is None,

            # Markets without coordinates go after
            # markets with coordinates.
            item.get(
                "distance_km"
            ) is None,

            # Nearest first.
            (
                item.get(
                    "distance_km"
                )
                if item.get(
                    "distance_km"
                ) is not None
                else float("inf")
            ),

            # Better effective price.
            -(
                safe_float(
                    item.get(
                        "net_price_per_quintal"
                    )
                )
                or
                safe_float(
                    item.get(
                        "modal_price"
                    )
                )
                or
                0
            ),
        ),
    )

    # =====================================================
    # 9. TRUE NEAREST MARKET
    # Distance only.
    # =====================================================

    markets_with_coordinates = [
        item
        for item in merged
        if item.get(
            "distance_km"
        ) is not None
    ]

    nearest_market = min(
        markets_with_coordinates,

        key=lambda item:
            item[
                "distance_km"
            ],

        default=None,
    )

    # =====================================================
    # 10. NEARBY MARKETS
    # =====================================================

    nearby_markets = [
        item
        for item in alternatives
        if (
            item.get(
                "distance_km"
            ) is not None
            and
            item[
                "distance_km"
            ]
            <= MAX_NEARBY_DISTANCE_KM
        )
    ]

    nearby_valued_markets = [
        item
        for item in nearby_markets
        if item.get(
            "modal_price"
        ) is not None
    ]

    # =====================================================
    # 11. HIGHEST CURRENT ACTUAL PRICE
    # =====================================================

    highest_actual = max(
        actual_markets,

        key=lambda item:
            safe_float(
                item.get(
                    "modal_price"
                )
            )
            or 0,

        default=None,
    )

    # =====================================================
    # 12. BEST ECONOMIC OPTION
    # =====================================================

    best_market = economic.get(
        "best_market"
    )

    recommendation_type = None
    recommendation_label = None

    if best_market:

        best_key = (
            norm_market_name(
                best_market.get(
                    "market",
                    "",
                )
            ),

            best_market.get(
                "date"
            ),
        )

        for item in merged:

            item_key = (
                norm_market_name(
                    item.get(
                        "market",
                        "",
                    )
                ),

                item.get(
                    "date"
                ),
            )

            item[
                "is_best_option"
            ] = (
                item_key
                == best_key
            )

        if best_market.get(
            "price_is_estimated"
        ):

            recommendation_type = (
                "Estimated recommendation"
            )

            recommendation_label = (
                "Best option using "
                "Telangana average estimate"
            )

            explanation = (
                f"{best_market['market']} was selected "
                "using the Telangana statewide average "
                "because a current crop-specific price "
                "was not available for that market. "
                "Transport cost and selling quantity "
                "were included in the comparison."
            )

        else:

            recommendation_type = (
                "Actual price recommendation"
            )

            recommendation_label = (
                "Best option using "
                "current market price"
            )

            explanation = (
                f"{best_market['market']} was selected "
                "using the current AGMARKNET price "
                "after accounting for estimated "
                "transport cost and net return."
            )

    else:

        explanation = (
            "No market had enough price information "
            "for an economic recommendation."
        )

    # =====================================================
    # 13. DEBUG
    # =====================================================

    print()
    print(
        "========== CropConn8t =========="
    )

    print(
        "Crop:",
        crop_name,
    )

    print(
        "Origin:",
        latitude,
        longitude,
    )

    print(
        "District parameter:",
        district_id,
    )

    print(
        "Total Telangana markets:",
        len(master),
    )

    print(
        "Actual price markets:",
        len(actual_markets),
    )

    print(
        "Estimated markets:",
        len(estimated_markets),
    )

    print(
        "Markets with coordinates:",
        len(
            markets_with_coordinates
        ),
    )

    print(
        "Nearest:",
        (
            nearest_market.get(
                "market"
            )
            if nearest_market
            else None
        ),
        (
            nearest_market.get(
                "distance_km"
            )
            if nearest_market
            else None
        ),
    )

    print(
        "Best economic:",
        (
            best_market.get(
                "market"
            )
            if best_market
            else None
        ),
    )

    print(
        "==============================="
    )

    print()

    # =====================================================
    # RESPONSE
    # =====================================================

    return {
        "state":
            "Telangana",

        "crop":
            crop_name,

        "year":
            title,

        "count":
            len(actual_markets),

        "average_modal_price":
            observed_average,

        "telangana_average_price":
            statewide_average,

        "highest_market":
            (
                {
                    "market":
                        highest_actual[
                            "market"
                        ],

                    "price":
                        highest_actual[
                            "modal_price"
                        ],

                    "date":
                        highest_actual[
                            "date"
                        ],

                    "variety":
                        highest_actual[
                            "variety"
                        ],
                }
                if highest_actual
                else None
            ),

        "nearest_market":
            nearest_market,

        "best_nearby_market":
            best_market,

        "recommendation_type":
            recommendation_type,

        "recommendation_label":
            recommendation_label,

        "recommendation_explanation":
            explanation,

        "recommendation_status":
            economic.get(
                "status"
            ),

        "recommendation_settings":
            economic.get(
                "settings"
            ),

        # All evaluated markets.
        "markets":
            alternatives,

        "alternatives":
            alternatives,

        # Nearby markets that also have a price
        # or Telangana fallback estimate.
        "nearby_alternatives":
            nearby_valued_markets,

        "market_master_count":
            len(master),

        "actual_price_market_count":
            len(actual_markets),

        "estimated_price_market_count":
            len(estimated_markets),

        "markets_with_coordinates":
            len(
                markets_with_coordinates
            ),

        "nearby_market_count":
            len(
                nearby_markets
            ),

        "nearby_valued_market_count":
            len(
                nearby_valued_markets
            ),

        "price_fallback_used":
            len(
                estimated_markets
            ) > 0,
    }


# =========================================================
# GENERAL PRICES
# =========================================================

@app.get("/prices/general")
def prices_general():

    return {
        "state":
            "Telangana",

        "prices":
            general_pricing(
                [
                    "maize",
                    "rice",
                    "cotton",
                    "groundnut",
                    "banana",
                ]
            ),
    }