import pytest

from app.engines.inflation_engine import (
    get_inflation_rate,
    adjust_for_inflation,
    future_value,
    real_return,
)


# ─────────────────────────
# GET INFLATION RATE
# ─────────────────────────
def test_get_inflation_rate_uses_country_first():
    assert get_inflation_rate("RS", "EUR") == 0.06


def test_get_inflation_rate_falls_back_to_currency():
    assert get_inflation_rate("XX", "EUR") == 0.025


def test_get_inflation_rate_uses_default_when_unknown_country_and_currency():
    assert get_inflation_rate("XX", "YYY") == 0.03


# ─────────────────────────
# ADJUST FOR INFLATION
# ─────────────────────────
def test_adjust_for_inflation_discounts_amount():
    result = adjust_for_inflation(
        amount=1000,
        years=2,
        country="RS",
        currency="EUR",
    )

    assert result == round(1000 / ((1 + 0.06) ** 2), 2)


def test_adjust_for_inflation_zero_years_returns_original_amount():
    result = adjust_for_inflation(
        amount=1000,
        years=0,
        country="RS",
        currency="EUR",
    )

    assert result == 1000


# ─────────────────────────
# FUTURE VALUE
# ─────────────────────────
def test_future_value_increases_amount():
    result = future_value(
        amount=1000,
        years=2,
        country="RS",
        currency="EUR",
    )

    assert result == round(1000 * ((1 + 0.06) ** 2), 2)


def test_future_value_zero_years_returns_original_amount():
    result = future_value(
        amount=1000,
        years=0,
        country="RS",
        currency="EUR",
    )

    assert result == 1000


# ─────────────────────────
# REAL RETURN
# ─────────────────────────
def test_real_return_subtracts_inflation_effect():
    result = real_return(
        nominal_return=0.10,
        country="RS",
        currency="EUR",
    )

    assert result == round((1 + 0.10) / (1 + 0.06) - 1, 4)


def test_real_return_can_be_negative():
    result = real_return(
        nominal_return=0.02,
        country="RS",
        currency="EUR",
    )

    assert result < 0
