# tests/agents/test_business_agent.py

from types import SimpleNamespace
import asyncio

import pytest

from app.agents import business_agent
from app.core.california_config import CaliforniaRegion


# ─────────────────────────────────
# Test helpers
# ─────────────────────────────────

def enum_value(value):
    return SimpleNamespace(value=value)


@pytest.fixture
def user():
    """Minimal California-shaped user object for business_agent v5.2.5."""
    return SimpleNamespace(
        personal=SimpleNamespace(age=32),
        location=SimpleNamespace(
            region=CaliforniaRegion.BAY_AREA,
            city="Palo Alto",
        ),
        professional=SimpleNamespace(
            profession="Software Engineer",
            sector=enum_value("Technology"),
            employment_status=enum_value("full-time"),
            interests=["fitness", "AI"],
            prior_experience="Built small SaaS tools",
            weekly_hours=enum_value("5-15"),
        ),
        financial=SimpleNamespace(
            income=12000,
            expenses=6000,
            monthly_debt=500,
            savings=50000,
            currency=enum_value("USD"),
        ),
        preferences=SimpleNamespace(
            risk_profile=enum_value("medium"),
            horizon=enum_value("5-8"),
        ),
    )


@pytest.fixture
def mixed_config():
    return {
        "loan_amount": 40000,
        "loan_years": 7,
        "savings_to_use": 30000,
        "interest_rate": 0.09,
    }


@pytest.fixture(autouse=True)
def block_real_llm_calls(monkeypatch):
    """Fail fast if this unit test accidentally tries to call a live LLM."""

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Business-agent unit test attempted a real LLM call")

    monkeypatch.setattr(business_agent, "call_llm", fail_if_called)


# ─────────────────────────────────
# Core helpers
# ─────────────────────────────────

@pytest.mark.parametrize(
    "config, expected",
    [
        ({"loan_amount": 0, "savings_to_use": 10000}, "cash"),
        ({"loan_amount": 10000, "savings_to_use": 0}, "loan"),
        ({"loan_amount": 10000, "savings_to_use": 5000}, "mixed"),
    ],
)
def test_detect_mode(config, expected):
    assert business_agent._detect_mode(config) == expected


@pytest.mark.parametrize(
    "hours, expected",
    [
        ("0-5", ["passive_income"]),
        ("5-15", ["ecommerce", "creative", "passive_income"]),
        ("15-30", ["saas", "ecommerce", "services", "creative", "passive_income"]),
    ],
)
def test_get_acceptable_types_for_hours(hours, expected):
    assert business_agent._get_acceptable_types_for_hours(hours) == expected


@pytest.mark.parametrize(
    "hours, expected",
    [
        ("0-5", "passive_income"),
        ("5-15", "ecommerce"),
        ("15-30", "services"),
        ("30+", "services"),
        ("unknown", "services"),
    ],
)
def test_fallback_type_for_hours(hours, expected):
    assert business_agent._fallback_type_for_hours(hours) == expected


# ─────────────────────────────────
# Prompt building
# ─────────────────────────────────

def test_build_prompt_includes_current_california_profile_and_mixed_config(user, mixed_config):
    prompt = business_agent.build_prompt(user, mixed_config, rag_context="RAG CONTEXT HERE")

    assert "Age: 32" in prompt
    assert "Region: Bay Area" in prompt
    assert "City: Palo Alto" in prompt
    assert "Profession: Software Engineer" in prompt
    assert "Sector: Technology" in prompt
    assert "Interests: fitness, AI" in prompt
    assert "Prior: Built small SaaS tools" in prompt
    assert "5-15h/week" in prompt
    assert "Income: $12,000/mo" in prompt
    assert "Savings: $50,000" in prompt
    assert "FUNDING MODE: MIXED" in prompt
    assert "Loan: $40,000" in prompt
    assert "Savings: $30,000" in prompt
    assert "Total capital: $70,000" in prompt
    assert "PREFERENCES: medium risk, 5-8 yr horizon" in prompt
    assert "RAG CONTEXT HERE" in prompt


def test_build_prompt_for_low_hours_forces_passive_business_type(user):
    user.professional.weekly_hours = enum_value("0-5")

    prompt = business_agent.build_prompt(
        user,
        {"loan_amount": 0, "loan_years": 0, "savings_to_use": 10000, "interest_rate": 0},
    )

    assert "0-5h/week = TRULY PASSIVE ONLY" in prompt
    assert 'ONLY "passive_income" type acceptable' in prompt
    assert '"type": "passive_income"' in prompt
    assert "DO NOT recommend:" in prompt


def test_build_prompt_uses_defaults_for_missing_interests_and_experience(user):
    user.professional.interests = []
    user.professional.prior_experience = None
    user.professional.weekly_hours = enum_value("invalid")

    prompt = business_agent.build_prompt(
        user,
        {"loan_amount": 0, "loan_years": 0, "savings_to_use": 10000, "interest_rate": 0},
    )

    assert "Interests: Not specified" in prompt
    assert "Prior: No prior business experience" in prompt
    assert "Weekly hours: Unknown availability" in prompt


# ─────────────────────────────────
# Validation
# ─────────────────────────────────

def valid_raw_business_output():
    return {
        "title": "AI Fitness Lead-Gen Studio",
        "type": "ecommerce",
        "description": "A lightweight AI-assisted lead generation business for Bay Area fitness studios.",
        "allocation": {
            "initial_investment": 20000,
            "working_capital": 15000,
            "marketing_budget": 20000,
            "legal_and_setup": 5000,
            "reserve": 10000,
        },
        "risk": 0.55,
        "stability": 0.65,
        "market_context": {
            "industry_growth_rate_pct": 6,
            "key_competitors": ["local agencies"],
            "market_size_local_usd": 50000000,
            "demand_indicator": "Local gyms need cheaper customer acquisition.",
        },
        "unit_economics": {
            "revenue_model": "Monthly subscription",
            "price_per_unit_usd": 500,
            "unit_name": "client",
            "is_recurring": True,
            "target_units_year_1": 10,
            "target_units_year_3": 20,
            "gross_margin_pct": 65,
            "customer_acquisition_cost_usd": 250,
        },
        "projections": {
            "year_1": {"operating_costs": 25000},
            "year_3": {"operating_costs": 75000},
            "year_5": {"operating_costs": 100000},
        },
        "scenarios": {
            "best_case": {"annual_return_pct": 18, "narrative": "Strong growth."},
            "base_case": {"annual_return_pct": 10, "narrative": "Normal execution."},
            "worst_case": {"annual_return_pct": 2, "narrative": "Slow sales."},
        },
        "break_even": {
            "months_to_breakeven": 12,
            "monthly_revenue_needed_usd": 4000,
            "units_per_month_needed": 8,
        },
        "pros": ["Uses existing skills"],
        "cons": ["Requires sales"],
        "next_steps": ["Validate demand"],
        "time_to_profit": "9-18 months",
    }


def test_validate_business_output_returns_current_v525_schema(user, mixed_config):
    result = business_agent.validate_business_output(
        valid_raw_business_output(),
        user=user,
        config=mixed_config,
    )

    assert result["agent"] == "business"
    assert result["title"].startswith("[Mixed]")
    assert result["type"] == "ecommerce"
    assert result["description"]
    assert set(result["allocation"]) == {
        "initial_investment",
        "working_capital",
        "marketing_budget",
        "legal_and_setup",
        "reserve",
    }
    assert sum(result["allocation"].values()) == pytest.approx(70000, abs=0.01)
    assert 0 <= result["expected_return"] <= business_agent._calculate_max_return(user)
    assert 0 <= result["risk"] <= 1
    assert 0 <= result["stability"] <= 1
    assert result["derived_status_override"] in {"profitable", "marginal", "not_profitable"}
    assert "market_context" in result
    assert "unit_economics" in result
    assert "projections" in result
    assert "scenarios" in result
    assert "break_even" in result
    assert "calculation_breakdown" in result


def test_validate_business_output_clamps_and_derives_values(user, mixed_config):
    raw = {
        "title": "Overstated SaaS",
        "type": "not_a_real_type",
        "risk": -10,
        "stability": 99,
        "allocation": {},
        "unit_economics": {
            "revenue_model": "Monthly subscription",
            "price_per_unit_usd": 1000,
            "unit_name": "subscriber",
            "is_recurring": True,
            "target_units_year_1": 10,
            "target_units_year_3": 1000,
            "gross_margin_pct": 70,
        },
    }

    result = business_agent.validate_business_output(raw, user=user, config=mixed_config)

    assert result["title"].startswith("[Mixed]")
    assert result["type"] == "ecommerce"  # invalid type fallback for 5-15h/week
    assert result["risk"] == 0
    assert result["stability"] == 1
    assert result["unit_economics"]["target_units_year_3"] == 30  # max 3x Y1
    assert sum(result["allocation"].values()) == pytest.approx(70000, abs=0.01)
    assert result["expected_return"] <= business_agent._calculate_max_return(user)


def test_validate_business_output_forces_passive_type_when_user_has_0_5_hours(user):
    user.professional.weekly_hours = enum_value("0-5")
    raw = valid_raw_business_output()
    raw["type"] = "saas"

    result = business_agent.validate_business_output(
        raw,
        user=user,
        config={"loan_amount": 0, "loan_years": 0, "savings_to_use": 10000, "interest_rate": 0},
    )

    assert result["type"] == "passive_income"
    assert result["title"].startswith("[Cash-Only]")
    assert result["expected_return"] <= business_agent._calculate_max_return(user)


# ─────────────────────────────────
# Async agent flow
# ─────────────────────────────────

def test_generate_business_idea_llm_uses_rag_prompt_and_retry_wrapper(monkeypatch, user, mixed_config):
    captured = {}

    def fake_build_rag_context(user_arg):
        assert user_arg is user
        return "RAG MOCK", ["chunk-business-1"]

    def fake_call_llm(prompt):
        captured["prompt"] = prompt
        return '{"title": "Raw result"}'

    async def fake_call_llm_with_retry(llm_call, agent_name):
        captured["agent_name"] = agent_name
        captured["llm_result"] = llm_call()
        return {"title": "Raw result"}

    monkeypatch.setattr(business_agent, "_build_rag_context", fake_build_rag_context)
    monkeypatch.setattr(business_agent, "call_llm", fake_call_llm)
    monkeypatch.setattr(business_agent, "call_llm_with_retry", fake_call_llm_with_retry)

    result, rag_sources = asyncio.run(
        business_agent.generate_business_idea_llm(user, mixed_config)
    )

    assert result == {"title": "Raw result"}
    assert rag_sources == ["chunk-business-1"]
    assert captured["agent_name"] == "business_mixed"
    assert "RAG MOCK" in captured["prompt"]
    assert "FUNDING MODE: MIXED" in captured["prompt"]


def test_run_business_agent_generates_validates_and_adds_metadata(monkeypatch, user, mixed_config):
    async def fake_generate_business_idea_llm(user_arg, config_arg):
        assert user_arg is user
        assert config_arg is mixed_config
        return valid_raw_business_output(), ["chunk-business-1", "chunk-tax-1"]

    monkeypatch.setattr(
        business_agent,
        "generate_business_idea_llm",
        fake_generate_business_idea_llm,
    )

    result = asyncio.run(business_agent.run_business_agent(user, mixed_config))

    assert result["agent"] == "business"
    assert result["rag_sources"] == ["chunk-business-1", "chunk-tax-1"]
    assert result["funding_mode"] == "mixed"
    assert result["loan_amount"] == 40000
    assert result["loan_years"] == 7
    assert result["savings_used"] == 30000
    assert result["interest_rate"] == 0.09
    assert result["total_capital"] == 70000
    assert result["title"].startswith("[Mixed]")
    assert result["derived_status_override"] in {"profitable", "marginal", "not_profitable"}


def test_run_business_agent_defaults_to_all_savings_when_config_is_none(monkeypatch, user):
    captured = {}

    async def fake_generate_business_idea_llm(user_arg, config_arg):
        captured["config"] = config_arg
        return valid_raw_business_output(), []

    monkeypatch.setattr(
        business_agent,
        "generate_business_idea_llm",
        fake_generate_business_idea_llm,
    )

    result = asyncio.run(business_agent.run_business_agent(user, None))

    assert captured["config"] == {
        "loan_amount": 0,
        "loan_years": 0,
        "savings_to_use": 50000,
        "interest_rate": 0,
    }
    assert result["funding_mode"] == "cash"
    assert result["total_capital"] == 50000
