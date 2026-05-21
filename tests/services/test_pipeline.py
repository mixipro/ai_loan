"""
Current CaliforniaCFO deterministic pipeline tests.

These replace the legacy pre-California engine pipeline tests. They validate the
non-LLM pipeline pieces used before agent execution:

    UserInput -> risk -> all loan rates -> all strategy loans

They also include a small investment-engine integration check using deterministic
mock strategies. No LLM or external API calls are made.
"""

from copy import deepcopy

import pytest

from app.models.user import UserInput
from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_all_loan_rates, calculate_interest_rate
from app.engines.loan_engine import calculate_all_strategy_loans, calculate_loan_offer
from app.engines.investment_engine import get_best_investments


# ─────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────


def make_user(**overrides) -> UserInput:
    payload = {
        "personal": {"age": 35},
        "location": {"region": "BAY_AREA", "city": "San Francisco"},
        "financial": {
            "income": 26000,
            "expenses": 7000,
            "monthly_debt": 0,
            "savings": 500000,
            "currency": "USD",
        },
        "professional": {
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "full-time",
            "interests": ["ai/ml", "investing"],
            "prior_experience": "Built internal automation tools.",
            "weekly_hours": "15-30",
            "tech_role": "Software Engineer",
            "equity_compensation": "RSU (Restricted Stock Units)",
            "company_stage": "Public Company",
            "qsbs_eligible": False,
            "entertainment_role": "Not Applicable",
        },
        "preferences": {"risk_profile": "medium", "horizon": "5-8"},
    }

    for section, values in overrides.items():
        if isinstance(values, dict) and section in payload:
            payload[section] = {**payload[section], **values}
        else:
            payload[section] = values

    return UserInput(**payload)


def run_engine_pipeline(user: UserInput) -> tuple[dict, dict, dict]:
    risk = calculate_risk_score(user)
    rates = calculate_all_loan_rates(risk)
    loans = calculate_all_strategy_loans(user, risk, rates)
    return risk, rates, loans


def make_strategy_loans() -> dict:
    return {
        "business": {
            "approved": False,
            "max_loan_amount": 0,
            "loan_amount": 0,
            "interest_rate": 0,
            "loan_years": 0,
        },
        "real_estate": {
            "approved": False,
            "max_loan_amount": 0,
            "loan_amount": 0,
            "interest_rate": 0,
            "loan_years": 0,
        },
        "stock_margin": {
            "approved": False,
            "max_loan_amount": 0,
            "loan_amount": 0,
            "interest_rate": 0,
            "loan_years": 0,
        },
        "stock": {
            "approved": False,
            "max_loan_amount": 0,
            "loan_amount": 0,
            "interest_rate": 0,
            "loan_years": 0,
        },
    }


# ─────────────────────────────────────────────────────────────
# Risk -> rates -> loans pipeline
# ─────────────────────────────────────────────────────────────


def test_engine_pipeline_success_for_california_user():
    user = make_user()

    risk, rates, loans = run_engine_pipeline(user)

    assert risk["country"] == "US"
    assert risk["region"] == "BAY_AREA"
    assert risk["level"] in {"low_risk", "medium_risk", "high_risk"}
    assert risk["creditworthiness"] in {"high", "medium", "low"}
    assert risk["disposable_income"] == 19000

    assert set(rates) == {"personal", "business", "mortgage", "margin", "sbloc"}
    assert rates["business"]["loan_type"] == "business"
    assert rates["mortgage"]["loan_type"] == "mortgage"
    assert rates["margin"]["loan_type"] == "margin"

    assert set(loans) == {"business", "real_estate", "stock_margin", "personal"}
    assert loans["business"]["approved"] is True
    assert loans["real_estate"]["approved"] is True
    assert loans["stock_margin"]["approved"] is True
    assert loans["personal"]["approved"] is True

    for loan in loans.values():
        assert loan["country"] == "US"
        assert loan["region"] == "BAY_AREA"
        assert loan["max_loan_amount"] >= 0
        assert loan["monthly_payment"] >= 0
        assert loan["interest_rate"] > 0


def test_margin_loan_is_capped_at_50_percent_of_savings():
    user = make_user(financial={"savings": 100000})
    risk, rates, loans = run_engine_pipeline(user)

    assert loans["stock_margin"]["approved"] is True
    assert loans["stock_margin"]["max_loan_amount"] <= user.financial.savings * 0.5


def test_mortgage_is_capped_by_twenty_percent_down_payment_rule():
    user = make_user(financial={"savings": 100000})
    risk, rates, loans = run_engine_pipeline(user)

    assert loans["real_estate"]["approved"] is True
    assert loans["real_estate"]["max_loan_amount"] <= user.financial.savings * 4.0


def test_business_and_mortgage_reject_when_existing_debt_exceeds_dti_buffer():
    user = make_user(
        financial={
            "income": 5000,
            "expenses": 1000,
            "monthly_debt": 2200,
            "savings": 80000,
        }
    )
    risk = calculate_risk_score(user)

    business_rate = calculate_interest_rate(risk, "business")
    mortgage_rate = calculate_interest_rate(risk, "mortgage")

    business_loan = calculate_loan_offer(user, risk, business_rate, "business")
    mortgage_loan = calculate_loan_offer(user, risk, mortgage_rate, "mortgage")

    assert business_loan["approved"] is False
    assert business_loan["reason"] == "Existing debt exceeds DTI limit"
    assert mortgage_loan["approved"] is False
    assert mortgage_loan["reason"] == "Existing debt exceeds DTI limit"


# ─────────────────────────────────────────────────────────────
# Investment engine integration with deterministic strategies
# ─────────────────────────────────────────────────────────────


def test_investment_engine_ranks_deterministic_cash_strategies():
    user = make_user(financial={"savings": 300000})
    strategy_loans = make_strategy_loans()

    agent_results = [
        {
            "agent": "business",
            "title": "Cash services business",
            "type": "services",
            "expected_return": 0.12,
            "risk": 0.55,
            "stability": 0.60,
            "allocation": {"setup": "70%", "reserve": "30%"},
            "time_to_profit": "12-24 months",
            "funding_mode": "cash",
            "loan_amount": 0,
            "savings_used": 100000,
        },
        {
            "agent": "real_estate",
            "title": "Cash REIT-like real estate exposure",
            "type": "REIT",
            "expected_return": 0.07,
            "risk": 0.35,
            "stability": 0.80,
            "allocation": {"reit": "90%", "reserve": "10%"},
            "time_to_profit": "2-3 years",
            "funding_mode": "cash",
            "loan_amount": 0,
            "savings_used": 100000,
        },
        {
            "agent": "stock",
            "title": "Cash diversified ETF portfolio",
            "expected_return": 0.10,
            "risk": 0.45,
            "stability": 0.70,
            "allocation": {"VOO": "60%", "BND": "20%", "cash": "20%"},
            "time_to_profit": "5-8 years",
            "funding_mode": "cash",
            "loan_amount": 0,
            "savings_used": 100000,
        },
    ]

    ranked = get_best_investments(user, deepcopy(agent_results), strategy_loans)

    assert len(ranked) == 3
    assert {item["agent"] for item in ranked} == {"business", "real_estate", "stock"}

    scores = [item["score"] for item in ranked]
    assert scores == sorted(scores, reverse=True)

    for item in ranked:
        assert item["uses_loan"] is False
        assert item["total_capital"] == 100000
        assert isinstance(item["net_return"], float)
        assert item["status"] in {"profitable", "marginal", "not_profitable", "rejected"}
        assert item["loan_info"]["amount"] == 0


def test_investment_engine_applies_strategy_specific_margin_loan():
    user = make_user(financial={"savings": 200000})
    strategy_loans = make_strategy_loans()
    strategy_loans["stock"] = {
        "approved": True,
        "max_loan_amount": 50000,
        "loan_amount": 50000,
        "interest_rate": 0.10,
        "loan_years": 5,
    }
    strategy_loans["stock_margin"] = deepcopy(strategy_loans["stock"])

    ranked = get_best_investments(
        user,
        [
            {
                "agent": "stock",
                "title": "Margin ETF portfolio",
                "expected_return": 0.12,
                "risk": 0.40,
                "stability": 0.70,
                "allocation": {"VOO": "70%", "cash": "30%"},
                "time_to_profit": "5-8 years",
                "funding_mode": "margin",
                "loan_amount": 50000,
                "savings_used": 100000,
            }
        ],
        strategy_loans,
    )

    stock = ranked[0]

    assert stock["agent"] == "stock"
    assert stock["uses_loan"] is True
    assert stock["loan_info"]["type"] == "margin"
    assert stock["loan_info"]["amount"] == 50000
    assert stock["loan_info"]["annual_payment"] == 5000
    assert stock["total_capital"] == 150000
