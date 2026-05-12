# app/engines/california_tax_engine.py

"""
California-specific tax calculations.
Includes state progressive tax, federal tax, Prop 13, and QSBS logic.
"""

from app.core.california_config import (
    CALIFORNIA_STATE_TAX_SINGLE, CALIFORNIA_STATE_TAX_MARRIED,
    FEDERAL_TAX_SINGLE, MENTAL_HEALTH_TAX_THRESHOLD, MENTAL_HEALTH_TAX_RATE,
    PROP_13_BASE_RATE, QSBS_EXCLUSION_MAX,
)


# ═══════════════════════════════════════════════════════════════
# 💰 INCOME TAX CALCULATION
# ═══════════════════════════════════════════════════════════════

def _calculate_progressive_tax(income: float, brackets: list[tuple]) -> float:
    """
    Generic progressive tax calculator.
    Brackets: list of (max_income, rate) tuples.
    """
    if income <= 0:
        return 0

    tax = 0.0
    previous_threshold = 0.0

    for max_income, rate in brackets:
        if income <= max_income:
            tax += (income - previous_threshold) * rate
            return tax
        else:
            tax += (max_income - previous_threshold) * rate
            previous_threshold = max_income

    return tax


def calculate_california_state_tax(income: float, married: bool = False) -> float:
    """Calculates California state income tax."""
    brackets = CALIFORNIA_STATE_TAX_MARRIED if married else CALIFORNIA_STATE_TAX_SINGLE
    base_tax = _calculate_progressive_tax(income, brackets)

    # Mental Health Tax (additional 1% on income > $1M)
    if income > MENTAL_HEALTH_TAX_THRESHOLD:
        base_tax += (income - MENTAL_HEALTH_TAX_THRESHOLD) * MENTAL_HEALTH_TAX_RATE

    return base_tax


def calculate_federal_tax(income: float) -> float:
    """Calculates federal income tax (single filer for simplicity)."""
    return _calculate_progressive_tax(income, FEDERAL_TAX_SINGLE)


def calculate_total_income_tax(income: float, married: bool = False) -> dict:
    """
    Returns full tax breakdown for an income.
    """
    state = calculate_california_state_tax(income, married)
    federal = calculate_federal_tax(income)
    total = state + federal

    effective_rate = total / income if income > 0 else 0
    after_tax = income - total

    # Calculate marginal rate (rate on next $1)
    state_marginal = calculate_california_state_tax(income + 1, married) - state
    federal_marginal = calculate_federal_tax(income + 1) - federal
    marginal_rate = state_marginal + federal_marginal

    return {
        "gross_income": income,
        "state_tax": round(state, 2),
        "federal_tax": round(federal, 2),
        "total_tax": round(total, 2),
        "after_tax_income": round(after_tax, 2),
        "effective_rate": round(effective_rate, 4),
        "marginal_rate": round(marginal_rate, 4),
    }


# ═══════════════════════════════════════════════════════════════
# 🏠 PROP 13 PROPERTY TAX
# ═══════════════════════════════════════════════════════════════

def calculate_property_tax_prop13(
        purchase_price: float,
        years_owned: int,
        local_surcharge: float = 0.005,
) -> dict:
    """
    Calculates property tax under Prop 13.

    Args:
        purchase_price: Original purchase price
        years_owned: How long owned (impacts assessed value via 2% cap)
        local_surcharge: Local additional assessments (Mello-Roos, etc.)

    Returns:
        Dict with annual tax + 30-year savings vs new buyer
    """
    # Assessed value grows max 2% per year
    assessed_value = purchase_price * ((1 + 0.02) ** years_owned)

    annual_tax = assessed_value * (PROP_13_BASE_RATE + local_surcharge)

    # If buying today at current market value (assume same property worth more)
    # New buyer would pay tax on current market value
    market_value = purchase_price * ((1 + 0.06) ** years_owned)  # ~6% appreciation
    new_buyer_tax = market_value * (PROP_13_BASE_RATE + local_surcharge)

    annual_savings = new_buyer_tax - annual_tax

    return {
        "purchase_price": purchase_price,
        "years_owned": years_owned,
        "assessed_value": round(assessed_value, 2),
        "market_value_estimate": round(market_value, 2),
        "annual_tax": round(annual_tax, 2),
        "new_buyer_would_pay": round(new_buyer_tax, 2),
        "annual_savings_vs_new_buyer": round(annual_savings, 2),
        "explanation": (
            f"Under Prop 13, owning {years_owned} years means assessed value capped at "
            f"${assessed_value:,.0f} (vs market ${market_value:,.0f}). "
            f"Annual savings vs new buyer: ${annual_savings:,.0f}."
        ),
    }


# ═══════════════════════════════════════════════════════════════
# 💎 QSBS EXCLUSION
# ═══════════════════════════════════════════════════════════════

def calculate_qsbs_benefit(
        sale_proceeds: float,
        cost_basis: float,
        holding_years: int,
) -> dict:
    """
    Calculates potential QSBS tax exclusion benefit.

    Args:
        sale_proceeds: Total received from selling startup stock
        cost_basis: Original cost (what you paid)
        holding_years: How long held

    Returns:
        Dict with tax savings analysis
    """
    capital_gain = sale_proceeds - cost_basis

    # QSBS requires 5+ year holding period
    qualifies = holding_years >= 5

    if not qualifies:
        return {
            "qualifies": False,
            "reason": f"Holding period {holding_years} years < 5 year minimum",
            "potential_savings": 0,
            "advice": "Hold for at least 5 years to qualify for QSBS exclusion",
        }

    # Exclusion capped at $10M
    excluded_gain = min(capital_gain, QSBS_EXCLUSION_MAX)
    taxable_gain = capital_gain - excluded_gain

    # What you'd pay WITHOUT QSBS:
    # - Federal capital gains: 20% (top bracket)
    # - California state: 13.3% (top bracket, treated as income)
    without_qsbs_federal = capital_gain * 0.20
    without_qsbs_state = capital_gain * 0.133
    without_qsbs_total = without_qsbs_federal + without_qsbs_state

    # What you actually pay WITH QSBS:
    with_qsbs_federal = taxable_gain * 0.20
    with_qsbs_state = taxable_gain * 0.133
    with_qsbs_total = with_qsbs_federal + with_qsbs_state

    savings = without_qsbs_total - with_qsbs_total

    return {
        "qualifies": True,
        "capital_gain": round(capital_gain, 2),
        "excluded_amount": round(excluded_gain, 2),
        "taxable_amount": round(taxable_gain, 2),
        "tax_without_qsbs": round(without_qsbs_total, 2),
        "tax_with_qsbs": round(with_qsbs_total, 2),
        "savings": round(savings, 2),
        "explanation": (
            f"QSBS exclusion saves ${savings:,.0f} on ${capital_gain:,.0f} gain. "
            f"Up to $10M is federal + state tax-free."
        ),
    }


# ═══════════════════════════════════════════════════════════════
# 🧮 COMBINED ANALYSIS
# ═══════════════════════════════════════════════════════════════

def analyze_california_tax_situation(income: float, married: bool = False) -> dict:
    """High-level tax analysis for California resident."""
    tax_breakdown = calculate_total_income_tax(income, married)

    # Tax-saving recommendations based on income level
    recommendations = []

    if income > 200000:
        recommendations.append("Consider maximizing 401(k) contributions ($23k/yr) to reduce taxable income")
        recommendations.append("Look into HSA if eligible ($4,150 individual / $8,300 family)")

    if income > 500000:
        recommendations.append("Consider Mega Backdoor Roth if employer 401(k) supports it")
        recommendations.append("California muni bonds offer double tax-free interest")

    if income > 1_000_000:
        recommendations.append("Mental Health Tax (1%) applies on income above $1M")
        recommendations.append("Charitable remainder trusts can reduce large gains")

    return {
        **tax_breakdown,
        "recommendations": recommendations,
    }