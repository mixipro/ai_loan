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

from app.models.user import UserInput
from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_interest_rate
from app.engines.loan_engine import calculate_loan_offer
from app.services.orchestrator import run_pipeline


def test_run_pipeline_returns_expected_shape(base_user):
    result = run_pipeline(base_user)

    assert result["status"] == "Pipeline working"
    assert "summary" in result


def test_run_pipeline_calculates_disposable_income(base_user):
    result = run_pipeline(base_user)

    assert result["summary"]["income"] == 1500
    assert result["summary"]["expenses"] == 500
    assert result["summary"]["disposable_income"] == 1000


def test_run_pipeline_preserves_location_and_savings(base_user):
    result = run_pipeline(base_user)

    assert result["summary"]["country"] == base_user.location.country
    assert result["summary"]["city"] == "Belgrade"
    assert result["summary"]["savings"] == 5000


def test_run_pipeline_works_with_high_income_user(high_income_user):
    result = run_pipeline(high_income_user)

    assert result["summary"]["country"] == high_income_user.location.country
    assert result["summary"]["city"] == "Berlin"
    assert result["summary"]["disposable_income"] == 2500


def test_full_pipeline():
    user = UserInput(
        personal={"age": 30},
        location={"country": "RS", "city": "Belgrade"},
        financial={
            "income": 1500,
            "expenses": 500,
            "debt": 100,
            "savings": 5000,
            "currency": "EUR"
        },
        professional={
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "full-time"
        },
        preferences={
            "risk_profile": "medium",
            "horizon": "3-5"
        }
    )

    risk = calculate_risk_score(user)
    interest = calculate_interest_rate(risk, user.location.country.value)
    loan = calculate_loan_offer(user, risk, interest)

    assert loan["approved"] is True
    assert loan["max_loan_amount"] > 0
    assert loan["monthly_payment"] > 0
    assert interest["interest_rate"] > 0
    assert risk["level"] in ["low_risk", "medium_risk", "high_risk"]
