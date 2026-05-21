# tests/agents/test_real_estate_agent.py

from types import SimpleNamespace
import asyncio

import pytest

from app.agents import real_estate_agent
from app.core.california_config import CaliforniaRegion


# ─────────────────────────────────
# Test helpers
# ─────────────────────────────────

def enum_value(value):
    return SimpleNamespace(value=value)


@pytest.fixture
def user():
    """Minimal California-shaped user object for real_estate_agent v5.2.5."""
    return SimpleNamespace(
        personal=SimpleNamespace(age=36),
        location=SimpleNamespace(
            region=CaliforniaRegion.BAY_AREA,
            city="Palo Alto",
        ),
        professional=SimpleNamespace(
            profession="Product Manager",
            sector=enum_value("Technology"),
            employment_status=enum_value("full-time"),
            interests=["real estate", "investing"],
            prior_experience="Managed a small rental property with family.",
            weekly_hours=enum_value("5-15"),
        ),
        financial=SimpleNamespace(
            income=18000,
            expenses=7500,
            monthly_debt=500,
            savings=120000,
            currency=enum_value("USD"),
        ),
        preferences=SimpleNamespace(
            risk_profile=enum_value("medium"),
            horizon=enum_value("5-8"),
        ),
    )


@pytest.fixture
def mortgage_config():
    return {
        "loan_amount": 320000,
        "loan_years": 30,
        "savings_to_use": 80000,
        "interest_rate": 0.065,
    }


@pytest.fixture(autouse=True)
def block_real_llm_calls(monkeypatch):
    """Fail fast if this unit test accidentally tries to call a live LLM."""

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Real-estate-agent unit test attempted a real LLM call")

    monkeypatch.setattr(real_estate_agent, "call_llm", fail_if_called)


# ─────────────────────────────────
# Core helpers / config validation
# ─────────────────────────────────

def test_calculate_loan_payment_returns_expected_shape():
    result = real_estate_agent._calculate_loan_payment(
        loan_amount=320000,
        rate=0.065,
        years=30,
    )

    assert result["monthly_payment"] > 0
    assert result["annual_payment"] == pytest.approx(result["monthly_payment"] * 12, abs=0.10)
    assert result["total_paid"] > 320000
    assert result["total_interest"] > 0


@pytest.mark.parametrize(
    "config, expected_valid, expected_reason",
    [
        (
            {"loan_amount": 0, "savings_to_use": 100000},
            False,
            "requires a mortgage",
        ),
        (
            {"loan_amount": 400000, "savings_to_use": 50000},
            False,
            "Down payment",
        ),
        (
            {"loan_amount": 320000, "savings_to_use": 80000},
            True,
            "",
        ),
    ],
)
def test_validate_real_estate_config(config, expected_valid, expected_reason):
    is_valid, reason = real_estate_agent._validate_real_estate_config(config)

    assert is_valid is expected_valid
    assert expected_reason in reason


# ─────────────────────────────────
# Prompt building
# ─────────────────────────────────

def test_build_prompt_includes_current_california_profile_and_mortgage_config(
    user, mortgage_config
):
    prompt = real_estate_agent.build_prompt(
        user,
        mortgage_config,
        rag_context="RAG CONTEXT HERE",
    )

    assert "Age: 36" in prompt
    assert "Region: Bay Area" in prompt
    assert "City: Palo Alto" in prompt
    assert "Interests: real estate, investing" in prompt
    assert "Prior experience: Managed a small rental property with family." in prompt
    assert "Weekly hours: 5-15" in prompt
    assert "Income: $18,000/mo" in prompt
    assert "Savings: $120,000" in prompt
    assert "Mortgage: $320,000 @ 6.50% × 30yr" in prompt
    assert "Down payment: $80,000 (20.0%)" in prompt
    assert "Total property value: $400,000" in prompt
    assert "PREFERENCES: medium risk, 5-8 yr horizon" in prompt
    assert "Prop 13" in prompt
    assert "RAG CONTEXT HERE" in prompt


def test_build_prompt_uses_defaults_for_missing_interests_and_experience(user, mortgage_config):
    user.professional.interests = []
    user.professional.prior_experience = None

    prompt = real_estate_agent.build_prompt(user, mortgage_config)

    assert "Interests: Not specified" in prompt
    assert "Prior experience: No prior real estate experience" in prompt


# ─────────────────────────────────
# Validation
# ─────────────────────────────────

def valid_raw_real_estate_output():
    return {
        "title": "Entry-Level Bay Area Rental Condo",
        "type": "rental",
        "description": (
            "A direct rental-property strategy using a conservative mortgage and "
            "Prop 13 tax stability."
        ),
        "allocation": {
            "down_payment": 80000,
            "property_value": 280000,
            "taxes_and_fees": 16000,
            "renovation_reserve": 16000,
            "emergency_fund": 8000,
        },
        "expected_return": 0.06,
        "risk": 0.40,
        "stability": 0.78,
        "property_market_context": {
            "median_property_value_usd": 900000,
            "median_rent_monthly_usd": 3200,
            "rent_to_price_ratio_pct": 0.55,
            "appreciation_rate_pct_5yr": 4.5,
            "comparable_properties": ["Condo A", "Condo B", "Condo C"],
            "demand_indicator": "Rental demand remains supported by tech employment.",
        },
        "property_economics": {
            "purchase_price_usd": 400000,
            "down_payment_usd": 80000,
            "monthly_rent_usd": 3200,
            "annual_rental_income_usd": 38400,
            "vacancy_rate_pct": 8,
            "expected_annual_appreciation_pct": 4.5,
            "is_rental": True,
            "is_flip": False,
        },
        "scenarios": {
            "best_case": {
                "appreciation_pct": 8,
                "cash_flow_pct": 5,
                "total_roi_pct": 13,
                "narrative": "Strong appreciation and low vacancy.",
            },
            "base_case": {
                "appreciation_pct": 4.5,
                "cash_flow_pct": 1.5,
                "total_roi_pct": 6,
                "narrative": "Normal rental demand.",
            },
            "worst_case": {
                "appreciation_pct": -3,
                "cash_flow_pct": -1,
                "total_roi_pct": -4,
                "narrative": "Vacancy spike and price decline.",
            },
        },
        "break_even": {
            "years_to_breakeven": 5,
            "cumulative_cash_flow_breakeven_year": 5,
            "explanation": "Equity buildup and appreciation recover the down payment.",
        },
        "pros": ["Prop 13 tax stability"],
        "cons": ["Illiquid asset"],
        "next_steps": ["Pre-approval", "Inspect target properties"],
        "time_to_profit": "2-3 years",
    }


def test_validate_real_estate_output_returns_current_v525_schema(user, mortgage_config):
    result = real_estate_agent.validate_real_estate_output(
        valid_raw_real_estate_output(),
        user=user,
        config=mortgage_config,
    )

    assert result["agent"] == "real_estate"
    assert result["title"] == "Entry-Level Bay Area Rental Condo"
    assert result["type"] == "rental"
    assert result["description"]
    assert set(result["allocation"]) == {
        "down_payment",
        "property_value",
        "taxes_and_fees",
        "renovation_reserve",
        "emergency_fund",
    }
    assert sum(result["allocation"].values()) == pytest.approx(400000, abs=0.01)
    assert -0.20 <= result["expected_return"] <= 0.225
    assert 0 <= result["risk"] <= 1
    assert 0 <= result["stability"] <= 1
    assert result["derived_status_override"] in {
        "profitable",
        "marginal",
        "not_profitable",
    }
    assert "property_market_context" in result
    assert "property_economics" in result
    assert "projections" in result
    assert "scenarios" in result
    assert "break_even" in result
    assert "calculation_breakdown" in result


def test_validate_real_estate_output_defaults_type_and_clamps_values(user, mortgage_config):
    raw = {
        "title": "Overstated Property Plan",
        "type": "not_a_real_property_type",
        "risk": -10,
        "stability": 99,
        "allocation": {},
        "property_economics": {
            "monthly_rent_usd": 999999999,
            "vacancy_rate_pct": 999,
            "expected_annual_appreciation_pct": 999,
        },
    }

    result = real_estate_agent.validate_real_estate_output(
        raw,
        user=user,
        config=mortgage_config,
    )

    assert result["type"] == "rental"
    assert result["risk"] == 0.20
    assert result["stability"] == 0.90
    assert sum(result["allocation"].values()) == pytest.approx(400000, abs=0.01)
    assert result["property_economics"]["monthly_rent_usd"] == 1_000_000
    assert result["property_economics"]["vacancy_rate_pct"] == 100
    assert result["property_economics"]["expected_annual_appreciation_pct"] == 15


# ─────────────────────────────────
# Async agent flow
# ─────────────────────────────────

def test_generate_real_estate_strategy_llm_uses_rag_prompt_and_retry_wrapper(
    monkeypatch, user, mortgage_config
):
    captured = {}

    def fake_build_rag_context(user_arg):
        assert user_arg is user
        return "RAG MOCK", ["chunk-real-estate-1"]

    def fake_call_llm(prompt):
        captured["prompt"] = prompt
        return '{"title": "Raw result"}'

    async def fake_call_llm_with_retry(llm_call, agent_name):
        captured["agent_name"] = agent_name
        captured["llm_result"] = llm_call()
        return {"title": "Raw result"}

    monkeypatch.setattr(real_estate_agent, "_build_rag_context", fake_build_rag_context)
    monkeypatch.setattr(real_estate_agent, "call_llm", fake_call_llm)
    monkeypatch.setattr(real_estate_agent, "call_llm_with_retry", fake_call_llm_with_retry)

    result, rag_sources = asyncio.run(
        real_estate_agent.generate_real_estate_strategy_llm(user, mortgage_config)
    )

    assert result == {"title": "Raw result"}
    assert rag_sources == ["chunk-real-estate-1"]
    assert captured["agent_name"] == "real_estate"
    assert "RAG MOCK" in captured["prompt"]
    assert "MORTGAGE CONFIGURATION" in captured["prompt"]


def test_run_real_estate_agent_rejects_missing_or_invalid_config(user):
    missing = asyncio.run(real_estate_agent.run_real_estate_agent(user, None))
    invalid = asyncio.run(
        real_estate_agent.run_real_estate_agent(
            user,
            {"loan_amount": 0, "loan_years": 30, "savings_to_use": 80000, "interest_rate": 0.065},
        )
    )

    assert missing["rejected"] is True
    assert missing["title"] == "Real Estate — Not Configured"
    assert invalid["rejected"] is True
    assert invalid["funding_mode"] == "rejected"
    assert "requires a mortgage" in invalid["rejection_reason"]


def test_run_real_estate_agent_generates_validates_and_adds_metadata(
    monkeypatch, user, mortgage_config
):
    async def fake_generate_real_estate_strategy_llm(user_arg, config_arg):
        assert user_arg is user
        assert config_arg is mortgage_config
        return valid_raw_real_estate_output(), ["chunk-real-estate-1", "chunk-tax-1"]

    monkeypatch.setattr(
        real_estate_agent,
        "generate_real_estate_strategy_llm",
        fake_generate_real_estate_strategy_llm,
    )

    result = asyncio.run(real_estate_agent.run_real_estate_agent(user, mortgage_config))

    assert result["agent"] == "real_estate"
    assert result["rejected"] is False
    assert result["rag_sources"] == ["chunk-real-estate-1", "chunk-tax-1"]
    assert result["funding_mode"] == "mortgage"
    assert result["loan_amount"] == 320000
    assert result["loan_years"] == 30
    assert result["savings_used"] == 80000
    assert result["interest_rate"] == 0.065
    assert result["total_capital"] == 400000
    assert result["down_payment_pct"] == 0.20
    assert result["derived_status_override"] in {
        "profitable",
        "marginal",
        "not_profitable",
    }
