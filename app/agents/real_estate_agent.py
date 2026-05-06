# app/agents/real_estate_agent.py

from app.services.llm_service import call_llm
from app.agents._common import parse_llm_json, clamp, safe_list, safe_str, safe_dict


def build_prompt(user, loan: dict) -> str:
    total_capital = user.financial.savings

    if loan.get("approved"):
        total_capital += loan.get("max_loan_amount", 0)

    return f"""
You are a senior real estate investment advisor.

Your task is to propose ONE realistic, well-detailed real estate strategy.

USER PROFILE:
- Age: {user.personal.age}
- Country: {user.location.country.value}
- City: {user.location.city}
- Currency: {user.financial.currency.value}

FINANCIAL DATA:
- Monthly income: {user.financial.income}
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
Propose ONE real estate strategy. Choose the right type based on capital:
- low capital  (< 30k) → REITs only (VNQ, SCHH, public REIT funds)
- mid capital  (30k-100k) → small rental property OR REIT-heavy portfolio
- high capital (> 100k) → direct property purchase (apartment, condo, rental)

Consider local market in {user.location.city}, {user.location.country.value}.

REQUIRED FIELDS:
1. title — short strategy name (e.g., "Rental Apartment in Belgrade")
2. type — one of: "REIT" | "rental" | "flip" | "mortgage" | "mixed"
3. description — what this strategy involves (2-3 sentences)
4. allocation — concrete split (down payment, taxes, fees, reserves)
5. expected_return — annual return (0.03–0.12)
6. risk — risk level (0–1)
7. stability — stability (0–1, real estate is typically high)
8. pros — 3 advantages (e.g., inflation hedge, passive income)
9. cons — 2 risks (e.g., illiquidity, maintenance)
10. next_steps — 3 actions (e.g., consult realtor, mortgage pre-approval)
11. time_to_profit — realistic timeline (e.g. "2-3 years for first cash flow")

STRICT RULES:
- Return ONLY valid JSON, no markdown fences

FORMAT:
{{
  "agent": "real_estate",
  "title": "...",
  "type": "rental",
  "description": "...",
  "allocation": {{
    "down_payment": 0,
    "taxes_and_fees": 0,
    "renovation_reserve": 0,
    "emergency_fund": 0
  }},
  "expected_return": 0.06,
  "risk": 0.3,
  "stability": 0.85,
  "pros": ["...", "...", "..."],
  "cons": ["...", "..."],
  "next_steps": ["...", "...", "..."],
  "time_to_profit": "..."
}}
"""


async def generate_real_estate_strategy_llm(user, loan: dict) -> dict:
    prompt = build_prompt(user, loan)
    raw = await call_llm(prompt)
    return parse_llm_json(raw)


def validate_real_estate_output(data: dict) -> dict:
    valid_types = {"REIT", "rental", "flip", "mortgage", "mixed"}
    type_value = safe_str(data.get("type"), "REIT")
    if type_value not in valid_types:
        type_value = "REIT"

    return {
        "agent": "real_estate",
        "title": safe_str(data.get("title"), "Real Estate Investment"),
        "type": type_value,
        "description": safe_str(
            data.get("description"),
            "A real estate investment focused on stability and inflation protection."
        ),
        "allocation": safe_dict(data.get("allocation"), {
            "down_payment": 0,
            "taxes_and_fees": 0,
            "renovation_reserve": 0,
            "emergency_fund": 0,
        }),
        "expected_return": clamp(data.get("expected_return"), 0.01, 0.12, 0.05),
        "risk": clamp(data.get("risk"), 0, 1, 0.3),
        "stability": clamp(data.get("stability"), 0, 1, 0.8),
        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), []),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "2-3 years"),
    }


async def run_real_estate_agent(user, loan: dict) -> dict:
    raw = await generate_real_estate_strategy_llm(user, loan)
    return validate_real_estate_output(raw)