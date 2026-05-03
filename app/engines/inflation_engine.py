# app/engines/inflation_engine.py

from enum import Enum


# ─────────────────────────
# 🌍 COUNTRY INFLATION (PRIMARY)
# ─────────────────────────
COUNTRY_INFLATION = {
    "US": 0.03,
    "DE": 0.025,
    "JP": 0.01,
    "IN": 0.06,
    "GB": 0.03,
    "FR": 0.025,
    "IT": 0.03,
    "BR": 0.05,
    "CA": 0.03,
    "RU": 0.07,
    "KR": 0.025,
    "AU": 0.03,
    "ES": 0.03,
    "MX": 0.05,
    "ID": 0.04,
    "NL": 0.025,
    "SA": 0.03,
    "TR": 0.08,
    "CH": 0.02,
    "RS": 0.06
}


# ─────────────────────────
# 💱 CURRENCY INFLATION (GLOBAL)
# ─────────────────────────
CURRENCY_INFLATION = {
    "USD": 0.03,
    "EUR": 0.025
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
    AgentType.STOCK: "currency",
    AgentType.REAL_ESTATE: "country",
    AgentType.BUSINESS: "country",
}


# ─────────────────────────
# 🔍 CORE FUNCTION
# ─────────────────────────
def get_inflation_rate(agent: AgentType, country: str, currency: str) -> float:
    """
    Inflacija zavisi od tipa investicije (agenta)
    """

    inflation_type = AGENT_INFLATION_TYPE.get(agent, "country")

    # 📈 GLOBAL (ETF, stock)
    if inflation_type == "currency":
        return CURRENCY_INFLATION.get(currency, 0.03)

    # 🏠 / 💼 LOCAL (real estate, business)
    return COUNTRY_INFLATION.get(country, 0.03)


# ─────────────────────────
# 📉 REAL VALUE
# ─────────────────────────
def adjust_for_inflation(
    amount: float,
    years: int,
    agent: AgentType,
    country: str,
    currency: str
) -> float:

    rate = get_inflation_rate(agent, country, currency)

    adjusted = amount / ((1 + rate) ** years)

    return round(adjusted, 2)


# ─────────────────────────
# 📈 FUTURE VALUE
# ─────────────────────────
def future_value(
    amount: float,
    years: int,
    agent: AgentType,
    country: str,
    currency: str
) -> float:

    rate = get_inflation_rate(agent, country, currency)

    future = amount * ((1 + rate) ** years)

    return round(future, 2)


# ─────────────────────────
# 💰 REAL RETURN (NAJBITNIJE)
# ─────────────────────────
def real_return(
    nominal_return: float,
    agent: AgentType,
    country: str,
    currency: str
) -> float:

    inflation = get_inflation_rate(agent, country, currency)

    return round((1 + nominal_return) / (1 + inflation) - 1, 4)