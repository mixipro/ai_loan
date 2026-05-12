# app/agents/business_agent.py

from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import parse_llm_json, clamp, safe_list, safe_str, safe_dict, call_llm_with_retry
from app.core.california_config import REGION_DATA

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

    # California region context
    region = user.location.region
    region_data = REGION_DATA[region]
    primary_industries = ", ".join(region_data["primary_industries"])

    interests_text = (
        ", ".join(user.professional.interests)
        if user.professional.interests
        else "Not specified"
    )

    experience_text = user.professional.prior_experience or "No prior business experience"

    hours_desc = HOURS_DESCRIPTIONS.get(
        user.professional.weekly_hours.value,
        "Unknown availability"
    )

    # ⭐ California-specific context
    tech_role = user.professional.tech_role.value if user.professional.tech_role else "N/A"
    equity = user.professional.equity_compensation.value if user.professional.equity_compensation else "N/A"

    return f"""
You are a senior California business strategist and startup advisor.

Your task is to propose ONE realistic, California-aware business idea based on the user's complete profile.

USER PROFILE:
- Age: {user.personal.age}
- Region: {region_data['display_name']} ({region.value})
- City: {user.location.city}
- Primary regional industries: {primary_industries}
- Regional vibe: {region_data['vibe']}
- Profession: {user.professional.profession.value}
- Sector: {user.professional.sector.value}
- Employment: {user.professional.employment_status.value}
- Tech role (if applicable): {tech_role}
- Equity compensation: {equity}
- Interests/Hobbies: {interests_text}
- Prior business experience: {experience_text}
- Weekly hours available: {hours_desc}

FINANCIAL DATA:
- Monthly income: ${user.financial.income} USD
- Monthly expenses: ${user.financial.expenses} USD
- Savings: ${user.financial.savings} USD
- Total available capital: ${round(total_capital, 2)} USD
- Cost of living index: {region_data['cost_of_living_index']}x US average

LOAN CONDITIONS:
- Approved: {loan.get("approved")}
- Max loan: ${loan.get("max_loan_amount", 0)}
- Interest rate: {loan.get("interest_rate")}
- Monthly payment: ${loan.get("monthly_payment", 0)}
- Loan years: {loan.get("loan_years")}

PREFERENCES:
- Risk tolerance: {user.preferences.risk_profile.value}
- Investment horizon: {user.preferences.horizon.value} years
- Primary goal: PROFIT (maximize income, build sustainable revenue)

🌴 CALIFORNIA BUSINESS CONTEXT:
- LLC franchise tax: $800/year minimum (mandatory, even for 0 revenue)
- California state income tax: progressive up to 13.3% (highest in US)
- {region_data['display_name']} specifics:
  * Cost of living: {region_data['cost_of_living_index']}x national average
  * Strong industries: {primary_industries}
  * Real estate context: median home ${region_data['median_home_price']:,}
- Consider tax implications: California treats capital gains as ordinary income
- If software/SaaS: Bay Area has the highest concentration of YC + VCs in world

YOUR TASK:
Propose ONE specific, realistic California-aware business idea that:
1. **Matches REGION** — Bay Area = tech/AI, LA = entertainment/media, SD = biotech/health, 
   Central Valley = agriculture/food, Sacramento = govt-adjacent services, etc.
2. **Combines PROFESSION + INTERESTS** with regional opportunity:
   - SF tech worker + fitness → AI fitness app for premium gyms
   - LA entertainment + writing → YouTube channel monetized via content
   - SD biotech worker + photography → medical/clinical content for healthcare brands
3. **Fits available capital**: ${round(total_capital, 2)} USD
4. **Respects WEEKLY HOURS** ({hours_desc})
5. **Considers California costs**:
   - Higher labor costs (CA min wage $16/hr+)
   - LLC fees + state tax
   - Higher commercial rents in major cities
6. **Aligns with risk tolerance** ({user.preferences.risk_profile.value}) and horizon ({user.preferences.horizon.value} years)

PRIORITIZATION RULES:
- The user's PRIMARY GOAL IS PROFIT
- Penalize ideas that ignore weekly hours
- Reward ideas where region + profession + interests create unique angle
- Be realistic — California is competitive, generic ideas won't work

REQUIRED FIELDS:
1. title — short business name/concept (5-10 words)
2. description — what the business does, why it fits user + California context (2-3 sentences)
3. allocation — how to split capital (USD amounts, must include LLC formation $800 reserve)
4. expected_return — annual return as decimal (0.05–0.30)
5. risk — risk level as decimal (0–1)
6. stability — stability as decimal (0–1)
7. pros — 3 specific advantages
8. cons — 2 specific risks/challenges (be honest about California costs/competition)
9. next_steps — 3 concrete actions (mention CA-specific: LLC filing, seller's permit if retail)
10. time_to_profit — realistic timeframe

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- All monetary amounts in USD
- Be SPECIFIC and California-aware

ALLOCATION RULES (CRITICAL):
- NEVER return zero values in allocation fields
- Allocation amounts MUST sum to approximately ${round(total_capital, 2)} USD
- Verify your math: initial_investment + working_capital + marketing_budget + reserve = ${round(total_capital, 2)}
- reserve should be minimum 10% as safety buffer (cover LLC tax + emergencies)

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