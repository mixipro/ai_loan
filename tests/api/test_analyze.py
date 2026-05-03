from copy import deepcopy

from fastapi.testclient import TestClient

from app.api import routes as api_routes
from app.main import app


client = TestClient(app)


def test_health_returns_running():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "running"}


def test_analyze_calls_engines_and_returns_result(monkeypatch, valid_user_payload):
    captured = {}

    def fake_calculate_risk_score(user):
        captured["risk_user"] = user
        return {
            "level": "medium_risk",
            "adjusted_score": 9.5,
        }

    def fake_calculate_interest_rate(risk, country):
        captured["interest_risk"] = risk
        captured["interest_country"] = country
        return {
            "interest_rate": 0.05,
            "country": country,
        }

    def fake_calculate_loan_offer(user, risk, interest):
        captured["loan_user"] = user
        captured["loan_risk"] = risk
        captured["loan_interest"] = interest
        return {
            "approved": True,
            "max_loan_amount": 10000,
        }

    monkeypatch.setattr(api_routes, "calculate_risk_score", fake_calculate_risk_score)
    monkeypatch.setattr(api_routes, "calculate_interest_rate", fake_calculate_interest_rate)
    monkeypatch.setattr(api_routes, "calculate_loan_offer", fake_calculate_loan_offer)

    response = client.post("/analyze", json=valid_user_payload)

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "risk": {
            "level": "medium_risk",
            "adjusted_score": 9.5,
        },
        "interest": {
            "interest_rate": 0.05,
            "country": "RS",
        },
        "loan": {
            "approved": True,
            "max_loan_amount": 10000,
        },
    }

    assert captured["risk_user"].financial.income == 1500
    assert captured["interest_country"] == "RS"
    assert captured["loan_risk"]["level"] == "medium_risk"
    assert captured["loan_interest"]["interest_rate"] == 0.05


def test_analyze_invalid_payload_returns_422(valid_user_payload):
    payload = deepcopy(valid_user_payload)
    payload["financial"]["expenses"] = 1500

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_invalid_city_for_country(valid_user_payload):
    payload = deepcopy(valid_user_payload)
    payload["location"] = {"country": "RS", "city": "Berlin"}

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_expenses_equal_to_income(valid_user_payload):
    payload = deepcopy(valid_user_payload)
    payload["financial"]["expenses"] = payload["financial"]["income"]

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_invalid_enum_value(valid_user_payload):
    payload = deepcopy(valid_user_payload)
    payload["preferences"]["risk_profile"] = "extreme"

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422
