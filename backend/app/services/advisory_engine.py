"""Deterministic advisory scoring engine — no AI dependency."""
from typing import Any


def score_rain(probability: float) -> int:
    """Rain risk (0–40 pts)."""
    if probability >= 70.0:
        return 40
    if probability >= 40.0:
        return 20
    return 0


def score_heat(temperature: float) -> int:
    """Heat risk (0–25 pts)."""
    if temperature >= 35.0:
        return 25
    if temperature >= 30.0:
        return 12
    return 0


def score_wind(speed: float) -> int:
    """Wind risk (0–20 pts)."""
    if speed >= 30.0:
        return 20
    if speed >= 15.0:
        return 10
    return 0


def score_humidity(humidity: float) -> int:
    """Humidity risk (0–15 pts)."""
    if humidity >= 85.0:
        return 15
    if humidity >= 65.0:
        return 7
    return 0


def band(total: int) -> str:
    """Overall risk band from total score (max 100)."""
    if total <= 30:
        return "low"
    if total <= 65:
        return "medium"
    return "high"


def generate_advisory(days: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score each day and return per-day advisory with band."""
    result: list[dict[str, Any]] = []
    for day in days:
        rain_pts = score_rain(day.get("rain_probability", 0.0))
        heat_pts = score_heat(day.get("temperature_max", 0.0))
        wind_pts = score_wind(day.get("wind_speed_max", 0.0))
        humidity_pts = score_humidity(day.get("humidity", 0.0))
        total = rain_pts + heat_pts + wind_pts + humidity_pts
        result.append({
            "date": day.get("date", ""),
            "rain_score": rain_pts,
            "heat_score": heat_pts,
            "wind_score": wind_pts,
            "humidity_score": humidity_pts,
            "total_score": total,
            "risk_band": band(total),
        })
    return result


def generate_recommendations(conditions: dict[str, Any]) -> dict[str, Any]:
    """Operation-specific go/no-go recommendations per §9.4."""
    rain_risk: str = conditions.get("rain_risk", "low")
    wind_risk: str = conditions.get("wind_risk", "low")
    rain_in_3h: bool = conditions.get("rain_in_3h", False)
    rain_prob: float = conditions.get("rain_probability", 0.0)
    temp_max: float = conditions.get("temperature_max", 0.0)
    overall_risk: str = conditions.get("overall_risk", "low")

    # Spraying
    if rain_risk == "high":
        spraying_status = "not_recommended"
        spraying_reason = "rain risk is high"
    elif wind_risk == "high":
        spraying_status = "not_recommended"
        spraying_reason = "wind risk is high"
    elif rain_in_3h:
        spraying_status = "not_recommended"
        spraying_reason = "rain expected within 3 hours"
    else:
        spraying_status = "recommended"
        spraying_reason = "conditions are favorable"

    # Irrigation
    if rain_prob >= 70.0:
        irrigation_need = "low"
    elif rain_prob >= 40.0:
        irrigation_need = "medium"
    else:
        irrigation_need = "high" if temp_max >= 30.0 else "medium"

    # Harvesting / field work
    if overall_risk == "high":
        harvesting_status = "not_recommended"
    elif overall_risk == "medium":
        harvesting_status = "caution"
    else:
        harvesting_status = "safe"

    return {
        "spraying": {"status": spraying_status, "reason": spraying_reason},
        "irrigation": {"need": irrigation_need},
        "harvesting": {"status": harvesting_status},
    }