# app/engines/inflation_engine.py

"""
California / US inflation engine.
USD-only, US CPI based.
Live web search will update these rates in Phase 2.
"""

from enum import Enum

# ─────────────────────────
# 🇺🇸 US INFLATION (baseline)
# Will be live-updated via Brave Search in Phase 2
# ─────────────────────────
US_INFLATION_BASELINE = 0.031  # 3.1% — US CPI April 2026 estimate

# Currency inflation (USD only for California-only system)
CURRENCY_INFLATION = {
    "USD": US_INFLATION_BASELINE,
}


# ─────────────────────────
# 🤖 AGENT TYPE
# ─────────────────────────
class AgentType(str, Enum):
    STOCK = "stock"
    REAL_ESTATE = "real_estate"
    BUSINESS = "business"


# ─────────────────────────
# 🔥 AGENT → INFLATION TYPE
# ─────────────────────────
AGENT_INFLATION_TYPE = {
    AgentType.STOCK: "currency",  # Global ETFs
    AgentType.REAL_ESTATE: "local",  # California-specific
    AgentType.BUSINESS: "local",  # California-specific
}


# ─────────────────────────
# 🔍 CORE FUNCTION
# ─────────────────────────
def get_inflation_rate(agent: AgentType, currency: str = "USD") -> float:
    """
    Returns inflation rate based on agent type.
    California-only system → US inflation for everything.

    Note: 'country' param removed since system is California-only.
    """
    inflation_type = AGENT_INFLATION_TYPE.get(agent, "local")

    # 📈 GLOBAL (ETF, stock) — currency-based
    if inflation_type == "currency":
        return CURRENCY_INFLATION.get(currency, US_INFLATION_BASELINE)

    # 🏠 / 💼 LOCAL (California real estate, business) — US CPI
    return US_INFLATION_BASELINE


# ─────────────────────────
# 📉 REAL VALUE
# ─────────────────────────
def adjust_for_inflation(
        amount: float,
        years: int,
        agent: AgentType,
        currency: str = "USD"
) -> float:
    """Adjusts amount for inflation (purchasing power)."""
    rate = get_inflation_rate(agent, currency)
    adjusted = amount / ((1 + rate) ** years)
    return round(adjusted, 2)


# ─────────────────────────
# 📈 FUTURE VALUE
# ─────────────────────────
def future_value(
        amount: float,
        years: int,
        agent: AgentType,
        currency: str = "USD"
) -> float:
    """Computes future value adjusted for inflation."""
    rate = get_inflation_rate(agent, currency)
    future = amount * ((1 + rate) ** years)
    return round(future, 2)


# ─────────────────────────
# 💰 REAL RETURN
# ─────────────────────────
def real_return(
        nominal_return: float,
        agent: AgentType,
        currency: str = "USD"
) -> float:
    """Computes real return after inflation (Fisher equation)."""
    inflation = get_inflation_rate(agent, currency)
    return round((1 + nominal_return) / (1 + inflation) - 1, 4)


# ─────────────────────────
# 🔄 BACKWARD COMPAT WRAPPER
# (za stare calls iz orchestrator-a koji prosleđuju country)
# ─────────────────────────
def get_inflation_rate_legacy(agent: AgentType, country: str, currency: str) -> float:
    """Legacy wrapper — ignores country, uses US baseline."""
    return get_inflation_rate(agent, currency)