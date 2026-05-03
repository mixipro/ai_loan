# app/agents/business_agent.py

import json
from app.services.llm_service import call_llm


# ─────────────────────────
# 🧠 PROMPT BUILDER (UPGRADE)
# ─────────────────────────
def build_prompt(user, loan: dict) -> str:

    total_capital = user.financial.savings

    if loan.get("approved"):
        total_capital += loan.get("max_loan_amount", 0)

    return f"""
You are a senior financial advisor and startup strategist.

Your task is to propose ONE realistic business idea based on the user's full financial situation.

USER PROFILE:
- Age: {user.personal.age}
- Country: {user.location.country.value}
- Profession: {user.professional.profession}


FINANCIAL DATA:
- Monthly income: {user.financial.income}
- Monthly expenses: {user.financial.expenses}
- Savings: {user.financial.savings}
- Total available capital (savings + loan): {round(total_capital, 2)}

LOAN CONDITIONS:
- Approved: {loan.get("approved")}
- Max loan: {loan.get("max_loan_amount")}
- Interest rate: {loan.get("interest_rate")}
- Monthly payment: {loan.get("monthly_payment")}
- Loan years: {loan.get("loan_years")}

PREFERENCES:
- Risk tolerance: {user.preferences.risk_profile}
- Investment horizon: {user.preferences.horizon}

IMPORTANT CONSTRAINTS:
- Business MUST be feasible with available capital
- Consider loan repayment pressure
- Consider user's skills and experience
- Consider local market conditions
- Match investment horizon:
    - short → fast cash flow
    - medium → balanced
    - long → scalable growth

REQUIREMENTS:
1. Suggest ONE realistic business idea
2. Estimate expected annual return (0.05–0.30)
3. Estimate risk (0–1)
4. Estimate stability (0–1)

STRICT RULES:
- Return ONLY valid JSON
- No explanation
- No text outside JSON

FORMAT:
{{
  "agent": "business",
  "idea": "...",
  "expected_return": 0.12,
  "risk": 0.6,
  "stability": 0.7
}}
"""


# ─────────────────────────
# 🤖 LLM CALL
# ─────────────────────────
def generate_business_idea_llm(user, loan: dict) -> dict:
    prompt = build_prompt(user, loan)

    raw = call_llm(prompt)

    try:
        data = json.loads(raw)
    except:
        raise ValueError(f"Invalid LLM output: {raw}")

    return data


# ─────────────────────────
# 🔒 VALIDATION (CRITICAL)
# ─────────────────────────
def validate_business_output(data: dict) -> dict:
    return {
        "agent": "business",
        "idea": data.get("idea", "Generic business"),
        "expected_return": min(max(data.get("expected_return", 0.1), 0.01), 0.3),
        "risk": min(max(data.get("risk", 0.5), 0), 1),
        "stability": min(max(data.get("stability", 0.5), 0), 1),
    }


# ─────────────────────────
# 🚀 FINAL ENTRY POINT
# ─────────────────────────
def run_business_agent(user, loan: dict) -> dict:
    raw = generate_business_idea_llm(user, loan)
    return validate_business_output(raw)