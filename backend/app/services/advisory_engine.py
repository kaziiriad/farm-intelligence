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


def generate_operation_advisory(
    operation: str,
    daily_scores: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build operation-specific response for a single operation type.

    Returns dict with keys: recommended, priority, best_window, reasons.
    """
    reasons: list[str] = []
    recommended = True
    priority: str | None = None
    best_window: str | None = None

    if operation == "spraying":
        for day in daily_scores:
            rain_score = day.get("rain_score", 0)
            wind_score = day.get("wind_score", 0)
            rain_prob = day.get("rain_probability", 0.0)
            wind_speed = day.get("wind_speed_max", 0.0)

            rain_risk = "high" if rain_score >= 40 else "medium" if rain_score >= 20 else "low"
            wind_risk = "high" if wind_score >= 20 else "medium" if wind_score >= 10 else "low"

            if rain_risk == "high":
                reasons.append(f"Rain risk high on {day['date']}")
                recommended = False
            elif wind_risk == "high":
                reasons.append(f"Wind risk high on {day['date']}")
                recommended = False

        # Best window: first day where both rain and wind risk are low
        if recommended:
            for day in daily_scores:
                rain_score = day.get("rain_score", 0)
                wind_score = day.get("wind_score", 0)
                if rain_score == 0 and wind_score == 0:
                    best_window = day["date"]
                    break

    elif operation == "irrigation":
        if not daily_scores:
            priority = "medium"
        else:
            day = daily_scores[0]  # use today
            rain_prob = day.get("rain_probability", 0.0)
            temp_max = day.get("temperature_max", 0.0)
            if rain_prob >= 70.0:
                priority = "low"
            elif rain_prob >= 40.0:
                priority = "medium"
            else:
                priority = "high" if temp_max >= 30.0 else "medium"
        recommended = priority != "low"

    elif operation == "harvesting":
        if not daily_scores:
            recommended = True
        else:
            day = daily_scores[0]
            risk_band = day.get("risk_band", "low")
            if risk_band == "high":
                reasons.append(f"Overall risk is high on {day['date']}")
                recommended = False
            elif risk_band == "medium":
                reasons.append(f"Overall risk is medium on {day['date']} — proceed with caution")
                recommended = True
            else:
                recommended = True

    return {
        "recommended": recommended,
        "priority": priority,
        "best_window": best_window,
        "reasons": reasons,
    }