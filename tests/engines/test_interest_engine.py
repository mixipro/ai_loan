"""
LEGACY TEST FILE — Skipped during California pivot.

This file was written for the pre-California multi-country model
(Country enum, EUR currency, COUNTRY_LOAN_YEARS, COUNTRY_INTEREST).
It has been preserved as documentation of the original test design
but is excluded from CI until refactored to the California-only model.

Status: Pre-pivot tests (May 2026 California pivot)
Refactor target: Post-defense
"""
import pytest

pytestmark = pytest.mark.skip(
    reason="Legacy pre-California pivot test — refactor scheduled post-defense"
)

import pytest

from app.engines import interest_engine


@pytest.fixture
def patched_country_interest(monkeypatch):
    rates = {"RS": (0.03, 0.09), "DE": (0.02, 0.06)}
    monkeypatch.setattr(interest_engine, "COUNTRY_INTEREST", rates)
    return rates


@pytest.mark.parametrize(
    "risk, expected_rate, expected_base_rate, expected_score_rate",
    [
        ({"level": "low_risk", "adjusted_score": 15}, 0.03, 0.03, 0.03),
        ({"level": "medium_risk", "adjusted_score": 7.5}, 0.06, 0.06, 0.06),
        ({"level": "high_risk", "adjusted_score": 0}, 0.09, 0.09, 0.09),
    ],
)
def test_calculate_interest_rate_by_risk_level(
    patched_country_interest,
    risk,
    expected_rate,
    expected_base_rate,
    expected_score_rate,
):
    result = interest_engine.calculate_interest_rate(risk, "RS")

    assert result["interest_rate"] == pytest.approx(expected_rate)
    assert result["base_rate"] == pytest.approx(expected_base_rate)
    assert result["score_rate"] == pytest.approx(expected_score_rate)
    assert result["min_rate"] == 0.03
    assert result["max_rate"] == 0.09
    assert result["risk_level"] == risk["level"]
    assert result["country"] == "RS"
    assert result["score"] == risk["adjusted_score"]


def test_calculate_interest_rate_blends_base_and_score_rate(patched_country_interest):
    risk = {"level": "medium_risk", "adjusted_score": 12}

    result = interest_engine.calculate_interest_rate(risk, "RS")

    assert result["base_rate"] == pytest.approx(0.06)
    assert result["score_rate"] == pytest.approx(0.042)
    assert result["interest_rate"] == pytest.approx(0.0528)


def test_calculate_interest_rate_clamps_score_above_max(patched_country_interest):
    risk = {"level": "low_risk", "adjusted_score": 100}

    result = interest_engine.calculate_interest_rate(risk, "RS")

    assert result["score_rate"] == pytest.approx(0.03)
    assert result["interest_rate"] >= result["min_rate"]
    assert result["interest_rate"] <= result["max_rate"]


def test_calculate_interest_rate_clamps_score_below_zero(patched_country_interest):
    risk = {"level": "high_risk", "adjusted_score": -10}

    result = interest_engine.calculate_interest_rate(risk, "RS")

    assert result["score_rate"] == pytest.approx(0.09)
    assert result["interest_rate"] >= result["min_rate"]
    assert result["interest_rate"] <= result["max_rate"]


def test_calculate_interest_rate_rejects_unsupported_country(patched_country_interest):
    risk = {"level": "low_risk", "adjusted_score": 10}

    with pytest.raises(ValueError, match="Unsupported country"):
        interest_engine.calculate_interest_rate(risk, "XX")


@pytest.mark.parametrize(
    "risk",
    [
        {"level": "low_risk"},
        {"adjusted_score": 10},
        {},
    ],
)
def test_calculate_interest_rate_rejects_invalid_risk_input(
    patched_country_interest,
    risk,
):
    with pytest.raises(ValueError, match="Invalid risk input"):
        interest_engine.calculate_interest_rate(risk, "RS")
