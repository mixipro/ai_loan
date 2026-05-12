from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.api import routes as api_routes
from app.main import app


client = TestClient(app)


@pytest.fixture
def valid_user_payload():
    return {
        "personal": {
            "age": 30,
        },
        "location": {
            "country": "RS",
            "city": "Belgrade",
        },
        "financial": {
            "income": 1500,
            "expenses": 700,
            "monthly_debt": 100,
            "savings": 5000,
            "currency": "EUR",
        },
        "professional": {
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "full-time",
            "interests": ["programming", "investing"],
            "prior_experience": "",
            "weekly_hours": "5-15",
        },
        "preferences": {
            "risk_profile": "medium",
            "horizon": "3-5",
        },
    }


def test_health_returns_running():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "running"}


def test_analyze_calls_pipeline_and_returns_result(monkeypatch, valid_user_payload):
    captured = {}

    expected_result = {
        "user_summary": {
            "country": "RS",
            "city": "Belgrade",
            "age": 30,
            "income": 1500,
            "expenses": 700,
            "monthly_debt": 100,
            "savings": 5000,
            "currency": "EUR",
            "risk_profile": "medium",
            "horizon": "3-5",
        },
        "risk": {
            "creditworthiness": "medium",
            "explanation": "Risk explanation",
            "score": 9.5,
            "level": "medium_risk",
            "country": "RS",
            "country_factor": 1.0,
            "disposable_income": 700,
            "debt_ratio": 0.07,
            "base_score": 9.5,
        },
        "interest": {
            "interest_rate": 0.05,
            "country": "RS",
        },
        "loan": {
            "approved": True,
            "max_loan_amount": 10000,
            "monthly_payment": 300,
            "interest_rate": 0.05,
            "loan_years": 3,
        },
        "strategies": [],
        "recommendation": None,
        "reasoning": "Mocked reasoning",
        "next_step": "Mocked next step",
        "profile_used": "medium",
    }

    async def fake_run_pipeline(user):
        captured["user"] = user
        return expected_result

    monkeypatch.setattr(api_routes, "run_pipeline", fake_run_pipeline)

    response = client.post("/analyze", json=valid_user_payload)

    assert response.status_code == 200
    assert response.json() == expected_result

    assert captured["user"].financial.income == 1500
    assert captured["user"].location.country.value == "RS"
    assert captured["user"].location.city == "Belgrade"
    assert captured["user"].preferences.risk_profile.value == "medium"


def test_analyze_rejects_expenses_greater_than_income(valid_user_payload):
    payload = deepcopy(valid_user_payload)
    payload["financial"]["expenses"] = 1500

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_expenses_equal_to_income(valid_user_payload):
    payload = deepcopy(valid_user_payload)
    payload["financial"]["expenses"] = payload["financial"]["income"]

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_invalid_city_for_country(valid_user_payload):
    payload = deepcopy(valid_user_payload)
    payload["location"] = {
        "country": "RS",
        "city": "Berlin",
    }

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_invalid_risk_profile(valid_user_payload):
    payload = deepcopy(valid_user_payload)
    payload["preferences"]["risk_profile"] = "extreme"

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_too_young_user(valid_user_payload):
    payload = deepcopy(valid_user_payload)
    payload["personal"]["age"] = 17

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422
