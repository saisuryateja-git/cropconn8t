"""Market recommendation engine: price + distance + transport + activity."""
from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional

DEFAULT_TRANSPORT_PER_KM_PER_QUINTAL = float(os.getenv("TRANSPORT_COST_PER_KM_PER_QUINTAL", "2.50"))
DEFAULT_FIXED_TRIP = float(os.getenv("TRANSPORT_FIXED_TRIP_COST", "0"))
SOFT_LIMIT_KM = float(os.getenv("SOFT_DISTANCE_LIMIT_KM", "100"))
HARD_LIMIT_KM = float(os.getenv("HARD_DISTANCE_LIMIT_KM", "200"))


def _f(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        v = float(value)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def distance_band(distance: Optional[float]) -> str:
    if distance is None:
        return "Unknown"
    if distance <= 25:
        return "Very Near"
    if distance <= 50:
        return "Near"
    if distance <= 100:
        return "Moderate"
    if distance <= 200:
        return "Far"
    return "Very Far"


def arrival_confidence(arrivals: Optional[float]) -> float:
    if arrivals is None:
        return 0.50
    if arrivals <= 0:
        return 0.15
    if arrivals < 1:
        return 0.30
    if arrivals < 5:
        return 0.45
    if arrivals < 20:
        return 0.60
    if arrivals < 50:
        return 0.75
    if arrivals < 100:
        return 0.90
    return 1.00


def distance_score(distance: Optional[float]) -> float:
    if distance is None:
        return 0.0
    if distance <= 10:
        return 1.0
    if distance <= 25:
        return 0.95
    if distance <= 50:
        return 0.85
    if distance <= 75:
        return 0.70
    if distance <= 100:
        return 0.55
    if distance <= 150:
        return 0.30
    if distance <= 200:
        return 0.15
    return 0.05


def analyze(
    markets: List[Dict[str, Any]],
    average_modal_price: Optional[float],
    quantity_quintals: float,
    transport_per_km_per_quintal: float = DEFAULT_TRANSPORT_PER_KM_PER_QUINTAL,
    fixed_trip_cost: float = DEFAULT_FIXED_TRIP,
) -> Dict[str, Any]:
    quantity = max(_f(quantity_quintals, 10.0) or 10.0, 0.1)
    avg = _f(average_modal_price, 0.0) or 0.0

    with_price = [m for m in markets if _f(m.get("modal_price"), 0) and _f(m.get("modal_price"), 0) > 0]
    max_price = max((_f(m.get("modal_price"), 0) or 0) for m in with_price) if with_price else 0

    out = []
    for market in markets:
        result = dict(market)
        price = _f(market.get("modal_price"))
        dist = _f(market.get("distance_km"))
        arrivals = _f(market.get("arrivals"))

        if price is not None:
            result["gross_value"] = round(price * quantity, 2)
            result["price_score"] = round(price / max_price, 4) if max_price else 0
        else:
            result["gross_value"] = None
            result["price_score"] = 0

        if dist is not None and price is not None:
            transport = fixed_trip_cost + dist * transport_per_km_per_quintal * quantity
            transport_per_q = transport / quantity
            net_price = price - transport_per_q
            net_return = net_price * quantity
        else:
            transport = None
            transport_per_q = None
            net_price = None
            net_return = None

        result["transport_cost"] = round(transport, 2) if transport is not None else None
        result["transport_cost_per_quintal"] = round(transport_per_q, 2) if transport_per_q is not None else None
        result["net_price_per_quintal"] = round(net_price, 2) if net_price is not None else None
        result["net_return"] = round(net_return, 2) if net_return is not None else None

        if price is not None and avg:
            result["price_advantage"] = round(price - avg, 2)
            result["price_advantage_percent"] = round((price - avg) / avg * 100, 2)
        else:
            result["price_advantage"] = None
            result["price_advantage_percent"] = None

        result["distance_score"] = round(distance_score(dist), 4)
        result["arrival_confidence"] = round(arrival_confidence(arrivals), 4)
        result["distance_category"] = distance_band(dist)
        result["quantity_quintals"] = quantity

        if net_return is not None and max_price:
            ref = max_price * quantity
            net_score = max(0.0, min(1.0, net_return / ref))
            result["net_return_score"] = round(net_score, 4)
        else:
            result["net_return_score"] = 0.0

        result["overall_score"] = round(
            result["net_return_score"] * 0.55
            + result["price_score"] * 0.20
            + result["distance_score"] * 0.15
            + result["arrival_confidence"] * 0.10,
            4,
        )
        out.append(result)

    # Only markets with a current price can be economically ranked.
    priced = [x for x in out if x.get("modal_price") is not None and x.get("distance_km") is not None]
    within_soft = [x for x in priced if x["distance_km"] <= SOFT_LIMIT_KM]
    within_hard = [x for x in priced if x["distance_km"] <= HARD_LIMIT_KM]

    best = None
    status = "NO_SUITABLE_MARKET"
    if within_soft:
        best = max(within_soft, key=lambda x: (x.get("net_return", -math.inf), x.get("overall_score", 0)))
        status = "BEST_WITHIN_100KM"
    elif within_hard:
        best = max(within_hard, key=lambda x: (x.get("net_return", -math.inf), x.get("overall_score", 0)))
        best = dict(best)
        best["recommendation_status"] = "FAR_BUT_BEST_AVAILABLE"
        status = "FAR_BUT_BEST_AVAILABLE"

    highest = max(with_price, key=lambda x: x.get("modal_price", 0), default=None)
    priced_with_dist = [x for x in priced if x.get("distance_km") is not None]
    nearest = min(priced_with_dist, key=lambda x: x["distance_km"], default=None)

    for x in out:
        x["is_best_option"] = bool(best and x.get("market") == best.get("market") and x.get("date") == best.get("date"))

    explanation = None
    if best:
        explanation = (
            f"{best['market']} was selected using estimated net return for {quantity:g} quintals. "
            f"Market price is ₹{best['modal_price']:.0f}/quintal. "
            f"Estimated transport is ₹{best['transport_cost_per_quintal']:.0f}/quintal, "
            f"leaving about ₹{best['net_price_per_quintal']:.0f}/quintal effective return. "
            f"Distance is {best['distance_km']:.1f} km."
        )

    return {
        "markets": sorted(out, key=lambda x: (x.get("overall_score", 0), x.get("net_return") or -math.inf), reverse=True),
        "best_market": best,
        "highest_price_market": highest,
        "nearest_market": nearest,
        "status": status,
        "recommendation_explanation": explanation,
        "settings": {
            "quantity_quintals": quantity,
            "transport_cost_per_km_per_quintal": transport_per_km_per_quintal,
            "soft_distance_limit_km": SOFT_LIMIT_KM,
            "hard_distance_limit_km": HARD_LIMIT_KM,
        },
    }
