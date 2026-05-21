# app/agents/real_estate_agent.py
"""
Unified Real Estate Agent v5.2.5 — SEGMENT-AWARE + RAG-AWARE REALISM.

v5.2.5 NEW:
  - Threshold raised from 0.5 → 0.8 (covers mid-tier $700k-1.4M in Bay Area)
  - Bay Area note expanded: per-tier breakdown (entry, mid-low, mid-high)
  - Counters RAG chunk that mentions Palo Alto $3.2M
  - Explicit cities OK vs NOT OK per price tier
"""

from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import (
    parse_llm_json, clamp, safe_list, safe_str, safe_dict,
    call_llm_with_retry
)
from app.core.california_config import REGION_DATA, get_city_real_estate_data
from app.engines.inflation_engine import real_return, AgentType
from app.rag.retriever import retrieve
from app.utils.logger import log_llm_interaction


def _build_rag_context(user) -> tuple[str, list]:
    region = user.location.region.value
    city = user.location.city
    interests = ", ".join(user.professional.interests) if user.professional.interests else ""

    primary_query = f"California {region} {city} real estate property mortgage Prop 13 {interests}"
    secondary_query = "California real estate tax mortgage Mello-Roos property"

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

    return "\n".join(context_parts), [c['id'] for c in all_chunks]


PROPERTY_TYPE_DEFAULTS = {
    "rental": {
        "appreciation_pct": 4.5, "vacancy_pct": 8,
        "annual_maint_pct": 1.5, "annual_insurance_pct": 0.5,
        "is_rental": True, "is_flip": False,
        "expected_return_typical": 0.06,
    },
    "primary": {
        "appreciation_pct": 4.5, "vacancy_pct": 0,
        "annual_maint_pct": 1.5, "annual_insurance_pct": 0.5,
        "is_rental": False, "is_flip": False,
        "expected_return_typical": 0.045,
    },
    "flip": {
        "appreciation_pct": 0, "vacancy_pct": 100,
        "annual_maint_pct": 0, "annual_insurance_pct": 0.6,
        "is_rental": False, "is_flip": True,
        "expected_return_typical": 0.15,
    },
    "commercial": {
        "appreciation_pct": 3.5, "vacancy_pct": 12,
        "annual_maint_pct": 1.0, "annual_insurance_pct": 0.7,
        "is_rental": True, "is_flip": False,
        "expected_return_typical": 0.07,
    },
    "garage": {
        "appreciation_pct": 3, "vacancy_pct": 5,
        "annual_maint_pct": 0.3, "annual_insurance_pct": 0.3,
        "is_rental": True, "is_flip": False,
        "expected_return_typical": 0.07,
    },
    "storage": {
        "appreciation_pct": 3.5, "vacancy_pct": 7,
        "annual_maint_pct": 0.5, "annual_insurance_pct": 0.4,
        "is_rental": True, "is_flip": False,
        "expected_return_typical": 0.08,
    },
    "land": {
        "appreciation_pct": 5, "vacancy_pct": 100,
        "annual_maint_pct": 0.2, "annual_insurance_pct": 0.2,
        "is_rental": False, "is_flip": False,
        "expected_return_typical": 0.05,
    },
    "mixed_use": {
        "appreciation_pct": 4.5, "vacancy_pct": 10,
        "annual_maint_pct": 1.5, "annual_insurance_pct": 0.6,
        "is_rental": True, "is_flip": False,
        "expected_return_typical": 0.07,
    },
}


def _calculate_loan_payment(loan_amount: float, rate: float, years: int) -> dict:
    if loan_amount <= 0 or rate <= 0 or years <= 0:
        return {"monthly_payment": 0, "annual_payment": 0, "total_paid": 0, "total_interest": 0}
    months = years * 12
    monthly_rate = rate / 12
    monthly_payment = (
            loan_amount * monthly_rate * ((1 + monthly_rate) ** months) /
            (((1 + monthly_rate) ** months) - 1)
    )
    annual_payment = monthly_payment * 12
    total_paid = monthly_payment * months
    return {
        "monthly_payment": round(monthly_payment, 2),
        "annual_payment": round(annual_payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_paid - loan_amount, 2),
    }


def _calculate_principal_paid_year_n(loan_amount: float, rate: float, years: int, year_n: int) -> float:
    if loan_amount <= 0 or rate <= 0 or years <= 0 or year_n > years:
        return 0
    annual_payment = _calculate_loan_payment(loan_amount, rate, years)["annual_payment"]
    remaining = loan_amount
    total_principal_paid = 0
    for year in range(1, year_n + 1):
        annual_interest = remaining * rate
        annual_principal = max(0, annual_payment - annual_interest)
        if year == year_n:
            return round(annual_principal, 2)
        total_principal_paid += annual_principal
        remaining -= annual_principal
        if remaining <= 0:
            return 0
    return 0


def _validate_real_estate_config(config: dict) -> tuple[bool, str]:
    loan_amount = config.get("loan_amount", 0)
    savings_to_use = config.get("savings_to_use", 0)

    if loan_amount <= 0:
        return False, (
            "Real estate strategy requires a mortgage. "
            "For passive real estate exposure without a mortgage, consider stocks "
            "(VNQ ETF for REIT exposure)."
        )

    total_value = loan_amount + savings_to_use
    if total_value <= 0:
        return False, "Total property value must be greater than zero."

    down_pct = savings_to_use / total_value
    if down_pct < 0.20:
        return False, (
            f"Down payment is {down_pct:.1%} of total property value "
            f"(${savings_to_use:,.0f} / ${total_value:,.0f}). "
            f"California conventional mortgages require minimum 20% down payment. "
            f"Increase savings allocation to at least ${total_value * 0.20:,.0f}."
        )

    return True, ""


# ─────────────────────────────────
# ⭐ v5.2.5 — SEGMENT-AWARE REALISM (RAG-aware)
# ─────────────────────────────────
def _build_realism_note(total_property_value: float, region, region_data: dict) -> str:
    """
    ⭐ v5.2.5:
    Per-tier realism breakdown for Bay Area (counters RAG chunk Palo Alto $3.2M mention).
    Threshold raised 0.5 → 0.8 (covers mid-tier).
    """
    median_home = region_data.get("median_home_price", 800000)
    # ⭐ v5.2.5: Threshold 0.5 → 0.8
    is_entry_level = total_property_value < median_home * 0.8

    if not is_entry_level:
        return ""

    region_value = region.value if hasattr(region, "value") else str(region)

    if region_value == "BAY_AREA":
        # ⭐ v5.2.5: Per-tier breakdown
        if total_property_value < 500_000:
            tier = "ENTRY"
            cities_ok = [
                "Vacaville, Fairfield (suburbs 50+ min from SF: starter homes $250-400k)",
                "Vallejo (older homes $250-350k — higher vacancy/management risk)",
                "Concord, Walnut Creek older condos ($300-400k)",
                "East Oakland (older condos $250-350k, varies by neighborhood)",
            ]
            cities_bad = [
                "San Francisco proper ($1.4M+ median)",
                "Palo Alto ($3.2M median — APARTMENT BUILDING territory)",
                "Mountain View ($2.2M median)",
                "Berkeley ($1.5M median)",
                "Fremont ($1.5M median)",
                "San Jose ($1.3M median)",
            ]
            rent_range = "$1,800-2,500/month"
        elif total_property_value < 800_000:
            tier = "MID-LOW"
            cities_ok = [
                "Concord, Walnut Creek 2BR condos ($500-700k)",
                "Hayward, San Leandro starter homes ($600-800k)",
                "Pleasant Hill, Antioch single-family ($600-750k)",
                "Oakland safer neighborhoods condos ($500-700k)",
            ]
            cities_bad = [
                "San Francisco (median $1.4M)",
                "Palo Alto, Mountain View, Berkeley",
                "South Bay tech corridor (Cupertino, Sunnyvale)",
            ]
            rent_range = "$2,500-3,500/month"
        else:  # 800k - 1.12M
            tier = "MID-HIGH"
            cities_ok = [
                "Redwood City, San Mateo condos ($800k-1.1M)",
                "East Palo Alto townhouses ($900k-1.2M)",
                "Mountain View older condos ($900k-1.1M)",
                "Hayward, Fremont newer condos ($800k-1.1M)",
                "Daly City, South San Francisco ($800k-1M)",
                "Sunnyvale older 1BR condos ($900k-1.1M)",
            ]
            cities_bad = [
                "Palo Alto proper ($3.2M median)",
                "Atherton, Woodside ($5M+)",
                "Los Altos ($4M+)",
                "Pacific Heights, Cow Hollow (SF luxury)",
            ]
            rent_range = "$3,000-4,200/month"

        return f"""
═══════════════════════════════════════════════════════════════
⚠️ REALISM CONSTRAINTS — {tier}-TIER SEGMENT (${total_property_value:,.0f} in Bay Area):
═══════════════════════════════════════════════════════════════

⛔ CITIES YOU CANNOT AFFORD AT THIS PRICE:
{chr(10).join(f"   - {c}" for c in cities_bad)}

⛔ DO NOT use Bay Area overall median (${median_home:,.0f}) as comparison — wrong segment
⛔ RAG may mention Palo Alto $3.2M or premium cities — those are IRRELEVANT for ${total_property_value:,.0f} budget
⛔ DO NOT use peninsula/SF median rent ($4,500-5,800) — irrelevant for this segment

✅ REALISTIC CITIES for ${total_property_value:,.0f}:
{chr(10).join(f"   - {c}" for c in cities_ok)}

✅ REALISTIC RENT for this segment: {rent_range}
✅ REALISTIC COMPARABLES: must be in similar price range
   GOOD examples for ${total_property_value:,.0f}: properties from the cities listed above
   BAD examples: anything in Palo Alto, SF proper, premium peninsula

⚠️ Entry/Mid-tier often has:
   - Higher vacancy (8-12% vs 5-8% premium)
   - HOA fees (older condos: $300-600/mo)
   - Longer commute to tech hubs = different rental demand
═══════════════════════════════════════════════════════════════
"""
    elif region_value == "LOS_ANGELES":
        return f"""
═══════════════════════════════════════════════════════════════
⚠️ REALISM CONSTRAINTS — ENTRY/MID SEGMENT (${total_property_value:,.0f} in LA):
═══════════════════════════════════════════════════════════════
⛔ DO NOT mention "Beverly Hills", "Santa Monica", "Westside",
   "Malibu", "West Hollywood" — unattainable at this price
⛔ DO NOT use LA median (${median_home:,.0f}) as comparison

✅ REALISTIC LOCATIONS at this price point:
   - Inland Empire: Riverside, San Bernardino, Moreno Valley
   - Antelope Valley: Lancaster, Palmdale
   - Eastern LA suburbs: El Monte, Baldwin Park
   - South LA: Inglewood, Compton older units

✅ REALISTIC RENT: $1,500-2,500/month
═══════════════════════════════════════════════════════════════
"""
    elif region_value == "SAN_DIEGO":
        return f"""
═══════════════════════════════════════════════════════════════
⚠️ REALISM CONSTRAINTS — ENTRY/MID SEGMENT (${total_property_value:,.0f} in San Diego):
═══════════════════════════════════════════════════════════════
⛔ DO NOT mention "La Jolla", "Coronado", "Del Mar",
   "Pacific Beach", "Mission Beach" — unattainable
⛔ DO NOT use SD median (${median_home:,.0f}) as comparison

✅ REALISTIC LOCATIONS at this price point:
   - El Cajon, Lemon Grove (older condos)
   - National City, Chula Vista (starter homes)
   - East County suburbs (Santee, La Mesa, Spring Valley)
   - Escondido, Vista (North County inland)

✅ REALISTIC RENT: $1,700-2,400/month
═══════════════════════════════════════════════════════════════
"""
    else:
        return f"""
═══════════════════════════════════════════════════════════════
⚠️ REALISM CONSTRAINTS — ENTRY/MID SEGMENT:
═══════════════════════════════════════════════════════════════
Property value ${total_property_value:,.0f} is significantly below {region_data['display_name']} median (${median_home:,.0f}).
Mention REALISTIC entry-level locations and comparables for this price tier.
Do NOT use overall regional median as comparison — wrong segment.
═══════════════════════════════════════════════════════════════
"""


def build_prompt(user, config: dict, rag_context: str = "") -> str:
    loan_amount = config.get("loan_amount", 0)
    loan_years = config.get("loan_years", 30)
    savings_to_use = config.get("savings_to_use", 0)
    interest_rate = config.get("interest_rate", 0.055)

    total_property_value = loan_amount + savings_to_use
    down_pct = savings_to_use / total_property_value if total_property_value > 0 else 0
    loan_payment = _calculate_loan_payment(loan_amount, interest_rate, loan_years)

    interests_text = ", ".join(user.professional.interests) if user.professional.interests else "Not specified"
    experience_text = user.professional.prior_experience or "No prior real estate experience"

    hours_value = user.professional.weekly_hours.value

    region = user.location.region
    region_data = REGION_DATA[region]
    city_data = get_city_real_estate_data(user.location.city, region)
    median_price = region_data["median_home_price"]

    # ⭐ v5.2.5 REALISM CHECK — Segment-aware constraints
    realism_note = _build_realism_note(total_property_value, region, region_data)

    return f"""
You are a senior California real estate investment advisor specializing in DIRECT property purchases.

⚠️ MATHEMATICAL CONSISTENCY MANDATORY. Numbers will be auto-verified.

USER PROFILE:
- Age: {user.personal.age} | Region: {region_data['display_name']} | City: {user.location.city}
- Interests: {interests_text}
- Prior experience: {experience_text}
- Weekly hours: {hours_value}
- Income: ${user.financial.income:,}/mo | Savings: ${user.financial.savings:,}

🏦 MORTGAGE CONFIGURATION:
- Mortgage: ${loan_amount:,.0f} @ {interest_rate * 100:.2f}% × {loan_years}yr
- Down payment: ${savings_to_use:,.0f} ({down_pct:.1%})
- Total property value: ${total_property_value:,.0f}
- Monthly payment: ${loan_payment['monthly_payment']:,.2f}
- Annual payment: ${loan_payment['annual_payment']:,.2f}

✅ Down payment validation: PASSED (≥20% required)

PREFERENCES: {user.preferences.risk_profile.value} risk, {user.preferences.horizon.value} yr horizon

🌴 CALIFORNIA — {region_data['display_name']}:
- Median home: ${median_price:,}
- Price/sqft: ${city_data['price_per_sqft']}
- Median 2BR rent: ${city_data['rent_2br']}/month
- Prop 13 effective tax: {city_data['property_tax_effective'] * 100:.2f}%
- Rental yield avg: {city_data['rental_yield_avg'] * 100:.1f}%
- Risks: {region_data['risk_factors']}

{rag_context}

{realism_note}

═══════════════════════════════════════════════════════════════
🏛️ CALIFORNIA-SPECIFIC (CRITICAL):
═══════════════════════════════════════════════════════════════
1. **Prop 13**: Tax capped at 1% purchase price + max 2%/yr increase
2. **1031 Exchange**: Defer capital gains via property swap
3. **Mello-Roos**: Special assessments in newer developments
4. **Earthquake**: {region_data['risk_factors'].get('earthquake', 'unknown')}
   CEA policy $800-3,000/yr
5. **Wildfire**: {region_data['risk_factors'].get('wildfire', 'unknown')}

═══════════════════════════════════════════════════════════════
🏠 PROPERTY TYPE SELECTION:
═══════════════════════════════════════════════════════════════
Choose ONE that fits total value ${total_property_value:,.0f}, region, hours, and interests:

  - "rental"      → Long-term rental (apartment, house, condo)
  - "primary"     → Primary residence (user lives in it)
  - "flip"        → Buy → renovate → sell (12-18 months, 30+h/week)
  - "commercial"  → Commercial space (office, retail)
  - "garage"      → Parking/garage rentals (passive)
  - "storage"     → Storage unit facility
  - "land"        → Land for development or hold
  - "mixed_use"   → Combined residential + commercial

═══════════════════════════════════════════════════════════════
🔢 v5.2 MATH RULES — REALISTIC PROJECTIONS
═══════════════════════════════════════════════════════════════

RULE 1: Allocation MUST sum to ${total_property_value:,.0f}
  - down_payment: ${savings_to_use:,.0f}
  - property_value: ${loan_amount:,.0f}
  - taxes_and_fees: 3-5% closing costs
  - renovation_reserve: 5-10% (flips: 15-20%)
  - emergency_fund: 3-5% of property value

RULE 2: Rental income MUST match California rates AND price segment
  IF realism constraints above were triggered, use rent from THAT range
  ELSE use city median rent ${city_data['rent_2br']}/mo

RULE 3: Operating costs realistic breakdown:
  - Property tax: Prop 13 ~1.25% of purchase price/yr
  - Maintenance: 1-1.5% of property value/yr (rental), 0.3% (garage/storage)
  - Insurance: 0.5-0.7% (higher in fire zones)
  - HOA: $200-800/mo if applicable
  - Vacancy: 5-10% reduction for rental

RULE 4: Appreciation (California):
  - Rental/Primary: 4-5%/yr (last decade avg)
  - Land: 5-7%/yr (development potential)
  - Commercial: 3-4%/yr
  - Flip: N/A (short-term, no appreciation)

RULE 5: Y1/Y3/Y5 projections show:
  - rental_income (after vacancy)
  - operating_costs (tax + maint + insurance + HOA)
  - mortgage_payment (fixed: ${loan_payment['annual_payment']:,.0f})
  - principal_paid (equity buildup, grows each year)
  - appreciation (capital gain)
  - cash_flow = rental_income - operating_costs - mortgage_payment
  - total_return = cash_flow + principal_paid + appreciation

RULE 6: Scenarios MUST include realistic California risks:
  - best_case: Hot market + low vacancy + appreciation 7-8%
  - base_case: Steady appreciation 4-5%, normal vacancy
  - worst_case: Recession + vacancy spike, NEGATIVE possible (recession + drop)

═══════════════════════════════════════════════════════════════
📝 OUTPUT FORMAT (STRICT JSON, no markdown):
═══════════════════════════════════════════════════════════════

{{
  "agent": "real_estate",
  "title": "...",
  "type": "rental",
  "description": "3-4 sentences. {region_data['display_name']}-specific. Mention Prop 13. USE REALISTIC CITY from constraints above.",

  "allocation": {{
    "down_payment": {savings_to_use},
    "property_value": {loan_amount},
    "taxes_and_fees": 0,
    "renovation_reserve": 0,
    "emergency_fund": 0
  }},

  "expected_return": 0.06,
  "risk": 0.35,
  "stability": 0.75,

  "property_market_context": {{
    "median_property_value_usd": {median_price},
    "median_rent_monthly_usd": 0,
    "rent_to_price_ratio_pct": 0.0,
    "appreciation_rate_pct_5yr": 4.5,
    "comparable_properties": ["...", "...", "..."],
    "demand_indicator": "..."
  }},

  "property_economics": {{
    "purchase_price_usd": {total_property_value},
    "down_payment_usd": {savings_to_use},
    "monthly_rent_usd": 0,
    "annual_rental_income_usd": 0,
    "vacancy_rate_pct": 8,
    "expected_annual_appreciation_pct": 4.5,
    "is_rental": true,
    "is_flip": false
  }},

  "projections": {{
    "year_1": {{
      "rental_income": 0, "operating_costs": 0,
      "mortgage_payment": {loan_payment['annual_payment']:.0f},
      "principal_paid": 0, "appreciation": 0,
      "cash_flow": 0, "total_return": 0
    }},
    "year_3": {{
      "rental_income": 0, "operating_costs": 0,
      "mortgage_payment": {loan_payment['annual_payment']:.0f},
      "principal_paid": 0, "appreciation": 0,
      "cash_flow": 0, "total_return": 0
    }},
    "year_5": {{
      "rental_income": 0, "operating_costs": 0,
      "mortgage_payment": {loan_payment['annual_payment']:.0f},
      "principal_paid": 0, "appreciation": 0,
      "cash_flow": 0, "total_return": 0
    }}
  }},

  "scenarios": {{
    "best_case": {{"appreciation_pct": 8, "cash_flow_pct": 5, "total_roi_pct": 13, "narrative": "Hot California market + low vacancy"}},
    "base_case": {{"appreciation_pct": 4.5, "cash_flow_pct": 1.5, "total_roi_pct": 6, "narrative": "Steady California appreciation"}},
    "worst_case": {{"appreciation_pct": -3, "cash_flow_pct": -1, "total_roi_pct": -4, "narrative": "Recession + vacancy spike"}}
  }},

  "break_even": {{"years_to_breakeven": 3, "cumulative_cash_flow_breakeven_year": 5, "explanation": "Year by which cumulative equity exceeds initial down payment."}},

  "pros": ["...", "...", "..."],
  "cons": ["...", "..."],
  "next_steps": ["...", "...", "..."],
  "time_to_profit": "..."
}}
"""


# ─────────────────────────
# 🏠 GENERATE REAL ESTATE STRATEGY
# ─────────────────────────
async def generate_real_estate_strategy_llm(
        user,
        config: dict
) -> tuple[dict, list]:
    # 🔍 RAG context
    rag_context, rag_chunk_ids = _build_rag_context(user)

    # 🧠 Prompt
    prompt = build_prompt(
        user=user,
        config=config,
        rag_context=rag_context
    )

    agent_name = "real_estate"

    try:
        # 🤖 LLM call
        response = await call_llm_with_retry(
            llm_call=lambda: call_llm(prompt),
            agent_name=agent_name
        )

        # 📝 success logging
        log_llm_interaction(
            agent=agent_name,
            prompt=prompt,
            raw_response=str(response),
            parsed_response=response,
            success=True
        )

        return response, rag_chunk_ids

    except Exception as e:

        # ❌ error logging
        log_llm_interaction(
            agent=agent_name,
            prompt=prompt,
            raw_response="",
            parsed_response=None,
            success=False,
            error=str(e)
        )

        raise


def _rescale_allocation_to_capital(allocation: dict, target_total: float) -> dict:
    if target_total <= 0:
        return allocation
    keys = ["down_payment", "property_value", "taxes_and_fees", "renovation_reserve", "emergency_fund"]
    for k in keys:
        if k not in allocation:
            allocation[k] = 0
        try:
            allocation[k] = max(0, float(allocation[k]))
        except (TypeError, ValueError):
            allocation[k] = 0

    current_sum = sum(allocation[k] for k in keys)
    if current_sum == 0:
        allocation["down_payment"] = round(target_total * 0.18, 2)
        allocation["property_value"] = round(target_total * 0.72, 2)
        allocation["taxes_and_fees"] = round(target_total * 0.04, 2)
        allocation["renovation_reserve"] = round(target_total * 0.04, 2)
        allocation["emergency_fund"] = round(target_total * 0.02, 2)
        return allocation

    ratio = target_total / current_sum
    for k in keys:
        allocation[k] = round(allocation[k] * ratio, 2)
    new_sum = sum(allocation[k] for k in keys)
    allocation["emergency_fund"] = round(allocation["emergency_fund"] + (target_total - new_sum), 2)
    return allocation


def _validate_property_market_context(data: dict, median_home_price: float) -> dict:
    mc = data.get("property_market_context") or {}
    return {
        "median_property_value_usd": int(clamp(mc.get("median_property_value_usd"), 0, 50_000_000, median_home_price)),
        "median_rent_monthly_usd": int(clamp(mc.get("median_rent_monthly_usd"), 0, 50_000, 0)),
        "rent_to_price_ratio_pct": round(clamp(mc.get("rent_to_price_ratio_pct"), 0, 5, 0.5), 2),
        "appreciation_rate_pct_5yr": round(clamp(mc.get("appreciation_rate_pct_5yr"), -10, 15, 4.5), 1),
        "comparable_properties": safe_list(mc.get("comparable_properties"), ["Comparable 1", "Comparable 2"])[:5],
        "demand_indicator": safe_str(mc.get("demand_indicator"), "Market demand assessment")[:200],
    }


def _validate_property_economics(data: dict, total_value: float, down_payment: float, type_value: str) -> dict:
    pe = data.get("property_economics") or {}
    defaults = PROPERTY_TYPE_DEFAULTS.get(type_value, PROPERTY_TYPE_DEFAULTS["rental"])

    monthly_rent = clamp(pe.get("monthly_rent_usd"), 0, 1_000_000, 0)
    annual_rent_raw = monthly_rent * 12

    llm_annual_rent = clamp(pe.get("annual_rental_income_usd"), 0, 100_000_000, 0)
    if llm_annual_rent > 0 and abs(llm_annual_rent - annual_rent_raw) < annual_rent_raw * 0.5:
        annual_rent = llm_annual_rent
    else:
        annual_rent = annual_rent_raw

    return {
        "purchase_price_usd": round(clamp(pe.get("purchase_price_usd"), 0, 100_000_000, total_value), 2),
        "down_payment_usd": round(clamp(pe.get("down_payment_usd"), 0, 100_000_000, down_payment), 2),
        "monthly_rent_usd": round(monthly_rent, 2),
        "annual_rental_income_usd": round(annual_rent, 2),
        "vacancy_rate_pct": round(clamp(pe.get("vacancy_rate_pct"), 0, 100, defaults["vacancy_pct"]), 1),
        "expected_annual_appreciation_pct": round(
            clamp(pe.get("expected_annual_appreciation_pct"), -10, 15, defaults["appreciation_pct"]), 2),
        "is_rental": bool(pe.get("is_rental", defaults["is_rental"])),
        "is_flip": bool(pe.get("is_flip", defaults["is_flip"])),
    }


def _recompute_projections(data: dict, property_econ: dict, config: dict, type_value: str) -> dict:
    loan_amount = config.get("loan_amount", 0)
    rate = config.get("interest_rate", 0.055)
    years = config.get("loan_years", 30)
    total_value = property_econ["purchase_price_usd"]
    monthly_rent = property_econ["monthly_rent_usd"]
    vacancy = property_econ["vacancy_rate_pct"] / 100
    appreciation_pct = property_econ["expected_annual_appreciation_pct"] / 100
    is_rental = property_econ["is_rental"]
    is_flip = property_econ["is_flip"]

    defaults = PROPERTY_TYPE_DEFAULTS.get(type_value, PROPERTY_TYPE_DEFAULTS["rental"])
    maint_pct = defaults["annual_maint_pct"] / 100
    insurance_pct = defaults["annual_insurance_pct"] / 100

    annual_mortgage = _calculate_loan_payment(loan_amount, rate, years)["annual_payment"]

    def _build_year(year_n: int) -> dict:
        rental_income = round(monthly_rent * 12 * (1 - vacancy), 2) if is_rental else 0
        property_tax = total_value * 0.0125
        maintenance = total_value * maint_pct
        insurance = total_value * insurance_pct
        operating_costs = round(property_tax + maintenance + insurance, 2)
        principal_paid = _calculate_principal_paid_year_n(loan_amount, rate, years, year_n)

        if is_flip:
            appreciation = 0
        else:
            current_value = total_value * ((1 + appreciation_pct) ** year_n)
            previous_value = total_value * ((1 + appreciation_pct) ** (year_n - 1))
            appreciation = round(current_value - previous_value, 2)

        cash_flow = round(rental_income - operating_costs - annual_mortgage, 2)
        total_return = round(cash_flow + principal_paid + appreciation, 2)

        return {
            "rental_income": rental_income,
            "operating_costs": operating_costs,
            "mortgage_payment": round(annual_mortgage, 2),
            "principal_paid": round(principal_paid, 2),
            "appreciation": appreciation,
            "cash_flow": cash_flow,
            "total_return": total_return,
        }

    return {
        "year_1": _build_year(1),
        "year_3": _build_year(3),
        "year_5": _build_year(5),
    }


def _validate_scenarios(data: dict, base_return: float) -> dict:
    sc = data.get("scenarios") or {}

    def _v(key, default_appr_pct, default_cf_pct, narrative_default):
        item = sc.get(key) or {}
        appr_pct = round(clamp(item.get("appreciation_pct"), -15, 20, default_appr_pct), 1)
        cf_pct = round(clamp(item.get("cash_flow_pct"), -10, 15, default_cf_pct), 1)
        total_roi = round(appr_pct + cf_pct, 1)
        return {
            "appreciation_pct": appr_pct,
            "cash_flow_pct": cf_pct,
            "total_roi_pct": total_roi,
            "narrative": safe_str(item.get("narrative"), narrative_default)[:300],
        }

    best = _v("best_case", 8, 5, "Hot California market + low vacancy")
    base = _v("base_case", 4.5, 1.5, "Steady California appreciation")
    worst = _v("worst_case", -3, -1, "Recession + vacancy spike")

    if best["total_roi_pct"] <= base["total_roi_pct"] + 3:
        best["appreciation_pct"] = round(base["appreciation_pct"] + 3.5, 1)
        best["cash_flow_pct"] = round(base["cash_flow_pct"] + 3.5, 1)
        best["total_roi_pct"] = round(best["appreciation_pct"] + best["cash_flow_pct"], 1)

    if worst["total_roi_pct"] >= base["total_roi_pct"] - 3:
        worst["appreciation_pct"] = round(base["appreciation_pct"] - 7.5, 1)
        worst["cash_flow_pct"] = round(base["cash_flow_pct"] - 2.5, 1)
        worst["total_roi_pct"] = round(worst["appreciation_pct"] + worst["cash_flow_pct"], 1)

    return {"best_case": best, "base_case": base, "worst_case": worst}


def _validate_break_even(data: dict, projections: dict, down_payment: float) -> dict:
    be = data.get("break_even") or {}

    if down_payment <= 0:
        return {"years_to_breakeven": 0, "cumulative_cash_flow_breakeven_year": 0,
                "explanation": "Break-even N/A (no down payment)."}

    y1 = projections.get("year_1", {})
    y3 = projections.get("year_3", {})
    y5 = projections.get("year_5", {})

    y1_equity = y1.get("principal_paid", 0) + y1.get("appreciation", 0)
    y3_equity = y3.get("principal_paid", 0) + y3.get("appreciation", 0)
    y5_equity = y5.get("principal_paid", 0) + y5.get("appreciation", 0)

    avg_annual_equity = y3_equity if y3_equity > 0 else (y1_equity + y3_equity + y5_equity) / 3

    if avg_annual_equity <= 0:
        return {
            "years_to_breakeven": 30,
            "cumulative_cash_flow_breakeven_year": 30,
            "explanation": f"Property does not build equity. Down payment of ${down_payment:,.0f} may never be recovered.",
        }

    breakeven_year = max(1, int(down_payment / avg_annual_equity) + 1)
    breakeven_year = min(breakeven_year, 30)
    cumulative_at_breakeven = avg_annual_equity * breakeven_year

    return {
        "years_to_breakeven": breakeven_year,
        "cumulative_cash_flow_breakeven_year": int(clamp(be.get("cumulative_cash_flow_breakeven_year"), 1, 30, 5)),
        "explanation": safe_str(
            be.get("explanation"),
            f"By Year {breakeven_year}, you've built ~${cumulative_at_breakeven:,.0f} in equity "
            f"(principal payments + appreciation), exceeding your ${down_payment:,.0f} down payment. "
            f"Annual equity buildup averages ${avg_annual_equity:,.0f}/year."
        )[:300],
    }


def _derive_expected_return_from_projections(projections: dict, total_capital: float, type_value: str) -> float:
    if total_capital <= 0:
        return 0.0
    defaults = PROPERTY_TYPE_DEFAULTS.get(type_value, PROPERTY_TYPE_DEFAULTS["rental"])
    max_for_type = defaults["expected_return_typical"] * 1.5
    y1 = projections.get("year_1", {}).get("total_return", 0)
    y3 = projections.get("year_3", {}).get("total_return", 0)
    avg_return = (y1 + y3) / 2
    raw_roi = avg_return / total_capital
    return round(max(-0.20, min(raw_roi, max_for_type)), 4)


def _determine_status_from_projections(projections: dict, down_payment: float) -> str:
    if down_payment <= 0:
        return "not_profitable"

    y3_total = projections.get("year_3", {}).get("total_return", 0)
    y5_total = projections.get("year_5", {}).get("total_return", 0)
    y3_cash_flow = projections.get("year_3", {}).get("cash_flow", 0)

    if y3_cash_flow < -down_payment * 0.15:
        return "not_profitable"

    if y3_total > down_payment * 0.05 and y3_cash_flow > -down_payment * 0.02:
        return "profitable"
    elif y3_total > 0 or y5_total > 0:
        return "marginal"
    else:
        return "not_profitable"


def _build_calculation_breakdown(user, config: dict, property_econ: dict, projections: dict,
                                 type_value: str, expected_return: float, total_capital: float) -> dict:
    loan_amount = config.get("loan_amount", 0)
    savings_to_use = config.get("savings_to_use", 0)
    interest_rate = config.get("interest_rate", 0)
    loan_years = config.get("loan_years", 0)
    annual_mortgage = _calculate_loan_payment(loan_amount, interest_rate, loan_years)["annual_payment"]
    monthly_mortgage = annual_mortgage / 12 if annual_mortgage > 0 else 0

    currency = user.financial.currency.value
    y1 = projections.get("year_1", {})
    y3 = projections.get("year_3", {})

    monthly_rent = property_econ["monthly_rent_usd"]
    annual_rent_gross = monthly_rent * 12
    annual_rent_net = y1.get("rental_income", 0)
    vacancy = property_econ["vacancy_rate_pct"]
    appreciation_pct = property_econ["expected_annual_appreciation_pct"]
    is_rental = property_econ["is_rental"]
    is_flip = property_econ["is_flip"]

    try:
        agent_type = AgentType("real_estate")
        real_roi = real_return(nominal_return=expected_return, agent=agent_type, currency=currency)
        inflation_pct = round((expected_return - real_roi) * 100, 2)
    except Exception:
        real_roi = expected_return * 0.80
        inflation_pct = round(expected_return * 20, 2)

    steps = [
        {
            "step": 1,
            "title": "Your Capital (Down Payment + Mortgage)",
            "explanation": "Your total investment consists of cash down payment (your equity) and a mortgage from the bank.",
            "formula": f"${savings_to_use:,.0f} (down payment) + ${loan_amount:,.0f} (mortgage)",
            "result": f"${total_capital:,.0f} (total property value)",
            "value_usd": round(total_capital, 2),
        },
    ]

    if is_rental and monthly_rent > 0:
        steps.append({
            "step": 2,
            "title": "Annual Rental Income (after vacancy)",
            "explanation": f"Monthly rent × 12 months, minus typical {vacancy:.0f}% vacancy (tenants leaving, finding new ones).",
            "formula": f"${monthly_rent:,.0f}/mo × 12 × {100 - vacancy:.0f}% occupancy",
            "result": f"${annual_rent_net:,.0f}/year",
            "value_usd": round(annual_rent_net, 2),
        })
    elif is_flip:
        steps.append({
            "step": 2,
            "title": "Flip Strategy (No Rental Income)",
            "explanation": "Flip properties don't generate rental income — profit comes from buying low, renovating, and selling at a higher price within 12-18 months.",
            "formula": "Profit = Sale price - Purchase - Renovation - Holding costs",
            "result": "Targeting 15-25% return on capital in 12-18 months",
            "value_usd": 0,
        })

    op_costs = y1.get("operating_costs", 0)
    property_tax_annual = round(total_capital * 0.0125, 2)
    defaults = PROPERTY_TYPE_DEFAULTS.get(type_value, PROPERTY_TYPE_DEFAULTS["rental"])
    maint_annual = round(total_capital * defaults["annual_maint_pct"] / 100, 2)
    insurance_annual = round(total_capital * defaults["annual_insurance_pct"] / 100, 2)

    steps.append({
        "step": 3,
        "title": "Operating Costs (California-specific)",
        "explanation": f"Property tax under Prop 13 is locked at ~1.25% of purchase price. Plus annual maintenance ({defaults['annual_maint_pct']:.1f}%) and insurance ({defaults['annual_insurance_pct']:.1f}%).",
        "formula": f"Property tax: ${property_tax_annual:,.0f} + Maintenance: ${maint_annual:,.0f} + Insurance: ${insurance_annual:,.0f}",
        "result": f"-${op_costs:,.0f}/year",
        "value_usd": round(-op_costs, 2),
    })

    if annual_mortgage > 0:
        steps.append({
            "step": 4,
            "title": "Annual Mortgage Payment",
            "explanation": f"Your ${loan_amount:,.0f} mortgage at {interest_rate * 100:.2f}% over {loan_years} years. Part of this is interest (cost) and part is principal (equity you're buying back).",
            "formula": f"${monthly_mortgage:,.2f}/month × 12 months",
            "result": f"-${annual_mortgage:,.0f}/year",
            "value_usd": round(-annual_mortgage, 2),
        })

    y1_cash_flow = y1.get("cash_flow", 0)
    y1_principal = y1.get("principal_paid", 0)
    y1_appreciation = y1.get("appreciation", 0)

    if is_rental:
        steps.append({
            "step": 5,
            "title": "Year 1 Cash Flow + Equity Buildup",
            "explanation": "Real estate has TWO returns: cash flow (rent - costs) you receive monthly, AND equity buildup (principal repayment + appreciation) you accumulate as wealth.",
            "formula": f"Cash flow: ${y1_cash_flow:,.0f} + Principal paid: ${y1_principal:,.0f} + Appreciation: ${y1_appreciation:,.0f}",
            "result": f"Total Year 1 return: ${y1.get('total_return', 0):,.0f}",
            "value_usd": round(y1.get("total_return", 0), 2),
        })
    else:
        steps.append({
            "step": 5,
            "title": f"Year 1 {'Appreciation' if not is_flip else 'Equity Position'}",
            "explanation": f"For non-rental {'land/primary' if not is_flip else 'flip'} property, return comes from appreciation ({appreciation_pct:.1f}%/year) and mortgage principal paydown.",
            "formula": f"Appreciation: ${y1_appreciation:,.0f} + Principal paid: ${y1_principal:,.0f}",
            "result": f"Total Year 1 return: ${y1.get('total_return', 0):,.0f}",
            "value_usd": round(y1.get("total_return", 0), 2),
        })

    raw_avg = (y1.get("total_return", 0) + y3.get("total_return", 0)) / 2
    raw_roi = raw_avg / total_capital if total_capital > 0 else 0
    max_for_type = defaults["expected_return_typical"] * 1.5

    capped_note = None
    if raw_roi > max_for_type:
        capped_note = f"Raw ROI of {raw_roi * 100:.1f}% was capped at {max_for_type * 100:.1f}% for realistic {type_value} property returns in California."

    steps.append({
        "step": 6,
        "title": "Average Annual ROI (capped at type-realistic)",
        "explanation": "Your average annual return on capital over Year 1-3, including cash flow and equity buildup. Capped at California-realistic levels for this property type.",
        "formula": f"(Y1 return ${y1.get('total_return', 0):,.0f} + Y3 return ${y3.get('total_return', 0):,.0f}) ÷ 2 ÷ ${total_capital:,.0f}",
        "result": f"{expected_return * 100:+.2f}% nominal annual ROI",
        "value_pct": round(expected_return * 100, 2),
        "note": capped_note,
    })

    steps.append({
        "step": 7,
        "title": "Inflation-Adjusted (Real) Return",
        "explanation": f"Money loses purchasing power over time. California inflation is typically ~{inflation_pct:.1f}%/year. Real estate is partially inflation-protected (property value tracks inflation), but cash flow still loses value.",
        "formula": f"{expected_return * 100:.2f}% nominal - {inflation_pct:.2f}% inflation",
        "result": f"{real_roi * 100:+.2f}% real annual return",
        "value_pct": round(real_roi * 100, 2),
    })

    y3_cash = y3.get("cash_flow", 0)
    y3_total = y3.get("total_return", 0)
    y3_roi = y3_total / total_capital if total_capital > 0 else 0

    if is_rental:
        if y3_cash >= 0 and y3_total > 0:
            conclusion = (
                f"✅ This is a viable rental investment.\n\n"
                f"📊 By Year 3, you'll have:\n"
                f"• Monthly cash flow: ${y3_cash / 12:+,.0f}/month\n"
                f"• Total annual return: ${y3_total:,.0f} ({y3_roi * 100:.1f}% of capital)\n"
                f"• Equity buildup from appreciation + principal paydown"
            )
        elif y3_total > 0:
            conclusion = (
                f"⚠️ Cash flow is tight but TOTAL return is positive.\n\n"
                f"📊 Year 3 perspective:\n"
                f"• Cash flow: ${y3_cash:,.0f}/year (might be negative — you cover gap)\n"
                f"• Total return: ${y3_total:,.0f} (mostly from appreciation + equity)\n\n"
                f"💡 This works only if you can cover negative cash flow from other income."
            )
        else:
            conclusion = (
                f"❌ This rental loses money even with appreciation.\n\n"
                f"💡 Options:\n"
                f"• Increase down payment to reduce mortgage burden\n"
                f"• Find lower-priced property with better cash flow\n"
                f"• Consider different California region (lower property tax base)"
            )
    elif is_flip:
        conclusion = (
            f"🔨 Flip Strategy Summary:\n\n"
            f"• Target: Buy, renovate, sell within 12-18 months\n"
            f"• Expected profit: 15-25% on capital\n"
            f"• Critical: Renovation budget must be accurate\n"
            f"• Risk: Market timing, contractor delays, permits"
        )
    else:
        conclusion = (
            f"🏠 Long-term Appreciation Play:\n\n"
            f"• No rental income — return comes from {appreciation_pct:.1f}%/yr appreciation\n"
            f"• Year 5 expected total return: ${projections.get('year_5', {}).get('total_return', 0):,.0f}\n"
            f"• Tax-advantaged: Prop 13 caps annual tax increase at 2%\n"
            f"• Liquidity: Selling takes 30-90 days, transaction costs ~6%"
        )

    return {
        "steps": steps,
        "summary": {
            "total_capital": round(total_capital, 2),
            "annual_rental_gross": round(annual_rent_gross, 2),
            "annual_rental_net": round(annual_rent_net, 2),
            "annual_operating_costs": round(op_costs, 2),
            "annual_mortgage": round(annual_mortgage, 2),
            "nominal_return_pct": round(expected_return * 100, 2),
            "real_return_pct": round(real_roi * 100, 2),
            "inflation_pct": round(inflation_pct, 2),
        },
        "conclusion": conclusion,
    }


def validate_real_estate_output(data: dict, user=None, config: dict = None) -> dict:
    valid_types = {"rental", "primary", "flip", "commercial", "garage", "storage", "land", "mixed_use"}
    type_value = safe_str(data.get("type"), "rental")
    if type_value not in valid_types:
        type_value = "rental"

    defaults = PROPERTY_TYPE_DEFAULTS[type_value]

    if type_value == "flip":
        default_risk, default_stability = 0.55, 0.50
        risk_min, risk_max = 0.40, 0.80
        stab_min, stab_max = 0.30, 0.70
    elif type_value in ("land", "commercial"):
        default_risk, default_stability = 0.45, 0.65
        risk_min, risk_max = 0.30, 0.70
        stab_min, stab_max = 0.50, 0.85
    else:
        default_risk, default_stability = 0.35, 0.75
        risk_min, risk_max = 0.20, 0.65
        stab_min, stab_max = 0.55, 0.90

    risk_value = round(clamp(data.get("risk"), risk_min, risk_max, default_risk), 4)
    stability_value = round(clamp(data.get("stability"), stab_min, stab_max, default_stability), 4)

    if config:
        loan_amount = config.get("loan_amount", 0)
        savings_to_use = config.get("savings_to_use", 0)
        total_capital = loan_amount + savings_to_use
    else:
        loan_amount = 0
        savings_to_use = 0
        total_capital = 0

    if user:
        region_data = REGION_DATA[user.location.region]
        median_home_price = region_data["median_home_price"]
    else:
        median_home_price = 800000

    rescaled_alloc = _rescale_allocation_to_capital(data.get("allocation") or {}, total_capital)
    property_econ = _validate_property_economics(data, total_capital, savings_to_use, type_value)
    projections = _recompute_projections(data, property_econ, config or {}, type_value)
    derived_return = _derive_expected_return_from_projections(projections, total_capital, type_value)
    derived_status = _determine_status_from_projections(projections, savings_to_use)
    scenarios = _validate_scenarios(data, derived_return)
    break_even = _validate_break_even(data, projections, savings_to_use)
    market_context = _validate_property_market_context(data, median_home_price)
    calc_breakdown = _build_calculation_breakdown(user, config or {}, property_econ, projections, type_value,
                                                  derived_return, total_capital)

    return {
        "agent": "real_estate",
        "title": safe_str(data.get("title"), "Direct Property Investment"),
        "type": type_value,
        "description": safe_str(data.get("description"),
                                "A California direct property strategy with Prop 13 tax benefits."),
        "allocation": rescaled_alloc,
        "expected_return": derived_return,
        "risk": risk_value,
        "stability": stability_value,
        "property_market_context": market_context,
        "property_economics": property_econ,
        "projections": projections,
        "scenarios": scenarios,
        "break_even": break_even,
        "calculation_breakdown": calc_breakdown,
        "derived_status_override": derived_status,
        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), []),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "2-3 years"),
    }


async def run_real_estate_agent(user, config: dict) -> dict:
    """v5.2.5 real estate agent with RAG-aware segment realism."""
    if config is None:
        return {
            "agent": "real_estate",
            "rejected": True,
            "rejection_reason": "No configuration provided for real estate strategy.",
            "title": "Real Estate — Not Configured",
            "expected_return": 0, "risk": 0, "stability": 0,
            "pros": [], "cons": [], "next_steps": [],
            "rag_sources": [],
        }

    is_valid, reason = _validate_real_estate_config(config)
    if not is_valid:
        return {
            "agent": "real_estate",
            "rejected": True,
            "rejection_reason": reason,
            "title": "Real Estate — Strategy Rejected",
            "description": "Real estate strategy was not generated because the configuration did not meet minimum requirements. " + reason,
            "type": "rejected",
            "allocation": {},
            "expected_return": 0, "risk": 0, "stability": 0,
            "pros": [], "cons": [reason],
            "next_steps": [
                "Adjust the down payment to at least 20% of total property value",
                "Or consider passive real estate exposure via the stock strategy (VNQ ETF)",
            ],
            "time_to_profit": "N/A",
            "rag_sources": [],
            "funding_mode": "rejected",
            "loan_amount": config.get("loan_amount", 0),
            "loan_years": config.get("loan_years", 0),
            "savings_used": config.get("savings_to_use", 0),
            "interest_rate": config.get("interest_rate", 0),
            "total_capital": config.get("loan_amount", 0) + config.get("savings_to_use", 0),
        }

    raw, rag_chunk_ids = await generate_real_estate_strategy_llm(user, config)
    result = validate_real_estate_output(raw, user=user, config=config)
    result["rag_sources"] = rag_chunk_ids

    result["funding_mode"] = "mortgage"
    result["loan_amount"] = config.get("loan_amount", 0)
    result["loan_years"] = config.get("loan_years", 0)
    result["savings_used"] = config.get("savings_to_use", 0)
    result["interest_rate"] = config.get("interest_rate", 0)
    result["total_capital"] = config.get("loan_amount", 0) + config.get("savings_to_use", 0)
    result["down_payment_pct"] = round(config.get("savings_to_use", 0) / result["total_capital"], 4)
    result["rejected"] = False

    return result
