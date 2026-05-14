# app/agents/real_estate_agent.py

from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import (
    parse_llm_json, clamp, safe_list, safe_str, safe_dict,
    call_llm_with_retry
)
from app.core.california_config import REGION_DATA, get_city_real_estate_data
from app.rag.retriever import retrieve  # ⭐ RAG retriever


# ─────────────────────────────────
# 📚 RAG CONTEXT BUILDER
# ─────────────────────────────────
def _build_rag_context_re(user) -> tuple[str, list]:
    """
    Retrieves California real estate knowledge based on user profile.
    """
    region = user.location.region.value
    city = user.location.city
    interests = ", ".join(user.professional.interests) if user.professional.interests else ""

    # Build semantic queries
    primary_query = f"California {region} {city} real estate market Prop 13 {interests}"
    secondary_query = "California real estate tax mortgage REIT Mello-Roos"

    re_chunks = retrieve(primary_query, top_k=2, category_filter="real_estate")
    tax_chunks = retrieve(secondary_query, top_k=1, category_filter="tax")

    all_chunks = re_chunks + tax_chunks

    if not all_chunks:
        return "", []

    context_parts = ["📚 RELEVANT CALIFORNIA REAL ESTATE KNOWLEDGE BASE:\n"]
    for i, chunk in enumerate(all_chunks, 1):
        context_parts.append(
            f"\n═══ Knowledge {i}: {chunk['id']} "
            f"(relevance: {chunk['similarity_score'] * 100:.0f}%) ═══\n"
            f"Category: {chunk['category']} | Sources: {chunk.get('sources', 'N/A')}\n\n"
            f"{chunk['content'][:800]}\n"
        )

    context_text = "\n".join(context_parts)
    chunk_ids = [c['id'] for c in all_chunks]

    return context_text, chunk_ids


HOURS_RE_DESCRIPTIONS = {
    "0-5": "Less than 5h/week (PASSIVE — REIT or fully managed property)",
    "5-15": "5-15h/week (LIGHT — REIT-heavy, possibly small rental with property manager)",
    "15-30": "15-30h/week (MODERATE — direct rental possible, can handle tenants)",
    "30+": "30+h/week (HEAVY — flip projects, active development, multiple properties)"
}


def build_prompt(user, mortgage_loan: dict, rag_context: str = "") -> str:
    """
    Builds prompt for real estate agent (with RAG context).
    """
    total_capital = user.financial.savings

    if mortgage_loan.get("approved"):
        total_capital += mortgage_loan.get("max_loan_amount", 0)

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

    region = user.location.region
    region_data = REGION_DATA[region]
    city_data = get_city_real_estate_data(user.location.city, region)

    mortgage_amount = mortgage_loan.get("max_loan_amount", 0)
    mortgage_rate = mortgage_loan.get("interest_rate", 0)
    mortgage_rate_pct = mortgage_rate * 100
    mortgage_years = mortgage_loan.get("loan_years", 30)
    mortgage_monthly = mortgage_loan.get("monthly_payment", 0)
    mortgage_total_paid = mortgage_loan.get("total_paid", 0)
    mortgage_total_interest = mortgage_loan.get("total_interest", 0)

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
- Total available capital (savings + mortgage): ${round(total_capital, 2)} USD

🏦 MORTGAGE CONDITIONS (specific for real estate strategy):
- Loan type: 30-YEAR FIXED MORTGAGE (NOT personal loan — much better terms!)
- Approved: {mortgage_loan.get("approved")}
- Max mortgage amount: ${mortgage_amount} USD
- Interest rate: {mortgage_rate_pct:.2f}% APR (lower than personal loans!)
- Term: {mortgage_years} years
- Monthly payment: ${mortgage_monthly}
- 💰 TOTAL COST: ${mortgage_total_paid} over {mortgage_years} years
  (interest alone: ${mortgage_total_interest})

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
- Required down payment for median (20%): ${down_20pct:,.0f}

{rag_context}

═══════════════════════════════════════════════════════════
🏛️ CALIFORNIA-SPECIFIC RULES (CRITICAL):
═══════════════════════════════════════════════════════════

1. **Proposition 13** (HUGE benefit for buyers):
   - Property tax capped at 1% of purchase price + local fees
   - Annual increase: max 2% per year
   - Reassessment ONLY on sale → buying today LOCKS IN low taxes for life

2. **California REITs available**:
   - VNQ (Vanguard Real Estate ETF)
   - SCHH (Schwab US REIT)
   - IYR (iShares US Real Estate)
   - CA-specific: PSA (Public Storage HQ in Glendale), AMT (American Tower)

3. **1031 Exchange** (defer capital gains by swapping properties)

4. **Mello-Roos taxes** (special assessments in newer developments)

5. **California Earthquake Risk**:
   - {region_data['risk_factors'].get('earthquake', 'unknown')} for {region_data['display_name']}
   - Separate CEA policy: $800-3,000/year

6. **Wildfire Risk**:
   - {region_data['risk_factors'].get('wildfire', 'unknown')} for {region_data['display_name']}

═══════════════════════════════════════════════════════════
🏠 CAPITAL DECISION TREE:
═══════════════════════════════════════════════════════════

User's total capital (savings + mortgage): ${round(total_capital, 2)} USD
Median home in {region_data['display_name']}: ${median_price:,}
20% down on median: ${down_20pct:,.0f}

IF total_capital >= ${median_price:,.0f}:
    → PRIMARY: Direct purchase in {user.location.city} (savings = down payment)
    → Lock in Prop 13 tax benefit FOREVER
    → Type: "rental" (long-term) or "primary" (residence)

ELIF user.savings >= ${down_20pct:,.0f}:
    → PRIMARY: Use savings as 20% down + mortgage for rest
    → Type: "rental" or "primary"

ELIF user.savings >= ${down_20pct * 0.5:,.0f}:
    → PRIMARY: REIT-heavy portfolio (mortgage not used effectively)
    → SECONDARY: Cheaper region within CA
    → Type: "REIT" or "mixed"

ELIF user.savings >= $20,000:
    → PRIMARY: REIT only (VNQ + SCHH diversified) — NO MORTGAGE
    → Type: "REIT"

ELSE:
    → REIT or specialty (storage, small commercial)
    → Type: "REIT"

═══════════════════════════════════════════════════════════
TIME COMMITMENT FILTER:
═══════════════════════════════════════════════════════════
- 0-5h/week → REIT only
- 5-15h/week → REIT-heavy, or single rental WITH property manager (-10% rent)
- 15-30h/week → direct rental OK, owner-managed
- 30+h/week → flip projects, multi-unit OK

═══════════════════════════════════════════════════════════
INTERESTS BONUS:
═══════════════════════════════════════════════════════════
- "design"/"interior design" → flip projects
- "travel" → Airbnb / short-term rental
- "sustainability" → green retrofits + solar (CA tax credits!)
- "real estate" → advanced strategies (1031, BRRRR)

═══════════════════════════════════════════════════════════
HONESTY RULES:
═══════════════════════════════════════════════════════════
- Be honest about California costs
- Don't sugarcoat earthquake/wildfire risks
- {user.location.city} is expensive — if user can't afford, suggest REIT or cheaper region
- DO NOT invent ticker symbols
- ⚠️ Be HONEST about mortgage burden: ${mortgage_monthly}/mo for 30 years is REAL commitment
- ⚠️ If user doesn't choose direct property, mortgage isn't used → ignore mortgage in allocation

═══════════════════════════════════════════════════════════
ALLOCATION RULES (CRITICAL):
═══════════════════════════════════════════════════════════
- NEVER return zero values (except renovation_reserve for REIT)
- For REIT-only strategy: allocation should sum to user.savings (mortgage NOT used)
- For direct property: allocation should sum to ${round(total_capital, 2)} (savings + mortgage)
- emergency_fund: minimum 10-15% of total
- taxes_and_fees: 3-5% of property value (closing costs, escrow)

═══════════════════════════════════════════════════════════

REQUIRED FIELDS:
1. title — short strategy name (e.g., "Prop 13-Locked Rental in Oakland")
2. type — one of: "REIT" | "rental" | "flip" | "mortgage" | "land" | "garage" | "storage" | "commercial" | "mixed" | "primary"
3. description — California-aware strategy (mention Prop 13, regional dynamics, 3-4 sentences)
4. allocation — concrete USD split
5. expected_return — annual return (0.03–0.12)
6. risk — risk level (0–1)
7. stability — stability (0–1)
8. pros — 3 advantages
9. cons — 2 risks (honest about earthquake/wildfire/mortgage burden)
10. next_steps — 3 concrete actions (CA-specific)
11. time_to_profit — realistic timeline

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- All amounts in USD
- For direct property: factor in mortgage payment ${mortgage_monthly}/mo

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


async def generate_real_estate_strategy_llm(user, mortgage_loan: dict) -> tuple[dict, list]:
    """
    Generates real estate strategy with RAG context.
    Returns: (llm_response, rag_chunk_ids)
    """
    # ⭐ Step 1: Retrieve California real estate knowledge
    rag_context, rag_chunk_ids = _build_rag_context_re(user)

    # Step 2: Build prompt with RAG context injected
    prompt = build_prompt(user, mortgage_loan, rag_context=rag_context)

    # Step 3: LLM call
    response = await call_llm_with_retry(
        llm_call=lambda: call_llm(prompt),
        agent_name="real_estate"
    )

    return response, rag_chunk_ids


def validate_real_estate_output(data: dict) -> dict:
    valid_types = {
        "REIT", "rental", "flip", "mortgage",
        "land", "garage", "storage", "commercial", "mixed", "primary"
    }
    type_value = safe_str(data.get("type"), "REIT")
    if type_value not in valid_types:
        type_value = "REIT"

    # ⭐ BUG #5 FIX: REIT realistic risk/stability calibration
    if type_value == "REIT":
        default_risk = 0.40
        default_stability = 0.70
        risk_min, risk_max = 0.30, 0.65
        stab_min, stab_max = 0.50, 0.80
    else:
        default_risk = 0.30
        default_stability = 0.80
        risk_min, risk_max = 0.20, 0.70
        stab_min, stab_max = 0.60, 0.90

    # ⭐ BUG #7 FIX: Round all numeric values
    raw_return = data.get("expected_return")
    expected_return = round(clamp(raw_return, 0.01, 0.12, 0.05), 4)

    raw_risk = data.get("risk")
    risk_value = round(clamp(raw_risk, risk_min, risk_max, default_risk), 4)

    raw_stability = data.get("stability")
    stability_value = round(clamp(raw_stability, stab_min, stab_max, default_stability), 4)

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
        "expected_return": expected_return,
        "risk": risk_value,
        "stability": stability_value,
        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), []),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "2-3 years"),
    }


async def run_real_estate_agent(user, mortgage_loan: dict) -> dict:
    """Real estate agent with mortgage + RAG context."""
    # ⭐ FIX: generate_real_estate_strategy_llm returns tuple
    raw, rag_chunk_ids = await generate_real_estate_strategy_llm(user, mortgage_loan)
    result = validate_real_estate_output(raw)
    result["rag_sources"] = rag_chunk_ids  # ⭐ Transparency
    return result