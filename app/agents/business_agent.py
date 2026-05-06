# app/agents/business_agent.py

from app.services.llm_service import call_llm
from app.agents._common import parse_llm_json, clamp, safe_list, safe_str, safe_dict


def build_prompt(user, loan: dict) -> str:
    total_capital = user.financial.savings

    if loan.get("approved"):
        total_capital += loan.get("max_loan_amount", 0)

    return f"""
You are a senior financial advisor and startup strategist.

Your task is to propose ONE realistic, well-detailed business idea based on the user's full financial situation.

USER PROFILE:
- Age: {user.personal.age}
- Country: {user.location.country.value}
- City: {user.location.city}
- Profession: {user.professional.profession.value}
- Sector: {user.professional.sector.value}
- Employment: {user.professional.employment_status.value}

FINANCIAL DATA:
- Monthly income: {user.financial.income} {user.financial.currency.value}
- Monthly expenses: {user.financial.expenses} {user.financial.currency.value}
- Savings: {user.financial.savings} {user.financial.currency.value}
- Total available capital (savings + loan): {round(total_capital, 2)} {user.financial.currency.value}

LOAN CONDITIONS:
- Approved: {loan.get("approved")}
- Max loan: {loan.get("max_loan_amount")}
- Interest rate: {loan.get("interest_rate")}
- Monthly payment: {loan.get("monthly_payment")}
- Loan years: {loan.get("loan_years")}

PREFERENCES:
- Risk tolerance: {user.preferences.risk_profile.value}
- Investment horizon: {user.preferences.horizon.value} years

YOUR TASK:
Propose ONE specific, realistic business idea that:
- Fits the available capital (total: {round(total_capital, 2)})
- Matches user's profession and skills (leverage their background)
- Considers local market in {user.location.city}, {user.location.country.value}
- Aligns with risk tolerance and investment horizon
- Accounts for loan repayment pressure (if loan is used)

REQUIRED FIELDS:
1. title — short business name/concept (5-10 words)
2. description — what the business does, why it fits user (2-3 sentences)
3. allocation — how to split the capital (3-4 categories with amounts)
4. expected_return — annual return as decimal (0.05–0.30)
5. risk — risk level as decimal (0–1, where 1 = highest)
6. stability — stability as decimal (0–1, where 1 = most stable)
7. pros — 3 specific advantages of this idea
8. cons — 2 specific risks/challenges
9. next_steps — 3 concrete actions user should take to start
10. time_to_profit — realistic timeframe (e.g. "6-12 months")

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- All monetary amounts in user's currency ({user.financial.currency.value})
- Allocation amounts must sum to approximately {round(total_capital, 2)}
- Be specific and realistic — no generic advice

FORMAT:
{{
  "agent": "business",
  "title": "...",
  "description": "...",
  "allocation": {{
    "initial_investment": 0,
    "working_capital": 0,
    "marketing_budget": 0,
    "reserve": 0
  }},
  "expected_return": 0.15,
  "risk": 0.5,
  "stability": 0.7,
  "pros": ["...", "...", "..."],
  "cons": ["...", "..."],
  "next_steps": ["...", "...", "..."],
  "time_to_profit": "..."
}}
"""


async def generate_business_idea_llm(user, loan: dict) -> dict:
    prompt = build_prompt(user, loan)
    raw = await call_llm(prompt)
    return parse_llm_json(raw)


def validate_business_output(data: dict) -> dict:
    """
    Validira i normalizuje output.
    Sva polja imaju default-e ako LLM nešto izostavi.
    """
    return {
        "agent": "business",
        "title": safe_str(data.get("title"), "Business opportunity"),
        "description": safe_str(
            data.get("description"),
            "A business venture leveraging user's skills and available capital."
        ),
        "allocation": safe_dict(data.get("allocation"), {
            "initial_investment": 0,
            "working_capital": 0,
            "marketing_budget": 0,
            "reserve": 0,
        }),
        "expected_return": clamp(data.get("expected_return"), 0.01, 0.3, 0.1),
        "risk": clamp(data.get("risk"), 0, 1, 0.5),
        "stability": clamp(data.get("stability"), 0, 1, 0.5),
        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), []),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "6-12 months"),
    }


async def run_business_agent(user, loan: dict) -> dict:
    raw = await generate_business_idea_llm(user, loan)
    return validate_business_output(raw)