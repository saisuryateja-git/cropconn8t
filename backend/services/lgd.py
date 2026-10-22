"""
LGD-backed location service for Telangana.

Uses the supplied Telangana LGD village dataset
as the location master.
"""

from __future__ import annotations

import csv

from functools import lru_cache

from pathlib import Path

from typing import (
    Dict,
    List,
    Optional,
)


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "telangana_villages.csv"
)


def _norm(
    value: str
) -> str:

    return " ".join(
        (
            value or ""
        )
        .strip()
        .lower()
        .split()
    )


@lru_cache(maxsize=1)
def _rows() -> List[dict]:

    if not DATA_FILE.exists():

        raise FileNotFoundError(
            f"LGD dataset not found: {DATA_FILE}"
        )

    with DATA_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        return list(
            csv.DictReader(
                file
            )
        )


@lru_cache(maxsize=1)
def _districts_by_lgd() -> Dict[
    str,
    dict,
]:

    result = {}

    for row in _rows():

        code = str(
            row.get(
                "districtCode",
                "",
            )
        ).strip()

        if not code:
            continue

        if code not in result:

            result[code] = {
                "lgd_id":
                    code,

                "district_name":
                    str(
                        row.get(
                            "districtNameEnglish",
                            "",
                        )
                    ).strip(),

                "state_name":
                    str(
                        row.get(
                            "stateNameEnglish",
                            "",
                        )
                    ).strip(),
            }

    return result


@lru_cache(maxsize=1)
def _subdistricts() -> List[dict]:

    seen = {}

    for row in _rows():

        district_code = str(
            row.get(
                "districtCode",
                "",
            )
        ).strip()

        subdistrict_code = str(
            row.get(
                "subdistrictCode",
                "",
            )
        ).strip()

        if not subdistrict_code:
            continue

        key = (
            district_code,
            subdistrict_code,
        )

        if key not in seen:

            seen[key] = {
                "subdistrict_code":
                    subdistrict_code,

                "subdistrict_name":
                    str(
                        row.get(
                            "subdistrictNameEnglish",
                            "",
                        )
                    ).strip(),

                "district_lgd_id":
                    district_code,

                "district_name":
                    str(
                        row.get(
                            "districtNameEnglish",
                            "",
                        )
                    ).strip(),

                "village_count":
                    0,
            }

        seen[key][
            "village_count"
        ] += 1

    return sorted(
        seen.values(),
        key=lambda item:
        item[
            "subdistrict_name"
        ].lower(),
    )


@lru_cache(maxsize=1)
def _villages() -> List[dict]:

    result = []

    for row in _rows():

        village_name = str(
            row.get(
                "villageNameEnglish",
                "",
            )
        ).strip()

        village_code = str(
            row.get(
                "villageCode",
                "",
            )
        ).strip()

        subdistrict_code = str(
            row.get(
                "subdistrictCode",
                "",
            )
        ).strip()

        if not village_name:
            continue

        result.append(
            {
                "village_code":
                    village_code,

                "village_name":
                    village_name,

                "pincode":
                    (
                        str(
                            row.get(
                                "pincode",
                                "",
                            )
                        ).strip()
                        or None
                    ),

                "subdistrict_code":
                    subdistrict_code,

                "subdistrict_name":
                    str(
                        row.get(
                            "subdistrictNameEnglish",
                            "",
                        )
                    ).strip(),

                "district_lgd_id":
                    str(
                        row.get(
                            "districtCode",
                            "",
                        )
                    ).strip(),

                "district_name":
                    str(
                        row.get(
                            "districtNameEnglish",
                            "",
                        )
                    ).strip(),
            }
        )

    return result


def district_list() -> List[dict]:

    return sorted(
        _districts_by_lgd().values(),
        key=lambda item:
        item[
            "district_name"
        ].lower(),
    )


def subdistricts_for_lgd_district(
    lgd_id: str,
) -> List[dict]:

    return [
        item
        for item in _subdistricts()
        if item[
            "district_lgd_id"
        ]
        == str(
            lgd_id
        )
    ]


def villages_for_subdistrict(
    subdistrict_code: str,
) -> List[dict]:

    return [
        item
        for item in _villages()
        if item[
            "subdistrict_code"
        ]
        == str(
            subdistrict_code
        )
    ]


def villages_for_district(
    lgd_id: str,
) -> List[dict]:

    return [
        item
        for item in _villages()
        if item[
            "district_lgd_id"
        ]
        == str(
            lgd_id
        )
    ]


def find_district_by_name(
    name: str,
) -> Optional[dict]:

    target = _norm(
        name
    )

    for item in (
        _districts_by_lgd()
        .values()
    ):

        if (
            _norm(
                item[
                    "district_name"
                ]
            )
            == target
        ):
            return item

    return None


def find_subdistrict(
    name: str,
    district_lgd_id: Optional[
        str
    ] = None,
) -> Optional[dict]:

    target = _norm(
        name
    )

    for item in _subdistricts():

        if (
            district_lgd_id
            and item[
                "district_lgd_id"
            ]
            != str(
                district_lgd_id
            )
        ):
            continue

        if (
            _norm(
                item[
                    "subdistrict_name"
                ]
            )
            == target
        ):
            return item

    return None


def find_village(
    name: str,
    district_lgd_id: Optional[
        str
    ] = None,
    subdistrict_code: Optional[
        str
    ] = None,
) -> Optional[dict]:

    target = _norm(
        name
    )

    for item in _villages():

        if (
            district_lgd_id
            and item[
                "district_lgd_id"
            ]
            != str(
                district_lgd_id
            )
        ):
            continue

        if (
            subdistrict_code
            and item[
                "subdistrict_code"
            ]
            != str(
                subdistrict_code
            )
        ):
            continue

        if (
            _norm(
                item[
                    "village_name"
                ]
            )
            == target
        ):
            return item

    return None


def search_locations(
    query: str,
    limit: int = 20,
) -> List[dict]:

    target = _norm(
        query
    )

    if not target:
        return []

    scored = []

    for item in _villages():

        fields = [
            item[
                "village_name"
            ],
            item[
                "subdistrict_name"
            ],
            item[
                "district_name"
            ],
            item[
                "pincode"
            ] or "",
        ]

        normalized = [
            _norm(value)
            for value in fields
        ]

        score = 999

        if normalized[0] == target:

            score = 0

        elif target in normalized[0]:

            score = 1

        elif any(
            target == value
            for value in normalized[
                1:
            ]
        ):

            score = 2

        elif any(
            target in value
            for value in normalized[
                1:
            ]
        ):

            score = 3

        elif (
            target
            in " ".join(
                normalized
            )
        ):

            score = 4

        if score < 999:

            scored.append(
                (
                    score,
                    item,
                )
            )

    scored.sort(
        key=lambda pair: (
            pair[0],
            pair[1][
                "village_name"
            ].lower(),
        )
    )

    return [
        item
        for _, item
        in scored[:limit]
    ]


def location_from_hierarchy(
    village_code: str,
) -> Optional[str]:

    for item in _villages():

        if (
            item[
                "village_code"
            ]
            == str(
                village_code
            )
        ):

            return ", ".join(
                [
                    item[
                        "village_name"
                    ],
                    item[
                        "subdistrict_name"
                    ],
                    item[
                        "district_name"
                    ],
                    "Telangana",
                    "India",
                ]
            )

    return None