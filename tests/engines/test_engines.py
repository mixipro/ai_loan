# tests/engines/test_engines.py

from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.models.user import UserInput
from app.core.california_config import CaliforniaRegion
from app.engines import risk_engine, interest_engine, loan_engine
from app.engines import inflation_engine, investment_engine, california_tax_engine
from app.engines.inflation_engine import AgentType


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────


def _base_user_payload(**overrides):
    payload = {
        "personal": {"age": 35},
        "location": {"region": "BAY_AREA", "city": "Palo Alto"},
        "financial": {
            "income": 12_000,
            "expenses": 4_000,
            "monthly_debt": 500,
            "savings": 100_000,
            "currency": "USD",
        },
        "professional": {
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "full-time",
            "interests": ["programming", "ai/ml", "investing"],
            "prior_experience": "Built internal tools and small SaaS products.",
            "weekly_hours": "15-30",
            "tech_role": "Software Engineer",
            "equity_compensation": "None",
            "company_stage": "Public Company",
            "qsbs_eligible": False,
            "entertainment_role": "Not Applicable",
        },
        "preferences": {"risk_profile": "medium", "horizon": "5-8"},
    }

    for section, values in overrides.items():
        if isinstance(values, dict) and section in payload and isinstance(payload[section], dict):
            payload[section].update(values)
        else:
            payload[section] = values

    return payload


@pytest.fixture
def bay_area_tech_user():
    return UserInput(**_base_user_payload())


@pytest.fixture
def high_income_user():
    return UserInput(**_base_user_payload(
        financial={
            "income": 50_000,
            "expenses": 5_000,
            "monthly_debt": 0,
            "savings": 20_000,
            "currency": "USD",
        }
    ))


def _namespace_user(*, income=3_000, expenses=1_000, debt=0, savings=10_000, region="BAY_AREA"):
    return SimpleNamespace(
        financial=SimpleNamespace(
            income=income,
            expenses=expenses,
            monthly_debt=debt,
            savings=savings,
            currency=SimpleNamespace(value="USD"),
        ),
        location=SimpleNamespace(region=SimpleNamespace(value=region)),
    )


# ─────────────────────────────────────────────────────────────
# risk_engine
# ─────────────────────────────────────────────────────────────


def test_risk_engine_scores_bay_area_tech_user_as_low_risk(bay_area_tech_user):
    result = risk_engine.calculate_risk_score(bay_area_tech_user)

    assert result["level"] == "low_risk"
    assert result["creditworthiness"] == "high"
    assert result["region"] == "BAY_AREA"
    assert result["region_display_name"] == "Bay Area"
    assert result["country"] == "US"

    # Score components: disposable + savings + debt + employment + age + Bay Area tech premium.
    assert result["base_score"] == 19
    assert result["adjusted_score"] == pytest.approx(22.35)
    assert result["industry_adjustment"] == 5
    assert result["equity_bonus"] == 0
    assert result["disposable_income"] == 8_000
    assert result["debt_ratio"] == pytest.approx(0.04)


def test_risk_engine_applies_equity_compensation_bonus():
    user = UserInput(**_base_user_payload(
        professional={"equity_compensation": "RSU (Restricted Stock Units)"}
    ))

    result = risk_engine.calculate_risk_score(user)

    assert result["equity_bonus"] == 1
    assert result["base_score"] == 20
    assert result["adjusted_score"] == pytest.approx(23.53)


def test_risk_engine_penalizes_la_entertainment_volatility():
    user = UserInput(**_base_user_payload(
        location={"region": "LOS_ANGELES", "city": "Burbank"},
        professional={
            "sector": "Entertainment",
            "profession": "Producer",
            "employment_status": "freelancer",
            "weekly_hours": "30+",
            "tech_role": None,
            "equity_compensation": "None",
            "company_stage": "Not Applicable",
            "entertainment_role": "Independent Contractor",
        },
    ))

    result = risk_engine.calculate_risk_score(user)

    assert result["region"] == "LOS_ANGELES"
    assert result["industry_adjustment"] == -2
    assert result["region_factor"] == 1.0


# ─────────────────────────────────────────────────────────────
# interest_engine
# ─────────────────────────────────────────────────────────────


def test_interest_engine_low_risk_uses_minimum_business_rate():
    risk = {"level": "low_risk", "adjusted_score": 20}

    result = interest_engine.calculate_interest_rate(risk, loan_type="business")

    assert result["loan_type"] == "business"
    assert result["risk_level"] == "low_risk"
    assert result["interest_rate"] == pytest.approx(0.07)
    assert result["base_rate"] == pytest.approx(0.07)
    assert result["min_rate"] == 0.07
    assert result["max_rate"] == 0.13
    assert result["default_years"] == 7
    assert result["max_years"] == 10


def test_interest_engine_medium_risk_blends_base_and_score_rate():
    risk = {"level": "medium_risk", "adjusted_score": 8}

    result = interest_engine.calculate_interest_rate(risk, loan_type="personal")

    assert result["interest_rate"] == pytest.approx(0.1088)
    assert result["base_rate"] == pytest.approx(0.11)
    assert result["score_rate"] == pytest.approx(0.107)
    assert result["dti_limit"] == 0.35


def test_interest_engine_calculates_all_supported_loan_rates():
    risk = {"level": "low_risk", "adjusted_score": 15}

    result = interest_engine.calculate_all_loan_rates(risk)

    assert set(result) == {"personal", "business", "mortgage", "margin", "sbloc"}
    assert result["mortgage"]["loan_type"] == "mortgage"
    assert result["margin"]["loan_type"] == "margin"


@pytest.mark.parametrize(
    "risk,loan_type,expected_message",
    [
        ({"level": "low_risk", "adjusted_score": 10}, "crypto", "Unsupported loan type"),
        ({"level": "low_risk"}, "personal", "Invalid risk input"),
    ],
)
def test_interest_engine_rejects_invalid_inputs(risk, loan_type, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        interest_engine.calculate_interest_rate(risk, loan_type=loan_type)


# ─────────────────────────────────────────────────────────────
# loan_engine
# ─────────────────────────────────────────────────────────────


def test_loan_engine_approves_business_loan_with_dti_limit(bay_area_tech_user):
    risk = {"level": "low_risk"}
    interest = {"interest_rate": 0.07}

    result = loan_engine.calculate_loan_offer(
        bay_area_tech_user,
        risk,
        interest,
        loan_type="business",
    )

    assert result["approved"] is True
    assert result["loan_type"] == "business"
    assert result["loan_years"] == interest_engine.LOAN_TYPES["business"]["default_years"]
    assert result["interest_rate"] == 0.07
    assert result["monthly_payment"] <= result["max_allowed_payment"]
    assert result["dti_used"] <= interest_engine.LOAN_TYPES["business"]["dti_limit"]
    assert result["region"] == "BAY_AREA"


def test_loan_engine_rejects_when_no_disposable_income():
    user = _namespace_user(income=3_000, expenses=3_500, debt=0)

    result = loan_engine.calculate_loan_offer(
        user,
        {"level": "low_risk"},
        {"interest_rate": 0.07},
        loan_type="personal",
    )

    assert result == {"approved": False, "reason": "No disposable income"}


def test_loan_engine_rejects_when_existing_debt_exceeds_dti_limit():
    user = _namespace_user(income=3_000, expenses=1_000, debt=2_000)

    result = loan_engine.calculate_loan_offer(
        user,
        {"level": "low_risk"},
        {"interest_rate": 0.07},
        loan_type="personal",
    )

    assert result == {"approved": False, "reason": "Existing debt exceeds DTI limit"}


def test_loan_engine_caps_margin_loan_at_50_percent_of_savings(high_income_user):
    result = loan_engine.calculate_loan_offer(
        high_income_user,
        {"level": "low_risk"},
        {"interest_rate": 0.08},
        loan_type="margin",
    )

    assert result["approved"] is True
    assert result["loan_type"] == "margin"
    assert result["max_loan_amount"] == 10_000


def test_loan_engine_caps_mortgage_at_four_times_savings(high_income_user):
    result = loan_engine.calculate_loan_offer(
        high_income_user,
        {"level": "low_risk"},
        {"interest_rate": 0.06},
        loan_type="mortgage",
    )

    assert result["approved"] is True
    assert result["loan_type"] == "mortgage"
    assert result["max_loan_amount"] == 80_000


def test_loan_engine_applies_medium_and_high_risk_haircuts(bay_area_tech_user):
    low = loan_engine.calculate_loan_offer(
        bay_area_tech_user, {"level": "low_risk"}, {"interest_rate": 0.07}, "business"
    )
    medium = loan_engine.calculate_loan_offer(
        bay_area_tech_user, {"level": "medium_risk"}, {"interest_rate": 0.07}, "business"
    )
    high = loan_engine.calculate_loan_offer(
        bay_area_tech_user, {"level": "high_risk"}, {"interest_rate": 0.07}, "business"
    )

    assert medium["max_loan_amount"] == pytest.approx(low["max_loan_amount"] * 0.85, abs=1.0)
    assert high["max_loan_amount"] == pytest.approx(low["max_loan_amount"] * 0.70, abs=1.0)


def test_loan_engine_calculates_all_strategy_loans(bay_area_tech_user):
    all_rates = {
        "business": {"interest_rate": 0.07},
        "mortgage": {"interest_rate": 0.06},
        "margin": {"interest_rate": 0.09},
        "personal": {"interest_rate": 0.10},
    }

    result = loan_engine.calculate_all_strategy_loans(
        bay_area_tech_user,
        {"level": "low_risk"},
        all_rates,
    )

    assert set(result) == {"business", "real_estate", "stock_margin", "personal"}
    assert result["business"]["loan_type"] == "business"
    assert result["real_estate"]["loan_type"] == "mortgage"
    assert result["stock_margin"]["loan_type"] == "margin"


def test_loan_engine_custom_loan_zero_amount_returns_no_loan_scenario(bay_area_tech_user):
    result = loan_engine.calculate_custom_loan(
        loan_amount=0,
        loan_years=5,
        annual_rate=0.07,
        user=bay_area_tech_user,
        risk={"level": "low_risk"},
        loan_type="business",
    )

    assert result["approved"] is True
    assert result["scenario"] == "no_loan"
    assert result["loan_amount"] == 0
    assert result["monthly_payment"] == 0


def test_loan_engine_custom_loan_rejects_excess_years(bay_area_tech_user):
    result = loan_engine.calculate_custom_loan(
        loan_amount=10_000,
        loan_years=11,
        annual_rate=0.07,
        user=bay_area_tech_user,
        risk={"level": "low_risk"},
        loan_type="business",
    )

    assert result["approved"] is False
    assert "exceeds maximum" in result["reason"]


# ─────────────────────────────────────────────────────────────
# inflation_engine
# ─────────────────────────────────────────────────────────────


def test_inflation_engine_returns_us_baseline_for_all_agent_types():
    for agent in (AgentType.STOCK, AgentType.REAL_ESTATE, AgentType.BUSINESS):
        assert inflation_engine.get_inflation_rate(agent, "USD") == pytest.approx(
            inflation_engine.US_INFLATION_BASELINE
        )


def test_inflation_engine_adjusts_present_and_future_value():
    amount = 10_000
    years = 2
    rate = inflation_engine.US_INFLATION_BASELINE

    assert inflation_engine.adjust_for_inflation(amount, years, AgentType.STOCK) == pytest.approx(
        round(amount / ((1 + rate) ** years), 2)
    )
    assert inflation_engine.future_value(amount, years, AgentType.STOCK) == pytest.approx(
        round(amount * ((1 + rate) ** years), 2)
    )


def test_inflation_engine_real_return_uses_fisher_equation():
    nominal = 0.10
    rate = inflation_engine.US_INFLATION_BASELINE

    result = inflation_engine.real_return(nominal, AgentType.BUSINESS)

    assert result == pytest.approx(round((1 + nominal) / (1 + rate) - 1, 4))


def test_inflation_engine_legacy_wrapper_ignores_country():
    direct = inflation_engine.get_inflation_rate(AgentType.REAL_ESTATE, "USD")
    legacy = inflation_engine.get_inflation_rate_legacy(AgentType.REAL_ESTATE, "RS", "USD")

    assert legacy == direct


# ─────────────────────────────────────────────────────────────
# investment_engine
# ─────────────────────────────────────────────────────────────


def test_investment_engine_score_formula():
    result = investment_engine.calculate_score(net_return=0.10, risk=0.40, stability=0.70)

    assert result == pytest.approx(0.38)


def test_investment_engine_annual_payment_margin_is_interest_only():
    margin_payment = investment_engine.calculate_annual_payment(10_000, 0.10, 5, loan_type="margin")
    amortized_payment = investment_engine.calculate_annual_payment(10_000, 0.10, 5, loan_type="business")

    assert margin_payment == 1_000
    assert amortized_payment > margin_payment


def test_investment_engine_annual_payment_handles_zero_loan():
    assert investment_engine.calculate_annual_payment(0, 0.10, 5) == 0
    assert investment_engine.calculate_annual_payment(10_000, 0.10, 0) == 0


def test_investment_engine_margin_call_risk_is_bounded():
    result = investment_engine.calculate_margin_call_risk(real_roi=-0.20, volatility=2.0, ltv=0.8)

    assert result["margin_call_probability"] <= 0.60
    assert result["expected_severity_loss"] > 0
    assert result["risk_adjusted_penalty"] == pytest.approx(
        result["margin_call_probability"] * result["expected_severity_loss"], abs=0.001
    )


def test_investment_engine_evaluates_cash_only_strategy(bay_area_tech_user):
    agent = {
        "agent": "business",
        "title": "Cash services business",
        "expected_return": 0.10,
        "risk": 0.40,
        "stability": 0.70,
        "savings_used": 10_000,
        "loan_amount": 0,
        "funding_mode": "cash",
    }

    result = investment_engine.evaluate_single_strategy(
        bay_area_tech_user,
        agent,
        strategy_loans={},
    )

    assert result["uses_loan"] is False
    assert result["loan_info"]["type"] == "business_cash_only"
    assert result["total_capital"] == 10_000
    assert result["nominal_return"] == 0.10
    assert result["real_return"] == inflation_engine.real_return(0.10, AgentType.BUSINESS)
    assert result["net_return"] == result["real_return"]
    assert result["status"] in {"profitable", "marginal", "not_profitable"}


def test_investment_engine_evaluates_config_driven_business_loan(bay_area_tech_user):
    agent = {
        "agent": "business",
        "title": "Loan-backed business",
        "expected_return": 0.20,
        "risk": 0.50,
        "stability": 0.50,
        "savings_used": 10_000,
        "loan_amount": 50_000,
        "funding_mode": "mixed",
    }
    loans = {
        "business": {
            "approved": True,
            "max_loan_amount": 50_000,
            "interest_rate": 0.07,
            "loan_years": 7,
        }
    }

    result = investment_engine.evaluate_single_strategy(bay_area_tech_user, agent, loans)

    assert result["uses_loan"] is True
    assert result["loan_info"]["type"] == "business"
    assert result["loan_info"]["amount"] == 50_000
    assert result["total_capital"] == 60_000
    assert result["annual_payment"] > 0
    assert result["net_return_dollars"] == pytest.approx(
        result["gross_return_dollars"] - result["annual_payment"], abs=0.01
    )


def test_investment_engine_reit_skips_mortgage_even_when_loan_is_present(bay_area_tech_user):
    agent = {
        "agent": "real_estate",
        "type": "REIT",
        "title": "REIT exposure",
        "expected_return": 0.08,
        "risk": 0.35,
        "stability": 0.75,
        "savings_used": 20_000,
        "loan_amount": 80_000,
        "funding_mode": "mortgage",
    }
    loans = {
        "real_estate": {
            "approved": True,
            "max_loan_amount": 80_000,
            "interest_rate": 0.06,
            "loan_years": 30,
        }
    }

    result = investment_engine.evaluate_single_strategy(bay_area_tech_user, agent, loans)

    assert result["uses_loan"] is False
    assert result["loan_info"]["type"] == "reit_no_mortgage"
    assert result["annual_payment"] == 0
    assert result["total_capital"] == 20_000


def test_investment_engine_stock_margin_uses_existing_margin_call_risk(bay_area_tech_user):
    agent = {
        "agent": "stock",
        "title": "Margin stock strategy",
        "expected_return": 0.12,
        "risk": 0.50,
        "stability": 0.60,
        "savings_used": 20_000,
        "loan_amount": 10_000,
        "funding_mode": "margin",
        "margin_call_risk": {
            "margin_call_probability": 0.20,
            "expected_severity_loss": 0.15,
        },
    }
    loans = {
        "stock": {
            "approved": True,
            "max_loan_amount": 10_000,
            "interest_rate": 0.10,
            "loan_years": 5,
        }
    }

    result = investment_engine.evaluate_single_strategy(bay_area_tech_user, agent, loans)

    assert result["uses_loan"] is True
    assert result["loan_info"]["type"] == "margin"
    assert result["annual_payment"] == 1_000
    assert result["margin_call_risk"]["risk_adjusted_penalty"] == pytest.approx(0.03)


def test_investment_engine_downgrades_agent_profitable_status_when_net_return_is_negative(bay_area_tech_user):
    agent = {
        "agent": "business",
        "title": "Weak loan-backed business",
        "expected_return": 0.02,
        "risk": 0.50,
        "stability": 0.50,
        "savings_used": 5_000,
        "loan_amount": 80_000,
        "funding_mode": "mixed",
        "derived_status_override": "profitable",
    }
    loans = {
        "business": {
            "approved": True,
            "max_loan_amount": 80_000,
            "interest_rate": 0.13,
            "loan_years": 7,
        }
    }

    result = investment_engine.evaluate_single_strategy(bay_area_tech_user, agent, loans)

    assert result["net_return"] < 0
    assert result["status"] in {"marginal", "not_profitable"}


def test_investment_engine_evaluates_and_ranks_multiple_strategies(bay_area_tech_user):
    agents = [
        {
            "agent": "business",
            "title": "Business",
            "expected_return": 0.05,
            "risk": 0.70,
            "stability": 0.30,
            "savings_used": 10_000,
            "loan_amount": 0,
            "funding_mode": "cash",
        },
        {
            "agent": "stock",
            "title": "Stocks",
            "expected_return": 0.12,
            "risk": 0.40,
            "stability": 0.70,
            "savings_used": 10_000,
            "loan_amount": 0,
            "funding_mode": "cash",
        },
    ]

    result = investment_engine.get_best_investments(bay_area_tech_user, agents, strategy_loans={})

    assert len(result) == 2
    assert result == sorted(result, key=lambda item: item["score"], reverse=True)
    assert result[0]["score"] >= result[1]["score"]


# ─────────────────────────────────────────────────────────────
# california_tax_engine
# ─────────────────────────────────────────────────────────────


def test_tax_engine_progressive_tax_with_custom_brackets():
    brackets = [(10_000, 0.10), (20_000, 0.20)]

    assert california_tax_engine._calculate_progressive_tax(0, brackets) == 0
    assert california_tax_engine._calculate_progressive_tax(5_000, brackets) == 500
    assert california_tax_engine._calculate_progressive_tax(15_000, brackets) == 2_000
    assert california_tax_engine._calculate_progressive_tax(25_000, brackets) == 3_000


def test_tax_engine_total_income_tax_shape_and_consistency():
    result = california_tax_engine.calculate_total_income_tax(250_000)

    assert result["gross_income"] == 250_000
    assert result["state_tax"] > 0
    assert result["federal_tax"] > 0
    assert result["total_tax"] == pytest.approx(result["state_tax"] + result["federal_tax"])
    assert result["after_tax_income"] == pytest.approx(250_000 - result["total_tax"])
    assert 0 < result["effective_rate"] < 1
    assert 0 < result["marginal_rate"] < 1


def test_tax_engine_mental_health_tax_applies_above_one_million():
    below = california_tax_engine.calculate_california_state_tax(1_000_000)
    above = california_tax_engine.calculate_california_state_tax(1_100_000)

    assert above > below
    assert above - below > 100_000 * 0.01


def test_tax_engine_prop13_assessed_value_grows_slower_than_market_value():
    result = california_tax_engine.calculate_property_tax_prop13(
        purchase_price=500_000,
        years_owned=10,
    )

    assert result["assessed_value"] < result["market_value_estimate"]
    assert result["annual_tax"] < result["new_buyer_would_pay"]
    assert result["annual_savings_vs_new_buyer"] > 0
    assert "Prop 13" in result["explanation"]


def test_tax_engine_qsbs_rejects_short_holding_period():
    result = california_tax_engine.calculate_qsbs_benefit(
        sale_proceeds=2_000_000,
        cost_basis=100_000,
        holding_years=3,
    )

    assert result["qualifies"] is False
    assert result["potential_savings"] == 0
    assert "5 year minimum" in result["reason"]


def test_tax_engine_qsbs_caps_exclusion_at_ten_million():
    result = california_tax_engine.calculate_qsbs_benefit(
        sale_proceeds=12_000_000,
        cost_basis=0,
        holding_years=5,
    )

    assert result["qualifies"] is True
    assert result["capital_gain"] == 12_000_000
    assert result["excluded_amount"] == 10_000_000
    assert result["taxable_amount"] == 2_000_000
    assert result["savings"] == pytest.approx(3_330_000)


def test_tax_engine_analysis_adds_high_income_recommendations():
    result = california_tax_engine.analyze_california_tax_situation(1_200_000)

    assert result["gross_income"] == 1_200_000
    assert any("Mental Health Tax" in recommendation for recommendation in result["recommendations"])
    assert any("Mega Backdoor Roth" in recommendation for recommendation in result["recommendations"])
