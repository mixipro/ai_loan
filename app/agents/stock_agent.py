# app/agents/stock_agent.py

from app.services.llm_service import call_llm
from app.agents._common import parse_llm_json, clamp, safe_list, safe_str, safe_dict


def build_prompt(user, loan: dict) -> str:
    total_capital = user.financial.savings

    if loan.get("approved"):
        total_capital += loan.get("max_loan_amount", 0)

    return f"""
You are a senior portfolio manager and stock market strategist.

Your task is to propose ONE realistic, well-detailed stock/ETF investment strategy.

USER PROFILE:
- Age: {user.personal.age}
- Country: {user.location.country.value}
- Currency: {user.financial.currency.value}

FINANCIAL DATA:
- Monthly income: {user.financial.income}
- Monthly expenses: {user.financial.expenses}
- Savings: {user.financial.savings}
- Total available capital: {round(total_capital, 2)} {user.financial.currency.value}

LOAN CONDITIONS:
- Approved: {loan.get("approved")}
- Max loan: {loan.get("max_loan_amount")}
- Interest rate: {loan.get("interest_rate")}
- Monthly payment: {loan.get("monthly_payment")}

PREFERENCES:
- Risk tolerance: {user.preferences.risk_profile.value}
- Investment horizon: {user.preferences.horizon.value} years

YOUR TASK:
Propose ONE diversified stock/ETF portfolio that:
- Focuses on GROWTH (capital appreciation), not active income
- Matches risk tolerance:
    - low    → bonds, dividend ETFs (VOO, VYM, BND, SCHD)
    - medium → broad market ETFs (VOO, VTI, VXUS, IWM)
    - high   → growth ETFs, tech, emerging markets (QQQ, ARKK, SOXX, EEM)
- Matches investment horizon:
    - short (1-3) → lower volatility, more bonds
    - medium (3-5) → balanced ETF mix
    - long (5+)   → aggressive growth, more equities

REQUIRED FIELDS:
1. title — short portfolio name (e.g., "Conservative Dividend Portfolio")
2. description — what this portfolio invests in and why (2-3 sentences)
3. allocation — concrete split with tickers and percentages
4. expected_return — annual return as decimal (0.04–0.20)
5. risk — risk level (0–1)
6. stability — stability (0–1)
7. pros — 3 advantages
8. cons — 2 risks
9. next_steps — 3 concrete actions (broker, account type, first ETFs to buy)
10. time_to_profit — realistic horizon (e.g. "3-5 years")

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- Allocation must contain CONCRETE TICKERS with percentages

FORMAT:
{{
  "agent": "stock",
  "title": "...",
  "description": "...",
  "allocation": {{
    "VOO": "40%",
    "VXUS": "30%",
    "BND": "20%",
    "Cash reserve": "10%"
  }},
  "expected_return": 0.08,
  "risk": 0.5,
  "stability": 0.6,
  "pros": ["...", "...", "..."],
  "cons": ["...", "..."],
  "next_steps": ["...", "...", "..."],
  "time_to_profit": "..."
}}
"""


async def generate_stock_strategy_llm(user, loan: dict) -> dict:
    prompt = build_prompt(user, loan)
    raw = await call_llm(prompt)
    return parse_llm_json(raw)


def validate_stock_output(data: dict) -> dict:
    return {
        "agent": "stock",
        "title": safe_str(data.get("title"), "Diversified ETF Portfolio"),
        "description": safe_str(
            data.get("description"),
            "A diversified portfolio of ETFs balancing growth and stability."
        ),
        "allocation": safe_dict(data.get("allocation"), {
            "VOO": "40%",
            "VXUS": "30%",
            "BND": "20%",
            "Cash reserve": "10%",
        }),
        "expected_return": clamp(data.get("expected_return"), 0.01, 0.2, 0.07),
        "risk": clamp(data.get("risk"), 0, 1, 0.5),
        "stability": clamp(data.get("stability"), 0, 1, 0.6),
        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), []),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "3-5 years"),
    }


async def run_stock_agent(user, loan: dict) -> dict:
    raw = await generate_stock_strategy_llm(user, loan)
    return validate_stock_output(raw)