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
from pydantic import ValidationError

from app.engines.risk_engine import calculate_risk_score
from app.models.user import (
    FinancialInfo,
    LocationInfo,
    PersonalInfo,
    ProfessionalInfo,
    Country,
    EmploymentStatus,
)


# ─────────────────────────
# ✅ BASIC OUTPUT SHAPE
# ─────────────────────────
def test_risk_score_returns_expected_keys(base_user):
    result = calculate_risk_score(base_user)

    assert result.keys() == {
        "base_score",
        "adjusted_score",
        "level",
        "country",
        "country_factor",
        "disposable_income",
        "debt_ratio",
    }


# ─────────────────────────
# ✅ BASE USER SCORING
# ─────────────────────────
def test_base_user_risk_score(base_user):
    result = calculate_risk_score(base_user)

    assert result["base_score"] > 0
    assert result["adjusted_score"] > 0
    assert result["country"] == "RS"
    assert result["disposable_income"] == 1000
    assert result["debt_ratio"] == 0.07
    assert result["level"] in ["low_risk", "medium_risk", "high_risk"]


# ─────────────────────────
# 💰 HIGH INCOME USER
# ─────────────────────────
def test_high_income_user_has_strong_score(high_income_user):
    result = calculate_risk_score(high_income_user)

    assert result["base_score"] == 13
    assert result["adjusted_score"] >= 8
    assert result["level"] in ["low_risk", "medium_risk"]


# ─────────────────────────
# ❌ LOW INCOME USER
# ─────────────────────────
def test_low_income_user_is_high_risk(low_income_user):
    result = calculate_risk_score(low_income_user)

    assert result["base_score"] == 4
    assert result["level"] == "high_risk"


# ─────────────────────────
# 📉 HIGH DEBT PENALTY
# ─────────────────────────
def test_high_debt_worsens_score(base_user):
    financial_data = base_user.financial.model_dump()
    financial_data["debt"] = 2000

    user = base_user.model_copy(update={
        "financial": FinancialInfo(**financial_data)
    })

    result = calculate_risk_score(user)

    assert result["debt_ratio"] == 1.33
    assert result["level"] == "high_risk"


# ─────────────────────────
# 💼 EMPLOYMENT STATUS SCORING
# ─────────────────────────
@pytest.mark.parametrize(
    "employment_status, expected_min_score_change",
    [
        (EmploymentStatus.FULL_TIME, 0),
        (EmploymentStatus.PART_TIME, -1),
        (EmploymentStatus.SELF_EMPLOYED, -1),
        (EmploymentStatus.FREELANCER, -2),
        (EmploymentStatus.UNEMPLOYED, -4),
        (EmploymentStatus.STUDENT, -4),
        (EmploymentStatus.RETIRED, -4),
    ],
)
def test_employment_status_affects_score(base_user, employment_status, expected_min_score_change):
    original = calculate_risk_score(base_user)

    professional = base_user.professional.model_dump()
    professional["employment_status"] = employment_status

    user = base_user.model_copy(update={
        "professional": ProfessionalInfo(**professional)
    })

    result = calculate_risk_score(user)

    assert result["base_score"] == original["base_score"] + expected_min_score_change


# ─────────────────────────
# 👤 AGE SCORING
# ─────────────────────────
@pytest.mark.parametrize(
    "age, expected_base_score",
    [
        (18, 7),
        (22, 9),
        (30, 11),
        (60, 10),
        (70, 7),
    ],
)
def test_age_scoring(base_user, age, expected_base_score):
    user = base_user.model_copy(update={
        "personal": PersonalInfo(age=age)
    })

    result = calculate_risk_score(user)

    assert result["base_score"] == expected_base_score


# ─────────────────────────
# 🌍 COUNTRY FACTOR
# ─────────────────────────
def test_country_factor_changes_adjusted_score(base_user):
    user_rs = base_user

    user_ch = base_user.model_copy(update={
        "location": LocationInfo(
            country=Country.SWITZERLAND,
            city="Zurich",
        )
    })

    risk_rs = calculate_risk_score(user_rs)
    risk_ch = calculate_risk_score(user_ch)

    assert risk_ch["country"] == "CH"
    assert risk_ch["adjusted_score"] > risk_rs["adjusted_score"]


# ─────────────────────────
# 🔒 VALIDATION STILL BLOCKS ZERO DISPOSABLE
# ─────────────────────────
def test_expenses_equal_income_is_invalid(base_user):
    financial_data = base_user.financial.model_dump()
    financial_data["expenses"] = base_user.financial.income

    with pytest.raises(ValidationError):
        FinancialInfo(**financial_data)
