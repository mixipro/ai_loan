from fastapi.testclient import TestClient

from app.api import routes as api_routes
from app.main import app
from app.models.user import UserInput


client = TestClient(app)


def test_health_returns_running():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "running"}


def test_analyze_calls_pipeline_and_returns_result(monkeypatch, valid_user_payload):
    captured = {}

    def fake_run_pipeline(user):
        captured["user"] = user
        return {
            "status": "mocked",
            "income": user.financial.income,
            "city": user.location.city,
        }

    monkeypatch.setattr(api_routes, "run_pipeline", fake_run_pipeline)

    response = client.post("/analyze", json=valid_user_payload)

    assert response.status_code == 200
    assert response.json() == {
        "status": "mocked",
        "income": 1500,
        "city": "Belgrade",
    }
    assert isinstance(captured["user"], UserInput)


def test_analyze_rejects_invalid_city_for_country(valid_user_payload):
    payload = valid_user_payload.copy()
    payload["location"] = {"country": "RS", "city": "Berlin"}

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_expenses_equal_to_income(valid_user_payload):
    payload = valid_user_payload.copy()
    payload["financial"] = {
        **valid_user_payload["financial"],
        "expenses": valid_user_payload["financial"]["income"],
    }

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_invalid_enum_value(valid_user_payload):
    payload = valid_user_payload.copy()
    payload["preferences"] = {
        **valid_user_payload["preferences"],
        "risk_profile": "extreme",
    }

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422
