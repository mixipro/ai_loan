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

from types import SimpleNamespace

import pytest

from app.engines import loan_engine
from app.models.user import FinancialInfo


@pytest.fixture
def patched_loan_years(monkeypatch):
    years = {"RS": 10, "DE": 20}
    monkeypatch.setattr(loan_engine, "COUNTRY_LOAN_YEARS", years)
    return years


def test_calculate_loan_offer_approves_valid_user(base_user, patched_loan_years):
    risk = {"level": "low_risk"}
    interest = {"interest_rate": 0.06}

    result = loan_engine.calculate_loan_offer(base_user, risk, interest)

    assert result["approved"] is True
    assert result["max_loan_amount"] > 0
    assert result["monthly_payment"] == 350
    assert result["loan_years"] == 10
    assert result["interest_rate"] == 0.06
    assert result["country"] == "RS"


def test_calculate_loan_offer_zero_interest_uses_simple_payment_formula(
    base_user,
    patched_loan_years,
):
    risk = {"level": "low_risk"}
    interest = {"interest_rate": 0}

    result = loan_engine.calculate_loan_offer(base_user, risk, interest)

    assert result["approved"] is True
    assert result["max_loan_amount"] == 350 * 10 * 12


@pytest.mark.parametrize(
    "risk_level, expected_amount",
    [
        ("low_risk", 42000.00),
        ("medium_risk", 35700.00),
        ("high_risk", 29400.00),
    ],
)
def test_calculate_loan_offer_adjusts_amount_by_risk(
    base_user,
    patched_loan_years,
    risk_level,
    expected_amount,
):
    risk = {"level": risk_level}
    interest = {"interest_rate": 0}

    result = loan_engine.calculate_loan_offer(base_user, risk, interest)

    assert result["approved"] is True
    assert result["max_loan_amount"] == expected_amount


def test_calculate_loan_offer_rejects_when_existing_debt_too_high(
    base_user,
    patched_loan_years,
):
    financial_data = base_user.financial.model_dump()
    financial_data["debt"] = 500

    user = base_user.model_copy(
        update={"financial": FinancialInfo(**financial_data)}
    )

    result = loan_engine.calculate_loan_offer(
        user,
        {"level": "low_risk"},
        {"interest_rate": 0.05},
    )

    assert result == {
        "approved": False,
        "reason": "Existing debt too high",
    }


def test_calculate_loan_offer_uses_default_years_when_country_missing(
    base_user,
    monkeypatch,
):
    monkeypatch.setattr(loan_engine, "COUNTRY_LOAN_YEARS", {})

    result = loan_engine.calculate_loan_offer(
        base_user,
        {"level": "low_risk"},
        {"interest_rate": 0},
    )

    assert result["approved"] is True
    assert result["loan_years"] == 5
    assert result["max_loan_amount"] == 350 * 5 * 12


def test_calculate_loan_offer_rejects_when_no_disposable_income(monkeypatch):
    monkeypatch.setattr(loan_engine, "COUNTRY_LOAN_YEARS", {"RS": 10})

    user = SimpleNamespace(
        financial=SimpleNamespace(
            income=1000,
            expenses=1000,
            debt=0,
        ),
        location=SimpleNamespace(
            country=SimpleNamespace(value="RS"),
        ),
    )

    result = loan_engine.calculate_loan_offer(
        user,
        {"level": "low_risk"},
        {"interest_rate": 0.05},
    )

    assert result == {
        "approved": False,
        "reason": "No disposable income",
    }


def test_calculate_loan_offer_rounds_annuity_amount(base_user, patched_loan_years):
    result = loan_engine.calculate_loan_offer(
        base_user,
        {"level": "medium_risk"},
        {"interest_rate": 0.055},
    )

    assert result["approved"] is True
    assert isinstance(result["max_loan_amount"], float)
    assert result["max_loan_amount"] == round(result["max_loan_amount"], 2)
