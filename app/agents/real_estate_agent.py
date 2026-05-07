# app/agents/real_estate_agent.py

from app.services.llm_service import call_llm
from app.agents._common import (
    parse_llm_json, clamp, safe_list, safe_str, safe_dict,
    call_llm_with_retry
)


# ─────────────────────────
# ⏰ HOURS DESCRIPTIONS
# ─────────────────────────
HOURS_RE_DESCRIPTIONS = {
    "0-5": "Less than 5h/week (PASSIVE — REIT or fully managed property)",
    "5-15": "5-15h/week (LIGHT — REIT-heavy, possibly small rental with property manager)",
    "15-30": "15-30h/week (MODERATE — direct rental possible, can handle tenants)",
    "30+": "30+h/week (HEAVY — flip projects, active development, multiple properties)"
}


# ─────────────────────────
# 🌍 REIT MARKET TIERS
# ─────────────────────────
DEVELOPED_REIT_MARKETS = {"US", "GB", "JP", "AU", "CA", "DE", "NL", "FR", "ES", "IT"}
LIMITED_REIT_MARKETS = {"RS", "TR", "BR", "MX", "IN", "ID", "RU", "KR", "SA", "CH"}


def get_reit_guidance(country_code: str) -> str:
    """
    Vraća kontekst za LLM o REIT mogućnostima u datoj zemlji.
    Sprečava halucinacije lokalnih REIT-ova koji ne postoje.
    """
    if country_code in DEVELOPED_REIT_MARKETS:
        return (
            f"REIT_AVAILABILITY: Country {country_code} has a DEVELOPED REIT market. "
            "You can safely recommend local REITs and ETFs. For US: VNQ, SCHH, IYR, REM. "
            "For UK: British Land, Land Securities. For Japan: J-REIT funds (Nippon Building Fund, NBF). "
            "Always recommend real, tradeable tickers."
        )
    elif country_code in LIMITED_REIT_MARKETS:
        return (
            f"REIT_AVAILABILITY: Country {country_code} has LIMITED or NO domestic REIT market. "
            "DO NOT invent local REIT tickers. Instead, suggest:\n"
            "  - Access to US REITs (VNQ, SCHH) via international broker (Interactive Brokers, eToro)\n"
            "  - OR direct rental property if capital allows\n"
            "  - OR alternative physical real estate (storage, land) ONLY if capital is insufficient\n"
            "Be honest if REIT investing is impractical for this user."
        )
    else:
        return (
            f"REIT_AVAILABILITY: Country {country_code} has uncertain REIT market access. "
            "Be conservative — only mention well-known international REITs (VNQ, SCHH) "
            "or recommend physical real estate alternatives."
        )


# ─────────────────────────
# 📝 PROMPT BUILDER
# ─────────────────────────
def build_prompt(user, loan: dict) -> str:
    total_capital = user.financial.savings

    if loan.get("approved"):
        total_capital += loan.get("max_loan_amount", 0)

    # Format interests
    interests_text = (
        ", ".join(user.professional.interests)
        if user.professional.interests
        else "Not specified"
    )

    # Format prior experience
    experience_text = user.professional.prior_experience or "No prior real estate experience"

    # Format weekly hours
    hours_desc = HOURS_RE_DESCRIPTIONS.get(
        user.professional.weekly_hours.value,
        "Unknown availability"
    )

    # REIT context po zemlji
    reit_context = get_reit_guidance(user.location.country.value)

    return f"""
You are a senior real estate investment advisor.

Your task is to propose ONE realistic, well-detailed real estate strategy that EXISTS, is ACCESSIBLE, and matches the user's capital level.

USER PROFILE:
- Age: {user.personal.age}
- Country: {user.location.country.value}
- City: {user.location.city}
- Currency: {user.financial.currency.value}
- Interests/Hobbies: {interests_text}
- Prior real estate experience: {experience_text}
- Weekly hours available: {hours_desc}

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

🌍 MARKET CONTEXT:
{reit_context}

═══════════════════════════════════════════════════════════
YOUR TASK — Match strategy to capital, time, AND market reality
═══════════════════════════════════════════════════════════

REAL ESTATE OPTIONS (in order of preference for sufficient capital):

🥇 PRIMARY OPTIONS (prefer when capital allows):
   1. RESIDENTIAL: apartment, condo, townhouse (rental or flip)
   2. COMMERCIAL: small office, retail unit, warehouse
   3. REIT: diversified ETFs (VNQ, SCHH for US-accessible markets)

🥈 ALTERNATIVE OPTIONS (use ONLY when primary is genuinely unaffordable):
   4. SPECIALTY: garage, parking spot, storage unit
   5. LAND: building plot, agricultural land

═══════════════════════════════════════════════════════════
🏠 CAPITAL DECISION TREE (FOLLOW STRICTLY):
═══════════════════════════════════════════════════════════

Step 1: Estimate REAL apartment price in {user.location.city}, {user.location.country.value}.
        Examples (use your knowledge):
        - Munich: €8,000-12,000/sqm
        - Tokyo: ¥1,000,000-1,500,000/sqm (~$7,000-10,000)
        - Belgrade: €2,000-4,000/sqm
        - Istanbul: $1,500-3,000/sqm
        - São Paulo: $1,500-2,500/sqm
        - Use realistic prices for {user.location.city}

Step 2: Calculate down payment needed (typically 20-30% of property price).

Step 3: Compare user's total capital ({round(total_capital, 2)} {user.financial.currency.value}) to down payment:

        IF capital >= 30% of decent apartment price (60-80sqm):
            → PRIMARY: Direct residential purchase (apartment/condo for rental)
            → Type: "rental" or "flip"

        ELIF capital >= 50% of small apartment (40sqm) OR capital > $50k:
            → PRIMARY: REIT-heavy portfolio (60-70% of capital)
            → SECONDARY: Optional 1 garage for diversification (max 30%)
            → Type: "REIT" or "mixed"

        ELIF capital >= $20k:
            → PRIMARY: REIT only (if available in market)
            → ALTERNATIVE: Single garage/storage unit if no REIT access
            → Type: "REIT" or "garage" (only if no REIT access)

        ELSE (capital < $20k):
            → REIT or specialty only
            → Type: "REIT"

Step 4: HARD RULE — Garage/parking is NEVER the primary recommendation 
        if user can afford a residential property (even small one).
        Garage is a fallback, not a default.

═══════════════════════════════════════════════════════════
TIME COMMITMENT FILTER (HARD RULE):
═══════════════════════════════════════════════════════════
- 0-5h/week → REIT, land, OR fully managed property
- 5-15h/week → REIT-heavy, or single rental WITH property manager
- 15-30h/week → direct rental OK, owner-managed
- 30+h/week → flip, multi-unit, active development

═══════════════════════════════════════════════════════════
EXPERIENCE FILTER:
═══════════════════════════════════════════════════════════
- No experience → REIT, land, or turnkey managed property
- Some experience → can handle direct rental
- Extensive experience → flip, BRRRR, multi-unit OK

═══════════════════════════════════════════════════════════
INTERESTS BONUS (subtle, not primary driver):
═══════════════════════════════════════════════════════════
- Loves "design"/"interior design" → flip projects
- Loves "travel" → Airbnb / short-term rental
- Loves "sustainability" → green retrofits
- Loves "real estate" → can suggest more advanced strategies

═══════════════════════════════════════════════════════════
HONESTY RULES:
═══════════════════════════════════════════════════════════
- If REIT is not realistic in this country, SAY SO and pivot to physical property
- If apartment is unaffordable, SAY SO and pivot (REIT first, garage as last resort)
- DO NOT invent ticker symbols that don't exist
- DO NOT default to garage as the "safe choice" — only when capital forces it

═══════════════════════════════════════════════════════════
ALLOCATION RULES (CRITICAL):
═══════════════════════════════════════════════════════════
- NEVER return zero values in allocation fields (except renovation_reserve which can be 0 for non-flip)
- Allocation amounts MUST sum to approximately {round(total_capital, 2)} {user.financial.currency.value}
- If you mention a price in description (e.g., "apartment costs €300,000"),
  that MUST appear as down_payment in allocation
- Verify your math: down_payment + taxes_and_fees + renovation_reserve + emergency_fund ≈ {round(total_capital, 2)}
- emergency_fund should be minimum 10-15% of total capital
- taxes_and_fees typically 3-5% of property value in most countries

═══════════════════════════════════════════════════════════

REQUIRED FIELDS:
1. title — short strategy name (e.g., "2BR Rental Apartment in Munich")
2. type — one of: "REIT" | "rental" | "flip" | "mortgage" | "land" | "garage" | "storage" | "commercial" | "mixed"
3. description — what this strategy involves (3-4 sentences). MENTION:
   - Realistic price estimate per sqm/unit in their city
   - Why this fits their capital
   - Why you chose this type over alternatives
4. allocation — concrete split (down_payment, taxes_and_fees, renovation_reserve, emergency_fund)
5. expected_return — annual return (0.03–0.12)
6. risk — risk level (0–1)
7. stability — stability (0–1)
8. pros — 3 advantages
9. cons — 2 risks (be HONEST about limitations)
10. next_steps — 3 concrete actions
11. time_to_profit — realistic timeline

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- DO NOT recommend strategies the user cannot afford
- DO NOT invent ticker symbols
- DO NOT default to garage as primary — follow the capital decision tree
- BE HONEST about market limitations

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


# ─────────────────────────
# 🤖 LLM CALL
# ─────────────────────────
async def generate_real_estate_strategy_llm(user, loan: dict) -> dict:
    prompt = build_prompt(user, loan)

    return await call_llm_with_retry(
        llm_call=lambda: call_llm(prompt),
        agent_name="real_estate"
    )


# ─────────────────────────
# ✅ VALIDATION
# ─────────────────────────
def validate_real_estate_output(data: dict) -> dict:
    valid_types = {
        "REIT", "rental", "flip", "mortgage",
        "land", "garage", "storage", "commercial", "mixed"
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


# ─────────────────────────
# 🚀 PUBLIC ENTRY
# ─────────────────────────
async def run_real_estate_agent(user, loan: dict) -> dict:
    raw = await generate_real_estate_strategy_llm(user, loan)
    return validate_real_estate_output(raw)