"""Advisory scoring engine tests — table-driven for every threshold boundary."""
import pytest

from app.services.advisory_engine import (
    band,
    generate_advisory,
    generate_operation_advisory,
    generate_recommendations,
    score_heat,
    score_humidity,
    score_rain,
    score_wind,
)


class TestScoreRain:
    """Rain risk (0–40 pts) per §9.4."""

    @pytest.mark.parametrize("prob,expected", [
        (69.9, 20),   # >= 40
        (70.0, 40),
        (80.0, 40),
        (39.9, 0),    # < 40
        (40.0, 20),
        (0.0, 0),
    ])
    def test_rain_probability_boundaries(self, prob: float, expected: int) -> None:
        assert score_rain(prob) == expected


class TestScoreHeat:
    """Heat risk (0–25 pts) per §9.4."""

    @pytest.mark.parametrize("temp,expected", [
        (29.9, 0),
        (30.0, 12),
        (34.9, 12),
        (35.0, 25),
        (40.0, 25),
        (20.0, 0),
    ])
    def test_heat_temperature_boundaries(self, temp: float, expected: int) -> None:
        assert score_heat(temp) == expected


class TestScoreWind:
    """Wind risk (0–20 pts) per §9.4."""

    @pytest.mark.parametrize("speed,expected", [
        (14.9, 0),
        (15.0, 10),
        (29.9, 10),
        (30.0, 20),
        (35.0, 20),
        (5.0, 0),
    ])
    def test_wind_speed_boundaries(self, speed: float, expected: int) -> None:
        assert score_wind(speed) == expected


class TestScoreHumidity:
    """Humidity risk (0–15 pts) per §9.4."""

    @pytest.mark.parametrize("humidity,expected", [
        (64.9, 0),
        (65.0, 7),
        (84.9, 7),
        (85.0, 15),
        (95.0, 15),
        (50.0, 0),
    ])
    def test_humidity_boundaries(self, humidity: float, expected: int) -> None:
        assert score_humidity(humidity) == expected


class TestBand:
    """Overall risk bands per §9.4."""

    @pytest.mark.parametrize("score,expected", [
        (0, "low"),
        (30, "low"),
        (31, "medium"),
        (50, "medium"),
        (65, "medium"),
        (66, "high"),
        (100, "high"),
    ])
    def test_risk_band_boundaries(self, score: int, expected: str) -> None:
        assert band(score) == expected


class TestGenerateAdvisory:
    """generate_advisory produces per-day scores + overall band."""

    def test_single_day_all_low(self) -> None:
        day = {
            "date": "2026-06-07",
            "rain_probability": 20.0,
            "temperature_max": 25.0,
            "wind_speed_max": 10.0,
            "humidity": 50.0,
        }
        result = generate_advisory([day])
        assert len(result) == 1
        d = result[0]
        assert d["date"] == "2026-06-07"
        assert d["rain_score"] == 0
        assert d["heat_score"] == 0
        assert d["wind_score"] == 0
        assert d["humidity_score"] == 0
        assert d["total_score"] == 0
        assert d["risk_band"] == "low"

    def test_single_day_high_risk(self) -> None:
        day = {
            "date": "2026-06-07",
            "rain_probability": 80.0,
            "temperature_max": 36.0,
            "wind_speed_max": 32.0,
            "humidity": 88.0,
        }
        result = generate_advisory([day])
        d = result[0]
        assert d["rain_score"] == 40
        assert d["heat_score"] == 25
        assert d["wind_score"] == 20
        assert d["humidity_score"] == 15
        assert d["total_score"] == 100
        assert d["risk_band"] == "high"

    def test_multiple_days(self) -> None:
        days = [
            {"date": "2026-06-07", "rain_probability": 20.0, "temperature_max": 25.0, "wind_speed_max": 10.0, "humidity": 50.0},
            {"date": "2026-06-08", "rain_probability": 75.0, "temperature_max": 30.0, "wind_speed_max": 16.0, "humidity": 60.0},
        ]
        result = generate_advisory(days)
        assert len(result) == 2
        assert result[0]["risk_band"] == "low"
        # day 2: rain=40 + heat=12 + wind=10 + humidity=0 = 62 -> medium
        assert result[1]["risk_band"] == "medium"


class TestGenerateRecommendations:
    """Operation-specific recommendations per §9.4."""

    def test_spraying_not_recommended_rain_high(self) -> None:
        conditions = {
            "rain_risk": "high",
            "wind_risk": "low",
            "rain_in_3h": False,
            "rain_probability": 0.0,
        }
        recs = generate_recommendations(conditions)
        assert recs["spraying"]["status"] == "not_recommended"
        assert "rain risk is high" in recs["spraying"]["reason"]

    def test_spraying_not_recommended_wind_high(self) -> None:
        conditions = {
            "rain_risk": "low",
            "wind_risk": "high",
            "rain_in_3h": False,
            "rain_probability": 0.0,
        }
        recs = generate_recommendations(conditions)
        assert recs["spraying"]["status"] == "not_recommended"
        assert "wind risk is high" in recs["spraying"]["reason"]

    def test_spraying_not_recommended_rain_in_3h(self) -> None:
        conditions = {
            "rain_risk": "low",
            "wind_risk": "low",
            "rain_in_3h": True,
            "rain_probability": 30.0,
        }
        recs = generate_recommendations(conditions)
        assert recs["spraying"]["status"] == "not_recommended"
        assert "rain expected within 3 hours" in recs["spraying"]["reason"]

    def test_spraying_recommended_low_risk(self) -> None:
        conditions = {
            "rain_risk": "low",
            "wind_risk": "low",
            "rain_in_3h": False,
            "rain_probability": 20.0,
        }
        recs = generate_recommendations(conditions)
        assert recs["spraying"]["status"] == "recommended"

    def test_irrigation_low_need_high_rain_prob(self) -> None:
        conditions = {"rain_probability": 75.0, "temperature_max": 25.0}
        recs = generate_recommendations(conditions)
        assert recs["irrigation"]["need"] == "low"

    def test_irrigation_medium_need_mid_rain(self) -> None:
        conditions = {"rain_probability": 50.0, "temperature_max": 25.0}
        recs = generate_recommendations(conditions)
        assert recs["irrigation"]["need"] == "medium"

    def test_irrigation_high_need_hot_dry(self) -> None:
        conditions = {"rain_probability": 30.0, "temperature_max": 32.0}
        recs = generate_recommendations(conditions)
        assert recs["irrigation"]["need"] == "high"

    def test_harvesting_not_recommended_high_risk(self) -> None:
        conditions = {"overall_risk": "high"}
        recs = generate_recommendations(conditions)
        assert recs["harvesting"]["status"] == "not_recommended"

    def test_harvesting_caution_medium_risk(self) -> None:
        conditions = {"overall_risk": "medium"}
        recs = generate_recommendations(conditions)
        assert recs["harvesting"]["status"] == "caution"

    def test_harvesting_safe_low_risk(self) -> None:
        conditions = {"overall_risk": "low"}
        recs = generate_recommendations(conditions)
        assert recs["harvesting"]["status"] == "safe"


class TestGenerateOperationAdvisory:
    """Tests for generate_operation_advisory."""

    def test_spraying_recommended_false_rain_high(self) -> None:
        """Spraying blocked when rain risk is high."""
        daily_scores = [
            {"date": "2026-06-07", "rain_score": 40, "wind_score": 0, "rain_probability": 80.0, "wind_speed_max": 5.0},
        ]
        result = generate_operation_advisory("spraying", daily_scores)
        assert result["recommended"] is False
        assert any("Rain risk high" in r for r in result["reasons"])

    def test_spraying_recommended_false_wind_high(self) -> None:
        """Spraying blocked when wind risk is high."""
        daily_scores = [
            {"date": "2026-06-07", "rain_score": 0, "wind_score": 20, "rain_probability": 10.0, "wind_speed_max": 30.0},
        ]
        result = generate_operation_advisory("spraying", daily_scores)
        assert result["recommended"] is False
        assert any("Wind risk high" in r for r in result["reasons"])

    def test_spraying_best_window_first_low_risk_day(self) -> None:
        """Best window is first day where rain and wind both low."""
        daily_scores = [
            {"date": "2026-06-07", "rain_score": 0, "wind_score": 0, "rain_probability": 10.0, "wind_speed_max": 5.0},
            {"date": "2026-06-08", "rain_score": 20, "wind_score": 0, "rain_probability": 40.0, "wind_speed_max": 5.0},
        ]
        result = generate_operation_advisory("spraying", daily_scores)
        assert result["recommended"] is True
        assert result["best_window"] == "2026-06-07"

    def test_irrigation_priority_low_rainy(self) -> None:
        """Irrigation low when rain probability is high."""
        daily_scores = [{"date": "2026-06-07", "rain_score": 0, "wind_score": 0, "rain_probability": 80.0, "temperature_max": 25.0}]
        result = generate_operation_advisory("irrigation", daily_scores)
        assert result["priority"] == "low"
        assert result["recommended"] is False

    def test_irrigation_priority_medium_moderate_rain(self) -> None:
        """Irrigation medium when rain probability is 40-69%."""
        daily_scores = [{"date": "2026-06-07", "rain_score": 20, "wind_score": 0, "rain_probability": 50.0, "temperature_max": 25.0}]
        result = generate_operation_advisory("irrigation", daily_scores)
        assert result["priority"] == "medium"
        assert result["recommended"] is True

    def test_irrigation_priority_high_hot_dry(self) -> None:
        """Irrigation high when rain probability <40% and temp >= 30."""
        daily_scores = [{"date": "2026-06-07", "rain_score": 0, "wind_score": 0, "rain_probability": 30.0, "temperature_max": 35.0}]
        result = generate_operation_advisory("irrigation", daily_scores)
        assert result["priority"] == "high"
        assert result["recommended"] is True

    def test_irrigation_empty_scores_priority_medium(self) -> None:
        """Irrigation with no daily scores defaults to medium priority."""
        result = generate_operation_advisory("irrigation", [])
        assert result["priority"] == "medium"
        assert result["recommended"] is True

    def test_harvesting_empty_scores_recommended(self) -> None:
        """Harvesting with no daily scores is recommended."""
        result = generate_operation_advisory("harvesting", [])
        assert result["recommended"] is True

    def test_harvesting_medium_risk_has_caution_reason(self) -> None:
        """Harvesting medium risk includes caution in reasons."""
        daily_scores = [{"date": "2026-06-07", "risk_band": "medium", "rain_score": 20, "wind_score": 10}]
        result = generate_operation_advisory("harvesting", daily_scores)
        assert result["recommended"] is True
        assert any("medium" in r.lower() for r in result["reasons"])