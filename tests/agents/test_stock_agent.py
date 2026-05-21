# tests/agents/test_stock_agent.py

from types import SimpleNamespace
import asyncio

import pytest

from app.agents import stock_agent
from app.core.california_config import CaliforniaRegion


# ─────────────────────────────────
# Test helpers
# ─────────────────────────────────

def enum_value(value):
    return SimpleNamespace(value=value)


@pytest.fixture
def user():
    """Minimal California-shaped user object for stock_agent v5.2."""
    return SimpleNamespace(
        personal=SimpleNamespace(age=34),
        location=SimpleNamespace(
            region=CaliforniaRegion.BAY_AREA,
            city="Sunnyvale",
        ),
        professional=SimpleNamespace(
            profession="Cloud Engineer",
            sector=enum_value("Technology"),
            employment_status=enum_value("full-time"),
            interests=["ai/ml", "investing"],
            prior_experience="Built cloud infrastructure and follows public markets.",
            weekly_hours=enum_value("15-30"),
        ),
        financial=SimpleNamespace(
            income=18000,
            expenses=7000,
            monthly_debt=0,
            savings=50000,
            currency=enum_value("USD"),
        ),
        preferences=SimpleNamespace(
            risk_profile=enum_value("high"),
            horizon=enum_value("8+"),
        ),
    )


@pytest.fixture
def margin_config():
    return {
        "loan_amount": 25000,
        "loan_years": 5,
        "savings_to_use": 50000,
        "interest_rate": 0.09,
    }


@pytest.fixture(autouse=True)
def block_real_llm_calls(monkeypatch):
    """Fail fast if this unit test accidentally tries to call a live LLM."""

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Stock-agent unit test attempted a real LLM call")

    monkeypatch.setattr(stock_agent, "call_llm", fail_if_called)


# ─────────────────────────────────
# Core helpers / config validation
# ─────────────────────────────────

def test_calculate_margin_interest():
    assert stock_agent._calculate_margin_interest(25000, 0.09) == 2250
    assert stock_agent._calculate_margin_interest(0, 0.09) == 0
    assert stock_agent._calculate_margin_interest(25000, 0) == 0


@pytest.mark.parametrize(
    "config, expected_valid, expected_loan_amount, expected_reason",
    [
        (
            {"loan_amount": 25000, "savings_to_use": 0},
            False,
            25000,
            "requires savings collateral",
        ),
        (
            {"loan_amount": 70000, "savings_to_use": 50000},
            True,
            50000,
            "",
        ),
        (
            {"loan_amount": 25000, "savings_to_use": 50000},
            True,
            25000,
            "",
        ),
    ],
)
def test_validate_stock_config(config, expected_valid, expected_loan_amount, expected_reason):
    is_valid, reason, capped_config = stock_agent._validate_stock_config(config)

    assert is_valid is expected_valid
    assert capped_config["loan_amount"] == expected_loan_amount
    assert expected_reason in reason


# ─────────────────────────────────
# Prompt building
# ─────────────────────────────────

def test_build_prompt_includes_current_california_profile_and_margin_config(user, margin_config):
    prompt = stock_agent.build_prompt(user, margin_config, rag_context="RAG CONTEXT HERE")

    assert "Age: 34" in prompt
    assert "Region: Bay Area" in prompt
    assert "Sector: Technology" in prompt
    assert "Interests: ai/ml, investing" in prompt
    assert "Prior experience: Built cloud infrastructure and follows public markets." in prompt
    assert "Weekly hours: 15-30" in prompt
    assert "Income: $18,000/mo" in prompt
    assert "Savings: $50,000" in prompt
    assert "FUNDING MODE: MARGIN-LEVERAGED" in prompt
    assert "Margin loan: $25,000 @ 9.00%" in prompt
    assert "Savings collateral: $50,000" in prompt
    assert "Total invested: $75,000" in prompt
    assert "PREFERENCES: high risk, 8+ yr horizon" in prompt
    assert "CA Capital Gains Tax" in prompt
    assert "RAG CONTEXT HERE" in prompt


def test_build_prompt_supports_cash_only_mode(user):
    prompt = stock_agent.build_prompt(
        user,
        {"loan_amount": 0, "loan_years": 0, "savings_to_use": 20000, "interest_rate": 0},
    )

    assert "FUNDING MODE: CASH-ONLY" in prompt
    assert "Savings invested: $20,000" in prompt
    assert "No margin interest burden" in prompt


def test_build_prompt_uses_defaults_for_missing_interests_and_experience(user, margin_config):
    user.professional.interests = []
    user.professional.prior_experience = None

    prompt = stock_agent.build_prompt(user, margin_config)

    assert "Interests: Not specified" in prompt
    assert "Prior experience: No prior investing experience" in prompt


# ─────────────────────────────────
# Validation
# ─────────────────────────────────

def valid_raw_stock_output():
    return {
        "title": "AI Infrastructure ETF Portfolio",
        "type": "tech_growth",
        "description": (
            "A California-aware growth portfolio focused on diversified AI and "
            "cloud infrastructure exposure."
        ),
        "allocation": {
            "stocks_etfs": 60000,
            "bonds": 5000,
            "reits": 5000,
            "cash_reserve": 2500,
            "international": 2500,
        },
        "expected_return": 0.12,
        "risk": 0.60,
        "stability": 0.45,
        "portfolio_composition": {
            "asset_classes": [
                {"name": "Nasdaq 100 ETF", "ticker": "QQQ", "weight_pct": 45, "expected_return_pct": 12},
                {"name": "S&P 500 ETF", "ticker": "VOO", "weight_pct": 25, "expected_return_pct": 8},
                {"name": "International ETF", "ticker": "VXUS", "weight_pct": 15, "expected_return_pct": 7},
                {"name": "Bond ETF", "ticker": "BND", "weight_pct": 10, "expected_return_pct": 4},
                {"name": "Cash Reserve", "ticker": "CASH", "weight_pct": 5, "expected_return_pct": 2},
            ],
            "dividend_yield_pct": 1.2,
            "expense_ratio_pct": 0.20,
        },
        "market_context": {
            "market_regime": "neutral",
            "sp500_yoy_change_pct": 12,
            "vix_level": 19,
            "ca_capital_gains_tax_pct": 13.3,
            "expected_volatility_pct": 22,
        },
        "scenarios": {
            "best_case": {
                "price_appreciation_pct": 18,
                "dividend_yield_pct": 1.5,
                "total_roi_pct": 19.5,
                "narrative": "AI growth bull case.",
            },
            "base_case": {
                "price_appreciation_pct": 8,
                "dividend_yield_pct": 1.2,
                "total_roi_pct": 9.2,
                "narrative": "Normal growth case.",
            },
            "worst_case": {
                "price_appreciation_pct": -20,
                "dividend_yield_pct": 1.2,
                "total_roi_pct": -18.8,
                "narrative": "Growth-stock drawdown.",
            },
        },
        "break_even": {
            "months_to_breakeven": 18,
            "drawdown_recovery_months": 24,
            "explanation": "Recovery after a typical growth-stock drawdown.",
        },
        "margin_call_risk": {
            "trigger_drawdown_pct": 25,
            "expected_severity_loss": 0.30,
            "explanation": "Moderate margin-call risk under a sharp drawdown.",
        },
        "pros": ["Diversified AI exposure"],
        "cons": ["High volatility"],
        "next_steps": ["Confirm risk tolerance", "Use limit orders"],
        "time_to_profit": "3-5 years",
    }


def test_validate_stock_output_returns_current_v52_schema(user, margin_config):
    result = stock_agent.validate_stock_output(
        valid_raw_stock_output(),
        user=user,
        config=margin_config,
    )

    assert result["agent"] == "stock"
    assert result["title"].startswith("[Margin]")
    assert result["type"] == "tech_growth"
    assert result["description"]
    assert set(result["allocation"]) == {
        "stocks_etfs",
        "bonds",
        "reits",
        "cash_reserve",
        "international",
    }
    assert sum(result["allocation"].values()) == pytest.approx(75000, abs=0.01)
    assert -0.20 <= result["expected_return"] <= 0.15
    assert 0 <= result["risk"] <= 1
    assert 0 <= result["stability"] <= 1
    assert result["derived_status_override"] in {
        "profitable",
        "marginal",
        "not_profitable",
    }
    assert "portfolio_composition" in result
    assert "market_context" in result
    assert "projections" in result
    assert "scenarios" in result
    assert "break_even" in result
    assert "margin_call_risk" in result
    assert "calculation_breakdown" in result


def test_validate_stock_output_defaults_type_normalizes_weights_and_clamps_values(
    user, margin_config
):
    raw = {
        "title": "Overstated Stock Strategy",
        "type": "not_a_real_stock_type",
        "risk": -10,
        "stability": 99,
        "portfolio_composition": {
            "asset_classes": [
                {"name": "S&P 500 ETF", "ticker": "VOO", "weight_pct": 80, "expected_return_pct": 99},
                {"name": "Bond ETF", "ticker": "BND", "weight_pct": 40, "expected_return_pct": -99},
            ],
            "dividend_yield_pct": 99,
            "expense_ratio_pct": 99,
        },
        "market_context": {
            "market_regime": "invalid",
            "vix_level": 999,
            "expected_volatility_pct": 999,
        },
    }

    result = stock_agent.validate_stock_output(raw, user=user, config=margin_config)

    assert result["type"] == "etf_diversified"
    assert result["risk"] == 0
    assert result["stability"] == 1
    assert result["portfolio_composition"]["dividend_yield_pct"] == 10
    assert result["portfolio_composition"]["expense_ratio_pct"] == 2
    assert sum(
        ac["weight_pct"] for ac in result["portfolio_composition"]["asset_classes"]
    ) == pytest.approx(100, abs=0.20)
    assert result["market_context"]["market_regime"] == "neutral"
    assert result["market_context"]["vix_level"] == 80
    assert result["market_context"]["expected_volatility_pct"] == 50


# ─────────────────────────────────
# Async agent flow
# ─────────────────────────────────

def test_generate_stock_strategy_llm_uses_rag_prompt_retry_wrapper_and_margin_agent_name(
    monkeypatch, user, margin_config
):
    captured = {}

    def fake_build_rag_context(user_arg):
        assert user_arg is user
        return "RAG MOCK", ["chunk-stock-1"]

    def fake_call_llm(prompt):
        captured["prompt"] = prompt
        return '{"title": "Raw result"}'

    async def fake_call_llm_with_retry(llm_call, agent_name):
        captured["agent_name"] = agent_name
        captured["llm_result"] = llm_call()
        return {"title": "Raw result"}

    monkeypatch.setattr(stock_agent, "_build_rag_context", fake_build_rag_context)
    monkeypatch.setattr(stock_agent, "call_llm", fake_call_llm)
    monkeypatch.setattr(stock_agent, "call_llm_with_retry", fake_call_llm_with_retry)

    result, rag_sources = asyncio.run(stock_agent.generate_stock_strategy_llm(user, margin_config))

    assert result == {"title": "Raw result"}
    assert rag_sources == ["chunk-stock-1"]
    assert captured["agent_name"] == "stock_margin"
    assert "RAG MOCK" in captured["prompt"]
    assert "FUNDING MODE: MARGIN-LEVERAGED" in captured["prompt"]


def test_run_stock_agent_rejects_margin_without_savings(user):
    result = asyncio.run(
        stock_agent.run_stock_agent(
            user,
            {"loan_amount": 25000, "loan_years": 5, "savings_to_use": 0, "interest_rate": 0.09},
        )
    )

    assert result["rejected"] is True
    assert result["funding_mode"] == "rejected"
    assert "requires savings collateral" in result["rejection_reason"]


def test_run_stock_agent_generates_validates_caps_margin_and_adds_metadata(
    monkeypatch, user
):
    input_config = {
        "loan_amount": 70000,
        "loan_years": 5,
        "savings_to_use": 50000,
        "interest_rate": 0.09,
    }
    captured = {}

    async def fake_generate_stock_strategy_llm(user_arg, config_arg):
        assert user_arg is user
        captured["config"] = config_arg
        return valid_raw_stock_output(), ["chunk-stock-1", "chunk-tax-1"]

    monkeypatch.setattr(
        stock_agent,
        "generate_stock_strategy_llm",
        fake_generate_stock_strategy_llm,
    )

    result = asyncio.run(stock_agent.run_stock_agent(user, input_config))

    assert captured["config"]["loan_amount"] == 50000  # capped to savings_to_use
    assert result["agent"] == "stock"
    assert result["rejected"] is False
    assert result["rag_sources"] == ["chunk-stock-1", "chunk-tax-1"]
    assert result["funding_mode"] == "margin"
    assert result["loan_amount"] == 50000
    assert result["loan_years"] == 5
    assert result["savings_used"] == 50000
    assert result["interest_rate"] == 0.09
    assert result["total_capital"] == 100000
    assert result["title"].startswith("[Margin]")


def test_run_stock_agent_defaults_to_all_savings_when_config_is_none(monkeypatch, user):
    captured = {}

    async def fake_generate_stock_strategy_llm(user_arg, config_arg):
        captured["config"] = config_arg
        return valid_raw_stock_output(), []

    monkeypatch.setattr(stock_agent, "generate_stock_strategy_llm", fake_generate_stock_strategy_llm)

    result = asyncio.run(stock_agent.run_stock_agent(user, None))

    assert captured["config"] == {
        "loan_amount": 0,
        "loan_years": 0,
        "savings_to_use": 50000,
        "interest_rate": 0,
    }
    assert result["funding_mode"] == "cash"
    assert result["total_capital"] == 50000
    assert result["title"].startswith("[Cash-Only]")
