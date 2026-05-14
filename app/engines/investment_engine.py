# app/engines/investment_engine.py

"""
California / US investment engine with REAL amortization-based net return.

Key features:
- Per-strategy loan type (business, mortgage, margin, none)
- Real net return = gross_return - annual_loan_payment (not just rate subtraction)
- Margin call risk modeling for stock leveraged strategies
- 5 strategy variants: business, business_cash, real_estate, stock_cash, stock_margin
- REIT detection: real_estate type=REIT skips mortgage automatically
"""

from app.engines.inflation_engine import real_return, AgentType


# ─────────────────────────────────
# 🎯 SCORE FORMULA
# Based on NET return (after all costs), not just gross
# ─────────────────────────────────
def calculate_score(net_return: float, risk: float, stability: float) -> float:
    """
    Score weighted toward net return (50%) + stability (30%) + low risk (20%).
    Negative net_return → still scored (low) so user sees comparison.
    """
    return round(
        net_return * 0.5 +
        stability * 0.3 +
        (1 - risk) * 0.2,
        4
    )


# ─────────────────────────────────
# 🏦 STRATEGY → LOAN TYPE MAPPING
# Each strategy uses different loan with different terms
# ⭐ business_cash added for "business with savings only" option
# ─────────────────────────────────
STRATEGY_LOAN_MAPPING = {
    "business": "business",  # Business loan (7%, 7yr)
    "business_cash": None,  # ⭐ NEW: business funded by savings only
    "real_estate": "mortgage",  # Mortgage (5.5%, 30yr) — except REIT
    "stock": None,  # Cash by default
    "stock_cash": None,  # Explicitly cash
    "stock_margin": "margin",  # Margin loan (8%, callable)
}


# ─────────────────────────────────
# 💸 AMORTIZATION CALCULATOR
# ─────────────────────────────────
def calculate_annual_payment(loan_amount: float, annual_rate: float, years: int) -> float:
    """
    Standard PMT formula for amortizing loan.
    Returns annual payment (principal + interest).
    """
    if loan_amount == 0 or years == 0:
        return 0.0

    monthly_rate = annual_rate / 12
    months = years * 12

    if monthly_rate == 0:
        monthly_payment = loan_amount / months
    else:
        monthly_payment = (
                loan_amount * monthly_rate * ((1 + monthly_rate) ** months)
                / ((1 + monthly_rate) ** months - 1)
        )

    return round(monthly_payment * 12, 2)


# ─────────────────────────────────
# 📉 MARGIN CALL RISK MODEL — ⭐ SOFTENED (BUG #4 FIX)
# Stock margin loans have unique risk — broker can force liquidation
# Previous coefficients were too punitive (40-50% probability for typical ETFs)
# Realistic margin call rates: 5-25% for diversified ETF portfolios
# ─────────────────────────────────
def calculate_margin_call_risk(real_roi: float, volatility: float, ltv: float = 0.5) -> dict:
    """
    Estimates margin call probability based on:
    - Expected return (negative returns → higher call risk)
    - Volatility (stock risk parameter)
    - LTV ratio (higher LTV → less buffer)

    Margin call triggers when equity / total_value < maintenance_margin (25%)

    ⭐ SOFTENED MODEL:
    - Reduced base coefficient (0.5 → 0.3) for realistic ETF portfolios
    - Smaller LTV penalty with higher threshold (0.3 → 0.4)
    - Reduced return penalty (×2 → ×1) for negative ROI scenarios
    - Lower severity baseline (15-35% → 10-25%)
    """
    # ⭐ Reduced from 0.5 to 0.3 — realistic for diversified ETFs
    base_probability = volatility * 0.3  # 0.0 to ~0.24 for typical risk

    # ⭐ Smaller LTV penalty, higher threshold
    ltv_penalty = max(0, (ltv - 0.4) * 0.3)  # ~0 to 0.03

    # ⭐ Reduced negative return penalty (×1 instead of ×2)
    return_penalty = max(0, -real_roi * 1.0)  # if real_roi = -10%, penalty = 0.10

    # ⭐ Capped at 60% instead of 95% (realistic worst case)
    probability = min(0.60, base_probability + ltv_penalty + return_penalty)

    # ⭐ Reduced severity: forced liquidation loss 10-25% (was 15-35%)
    severity = 0.10 + (volatility * 0.15)

    return {
        "margin_call_probability": round(probability, 3),
        "expected_severity_loss": round(severity, 3),
        "risk_adjusted_penalty": round(probability * severity, 4),
    }


# ─────────────────────────────────
# 🔍 CORE EVALUATION
# Evaluates ONE strategy against its specific loan
# ─────────────────────────────────
def evaluate_single_strategy(
        user,
        agent_data: dict,
        strategy_loans: dict,
) -> dict:
    """
    Evaluates a single strategy with its OWN loan (not shared with others).

    ⭐ BUG #2 FIX: real_estate strategies with type="REIT" now skip mortgage
       (REITs are publicly traded, no property purchase = no mortgage needed)
    """
    currency = user.financial.currency.value
    savings = user.financial.savings

    agent_name = agent_data["agent"]
    nominal = agent_data["expected_return"]
    risk = agent_data.get("risk", 0.5)
    stability = agent_data.get("stability", 0.5)

    # Map sub-variants to base types for inflation calculator
    # ⭐ business_cash maps to "business" for inflation calc
    if agent_name in ("stock_cash", "stock_margin"):
        base_agent_name = "stock"
    elif agent_name == "business_cash":
        base_agent_name = "business"
    else:
        base_agent_name = agent_name

    agent_type = AgentType(base_agent_name)

    # 📉 REAL ROI (after inflation)
    real_roi = real_return(
        nominal_return=nominal,
        agent=agent_type,
        currency=currency
    )

    # 🏦 DETERMINE LOAN FOR THIS STRATEGY
    loan_type = STRATEGY_LOAN_MAPPING.get(agent_name)

    # Strategy → loan key mapping for strategy_loans dict
    loan_key_mapping = {
        "business": "business",
        "business_cash": None,  # ⭐ NEW: no loan needed
        "real_estate": "real_estate",
        "stock": None,
        "stock_cash": None,
        "stock_margin": "stock_margin",
    }
    loan_key = loan_key_mapping.get(agent_name)

    # Get the specific loan offer for this strategy
    loan = strategy_loans.get(loan_key) if loan_key else None

    # ⭐ BUG #2 FIX: Check if real_estate is REIT (no mortgage needed)
    re_type = agent_data.get("type", "")
    is_reit = (agent_name == "real_estate" and re_type == "REIT")

    if is_reit:
        # REIT uses cash, not mortgage — public REITs traded like stocks
        loan = None
        loan_key = None
        loan_type = None

    # 💰 CALCULATE CAPITAL
    if loan and loan.get("approved"):
        loan_amount = loan["max_loan_amount"]
        loan_rate = loan["interest_rate"]
        loan_years = loan["loan_years"]
        total_capital = savings + loan_amount

        annual_payment = calculate_annual_payment(loan_amount, loan_rate, loan_years)

        uses_loan = True
        loan_info = {
            "type": loan_type,
            "amount": loan_amount,
            "rate": loan_rate,
            "years": loan_years,
            "annual_payment": annual_payment,
            "monthly_payment": round(annual_payment / 12, 2),
            "total_interest": round(annual_payment * loan_years - loan_amount, 2),
        }
    else:
        # Cash-only strategy (includes REIT and business_cash now!)
        loan_amount = 0
        annual_payment = 0
        total_capital = savings
        uses_loan = False

        # ⭐ Different label for REIT vs general cash
        if is_reit:
            cash_label = "reit_no_mortgage"
        elif agent_name == "business_cash":
            cash_label = "business_cash_only"
        else:
            cash_label = "cash_only"

        loan_info = {
            "type": cash_label,
            "amount": 0,
            "rate": 0,
            "years": 0,
            "annual_payment": 0,
            "monthly_payment": 0,
            "total_interest": 0,
        }

    # 📊 RETURN CALCULATIONS
    gross_return_dollars = total_capital * real_roi
    net_return_dollars = gross_return_dollars - annual_payment

    if total_capital > 0:
        net_return_pct = net_return_dollars / total_capital
    else:
        net_return_pct = 0

    # 🚨 MARGIN CALL RISK (only for stock_margin)
    margin_call_info = None
    if agent_name == "stock_margin" and uses_loan:
        margin_call_info = calculate_margin_call_risk(
            real_roi=real_roi,
            volatility=risk,
            ltv=0.5
        )
        # Adjust BOTH dollar and percentage by expected margin call loss
        risk_adjustment_pct = margin_call_info["risk_adjusted_penalty"]
        net_return_pct = net_return_pct - risk_adjustment_pct

        # Also adjust dollar amount to match percentage
        risk_adjustment_dollars = total_capital * risk_adjustment_pct
        net_return_dollars = net_return_dollars - risk_adjustment_dollars

    # 🎯 STATUS
    if net_return_pct > 0.01:
        status = "profitable"
    elif net_return_pct > -0.02:
        status = "marginal"
    else:
        status = "not_profitable"

    # 🏆 SCORE
    score = calculate_score(net_return_pct, risk, stability)

    # 📦 ENRICHED OUTPUT
    enriched = {
        **agent_data,
        "agent": agent_name,
        "nominal_return": round(nominal, 4),
        "real_return": round(real_roi, 4),
        "total_capital": round(total_capital, 2),
        "gross_return_dollars": round(gross_return_dollars, 2),
        "annual_payment": round(annual_payment, 2),
        "net_return_dollars": round(net_return_dollars, 2),
        "net_return": round(net_return_pct, 4),
        "uses_loan": uses_loan,
        "loan_info": loan_info,
        "score": score,
        "status": status,
    }

    if margin_call_info:
        enriched["margin_call_risk"] = margin_call_info

    return enriched


# ─────────────────────────────────
# 🔍 CORE ENGINE — EVALUATE ALL
# ─────────────────────────────────
def evaluate_investments(user, agents_results: list, strategy_loans: dict) -> list:
    """
    Evaluates all agent strategies with their OWN loan types.
    """
    results = []
    for agent_data in agents_results:
        enriched = evaluate_single_strategy(user, agent_data, strategy_loans)
        results.append(enriched)
    return results


# ─────────────────────────────────
# 🏆 RANKING
# ─────────────────────────────────
def rank_investments(results: list) -> list:
    return sorted(results, key=lambda x: x["score"], reverse=True)


# ─────────────────────────────────
# 🚀 FINAL PIPELINE
# ─────────────────────────────────
def get_best_investments(user, agents_results: list, strategy_loans: dict) -> list:
    """
    Args:
        user: UserInput
        agents_results: List of strategies from agents
                        (business, business_cash, real_estate, stock_cash, stock_margin)
        strategy_loans: {"business": loan, "real_estate": loan, "stock_margin": loan, "personal": loan}
    """
    evaluated = evaluate_investments(user, agents_results, strategy_loans)
    ranked = rank_investments(evaluated)
    return ranked