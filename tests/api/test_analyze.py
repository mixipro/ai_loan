# tests/api/test_analyze.py

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
            "age": 34,
        },
        "location": {
            "region": "BAY_AREA",
            "city": "San Francisco",
        },
        "financial": {
            "income": 28000,
            "expenses": 7000,
            "monthly_debt": 0,
            "savings": 650000,
            "currency": "USD",
        },
        "professional": {
            "sector": "Technology",
            "profession": "AI Engineer",
            "employment_status": "full-time",
            "interests": ["ai/ml", "investing", "programming", "startups"],
            "prior_experience": "Built AI infrastructure and evaluated public technology markets.",
            "weekly_hours": "30+",
            "tech_role": "Software Engineer",
            "equity_compensation": "RSU (Restricted Stock Units)",
            "company_stage": "Big Tech / FAANG",
            "qsbs_eligible": False,
            "entertainment_role": "Not Applicable",
        },
        "preferences": {
            "risk_profile": "high",
            "horizon": "8+",
        },
    }


@pytest.fixture
def valid_analyze_payload(valid_user_payload):
    return {
        "user": valid_user_payload,
        "config": {
            "business": {
                "loan_amount": 200000,
                "loan_years": 7,
                "savings_to_use": 100000,
                "interest_rate": 0.09,
            },
            "real_estate": {
                "loan_amount": 500000,
                "loan_years": 30,
                "savings_to_use": 200000,
                "interest_rate": 0.065,
            },
            "stock": {
                "loan_amount": 50000,
                "loan_years": 5,
                "savings_to_use": 100000,
                "interest_rate": 0.10,
            },
        },
    }


def test_analyze_calls_pipeline_with_user_and_strategy_config(
    monkeypatch: pytest.MonkeyPatch,
    valid_analyze_payload,
):
    captured = {}

    expected_result = {
        "risk": {
            "level": "low_risk",
            "creditworthiness": "high",
            "region": "BAY_AREA",
        },
        "strategies": [
            {"agent": "business", "net_return": 0.08, "status": "profitable"},
            {"agent": "real_estate", "net_return": 0.04, "status": "marginal"},
            {"agent": "stock", "net_return": 0.11, "status": "profitable"},
        ],
        "recommendation": {"agent": "stock", "title": "Mocked stock strategy"},
        "reasoning": "Mocked pipeline result",
    }

    async def fake_run_pipeline(user, config):
        captured["user"] = user
        captured["config"] = config
        return expected_result

    monkeypatch.setattr(api_routes, "run_pipeline", fake_run_pipeline)

    response = client.post("/analyze", json=valid_analyze_payload)

    assert response.status_code == 200
    assert response.json() == expected_result

    user = captured["user"]
    assert user.personal.age == 34
    assert user.location.region.value == "BAY_AREA"
    assert user.location.city == "San Francisco"
    assert user.financial.currency.value == "USD"
    assert user.professional.sector.value == "Technology"
    assert user.professional.profession == "AI Engineer"
    assert user.professional.weekly_hours.value == "30+"
    assert user.preferences.risk_profile.value == "high"
    assert user.preferences.horizon.value == "8+"

    assert captured["config"] == valid_analyze_payload["config"]


def test_analyze_accepts_empty_config_and_uses_strategy_defaults(
    monkeypatch: pytest.MonkeyPatch,
    valid_user_payload,
):
    captured = {}

    async def fake_run_pipeline(user, config):
        captured["config"] = config
        return {"ok": True, "config": config}

    monkeypatch.setattr(api_routes, "run_pipeline", fake_run_pipeline)

    response = client.post("/analyze", json={"user": valid_user_payload, "config": {}})

    assert response.status_code == 200
    assert captured["config"] == {
        "business": {
            "loan_amount": 0,
            "loan_years": 0,
            "savings_to_use": 0,
            "interest_rate": 0,
        },
        "real_estate": {
            "loan_amount": 0,
            "loan_years": 0,
            "savings_to_use": 0,
            "interest_rate": 0,
        },
        "stock": {
            "loan_amount": 0,
            "loan_years": 0,
            "savings_to_use": 0,
            "interest_rate": 0,
        },
    }


def test_analyze_returns_500_when_pipeline_raises(
    monkeypatch: pytest.MonkeyPatch,
    valid_analyze_payload,
):
    async def fake_run_pipeline(user, config):
        raise RuntimeError("mock pipeline failure")

    monkeypatch.setattr(api_routes, "run_pipeline", fake_run_pipeline)

    response = client.post("/analyze", json=valid_analyze_payload)

    assert response.status_code == 500
    assert response.json()["detail"] == "Analysis failed: mock pipeline failure"


def test_analyze_rejects_missing_config(valid_user_payload):
    response = client.post("/analyze", json={"user": valid_user_payload})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field,value",
    [
        ("expenses", 28000),
        ("expenses", 30000),
        ("income", 0),
        ("monthly_debt", -1),
        ("savings", -1),
        ("savings", 10_000_001),
    ],
)
def test_analyze_rejects_invalid_financial_values(
    valid_analyze_payload,
    field,
    value,
):
    payload = deepcopy(valid_analyze_payload)
    payload["user"]["financial"][field] = value

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_known_city_in_wrong_region(valid_analyze_payload):
    payload = deepcopy(valid_analyze_payload)
    payload["user"]["location"] = {
        "region": "BAY_AREA",
        "city": "Burbank",  # Valid CA catalog city, but belongs to LOS_ANGELES.
    }

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_accepts_custom_city_not_in_catalog(
    monkeypatch: pytest.MonkeyPatch,
    valid_analyze_payload,
):
    payload = deepcopy(valid_analyze_payload)
    payload["user"]["location"] = {
        "region": "BAY_AREA",
        "city": "Custom Startup District",
    }

    async def fake_run_pipeline(user, config):
        return {"city": user.location.city}

    monkeypatch.setattr(api_routes, "run_pipeline", fake_run_pipeline)

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    assert response.json() == {"city": "Custom Startup District"}


@pytest.mark.parametrize(
    "path,value",
    [
        (("user", "location", "region"), "SERBIA"),
        (("user", "financial", "currency"), "EUR"),
        (("user", "professional", "sector"), "IT"),
        (("user", "professional", "employment_status"), "employed"),
        (("user", "professional", "weekly_hours"), "40"),
        (("user", "preferences", "risk_profile"), "extreme"),
        (("user", "preferences", "horizon"), "10"),
        (("user", "personal", "age"), 17),
        (("user", "personal", "age"), 120),
    ],
)
def test_analyze_rejects_invalid_user_enums_and_age(
    valid_analyze_payload,
    path,
    value,
):
    payload = deepcopy(valid_analyze_payload)
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_more_than_four_interests(valid_analyze_payload):
    payload = deepcopy(valid_analyze_payload)
    payload["user"]["professional"]["interests"] = [
        "ai/ml",
        "investing",
        "programming",
        "startups",
        "real estate",
    ]

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "strategy,field,value",
    [
        ("business", "loan_amount", -1),
        ("business", "loan_years", -1),
        ("business", "loan_years", 31),
        ("business", "savings_to_use", -1),
        ("business", "interest_rate", -0.01),
        ("business", "interest_rate", 1.01),
        ("real_estate", "loan_amount", -1),
        ("real_estate", "loan_years", 31),
        ("stock", "savings_to_use", -1),
        ("stock", "interest_rate", 1.01),
    ],
)
def test_analyze_rejects_invalid_strategy_config(
    valid_analyze_payload,
    strategy,
    field,
    value,
):
    payload = deepcopy(valid_analyze_payload)
    payload["config"][strategy][field] = value

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_options_returns_california_catalogs():
    response = client.get("/options")

    assert response.status_code == 200
    data = response.json()

    assert "regions" in data
    assert "cities_by_region" in data
    assert "BAY_AREA" in data["cities_by_region"]
    assert "San Francisco" in data["cities_by_region"]["BAY_AREA"]
    assert "Technology" in data["sectors"]
    assert "professions_by_sector" in data
    assert "Technology" in data["professions_by_sector"]
    assert "high" in data["risk_profiles"]
    assert "8+" in data["horizons"]
    assert "30+" in data["weekly_hours"]


def test_info_returns_current_architecture_metadata():
    response = client.get("/info")

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "CaliforniaCFO"
    assert data["specialization"] == "California, USA"
    assert "3-agent" in data["architecture"]
    assert data["regions_covered"] >= 8
