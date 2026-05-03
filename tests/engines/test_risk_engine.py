import pytest
from pydantic import ValidationError

from app.engines.risk_engine import calculate_risk_score
from app.models.user import (
    FinancialInfo,
    PersonalInfo,
    LocationInfo,
    Country
)


# ─────────────────────────
# ✅ BASIC TEST
# ─────────────────────────
def test_risk_basic(base_user):
    result = calculate_risk_score(base_user)

    assert "level" in result
    assert "adjusted_score" in result
    assert result["adjusted_score"] > 0


# ─────────────────────────
# 💰 HIGH INCOME → LOW / MEDIUM RISK
# ─────────────────────────
def test_high_income_low_risk(high_income_user):
    result = calculate_risk_score(high_income_user)

    assert result["level"] in ["low_risk", "medium_risk"]
    assert result["adjusted_score"] >= 8


# ─────────────────────────
# ❌ LOW INCOME → HIGH RISK
# ─────────────────────────
def test_low_income_high_risk(low_income_user):
    result = calculate_risk_score(low_income_user)

    assert result["level"] == "high_risk"


# ─────────────────────────
# 📉 HIGH DEBT → WORSE SCORE
# ─────────────────────────
def test_high_debt(base_user):
    data = base_user.financial.model_dump()
    data["debt"] = 2000

    user = base_user.model_copy(update={
        "financial": FinancialInfo(**data)
    })

    result = calculate_risk_score(user)

    assert result["debt_ratio"] > 1
    assert result["level"] == "high_risk"


# ─────────────────────────
# 👤 AGE EDGE CASES
# ─────────────────────────
@pytest.mark.parametrize("age, expected_level", [
    (30, "low_risk"),
    (60, "medium_risk"),
    (20, "high_risk"),
])
def test_age_scoring(base_user, age, expected_level):
    user = base_user.model_copy(update={
        "personal": PersonalInfo(age=age)
    })

    result = calculate_risk_score(user)

    assert result["level"] in ["low_risk", "medium_risk", "high_risk"]


# ─────────────────────────
# 🌍 COUNTRY FACTOR
# ─────────────────────────
def test_country_factor_difference(base_user):
    user_rs = base_user

    user_ch = base_user.model_copy(update={
        "location": LocationInfo(
            country=Country.SWITZERLAND,
            city="Zurich"
        )
    })

    risk_rs = calculate_risk_score(user_rs)
    risk_ch = calculate_risk_score(user_ch)

    # CH stabilniji → bolji adjusted score
    assert risk_ch["adjusted_score"] > risk_rs["adjusted_score"]


# ─────────────────────────
# 💰 ZERO DISPOSABLE
# ─────────────────────────
def test_zero_disposable(base_user):
    data = base_user.financial.model_dump()
    data["expenses"] = base_user.financial.income

    with pytest.raises(ValidationError):
        FinancialInfo(**data)