import pytest
from app.models.user import UserInput


@pytest.fixture
def valid_user_payload():
    return {
        "personal": {"age": 30},
        "location": {"country": "RS", "city": "Belgrade"},
        "financial": {
            "income": 1500,
            "expenses": 500,
            "debt": 100,
            "savings": 5000,
            "currency": "EUR",
        },
        "professional": {
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "full-time",
        },
        "preferences": {
            "risk_profile": "medium",
            "horizon": "3-5",
        },
    }


@pytest.fixture
def base_user(valid_user_payload):
    return UserInput(**valid_user_payload)


@pytest.fixture
def low_income_user():
    return UserInput(
        personal={"age": 30},
        location={"country": "RS", "city": "Belgrade"},
        financial={
            "income": 500,
            "expenses": 480,
            "debt": 300,
            "savings": 0,
            "currency": "EUR",
        },
        professional={
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "freelancer",
        },
        preferences={
            "risk_profile": "low",
            "horizon": "1-3",
        },
    )


@pytest.fixture
def high_income_user():
    return UserInput(
        personal={"age": 35},
        location={"country": "DE", "city": "Berlin"},
        financial={
            "income": 4000,
            "expenses": 1500,
            "debt": 200,
            "savings": 20000,
            "currency": "EUR",
        },
        professional={
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "full-time",
        },
        preferences={
            "risk_profile": "high",
            "horizon": "5-8",
        },
    )
