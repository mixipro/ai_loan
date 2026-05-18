# app/engines/investment_engine.py

"""
California / US investment engine with REAL amortization-based net return.

v4.0 (CONFIG-DRIVEN):
- Per-strategy capital from user config (savings_to_use + loan_amount)
- Each agent embeds funding_mode in its result (cash / loan / mixed / margin / mortgage)
- Investment engine uses funding_mode to decide if loan applies

Legacy support:
- Old agent names (stock_cash, stock_margin, business_cash) still work
- REIT detection: real_estate type=REIT skips mortgage automatically
"""

from app.engines.inflation_engine import real_return, AgentType


# ─────────────────────────────────
# 🎯 SCORE FORMULA
# ─────────────────────────────────
def calculate_score(net_return: float, risk: float, stability: float) -> float:
    """
    Score weighted toward net return (50%) + stability (30%) + low risk (20%).
    """
    return round(
        net_return * 0.5 +
        stability * 0.3 +
        (1 - risk) * 0.2,
        4
    )


# ─────────────────────────────────
# 🏦 LOAN TYPE PER AGENT
# (Actual loan usage depends on funding_mode from agent result)
# ─────────────────────────────────
LOAN_TYPE_BY_AGENT = {
    "business": "business",
    "real_estate": "mortgage",
    "stock": "margin",
    # Legacy support
    "business_cash": None,
    "stock_cash": None,
    "stock_margin": "margin",
}


# ─────────────────────────────────
# 💸 AMORTIZATION CALCULATOR
# ─────────────────────────────────
def calculate_annual_payment(
        loan_amount: float,
        annual_rate: float,
        years: int,
        loan_type: str = "amortized",
) -> float:
    """
    Calculate annual loan burden depending on loan type.

    ⭐ v5.2.2 BUG #2 FIX:
      - "margin"     → INTEREST ONLY (broker doesn't require principal repayment)
                       Principal returned when position sold.
      - "amortized"  → STANDARD PMT formula (principal + interest)
                       Used for business loans, mortgages.

    Returns annual payment (USD).
    """
    if loan_amount == 0 or years == 0:
        return 0.0

    # ⭐ v5.2.2: Special case for margin loans
    if loan_type == "margin":
        # Margin loans charge interest only on borrowed amount
        # Principal is returned when investor sells the position
        return round(loan_amount * annual_rate, 2)

    # Standard amortization (business, mortgage)
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
# 📉 MARGIN CALL RISK MODEL
# ─────────────────────────────────
def calculate_margin_call_risk(real_roi: float, volatility: float, ltv: float = 0.5) -> dict:
    """
    Estimates margin call probability for leveraged stock positions.

    Softened model (BUG #4 FIX):
    - Reduced base coefficient (0.3) for realistic ETF portfolios
    - Smaller LTV penalty with higher threshold (0.4)
    - Reduced return penalty (×1) for negative ROI scenarios
    - Capped at 60% (realistic worst case)
    """
    base_probability = volatility * 0.3
    ltv_penalty = max(0, (ltv - 0.4) * 0.3)
    return_penalty = max(0, -real_roi * 1.0)

    probability = min(0.60, base_probability + ltv_penalty + return_penalty)
    severity = 0.10 + (volatility * 0.15)

    return {
        "margin_call_probability": round(probability, 3),
        "expected_severity_loss": round(severity, 3),
        "risk_adjusted_penalty": round(probability * severity, 4),
    }


# ─────────────────────────────────
# 🔍 CORE EVALUATION (v4.0 — config-aware)
# ─────────────────────────────────
def evaluate_single_strategy(
        user,
        agent_data: dict,
        strategy_loans: dict,
) -> dict:
    """
    Evaluates a single strategy with its OWN loan + capital from user config.

    v4.0 LOGIC:
    - Uses agent_data['funding_mode'] to decide whether loan applies
    - Uses agent_data['savings_used'] (per-strategy) instead of user.savings
    - Uses agent_data['loan_amount'] from config

    Legacy support: Old agent names still work via fallback mapping.

    BUG #2: real_estate type=REIT skips mortgage (REITs trade like stocks).
    """
    currency = user.financial.currency.value

    agent_name = agent_data["agent"]
    nominal = agent_data["expected_return"]
    risk = agent_data.get("risk", 0.5)
    stability = agent_data.get("stability", 0.5)

    # ⭐ v4.0: agent embeds savings_used and loan_amount in result
    savings_used = agent_data.get("savings_used", user.financial.savings)
    config_loan_amount = agent_data.get("loan_amount", 0)
    funding_mode = agent_data.get("funding_mode", "")

    # Map sub-variants to base types for inflation calculator
    if agent_name in ("stock_cash", "stock_margin", "stock"):
        base_agent_name = "stock"
    elif agent_name in ("business", "business_cash"):
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
    uses_loan_now = False
    loan_key = None
    loan_type = None

    if config_loan_amount > 0 and funding_mode in ("loan", "mixed", "margin", "mortgage"):
        # v4.0: agent told us this strategy uses a loan
        loan_type = LOAN_TYPE_BY_AGENT.get(agent_name)

        # Map agent name → strategy_loans key
        if agent_name == "business":
            loan_key = "business"
        elif agent_name == "real_estate":
            loan_key = "real_estate"
        elif agent_name == "stock":
            loan_key = "stock"  # orchestrator adds this alias
        else:
            loan_key = agent_name
        uses_loan_now = True
    else:
        # Legacy mapping (for old agent names)
        legacy_mapping = {
            "business": "business",
            "business_cash": None,
            "real_estate": "real_estate",
            "stock": None,
            "stock_cash": None,
            "stock_margin": "stock_margin",
        }
        legacy_loan_types = {
            "business": "business",
            "real_estate": "mortgage",
            "stock_margin": "margin",
        }
        loan_key = legacy_mapping.get(agent_name)
        loan_type = legacy_loan_types.get(agent_name)
        uses_loan_now = bool(loan_key)

    # Get the actual loan offer
    loan = strategy_loans.get(loan_key) if loan_key else None

    # BUG #2 FIX: REIT detection
    re_type = agent_data.get("type", "")
    is_reit = (agent_name == "real_estate" and re_type == "REIT")

    if is_reit:
        loan = None
        loan_key = None
        loan_type = None
        uses_loan_now = False

    # 💰 CALCULATE CAPITAL
    if loan and loan.get("approved") and uses_loan_now:
        loan_amount = loan["max_loan_amount"]
        loan_rate = loan["interest_rate"]
        loan_years = loan["loan_years"]

        # ⭐ v4.0: total_capital = savings_used + loan_amount
        total_capital = savings_used + loan_amount

        annual_payment = calculate_annual_payment(loan_amount, loan_rate, loan_years, loan_type=loan_type)

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
        # Cash-only strategy
        loan_amount = 0
        annual_payment = 0

        # ⭐ v4.0: total_capital = savings_used (per-strategy)
        total_capital = savings_used if savings_used > 0 else user.financial.savings
        uses_loan = False

        if is_reit:
            cash_label = "reit_no_mortgage"
        elif agent_name in ("business_cash",) or funding_mode == "cash":
            cash_label = f"{base_agent_name}_cash_only"
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

    # 🚨 MARGIN CALL RISK — v5.2.3: Respect agent's value for consistency
    margin_call_info = None
    is_stock_margin = (
            (agent_name == "stock_margin") or
            (agent_name == "stock" and funding_mode == "margin")
    )
    if is_stock_margin and uses_loan:
        # Check if stock_agent already provided margin_call_risk (preferred)
        existing_margin_call = agent_data.get("margin_call_risk")

        if existing_margin_call and existing_margin_call.get("margin_call_probability", 0) > 0:
            # Use agent's value — ensures consistency between calc_breakdown and summary
            margin_call_info = dict(existing_margin_call)
        else:
            # Fallback: compute fresh
            margin_call_info = calculate_margin_call_risk(
                real_roi=real_roi,
                volatility=risk,
                ltv=0.5
            )

        # Ensure risk_adjusted_penalty exists
        if "risk_adjusted_penalty" not in margin_call_info:
            prob = margin_call_info.get("margin_call_probability", 0)
            sev = margin_call_info.get("expected_severity_loss", 0)
            margin_call_info["risk_adjusted_penalty"] = round(prob * sev, 4)

        risk_adjustment_pct = margin_call_info["risk_adjusted_penalty"]
        net_return_pct = net_return_pct - risk_adjustment_pct
        risk_adjustment_dollars = total_capital * risk_adjustment_pct
        net_return_dollars = net_return_dollars - risk_adjustment_dollars

    # 🎯 STATUS — v5.2.3: HYBRID logic
    # Agent generates preliminary status from projections (Y1/Y3 cash flow).
    # Investment engine FINALIZES status after loan amortization + inflation.
    # If agent says "profitable" but post-loan net_return is negative, DOWNGRADE.
    agent_status_override = agent_data.get("derived_status_override")

    if agent_status_override == "profitable" and net_return_pct < 0:
        # Agent thinks profitable, but post-loan economics disagree → downgrade
        if net_return_pct > -0.05:
            status = "marginal"  # Small negative net (-5% to 0%)
        else:
            status = "not_profitable"  # Big negative net (< -5%)
    elif agent_status_override == "marginal" and net_return_pct < -0.05:
        # Agent thinks marginal but loss is significant → downgrade further
        status = "not_profitable"
    elif agent_status_override in ("profitable", "marginal", "not_profitable"):
        status = agent_status_override
    elif net_return_pct > 0.01:
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
# 🔍 EVALUATE ALL
# ─────────────────────────────────
def evaluate_investments(user, agents_results: list, strategy_loans: dict) -> list:
    """Evaluates all agent strategies with their OWN loan types."""
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
    Main entry point — evaluates and ranks all strategies.

    Args:
        user: UserInput
        agents_results: List of strategies from agents (3 in v4.0)
        strategy_loans: Loan offers keyed by strategy
    """
    evaluated = evaluate_investments(user, agents_results, strategy_loans)
    ranked = rank_investments(evaluated)
    return ranked
