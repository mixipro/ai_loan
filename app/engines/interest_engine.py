# app/engines/interest_engine.py

"""
California / US interest rate calculator.
Uses fixed US baseline rates instead of country-specific ranges.
Live web search will override these in Phase 2.
"""

# US baseline rates for different loan types
# Live web search will dynamically update these in Phase 2
US_INTEREST_RANGE = {
    "personal": (0.065, 0.155),  # 6.5% - 15.5% personal loans
    "mortgage": (0.055, 0.085),  # 5.5% - 8.5% mortgages
    "business": (0.07, 0.13),  # 7% - 13% business loans
}

# Default loan type (personal)
DEFAULT_LOAN_TYPE = "personal"


def calculate_interest_rate(risk: dict, loan_type: str = DEFAULT_LOAN_TYPE) -> dict:
    """
    Calculates interest rate for a California user based on risk profile.

    Args:
        risk: output from risk_engine
        loan_type: "personal", "mortgage", or "business"

    Returns:
        Dict with rate calculation breakdown
    """

    # ─────────────────────────
    # 🔒 VALIDATION
    # ─────────────────────────
    if loan_type not in US_INTEREST_RANGE:
        raise ValueError(f"Unsupported loan type: {loan_type}")

    if "level" not in risk or "adjusted_score" not in risk:
        raise ValueError("Invalid risk input")

    # ─────────────────────────
    # 🇺🇸 US RATE RANGE
    # ─────────────────────────
    min_rate, max_rate = US_INTEREST_RANGE[loan_type]

    level = risk["level"]
    score = risk["adjusted_score"]

    # ─────────────────────────
    # 🎯 BASE (DISCRETE)
    # ─────────────────────────
    if level == "low_risk":
        base_rate = min_rate
    elif level == "medium_risk":
        base_rate = (min_rate + max_rate) / 2
    else:
        base_rate = max_rate

    # ─────────────────────────
    # 📈 CONTINUOUS MODEL
    # ─────────────────────────
    normalized = score / 15
    normalized = max(0, min(normalized, 1))

    # Higher score → lower rate
    score_rate = min_rate + (max_rate - min_rate) * (1 - normalized)

    # ─────────────────────────
    # ⚖️ BLEND MODEL
    # ─────────────────────────
    final_rate = (base_rate * 0.6) + (score_rate * 0.4)
    final_rate = max(min_rate, min(final_rate, max_rate))

    # ─────────────────────────
    # 📊 OUTPUT
    # ─────────────────────────
    return {
        "interest_rate": round(final_rate, 4),
        "base_rate": round(base_rate, 4),
        "score_rate": round(score_rate, 4),
        "min_rate": min_rate,
        "max_rate": max_rate,
        "risk_level": level,
        "loan_type": loan_type,
        "country": "US",  # backward compat
        "score": score,
    }