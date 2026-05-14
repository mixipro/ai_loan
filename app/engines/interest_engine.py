# app/engines/interest_engine.py

"""
California / US multi-loan-type interest rate calculator.
Supports: personal, business, mortgage, margin (stock), sbloc.
"""

# ─────────────────────────────────
# 🏦 LOAN TYPE DEFINITIONS
# Each loan type has different rate range, duration, and use case
# ─────────────────────────────────
LOAN_TYPES = {
    "personal": {
        "rate_range": (0.065, 0.155),
        "default_years": 5,
        "max_years": 7,
        "dti_limit": 0.35,
        "purpose": "general",
        "description": "Unsecured personal loan",
    },
    "business": {
        "rate_range": (0.07, 0.13),
        "default_years": 7,
        "max_years": 10,
        "dti_limit": 0.35,
        "purpose": "business",
        "description": "Business loan for startup or operations",
    },
    "mortgage": {
        "rate_range": (0.055, 0.085),
        "default_years": 30,
        "max_years": 30,
        "dti_limit": 0.28,
        "purpose": "real_estate",
        "description": "Mortgage for real estate purchase",
    },
    "margin": {
        "rate_range": (0.08, 0.13),
        "default_years": 5,
        "max_years": 999,
        "dti_limit": 0.50,
        "purpose": "stock_leveraged",
        "description": "Margin loan for stock investing (CALLABLE — broker can force liquidation)",
    },
    "sbloc": {
        "rate_range": (0.05, 0.08),
        "default_years": 10,
        "max_years": 20,
        "dti_limit": 0.40,
        "purpose": "flexible_secured",
        "description": "Securities-backed line of credit",
    },
}

# Strategy → recommended loan type mapping
STRATEGY_TO_LOAN_TYPE = {
    "business":    "business",
    "real_estate": "mortgage",
    "stock":       "margin",       # stock_margin variant only
    "stock_cash":  None,           # cash-only, no loan
}


def calculate_interest_rate(risk: dict, loan_type: str = "personal") -> dict:
    """
    Calculates interest rate for given loan type based on risk profile.
    """
    if loan_type not in LOAN_TYPES:
        raise ValueError(f"Unsupported loan type: {loan_type}. Valid: {list(LOAN_TYPES.keys())}")

    if "level" not in risk or "adjusted_score" not in risk:
        raise ValueError("Invalid risk input")

    loan_config = LOAN_TYPES[loan_type]
    min_rate, max_rate = loan_config["rate_range"]

    level = risk["level"]
    score = risk["adjusted_score"]

    # 🎯 BASE (DISCRETE) by risk level
    if level == "low_risk":
        base_rate = min_rate
    elif level == "medium_risk":
        base_rate = (min_rate + max_rate) / 2
    else:
        base_rate = max_rate

    # 📈 CONTINUOUS MODEL by score
    normalized = score / 15
    normalized = max(0, min(normalized, 1))
    score_rate = min_rate + (max_rate - min_rate) * (1 - normalized)

    # ⚖️ BLEND
    final_rate = (base_rate * 0.6) + (score_rate * 0.4)
    final_rate = max(min_rate, min(final_rate, max_rate))

    return {
        "interest_rate": round(final_rate, 4),
        "base_rate": round(base_rate, 4),
        "score_rate": round(score_rate, 4),
        "min_rate": min_rate,
        "max_rate": max_rate,
        "risk_level": level,
        "loan_type": loan_type,
        "loan_description": loan_config["description"],
        "default_years": loan_config["default_years"],
        "max_years": loan_config["max_years"],
        "dti_limit": loan_config["dti_limit"],
        "country": "US",
        "score": score,
    }


def calculate_all_loan_rates(risk: dict) -> dict:
    """
    Calculates rates for ALL loan types simultaneously.
    Used by orchestrator to give each strategy its proper loan.
    """
    return {
        "personal":  calculate_interest_rate(risk, "personal"),
        "business":  calculate_interest_rate(risk, "business"),
        "mortgage":  calculate_interest_rate(risk, "mortgage"),
        "margin":    calculate_interest_rate(risk, "margin"),
        "sbloc":     calculate_interest_rate(risk, "sbloc"),
    }