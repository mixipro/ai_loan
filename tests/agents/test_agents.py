import asyncio

import pytest

from app.models.user import UserInput

from app.agents import _common
from app.agents import _tools
from app.agents import business_agent
from app.agents import real_estate_agent
from app.agents import stock_agent
from app.agents import judge_agent


@pytest.fixture
def sample_user():
    return UserInput(
        personal={
            "age": 30,
        },
        location={
            "country": "RS",
            "city": "Belgrade",
        },
        financial={
            "income": 1500,
            "expenses": 700,
            "monthly_debt": 100,
            "savings": 5000,
            "currency": "EUR",
        },
        professional={
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "full-time",
            "interests": ["programming", "investing"],
            "prior_experience": "Built a small SaaS prototype",
            "weekly_hours": "5-15",
        },
        preferences={
            "risk_profile": "medium",
            "horizon": "3-5",
        },
    )


@pytest.fixture
def approved_loan():
    return {
        "approved": True,
        "max_loan_amount": 10000,
        "interest_rate": 0.05,
        "monthly_payment": 250,
        "loan_years": 5,
    }


# ─────────────────────────
# _common.py
# ─────────────────────────

def test_parse_llm_json_accepts_plain_json():
    raw = '{"title": "Test", "expected_return": 0.1}'

    result = _common.parse_llm_json(raw)

    assert result == {
        "title": "Test",
        "expected_return": 0.1,
    }


def test_parse_llm_json_accepts_markdown_json_block():
    raw = """
```json
{"title": "Test", "risk": 0.4}"""
