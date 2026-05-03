import pytest
from pydantic import ValidationError

from app.models.user import (
    FinancialInfo,
    LocationInfo,
    PersonalInfo,
    Preferences,
    RiskProfile,
    UserInput,
)


def test_user_input_accepts_valid_payload(valid_user_payload):
    user = UserInput(**valid_user_payload)

    assert user.personal.age == 30
    assert user.location.country.value == "RS"
    assert user.location.city == "Belgrade"
    assert user.financial.income == 1500
    assert user.preferences.risk_profile == RiskProfile.MEDIUM


def test_location_rejects_city_not_in_selected_country():
    with pytest.raises(ValidationError) as exc:
        LocationInfo(country="RS", city="Berlin")

    assert "nije validan grad" in str(exc.value)


@pytest.mark.parametrize("age", [17, 120])
def test_personal_info_rejects_invalid_age_bounds(age):
    with pytest.raises(ValidationError):
        PersonalInfo(age=age)


@pytest.mark.parametrize("income, expenses", [(0, 0), (1000, 1000), (1000, 1200)])
def test_financial_info_rejects_invalid_income_or_expenses(income, expenses):
    with pytest.raises(ValidationError):
        FinancialInfo(
            income=income,
            expenses=expenses,
            debt=0,
            savings=0,
            currency="EUR",
        )


@pytest.mark.parametrize(
    "risk_profile, expected_goal",
    [
        ("low", "safety"),
        ("medium", "growth"),
        ("high", "profit"),
    ],
)
def test_risk_profile_goal_mapping(risk_profile, expected_goal):
    preferences = Preferences(risk_profile=risk_profile, horizon="3-5")

    assert preferences.risk_profile.goal == expected_goal


def test_user_input_rejects_invalid_profession(valid_user_payload):
    payload = valid_user_payload.copy()
    payload["professional"] = {
        **valid_user_payload["professional"],
        "profession": "Astronaut",
    }

    with pytest.raises(ValidationError):
        UserInput(**payload)
