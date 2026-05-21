from copy import deepcopy
import pytest
from app.models.analyze import AnalyzeConfig
from app.models.user import UserInput

BAY_AREA_TECH_USER_PAYLOAD = {
    "personal": {"age": 34},
    "location": {"region": "BAY_AREA", "city": "San Francisco"},
    "financial": {
        "income": 28000,
        "expenses": 7000,
        "monthly_debt": 500,
        "savings": 650000,
        "currency": "USD",
    },
    "professional": {
        "sector": "Technology",
        "profession": "AI Engineer",
        "employment_status": "full-time",
        "interests": ["ai/ml", "investing", "programming", "startups"],
        "prior_experience": "Built AI infrastructure products and analyzed public technology companies.",
        "weekly_hours": "30+",
        "tech_role": "Software Engineer",
        "equity_compensation": "RSU (Restricted Stock Units)",
        "company_stage": "Big Tech / FAANG",
        "qsbs_eligible": False,
        "entertainment_role": "Not Applicable",
    },
    "preferences": {"risk_profile": "high", "horizon": "8+"},
}

SACRAMENTO_LOW_RISK_USER_PAYLOAD = {
    "personal": {"age": 48},
    "location": {"region": "SACRAMENTO", "city": "Sacramento"},
    "financial": {
        "income": 9500,
        "expenses": 5200,
        "monthly_debt": 1200,
        "savings": 85000,
        "currency": "USD",
    },
    "professional": {
        "sector": "Government",
        "profession": "Public Administrator",
        "employment_status": "full-time",
        "interests": ["reading", "history", "online courses"],
        "prior_experience": "Public budgeting and long-term planning experience.",
        "weekly_hours": "5-15",
        "tech_role": None,
        "equity_compensation": "None",
        "company_stage": "Government",
        "qsbs_eligible": False,
        "entertainment_role": "Not Applicable",
    },
    "preferences": {"risk_profile": "low", "horizon": "3-5"},
}

LOS_ANGELES_ENTERTAINMENT_USER_PAYLOAD = {
    "personal": {"age": 37},
    "location": {"region": "LOS_ANGELES", "city": "Burbank"},
    "financial": {
        "income": 18000,
        "expenses": 6900,
        "monthly_debt": 300,
        "savings": 240000,
        "currency": "USD",
    },
    "professional": {
        "sector": "Entertainment",
        "profession": "Film Producer",
        "employment_status": "self-employed",
        "interests": ["videography", "writing", "investing", "podcasts"],
        "prior_experience": "Managed production budgets and audience-growth campaigns.",
        "weekly_hours": "15-30",
        "tech_role": None,
        "equity_compensation": "None",
        "company_stage": "Small Business",
        "qsbs_eligible": False,
        "entertainment_role": "Above-the-line (Writer/Director/Producer)",
    },
    "preferences": {"risk_profile": "medium", "horizon": "5-8"},
}

VALID_USER_PAYLOADS = [
    BAY_AREA_TECH_USER_PAYLOAD,
    SACRAMENTO_LOW_RISK_USER_PAYLOAD,
    LOS_ANGELES_ENTERTAINMENT_USER_PAYLOAD,
]

VALID_ANALYZE_CONFIG_PAYLOAD = {
    "business": {
        "loan_amount": 120000,
        "loan_years": 7,
        "savings_to_use": 80000,
        "interest_rate": 0.095,
    },
    "real_estate": {
        "loan_amount": 420000,
        "loan_years": 30,
        "savings_to_use": 180000,
        "interest_rate": 0.068,
    },
    "stock": {
        "loan_amount": 50000,
        "loan_years": 5,
        "savings_to_use": 100000,
        "interest_rate": 0.105,
    },
}


def clone_payload(payload: dict) -> dict:
    """Return an isolated mutable copy for tests."""
    return deepcopy(payload)


@pytest.fixture
def valid_user_payload() -> dict:
    return clone_payload(BAY_AREA_TECH_USER_PAYLOAD)


@pytest.fixture
def valid_user_payloads() -> list[dict]:
    return [clone_payload(payload) for payload in VALID_USER_PAYLOADS]


@pytest.fixture
def valid_user(valid_user_payload: dict) -> UserInput:
    return UserInput(**valid_user_payload)


@pytest.fixture
def low_risk_user_payload() -> dict:
    return clone_payload(SACRAMENTO_LOW_RISK_USER_PAYLOAD)


@pytest.fixture
def low_risk_user(low_risk_user_payload: dict) -> UserInput:
    return UserInput(**low_risk_user_payload)


@pytest.fixture
def entertainment_user_payload() -> dict:
    return clone_payload(LOS_ANGELES_ENTERTAINMENT_USER_PAYLOAD)


@pytest.fixture
def entertainment_user(entertainment_user_payload: dict) -> UserInput:
    return UserInput(**entertainment_user_payload)


@pytest.fixture
def analyze_config_payload() -> dict:
    return clone_payload(VALID_ANALYZE_CONFIG_PAYLOAD)


@pytest.fixture
def analyze_config(analyze_config_payload: dict) -> AnalyzeConfig:
    return AnalyzeConfig(**analyze_config_payload)


__all__ = [
    "BAY_AREA_TECH_USER_PAYLOAD",
    "SACRAMENTO_LOW_RISK_USER_PAYLOAD",
    "LOS_ANGELES_ENTERTAINMENT_USER_PAYLOAD",
    "VALID_USER_PAYLOADS",
    "VALID_ANALYZE_CONFIG_PAYLOAD",
    "clone_payload",
]
