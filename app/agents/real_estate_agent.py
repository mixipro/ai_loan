# app/agents/real_estate_agent.py

from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import (
    parse_llm_json, clamp, safe_list, safe_str, safe_dict,
    call_llm_with_retry
)
from app.core.california_config import REGION_DATA, get_city_real_estate_data

HOURS_RE_DESCRIPTIONS = {
    "0-5": "Less than 5h/week (PASSIVE — REIT or fully managed property)",
    "5-15": "5-15h/week (LIGHT — REIT-heavy, possibly small rental with property manager)",
    "15-30": "15-30h/week (MODERATE — direct rental possible, can handle tenants)",
    "30+": "30+h/week (HEAVY — flip projects, active development, multiple properties)"
}


def build_prompt(user, loan: dict) -> str:
    total_capital = user.financial.savings

    if loan.get("approved"):
        total_capital += loan.get("max_loan_amount", 0)

    interests_text = (
        ", ".join(user.professional.interests)
        if user.professional.interests
        else "Not specified"
    )

    experience_text = user.professional.prior_experience or "No prior real estate experience"

    hours_desc = HOURS_RE_DESCRIPTIONS.get(
        user.professional.weekly_hours.value,
        "Unknown availability"
    )

    # ⭐ California-specific data
    region = user.location.region
    region_data = REGION_DATA[region]
    city_data = get_city_real_estate_data(user.location.city, region)

    # Calculate down payment thresholds
    median_price = region_data["median_home_price"]
    down_20pct = median_price * 0.20

    return f"""
You are a senior California real estate investment advisor.

USER PROFILE:
- Age: {user.personal.age}
- Region: {region_data['display_name']} (California, USA)
- City: {user.location.city}
- Interests/Hobbies: {interests_text}
- Prior real estate experience: {experience_text}
- Weekly hours available: {hours_desc}

FINANCIAL DATA:
- Monthly income: ${user.financial.income} USD
- Savings: ${user.financial.savings} USD
- Total available capital: ${round(total_capital, 2)} USD

LOAN CONDITIONS:
- Approved: {loan.get("approved")}
- Max loan: ${loan.get("max_loan_amount", 0)}
- Interest rate: {loan.get("interest_rate")}
- Monthly payment: ${loan.get("monthly_payment", 0)}

PREFERENCES:
- Risk tolerance: {user.preferences.risk_profile.value}
- Investment horizon: {user.preferences.horizon.value} years

🌴 CALIFORNIA REAL ESTATE CONTEXT — {region_data['display_name']}:
- Median home price: ${median_price:,}
- City-specific price: ${city_data['price_per_sqft']}/sqft
- Median 2BR rent: ${city_data['rent_2br']}/month
- Property tax (Prop 13 effective): {city_data['property_tax_effective'] * 100:.2f}%
- Rental yield average: {city_data['rental_yield_avg'] * 100:.1f}%
- Risk factors: {region_data['risk_factors']}
- Required down payment for median ($-20%): ${down_20pct:,.0f}

═══════════════════════════════════════════════════════════
🏛️ CALIFORNIA-SPECIFIC RULES (CRITICAL):
═══════════════════════════════════════════════════════════

1. **Proposition 13** (HUGE benefit for buyers):
   - Property tax capped at 1% of purchase price + local fees
   - Annual increase: max 2% per year
   - Reassessment ONLY on sale → buying today LOCKS IN low taxes for life
   - Owner who bought 30 years ago pays MUCH less than new buyer

2. **California REITs available** (US-developed market):
   - VNQ (Vanguard Real Estate ETF)
   - SCHH (Schwab US REIT)
   - IYR (iShares US Real Estate)
   - CA-specific: PSA (Public Storage HQ in Glendale), AMT (American Tower)

3. **1031 Exchange** (defer capital gains by swapping properties)

4. **Mello-Roos taxes** (special assessments in newer developments — Inland Empire, Sacramento suburbs)
   - Can add 0.5-2% to property tax bill

5. **California Earthquake Risk**:
   - {region_data['risk_factors'].get('earthquake', 'unknown')} for {region_data['display_name']}
   - Standard insurance doesn't cover — separate CEA policy: $800-3,000/year
   - 10-20% deductible (high!)

6. **Wildfire Risk**:
   - {region_data['risk_factors'].get('wildfire', 'unknown')} for {region_data['display_name']}
   - High-risk areas: major insurers refusing new policies
   - Can affect mortgage approval

═══════════════════════════════════════════════════════════
🏠 CALIFORNIA CAPITAL DECISION TREE:
═══════════════════════════════════════════════════════════

User's capital: ${round(total_capital, 2)} USD
Median home in {region_data['display_name']}: ${median_price:,}
20% down on median: ${down_20pct:,.0f}

IF capital >= ${down_20pct:,.0f}:
    → PRIMARY: Direct purchase in {user.location.city}
    → Lock in Prop 13 tax benefit FOREVER
    → Type: "rental" (long-term) or "primary" (residence)

ELIF capital >= ${down_20pct * 0.5:,.0f}:
    → PRIMARY: REIT-heavy portfolio (VNQ, SCHH)
    → SECONDARY: Possibly cheaper region within CA
    → Type: "REIT" or "mixed"

ELIF capital >= $20,000:
    → PRIMARY: REIT only (VNQ + SCHH diversified)
    → Type: "REIT"

ELSE:
    → REIT or specialty (storage, small commercial)
    → Type: "REIT"

═══════════════════════════════════════════════════════════
TIME COMMITMENT FILTER:
═══════════════════════════════════════════════════════════
- 0-5h/week → REIT only (VNQ, SCHH)
- 5-15h/week → REIT-heavy, or single rental WITH property manager (-10% rent)
- 15-30h/week → direct rental OK, owner-managed
- 30+h/week → flip projects, multi-unit OK

═══════════════════════════════════════════════════════════
INTERESTS BONUS:
═══════════════════════════════════════════════════════════
- Loves "design"/"interior design" → flip projects in {user.location.city}
- Loves "travel" → Airbnb / short-term rental
- Loves "sustainability" → green retrofits + solar (CA tax credits!)
- Loves "real estate" → can suggest advanced strategies (1031, BRRRR)

═══════════════════════════════════════════════════════════
HONESTY RULES:
═══════════════════════════════════════════════════════════
- Be honest about California costs (high property tax base, but Prop 13 helps long-term)
- Don't sugarcoat earthquake/wildfire risks for the region
- {user.location.city} is expensive — if user can't afford, suggest cheaper CA regions or REIT
- DO NOT invent ticker symbols

═══════════════════════════════════════════════════════════
ALLOCATION RULES (CRITICAL):
═══════════════════════════════════════════════════════════
- NEVER return zero values in allocation fields (except renovation_reserve for REIT)
- Allocation sum MUST equal approximately ${round(total_capital, 2)} USD
- If buying property in {user.location.city}, down_payment should match Step calculation
- Verify: down_payment + taxes_and_fees + renovation_reserve + emergency_fund ≈ ${round(total_capital, 2)}
- emergency_fund: minimum 10-15% of total
- taxes_and_fees: 3-5% of property value (closing costs, escrow)

═══════════════════════════════════════════════════════════

REQUIRED FIELDS:
1. title — short strategy name (e.g., "Prop 13-Locked Rental in Oakland")
2. type — one of: "REIT" | "rental" | "flip" | "mortgage" | "land" | "garage" | "storage" | "commercial" | "mixed"
3. description — California-aware strategy (mention Prop 13, regional dynamics, 3-4 sentences)
4. allocation — concrete USD split
5. expected_return — annual return (0.03–0.12)
6. risk — risk level (0–1)
7. stability — stability (0–1)
8. pros — 3 advantages (mention Prop 13 lock-in if buying!)
9. cons — 2 risks (honest about earthquake/wildfire/CA costs)
10. next_steps — 3 concrete actions (CA-specific: title insurance, earthquake assessment, etc.)
11. time_to_profit — realistic timeline

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- Mention California-specific advantages where relevant
- All amounts in USD

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

    return await call_llm_with_retry(
        llm_call=lambda: call_llm(prompt),
        agent_name="real_estate"
    )


def validate_real_estate_output(data: dict) -> dict:
    valid_types = {
        "REIT", "rental", "flip", "mortgage",
        "land", "garage", "storage", "commercial", "mixed", "primary"
    }
    type_value = safe_str(data.get("type"), "REIT")
    if type_value not in valid_types:
        type_value = "REIT"

    return {
        "agent": "real_estate",
        "title": safe_str(data.get("title"), "Real Estate Investment"),
        "type": type_value,
        "description": safe_str(
            data.get("description"),
            "A California real estate strategy focused on stability and Prop 13 benefits."
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
