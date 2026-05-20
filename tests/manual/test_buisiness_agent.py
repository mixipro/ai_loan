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
from app.agents.business_agent import run_business_agent


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
        "employment_status": "full-time",

    },
    preferences={
        "risk_profile": "medium",
        "horizon": "3-5"
    }
)

loan = {
    "approved": True,
    "max_loan_amount": 10000,
    "interest_rate": 0.08,
    "monthly_payment": 200,
    "loan_years": 5
}

result = run_business_agent(user, loan)

print("\n🔥 RESULT:\n")
print(result)