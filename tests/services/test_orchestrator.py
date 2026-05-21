import asyncio
from copy import deepcopy
import pytest
from app.models.user import UserInput
from app.services import orchestrator


# ─────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────


def make_user(**overrides) -> UserInput:
    payload = {
        "personal": {"age": 34},
        "location": {"region": "BAY_AREA", "city": "San Francisco"},
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
            "interests": ["ai/ml", "investing", "programming"],
            "prior_experience": "Built AI infrastructure tools.",
            "weekly_hours": "30+",
            "tech_role": "Software Engineer",
            "equity_compensation": "RSU (Restricted Stock Units)",
            "company_stage": "Public Company",
            "qsbs_eligible": False,
            "entertainment_role": "Not Applicable",
        },
        "preferences": {"risk_profile": "high", "horizon": "8+"},
    }

    for section, values in overrides.items():
        if isinstance(values, dict) and section in payload:
            payload[section] = {**payload[section], **values}
        else:
            payload[section] = values

    return UserInput(**payload)


def make_config() -> dict:
    return {
        "business": {
            "loan_amount": 100000,
            "loan_years": 7,
            "savings_to_use": 120000,
            "interest_rate": 0.09,
        },
        "real_estate": {
            "loan_amount": 320000,
            "loan_years": 30,
            "savings_to_use": 120000,
            "interest_rate": 0.065,
        },
        "stock": {
            "loan_amount": 50000,
            "loan_years": 5,
            "savings_to_use": 100000,
            "interest_rate": 0.10,
        },
    }


def make_agent_result(
        agent: str,
        expected_return: float,
        *,
        risk: float = 0.45,
        stability: float = 0.70,
        funding_mode: str = "cash",
        loan_amount: float = 0,
        savings_used: float = 100000,
        rejected: bool = False,
) -> dict:
    base = {
        "agent": agent,
        "title": f"{agent} test strategy",
        "description": f"Deterministic {agent} strategy for orchestrator tests.",
        "allocation": {"core": "80%", "reserve": "20%"},
        "expected_return": expected_return,
        "risk": risk,
        "stability": stability,
        "pros": ["deterministic"],
        "cons": [],
        "next_steps": ["review"],
        "time_to_profit": "3-5 years",
        "funding_mode": funding_mode,
        "loan_amount": loan_amount,
        "savings_used": savings_used,
        "rag_sources": [],
        "projections": {
            "year_1": {},
            "year_3": {},
            "year_5": {},
        },
    }

    if agent == "real_estate":
        base["type"] = "rental"
        base["projections"] = {
            "year_1": {"total_return": 12000},
            "year_3": {"total_return": 18000},
            "year_5": {"total_return": 22000},
        }
    elif agent == "business":
        base["type"] = "services"
        base["projections"] = {
            "year_1": {"net_cash_flow": 10000},
            "year_3": {"net_cash_flow": 26000},
            "year_5": {"net_cash_flow": 36000},
        }
    elif agent == "stock":
        base["projections"] = {
            "year_1": {"net_return": 9000},
            "year_3": {"net_return": 20000},
            "year_5": {"net_return": 32000},
        }

    if rejected:
        base.update(
            {
                "rejected": True,
                "rejection_reason": f"{agent} rejected for test",
                "expected_return": 0,
                "risk": 0,
                "stability": 0,
            }
        )

    return base


@pytest.fixture
def user() -> UserInput:
    return make_user()


@pytest.fixture
def config() -> dict:
    return make_config()


# ─────────────────────────────────────────────────────────────
# Loan/config shim tests
# ─────────────────────────────────────────────────────────────


def test_build_strategy_loans_from_config(config):
    loans = orchestrator._build_strategy_loans_from_config(config)

    assert set(loans) == {"business", "real_estate", "stock_margin", "stock"}

    assert loans["business"]["approved"] is True
    assert loans["business"]["loan_type"] == "business"
    assert loans["business"]["max_loan_amount"] == 100000
    assert loans["business"]["savings_to_use"] == 120000
    assert loans["business"]["monthly_payment"] > 0
    assert loans["business"]["annual_payment"] > 0

    assert loans["real_estate"]["loan_type"] == "mortgage"
    assert loans["real_estate"]["loan_years"] == 30

    assert loans["stock"]["loan_type"] == "margin"
    assert loans["stock"] == loans["stock_margin"]


def test_build_strategy_loans_handles_zero_loan_config():
    loans = orchestrator._build_strategy_loans_from_config(
        {
            "business": {"loan_amount": 0, "loan_years": 0, "savings_to_use": 50000, "interest_rate": 0},
            "real_estate": {"loan_amount": 0, "loan_years": 0, "savings_to_use": 0, "interest_rate": 0},
            "stock": {"loan_amount": 0, "loan_years": 0, "savings_to_use": 25000, "interest_rate": 0},
        }
    )

    assert loans["business"]["approved"] is False
    assert loans["business"]["monthly_payment"] == 0
    assert loans["business"]["annual_payment"] == 0
    assert loans["stock"]["approved"] is False


# ─────────────────────────────────────────────────────────────
# Helper output tests
# ─────────────────────────────────────────────────────────────


def test_build_user_summary_uses_california_fields(user):
    summary = orchestrator._build_user_summary(user)

    assert summary == {
        "region": "BAY_AREA",
        "city": "San Francisco",
        "country": "US",
        "age": 34,
        "income": 28000,
        "expenses": 7000,
        "monthly_debt": 0,
        "savings": 650000,
        "currency": "USD",
        "risk_profile": "high",
        "horizon": "8+",
    }


def test_build_risk_explanation_separates_investment_preference_from_creditworthiness():
    explanation = orchestrator.build_risk_explanation("high", "low")

    assert "HIGH" in explanation
    assert "LOW" in explanation
    assert "loan terms" in explanation
    assert "investment selection" in explanation


# ─────────────────────────────────────────────────────────────
# run_all_agents tests
# ─────────────────────────────────────────────────────────────


def test_run_all_agents_passes_each_strategy_its_own_config(monkeypatch, user, config):
    captured = {}

    async def fake_business(user_arg, config_arg):
        captured["business"] = (user_arg, deepcopy(config_arg))
        return make_agent_result("business", 0.12)

    async def fake_real_estate(user_arg, config_arg):
        captured["real_estate"] = (user_arg, deepcopy(config_arg))
        return make_agent_result("real_estate", 0.07)

    async def fake_stock(user_arg, config_arg):
        captured["stock"] = (user_arg, deepcopy(config_arg))
        return make_agent_result("stock", 0.10)

    monkeypatch.setattr(orchestrator, "run_business_agent", fake_business)
    monkeypatch.setattr(orchestrator, "run_real_estate_agent", fake_real_estate)
    monkeypatch.setattr(orchestrator, "run_stock_agent", fake_stock)

    results = asyncio.run(orchestrator.run_all_agents(user, config))

    assert {r["agent"] for r in results} == {"business", "real_estate", "stock"}
    assert captured["business"] == (user, config["business"])
    assert captured["real_estate"] == (user, config["real_estate"])
    assert captured["stock"] == (user, config["stock"])


def test_run_all_agents_converts_agent_exception_to_rejected_result(monkeypatch, user, config):
    async def broken_business(user_arg, config_arg):
        raise RuntimeError("business boom")

    async def fake_real_estate(user_arg, config_arg):
        return make_agent_result("real_estate", 0.07)

    async def fake_stock(user_arg, config_arg):
        return make_agent_result("stock", 0.10)

    monkeypatch.setattr(orchestrator, "run_business_agent", broken_business)
    monkeypatch.setattr(orchestrator, "run_real_estate_agent", fake_real_estate)
    monkeypatch.setattr(orchestrator, "run_stock_agent", fake_stock)

    results = asyncio.run(orchestrator.run_all_agents(user, config))
    by_agent = {r["agent"]: r for r in results}

    assert by_agent["business"]["rejected"] is True
    assert "business boom" in by_agent["business"]["rejection_reason"]
    assert by_agent["real_estate"].get("rejected") is not True
    assert by_agent["stock"].get("rejected") is not True


# ─────────────────────────────────────────────────────────────
# run_pipeline tests
# ─────────────────────────────────────────────────────────────


def test_run_pipeline_returns_current_response_shape_without_llm(monkeypatch, user, config):
    captured = {}

    async def fake_run_all_agents(user_arg, config_arg):
        captured["run_all_agents"] = (user_arg, deepcopy(config_arg))
        return [
            make_agent_result(
                "business",
                0.16,
                risk=0.55,
                stability=0.62,
                funding_mode="mixed",
                loan_amount=config_arg["business"]["loan_amount"],
                savings_used=config_arg["business"]["savings_to_use"],
            ),
            make_agent_result(
                "real_estate",
                0.07,
                risk=0.35,
                stability=0.82,
                funding_mode="mortgage",
                loan_amount=config_arg["real_estate"]["loan_amount"],
                savings_used=config_arg["real_estate"]["savings_to_use"],
            ),
            make_agent_result(
                "stock",
                0.12,
                risk=0.50,
                stability=0.70,
                funding_mode="margin",
                loan_amount=config_arg["stock"]["loan_amount"],
                savings_used=config_arg["stock"]["savings_to_use"],
            ),
        ]

    async def fake_judge(user_arg, primary_loan_arg, strategies_arg):
        captured["judge"] = {
            "user": user_arg,
            "primary_loan": deepcopy(primary_loan_arg),
            "strategies": deepcopy(strategies_arg),
        }
        return {
            "recommended": strategies_arg[0],
            "reasoning": "mocked judge reasoning",
            "next_step": "review recommendation",
            "comparison": "mocked comparison",
            "profile_used": user_arg.preferences.risk_profile.value,
            "detailed_explanation": {"summary": "mocked"},
            "comparison_charts": {"roi": []},
        }

    monkeypatch.setattr(orchestrator, "run_all_agents", fake_run_all_agents)
    monkeypatch.setattr(orchestrator, "run_judge_agent", fake_judge)

    result = asyncio.run(orchestrator.run_pipeline(user, config))

    assert captured["run_all_agents"] == (user, config)
    assert captured["judge"]["user"] == user
    assert captured["judge"]["primary_loan"]["loan_type"] == "business"
    assert len(captured["judge"]["strategies"]) == 3

    assert result["user_summary"]["region"] == "BAY_AREA"
    assert result["user_summary"]["country"] == "US"
    assert result["risk"]["region"] == "BAY_AREA"
    assert result["risk"]["country"] == "US"

    assert result["config"] == config
    assert result["loans"]["business"]["loan_type"] == "business"
    assert result["loans"]["real_estate"]["loan_type"] == "mortgage"
    assert result["loans"]["stock"]["loan_type"] == "margin"

    assert len(result["strategies"]) == 3
    assert result["recommendation"] in result["strategies"]
    assert result["reasoning"] == "mocked judge reasoning"
    assert result["next_step"] == "review recommendation"
    assert result["comparison"] == "mocked comparison"
    assert result["profile_used"] == "high"
    assert result["rejected_count"] == 0
    assert result["detailed_explanation"] == {"summary": "mocked"}
    assert result["comparison_charts"] == {"roi": []}

    for strategy in result["strategies"]:
        assert "net_return" in strategy
        assert "score" in strategy
        assert "status" in strategy
        assert "loan_info" in strategy


def test_run_pipeline_handles_all_rejected_strategies_without_judge(monkeypatch, user, config):
    async def fake_run_all_agents(user_arg, config_arg):
        return [
            make_agent_result("business", 0, rejected=True),
            make_agent_result("real_estate", 0, rejected=True),
            make_agent_result("stock", 0, rejected=True),
        ]

    async def fail_if_judge_called(*args, **kwargs):
        raise AssertionError("Judge should not run when all strategies are rejected")

    monkeypatch.setattr(orchestrator, "run_all_agents", fake_run_all_agents)
    monkeypatch.setattr(orchestrator, "run_judge_agent", fail_if_judge_called)

    result = asyncio.run(orchestrator.run_pipeline(user, config))

    assert result["recommendation"] is None
    assert result["rejected_count"] == 3
    assert len(result["strategies"]) == 3
    assert all(strategy.get("rejected") is True for strategy in result["strategies"])
    assert "All strategies were rejected" in result["reasoning"]
    assert result["profile_used"] == "high"
