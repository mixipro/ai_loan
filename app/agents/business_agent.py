# app/agents/business_agent.py

from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import parse_llm_json, clamp, safe_list, safe_str, safe_dict, call_llm_with_retry

# Mapiranje weekly_hours → opis za LLM
HOURS_DESCRIPTIONS = {
    "0-5": "Less than 5h/week (PASSIVE — needs automation, hands-off operation)",
    "5-15": "5-15h/week (LIGHT — weekend/evening side hustle, productized service)",
    "15-30": "15-30h/week (MODERATE — serious side business, can take some calls)",
    "30+": "30+h/week (HEAVY — can run full operation, scaling business)"
}


def build_prompt(user, loan: dict) -> str:
    total_capital = user.financial.savings

    if loan.get("approved"):
        total_capital += loan.get("max_loan_amount", 0)

    # ⭐ Format interests
    interests_text = (
        ", ".join(user.professional.interests)
        if user.professional.interests
        else "Not specified"
    )

    # ⭐ Format prior experience
    experience_text = user.professional.prior_experience or "No prior business experience"

    # ⭐ Format weekly hours
    hours_desc = HOURS_DESCRIPTIONS.get(
        user.professional.weekly_hours.value,
        "Unknown availability"
    )

    return f"""
You are a senior financial advisor and startup strategist.

Your task is to propose ONE realistic, well-detailed business idea based on the user's complete profile.

USER PROFILE:
- Age: {user.personal.age}
- Country: {user.location.country.value}
- City: {user.location.city}
- Profession: {user.professional.profession.value}
- Sector: {user.professional.sector.value}
- Employment: {user.professional.employment_status.value}
- Interests/Hobbies: {interests_text}
- Prior business experience: {experience_text}
- Weekly hours available: {hours_desc}

FINANCIAL DATA:
- Monthly income: {user.financial.income} {user.financial.currency.value}
- Monthly expenses: {user.financial.expenses} {user.financial.currency.value}
- Savings: {user.financial.savings} {user.financial.currency.value}
- Total available capital: {round(total_capital, 2)} {user.financial.currency.value}

LOAN CONDITIONS:
- Approved: {loan.get("approved")}
- Max loan: {loan.get("max_loan_amount")}
- Interest rate: {loan.get("interest_rate")}
- Monthly payment: {loan.get("monthly_payment")}
- Loan years: {loan.get("loan_years")}

PREFERENCES:
- Risk tolerance: {user.preferences.risk_profile.value}
- Investment horizon: {user.preferences.horizon.value} years
- Primary goal: PROFIT (maximize income, build sustainable revenue)

YOUR TASK:
Propose ONE specific, realistic business idea that:
1. **Combines PROFESSION + INTERESTS** — bonus for unique combinations:
   - Software engineer + fitness → app/tech for gyms
   - Physiotherapist + photography → online wellness content
   - Chef + investing → food blog with monetization strategy
2. **Fits available capital**: {round(total_capital, 2)} {user.financial.currency.value}
3. **Respects WEEKLY HOURS** ({hours_desc}):
   - 0-5h → automation-heavy (dropshipping, digital products, vending, content monetization)
   - 5-15h → productized service, weekend operation, online course
   - 15-30h → service business with growth potential, agency model
   - 30+h → full operation, hiring, scaling, brick-and-mortar OK
4. **Leverages prior experience** if relevant: "{experience_text}"
5. **Considers local market** in {user.location.city}, {user.location.country.value}
6. **Aligns with risk tolerance** ({user.preferences.risk_profile.value}) and horizon ({user.preferences.horizon.value} years)
7. **Accounts for loan repayment** if loan is used

PRIORITIZATION RULES:
- The user's PRIMARY GOAL IS PROFIT — optimize for return-on-effort
- Penalize ideas that ignore weekly hours (DON'T suggest 60h/week business to someone with 5-15h available)
- Reward ideas where interests/profession combo creates a unique angle
- Be realistic — no "build the next Airbnb" generic advice

REQUIRED FIELDS:
1. title — short business name/concept (5-10 words)
2. description — what the business does, why it fits user (2-3 sentences, MENTION how interests/experience tie in)
3. allocation — how to split the capital (3-4 categories with amounts in {user.financial.currency.value})
4. expected_return — annual return as decimal (0.05–0.30)
5. risk — risk level as decimal (0–1, where 1 = highest)
6. stability — stability as decimal (0–1, where 1 = most stable)
7. pros — 3 specific advantages of this idea
8. cons — 2 specific risks/challenges
9. next_steps — 3 concrete actions user should take
10. time_to_profit — realistic timeframe (e.g. "6-12 months")

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- All monetary amounts in user's currency ({user.financial.currency.value})
- Be SPECIFIC and PERSONALIZED — generic ideas are unacceptable

ALLOCATION RULES (CRITICAL):
- NEVER return zero values in allocation fields
- Allocation amounts MUST sum to approximately {round(total_capital, 2)} {user.financial.currency.value}
- If you mention a specific amount in description (e.g., "€15,000 for equipment"),
  that MUST be reflected in the corresponding allocation field
- Verify your math: initial_investment + working_capital + marketing_budget + reserve = {round(total_capital, 2)}
- reserve should be minimum 10% of total capital as safety buffer

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

    # ⭐ Retry wrapper — pravi sopstveni LLM call po retry pokušaju
    return await call_llm_with_retry(
        llm_call=lambda: call_llm(prompt),
        agent_name="business"
    )


def validate_business_output(data: dict) -> dict:
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