# app/agents/business_agent.py
"""
Unified Business Agent v5.2.5 — TYPE TAXONOMY + HOURS-AWARE FILTERING.

v5.2.5 NEW:
  - BUSINESS_TYPE taxonomy (8 types: saas, ecommerce, services, food_beverage,
    retail, creative, passive_income, manufacturing)
  - Hours-aware type filtering (0-5h → ONLY passive_income)
  - "type" field included in return dict (was MISSING — frontend showed "?")
  - LLM prompt has explicit type guidance per hours bucket
  - Truck driver (0-5h) will get vending/storage/ATM, NOT fitness/SaaS

v5.2.3 RETAINED:
  - Unit economics Y3 cap (max 3x Y1 — prevent LLM hallucination)

v5.2.1 RETAINED:
  - Catastrophic Y1 loss check (>10% capital → not_profitable)
  - Marginal threshold 3.5% (clears CA inflation)

v5.2 RETAINED:
  - expected_return DERIVED from Y3 projections
  - Status determined from PROJECTIONS (hybrid)
  - TRANSPARENT calculation breakdown
"""

from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import (
    parse_llm_json, clamp, safe_list, safe_str, safe_dict, call_llm_with_retry
)
from app.core.california_config import REGION_DATA
from app.engines.inflation_engine import real_return, AgentType
from app.rag.retriever import retrieve


# ─────────────────────────────────
# 📚 RAG CONTEXT BUILDER
# ─────────────────────────────────
def _build_rag_context(user) -> tuple[str, list]:
    region = user.location.region.value
    profession = user.professional.profession
    sector = user.professional.sector.value
    interests = ", ".join(user.professional.interests) if user.professional.interests else ""

    primary_query = f"California {region} {sector} {profession} business {interests}"
    secondary_query = f"California {sector} business tax LLC franchise"

    business_chunks = retrieve(primary_query, top_k=2, category_filter="business")
    tax_chunks = retrieve(secondary_query, top_k=1, category_filter="tax")
    all_chunks = business_chunks + tax_chunks

    if not all_chunks:
        return "", []

    context_parts = ["📚 RELEVANT CALIFORNIA BUSINESS KNOWLEDGE BASE:\n"]
    for i, chunk in enumerate(all_chunks, 1):
        context_parts.append(
            f"\n═══ Knowledge {i}: {chunk['id']} "
            f"(relevance: {chunk['similarity_score'] * 100:.0f}%) ═══\n"
            f"Category: {chunk['category']} | Sources: {chunk.get('sources', 'N/A')}\n\n"
            f"{chunk['content'][:800]}\n"
        )

    return "\n".join(context_parts), [c['id'] for c in all_chunks]


# ─────────────────────────────────
# 📊 HOURS CONFIGURATION
# ─────────────────────────────────
HOURS_DESCRIPTIONS = {
    "0-5": "Less than 5h/week (PASSIVE — needs automation)",
    "5-15": "5-15h/week (LIGHT — weekend/evening side hustle)",
    "15-30": "15-30h/week (MODERATE — serious side business)",
    "30+": "30+h/week (HEAVY — full operation)"
}

HOURS_RETURN_CAP = {
    "0-5": {"max": 0.07, "label": "passive (3-7% realistic)"},
    "5-15": {"max": 0.12, "label": "light effort (7-12% realistic)"},
    "15-30": {"max": 0.16, "label": "moderate (10-16% realistic)"},
    "30+": {"max": 0.20, "label": "full commitment (15-20% realistic)"},
}

HORIZON_RETURN_MODIFIER = {
    "1-3": 1.20, "3-5": 1.10, "5-8": 1.00, "8+": 0.85,
}


# ─────────────────────────────────
# ⭐ v5.2.5 — BUSINESS TYPE TAXONOMY
# ─────────────────────────────────
BUSINESS_TYPE_DEFAULTS = {
    "saas": {
        "label": "SaaS / Software product",
        "min_hours": "15-30",
        "typical_gross_margin": 70,
        "default_unit_name": "monthly subscription",
        "default_price": 30,
    },
    "ecommerce": {
        "label": "E-commerce / Dropshipping",
        "min_hours": "5-15",
        "typical_gross_margin": 35,
        "default_unit_name": "order",
        "default_price": 45,
    },
    "services": {
        "label": "Consulting / Agency / Services",
        "min_hours": "15-30",
        "typical_gross_margin": 50,
        "default_unit_name": "client engagement",
        "default_price": 2000,
    },
    "food_beverage": {
        "label": "Restaurant / Café / Food truck",
        "min_hours": "30+",
        "typical_gross_margin": 30,
        "default_unit_name": "meal",
        "default_price": 15,
    },
    "retail": {
        "label": "Retail / Brick-and-mortar store",
        "min_hours": "30+",
        "typical_gross_margin": 40,
        "default_unit_name": "sale",
        "default_price": 50,
    },
    "creative": {
        "label": "Content / Courses / Creator economy",
        "min_hours": "5-15",
        "typical_gross_margin": 60,
        "default_unit_name": "subscriber",
        "default_price": 15,
    },
    "passive_income": {
        "label": "Vending / Storage / ATM / Laundromat",
        "min_hours": "0-5",
        "typical_gross_margin": 60,
        "default_unit_name": "machine/unit",
        "default_price": 200,
    },
    "manufacturing": {
        "label": "Manufacturing / Wholesale",
        "min_hours": "30+",
        "typical_gross_margin": 25,
        "default_unit_name": "unit sold",
        "default_price": 100,
    },
}

HOURS_RANK = {"0-5": 0, "5-15": 1, "15-30": 2, "30+": 3}


def _get_acceptable_types_for_hours(hours_value: str) -> list:
    """⭐ v5.2.5: Filter business types by available hours."""
    user_rank = HOURS_RANK.get(hours_value, 2)
    acceptable = []
    for type_key, defaults in BUSINESS_TYPE_DEFAULTS.items():
        min_rank = HOURS_RANK.get(defaults["min_hours"], 0)
        if user_rank >= min_rank:
            acceptable.append(type_key)
    return acceptable


def _fallback_type_for_hours(hours_value: str) -> str:
    """⭐ v5.2.5: Default type if LLM gives invalid choice."""
    if hours_value == "0-5":
        return "passive_income"
    elif hours_value == "5-15":
        return "ecommerce"
    elif hours_value == "15-30":
        return "services"
    else:  # 30+
        return "services"


def _calculate_max_return(user) -> float:
    if user is None:
        return 0.15
    hours_value = user.professional.weekly_hours.value
    horizon_value = user.preferences.horizon.value
    base_max = HOURS_RETURN_CAP.get(hours_value, {"max": 0.10})["max"]
    modifier = HORIZON_RETURN_MODIFIER.get(horizon_value, 1.0)
    return min(base_max * modifier, 0.25)


def _detect_mode(config: dict) -> str:
    loan_amount = config.get("loan_amount", 0)
    savings_to_use = config.get("savings_to_use", 0)
    if loan_amount > 0 and savings_to_use > 0:
        return "mixed"
    elif loan_amount > 0:
        return "loan"
    else:
        return "cash"


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


# ─────────────────────────────────
# 🎯 v5.2.5 PROMPT BUILDER (hours-aware types)
# ─────────────────────────────────
def build_prompt(user, config: dict, rag_context: str = "") -> str:
    loan_amount = config.get("loan_amount", 0)
    loan_years = config.get("loan_years", 7)
    savings_to_use = config.get("savings_to_use", 0)
    interest_rate = config.get("interest_rate", 0)

    total_capital = loan_amount + savings_to_use
    mode = _detect_mode(config)
    loan_payment = _calculate_loan_payment(loan_amount, interest_rate, loan_years)
    annual_loan_payment = loan_payment['annual_payment']

    region = user.location.region
    region_data = REGION_DATA[region]
    primary_industries = ", ".join(region_data["primary_industries"])

    interests_text = ", ".join(user.professional.interests) if user.professional.interests else "Not specified"
    experience_text = user.professional.prior_experience or "No prior business experience"

    hours_value = user.professional.weekly_hours.value
    hours_desc = HOURS_DESCRIPTIONS.get(hours_value, "Unknown availability")

    max_return = _calculate_max_return(user)
    return_label = HOURS_RETURN_CAP.get(hours_value, {"label": "moderate"})["label"]
    base_return_pct = round(max_return * 100, 1)

    # ⭐ v5.2.5: Type filtering by hours
    acceptable_types = _get_acceptable_types_for_hours(hours_value)
    types_block = "\n".join([
        f"  - \"{t}\": {BUSINESS_TYPE_DEFAULTS[t]['label']} "
        f"(unit: {BUSINESS_TYPE_DEFAULTS[t]['default_unit_name']}, "
        f"margin: {BUSINESS_TYPE_DEFAULTS[t]['typical_gross_margin']}%)"
        for t in acceptable_types
    ])
    default_type = _fallback_type_for_hours(hours_value)

    if hours_value == "0-5":
        type_constraint = f"""
═══════════════════════════════════════════════════════════════
⚠️ HOURS CONSTRAINT — 0-5h/week = TRULY PASSIVE ONLY:
═══════════════════════════════════════════════════════════════
User has NO TIME for active management. ONLY "passive_income" type acceptable.

⛔ DO NOT recommend:
   - SaaS (needs development + customer support)
   - E-commerce (needs marketing + fulfillment oversight)
   - Services/consulting (requires personal time per client)
   - Restaurants, food trucks, retail (active daily ops)
   - Real Estate Investment Platforms (needs technical work)
   - HealthTech / FitTech subscription services (needs ops)

✅ ONLY ACCEPTABLE — set "type": "passive_income"

✅ EXAMPLES of passive_income concepts:
   - Vending machine routes (5-10 machines, refill weekly)
   - Self-storage units (online booking, periodic inspections)
   - ATM placement deals (drop machines at retailers, fee per transaction)
   - Laundromat (coin-operated, weekly inspection)
   - Self-service car wash facility
   - Digital products (pre-made online courses, ebooks — passive after launch)
   - Domain portfolio / DNS leasing
═══════════════════════════════════════════════════════════════
"""
    else:
        type_constraint = f"""
═══════════════════════════════════════════════════════════════
✅ ACCEPTABLE BUSINESS TYPES for {hours_value}h/week ({hours_desc}):
═══════════════════════════════════════════════════════════════
{types_block}

⚠️ Pick ONE type that genuinely fits user's hours and skills.
═══════════════════════════════════════════════════════════════
"""

    if mode == "cash":
        capital_section = f"""💰 FUNDING MODE: CASH-ONLY
- Savings: ${round(savings_to_use, 2):,}
- Total capital: ${round(total_capital, 2):,}"""
        title_marker = "[Cash-Only]"
    elif mode == "loan":
        capital_section = f"""🏦 FUNDING MODE: LOAN-FUNDED
- Loan: ${round(loan_amount, 2):,} @ {interest_rate * 100:.2f}% × {loan_years}yr
- ANNUAL LOAN PAYMENT: ${annual_loan_payment:,.2f}
- Total capital: ${round(total_capital, 2):,}"""
        title_marker = "[Loan-Funded]"
    else:
        capital_section = f"""⚖️ FUNDING MODE: MIXED
- Loan: ${round(loan_amount, 2):,} @ {interest_rate * 100:.2f}% × {loan_years}yr
- Savings: ${round(savings_to_use, 2):,}
- Total capital: ${round(total_capital, 2):,}
- ANNUAL LOAN PAYMENT: ${annual_loan_payment:,.2f}"""
        title_marker = "[Mixed]"

    return f"""
You are a senior California business strategist and CFO-level financial planner.

⚠️ MATHEMATICAL CONSISTENCY MANDATORY. Numbers will be auto-verified.

USER PROFILE:
- Age: {user.personal.age} | Region: {region_data['display_name']} | City: {user.location.city}
- Profession: {user.professional.profession} | Sector: {user.professional.sector.value}
- Interests: {interests_text} | Prior: {experience_text}
- Weekly hours: {hours_desc}
- Income: ${user.financial.income:,}/mo | Savings: ${user.financial.savings:,}

{capital_section}

PREFERENCES: {user.preferences.risk_profile.value} risk, {user.preferences.horizon.value} yr horizon

{rag_context}

🌴 CALIFORNIA: LLC tax $800/yr, state tax up to 13.3%
{region_data['display_name']}: COL {region_data['cost_of_living_index']}x, industries: {primary_industries}

🚨 EXPECTED RETURN CAP: {max_return:.2f} ({return_label})

🚨 CRITICAL — Y1 CASH FLOW MUST BE REALISTIC:
For {hours_desc}, the loan payment of ${annual_loan_payment:,.0f}/yr is a FIXED COST.
Year 1 revenue must be sufficient to cover at least 60% of loan payment + operating costs.
DO NOT generate ideas where Y1 cash flow is < -10% of total capital (${total_capital * 0.10:,.0f}).
If business cannot generate enough revenue in Y1 to keep loss within 10% of capital, RECOMMEND SMALLER CAPITAL.

{type_constraint}

═══════════════════════════════════════════════════════════════
🔢 MATH RULES (v5.2)
═══════════════════════════════════════════════════════════════

1. Allocation sum = ${round(total_capital, 0):,.0f}
2. Revenue: if recurring → price × units × 12, else price × units
3. Base scenario ≈ {base_return_pct}% (matches expected_return)
4. Best > Base > Worst (best +5pp, worst -5 to -10pp)
5. Break-even units × price = monthly revenue needed
6. Market growth ≥ 0.5%
7. Y3 units MAX 3x Y1 units (realistic SaaS growth ≈ 44%/yr)

═══════════════════════════════════════════════════════════════
📝 OUTPUT FORMAT (STRICT JSON, no markdown):
═══════════════════════════════════════════════════════════════

{{
  "agent": "business",
  "title": "{title_marker} ...",
  "type": "{default_type}",
  "description": "3-4 sentences. {region_data['display_name']}-specific.",
  "allocation": {{
    "initial_investment": 0, "working_capital": 0, "marketing_budget": 0,
    "legal_and_setup": 0, "reserve": 0
  }},
  "expected_return": {max_return:.2f},
  "risk": 0.5,
  "stability": 0.7,
  "market_context": {{
    "industry_growth_rate_pct": 5.0,
    "key_competitors": ["...", "...", "..."],
    "market_size_local_usd": 50000000,
    "demand_indicator": "..."
  }},
  "unit_economics": {{
    "revenue_model": "Monthly subscription OR Per-event",
    "price_per_unit_usd": 0,
    "unit_name": "...",
    "is_recurring": true,
    "target_units_year_1": 0,
    "target_units_year_3": 0,
    "gross_margin_pct": 50,
    "customer_acquisition_cost_usd": 0
  }},
  "projections": {{
    "year_1": {{"revenue": 0, "operating_costs": 0, "loan_payment": {annual_loan_payment:.0f}, "net_cash_flow": 0}},
    "year_3": {{"revenue": 0, "operating_costs": 0, "loan_payment": {annual_loan_payment:.0f}, "net_cash_flow": 0}},
    "year_5": {{"revenue": 0, "operating_costs": 0, "loan_payment": {annual_loan_payment:.0f}, "net_cash_flow": 0}}
  }},
  "scenarios": {{
    "best_case": {{"annual_return_pct": {round(base_return_pct + 6)}, "narrative": "..."}},
    "base_case": {{"annual_return_pct": {base_return_pct}, "narrative": "..."}},
    "worst_case": {{"annual_return_pct": {round(base_return_pct - 8)}, "narrative": "..."}}
  }},
  "break_even": {{"months_to_breakeven": 14, "monthly_revenue_needed_usd": 0, "units_per_month_needed": 0}},
  "pros": ["...", "...", "..."],
  "cons": ["...", "..."],
  "next_steps": ["...", "...", "..."],
  "time_to_profit": "..."
}}
"""


# ─────────────────────────────────
# 🤖 LLM CALL
# ─────────────────────────────────
async def generate_business_idea_llm(user, config: dict) -> tuple[dict, list]:
    rag_context, rag_chunk_ids = _build_rag_context(user)
    prompt = build_prompt(user, config, rag_context=rag_context)
    mode = _detect_mode(config)
    agent_name = f"business_{mode}"
    response = await call_llm_with_retry(
        llm_call=lambda: call_llm(prompt),
        agent_name=agent_name
    )
    return response, rag_chunk_ids


# ─────────────────────────────────
# ✅ v5.1 VALIDATORS (retained)
# ─────────────────────────────────
def _rescale_allocation_to_capital(allocation: dict, target_total: float) -> dict:
    if target_total <= 0:
        return allocation
    keys = ["initial_investment", "working_capital", "marketing_budget", "legal_and_setup", "reserve"]
    for k in keys:
        if k not in allocation:
            allocation[k] = 0
        try:
            allocation[k] = max(0, float(allocation[k]))
        except (TypeError, ValueError):
            allocation[k] = 0
    current_sum = sum(allocation[k] for k in keys)
    if current_sum == 0:
        allocation["initial_investment"] = round(target_total * 0.40, 2)
        allocation["working_capital"] = round(target_total * 0.25, 2)
        allocation["marketing_budget"] = round(target_total * 0.15, 2)
        allocation["legal_and_setup"] = round(target_total * 0.05, 2)
        allocation["reserve"] = round(target_total * 0.15, 2)
        return allocation
    ratio = target_total / current_sum
    for k in keys:
        allocation[k] = round(allocation[k] * ratio, 2)
    new_sum = sum(allocation[k] for k in keys)
    allocation["reserve"] = round(allocation["reserve"] + (target_total - new_sum), 2)
    return allocation


def _validate_market_context(data: dict) -> dict:
    mc = data.get("market_context") or {}
    growth = clamp(mc.get("industry_growth_rate_pct"), -20, 50, 5)
    if growth < 0.5:
        growth = max(growth, 0.5)
    return {
        "industry_growth_rate_pct": round(growth, 1),
        "key_competitors": safe_list(mc.get("key_competitors"), ["Local competitor 1"])[:5],
        "market_size_local_usd": int(clamp(mc.get("market_size_local_usd"), 0, 10_000_000_000, 0)),
        "demand_indicator": safe_str(mc.get("demand_indicator"), "Market demand assessment unavailable")[:200],
    }


def _validate_unit_economics(data: dict) -> dict:
    """
    ⭐ v5.2.3 FIX #2:
    Validates unit economics AND caps Y3/Y5 targets to realistic growth.
    """
    ue = data.get("unit_economics") or {}
    revenue_model = safe_str(ue.get("revenue_model"), "Direct service/product sales")[:150]
    is_recurring = ue.get("is_recurring")
    if is_recurring is None:
        rm_lower = revenue_model.lower()
        is_recurring = any(kw in rm_lower for kw in [
            "subscription", "monthly", "recurring", "saas", "membership",
            "subscriber", "per month", "per-month"
        ])

    target_y1 = int(clamp(ue.get("target_units_year_1"), 0, 1_000_000, 0))
    target_y3 = int(clamp(ue.get("target_units_year_3"), 0, 5_000_000, 0))

    # ⭐ v5.2.3: Cap Y3 to 3x Y1 (realistic growth)
    if target_y1 > 0 and target_y3 > target_y1 * 3:
        target_y3 = target_y1 * 3

    return {
        "revenue_model": revenue_model,
        "price_per_unit_usd": round(clamp(ue.get("price_per_unit_usd"), 0, 1_000_000, 0), 2),
        "unit_name": safe_str(ue.get("unit_name"), "unit")[:50],
        "is_recurring": bool(is_recurring),
        "target_units_year_1": target_y1,
        "target_units_year_3": target_y3,
        "gross_margin_pct": round(clamp(ue.get("gross_margin_pct"), 0, 100, 50), 1),
        "customer_acquisition_cost_usd": round(clamp(ue.get("customer_acquisition_cost_usd"), 0, 100_000, 0), 2),
    }


def _recompute_projections(data: dict, unit_econ: dict, loan_payment_annual: float) -> dict:
    proj = data.get("projections") or {}
    price = unit_econ["price_per_unit_usd"]
    units_y1 = unit_econ["target_units_year_1"]
    units_y3 = unit_econ["target_units_year_3"]
    margin = unit_econ["gross_margin_pct"] / 100.0
    is_recurring = unit_econ["is_recurring"]
    period_mult = 12 if is_recurring else 1

    if units_y3 > units_y1 and units_y1 > 0:
        growth_rate = (units_y3 / units_y1) ** (1/2) - 1
        units_y5 = int(units_y3 * ((1 + growth_rate * 0.5) ** 2))
    else:
        units_y5 = int(units_y3 * 1.5)

    rev_y1 = round(price * units_y1 * period_mult, 2)
    rev_y3 = round(price * units_y3 * period_mult, 2)
    rev_y5 = round(price * units_y5 * period_mult, 2)

    def _build_year(llm_year: dict, computed_revenue: float) -> dict:
        llm_op_costs = clamp(llm_year.get("operating_costs"), 0, computed_revenue * 1.5, 0)
        if computed_revenue > 0:
            op_ratio = llm_op_costs / computed_revenue
            op_costs = round(llm_op_costs, 2) if 0.3 <= op_ratio <= 0.9 else round(computed_revenue * (1 - margin), 2)
        else:
            op_costs = 0
        net = round(computed_revenue - op_costs - loan_payment_annual, 2)
        return {
            "revenue": computed_revenue,
            "operating_costs": op_costs,
            "loan_payment": round(loan_payment_annual, 2),
            "net_cash_flow": net,
        }

    return {
        "year_1": _build_year(proj.get("year_1") or {}, rev_y1),
        "year_3": _build_year(proj.get("year_3") or {}, rev_y3),
        "year_5": _build_year(proj.get("year_5") or {}, rev_y5),
    }


def _validate_scenarios(data: dict, base_return: float) -> dict:
    sc = data.get("scenarios") or {}
    base_pct = round(base_return * 100, 1)

    def _v(key, default_pct, narrative_default):
        item = sc.get(key) or {}
        return {
            "annual_return_pct": round(clamp(item.get("annual_return_pct"), -50, 50, default_pct), 1),
            "narrative": safe_str(item.get("narrative"), narrative_default)[:300],
        }

    best = _v("best_case", base_pct + 6, "Strong execution + favorable market conditions")
    base = _v("base_case", base_pct, "Realistic outcome assuming normal execution")
    worst = _v("worst_case", base_pct - 8, "Slow customer acquisition or market downturn")

    if abs(base["annual_return_pct"] - base_pct) > 2:
        base["annual_return_pct"] = base_pct
    if best["annual_return_pct"] <= base["annual_return_pct"] + 2:
        best["annual_return_pct"] = round(base["annual_return_pct"] + 6, 1)
    if worst["annual_return_pct"] >= base["annual_return_pct"] - 3:
        worst["annual_return_pct"] = round(base["annual_return_pct"] - 8, 1)

    return {"best_case": best, "base_case": base, "worst_case": worst}


def _validate_break_even(data: dict, unit_econ: dict) -> dict:
    be = data.get("break_even") or {}
    months = int(clamp(be.get("months_to_breakeven"), 1, 60, 12))
    price = unit_econ["price_per_unit_usd"]
    is_recurring = unit_econ["is_recurring"]
    llm_units = clamp(be.get("units_per_month_needed"), 0, 100_000, 0)
    llm_revenue = clamp(be.get("monthly_revenue_needed_usd"), 0, 10_000_000, 0)

    if price > 0:
        if llm_units > 0:
            return {
                "months_to_breakeven": months,
                "monthly_revenue_needed_usd": round(llm_units * price, 2),
                "units_per_month_needed": round(llm_units, 1),
            }
        elif llm_revenue > 0:
            return {
                "months_to_breakeven": months,
                "monthly_revenue_needed_usd": round(llm_revenue, 2),
                "units_per_month_needed": round(llm_revenue / price, 1),
            }

    units_y1 = unit_econ["target_units_year_1"]
    if units_y1 > 0 and is_recurring:
        units_per_month = round(units_y1 * 0.6, 1)
    elif units_y1 > 0:
        units_per_month = round(units_y1 * 0.6 / 12, 1)
    else:
        units_per_month = 0
    monthly_rev = round(units_per_month * price, 2) if price > 0 else 0
    return {
        "months_to_breakeven": months,
        "monthly_revenue_needed_usd": monthly_rev,
        "units_per_month_needed": units_per_month,
    }


# ─────────────────────────────────
# ⭐ v5.2 — DERIVED EXPECTED RETURN
# ─────────────────────────────────
def _derive_expected_return_from_projections(
    projections: dict,
    total_capital: float,
    max_return: float,
) -> float:
    if total_capital <= 0:
        return 0.0
    y3_net = projections.get("year_3", {}).get("net_cash_flow", 0)
    raw_roi = y3_net / total_capital
    return round(max(0, min(raw_roi, max_return)), 4)


# ─────────────────────────────────
# ⭐ v5.2.1 — STRICT STATUS LOGIC
# ─────────────────────────────────
def _determine_status_from_projections(
    projections: dict,
    total_capital: float,
) -> str:
    """
    Strict status logic — v5.2.1:
      - NOT_PROFITABLE if Y1 loss > 10% of capital (catastrophic loss)
      - PROFITABLE    if Y1 cash flow > 0 AND Y3 ROI > 5%
      - MARGINAL      if Y1 cash flow > 0 OR Y3 ROI > 3.5% (clears inflation)
      - NOT_PROFITABLE otherwise
    """
    if total_capital <= 0:
        return "not_profitable"

    y1_net = projections.get("year_1", {}).get("net_cash_flow", 0)
    y3_net = projections.get("year_3", {}).get("net_cash_flow", 0)
    y3_roi = y3_net / total_capital

    # v5.2.1: Catastrophic Y1 loss → automatic NOT_PROFITABLE
    if y1_net < 0:
        y1_loss_pct = abs(y1_net) / total_capital
        if y1_loss_pct > 0.10:
            return "not_profitable"

    if y1_net > 0 and y3_roi > 0.05:
        return "profitable"
    elif y1_net > 0 or y3_roi > 0.035:
        return "marginal"
    else:
        return "not_profitable"


# ─────────────────────────────────
# ⭐ v5.2 — TRANSPARENT CALCULATION BREAKDOWN
# ─────────────────────────────────
def _build_calculation_breakdown(
    user, config: dict, projections: dict, expected_return: float,
    annual_loan_payment: float, total_capital: float,
) -> dict:
    loan_amount = config.get("loan_amount", 0)
    savings_to_use = config.get("savings_to_use", 0)
    interest_rate = config.get("interest_rate", 0)
    loan_years = config.get("loan_years", 0)
    currency = user.financial.currency.value
    hours = user.professional.weekly_hours.value
    max_return = _calculate_max_return(user)

    y1_net = projections.get("year_1", {}).get("net_cash_flow", 0)
    y3_net = projections.get("year_3", {}).get("net_cash_flow", 0)
    raw_y3_roi = y3_net / total_capital if total_capital > 0 else 0

    try:
        agent_type = AgentType("business")
        real_roi = real_return(nominal_return=expected_return, agent=agent_type, currency=currency)
        inflation_pct = round((expected_return - real_roi) * 100, 2)
    except Exception:
        real_roi = expected_return * 0.65
        inflation_pct = round(expected_return * 35, 2)

    gross_return_dollars = total_capital * real_roi
    net_return_dollars = gross_return_dollars - annual_loan_payment
    net_return_pct = (net_return_dollars / total_capital * 100) if total_capital > 0 else 0

    steps = [
        {
            "step": 1,
            "title": "Your Capital",
            "explanation": "The total money you're committing to this strategy (loan + savings).",
            "formula": f"${loan_amount:,.0f} (loan) + ${savings_to_use:,.0f} (savings)",
            "result": f"${total_capital:,.0f}",
            "value_usd": round(total_capital, 2),
        },
        {
            "step": 2,
            "title": "Projected Annual ROI (from business projections)",
            "explanation": (
                f"We calculated your expected return by looking at Year 3 net cash flow "
                f"(${y3_net:,.0f}) divided by your capital."
            ),
            "formula": f"${y3_net:,.0f} ÷ ${total_capital:,.0f} = {raw_y3_roi * 100:.1f}% raw ROI",
            "result": (
                f"{expected_return * 100:.1f}% (capped at {max_return * 100:.0f}% for {hours}h/week)"
                if raw_y3_roi > max_return
                else f"{expected_return * 100:.1f}%"
            ),
            "value_pct": round(expected_return * 100, 2),
            "note": (
                f"Raw ROI of {raw_y3_roi * 100:.0f}% was capped at {max_return * 100:.0f}% "
                f"because you have {hours} hours/week available."
                if raw_y3_roi > max_return
                else None
            ),
        },
        {
            "step": 3,
            "title": "Inflation Adjustment (California)",
            "explanation": (
                "Money loses value over time due to inflation. California inflation is typically "
                f"~{inflation_pct:.1f}%/year."
            ),
            "formula": (
                f"{expected_return * 100:.1f}% nominal - {inflation_pct:.1f}% inflation = "
                f"{real_roi * 100:.2f}% real return"
            ),
            "result": f"{real_roi * 100:.2f}% real annual return",
            "value_pct": round(real_roi * 100, 2),
        },
        {
            "step": 4,
            "title": "Gross Annual Return (in dollars)",
            "explanation": "How much your capital generates per year.",
            "formula": f"${total_capital:,.0f} × {real_roi * 100:.2f}% = ${gross_return_dollars:,.0f}",
            "result": f"${gross_return_dollars:,.0f}/year",
            "value_usd": round(gross_return_dollars, 2),
        },
    ]

    if annual_loan_payment > 0:
        monthly_pmt = annual_loan_payment / 12
        steps.append({
            "step": 5,
            "title": "Annual Loan Payment",
            "explanation": (
                f"You took out a ${loan_amount:,.0f} loan at {interest_rate * 100:.2f}% over "
                f"{loan_years} years."
            ),
            "formula": f"${monthly_pmt:,.2f}/month × 12 months = ${annual_loan_payment:,.0f}/year",
            "result": f"-${annual_loan_payment:,.0f}/year",
            "value_usd": round(-annual_loan_payment, 2),
        })
        steps.append({
            "step": 6,
            "title": "Net Annual Return (Final)",
            "explanation": "What's left after paying for inflation losses and your loan.",
            "formula": f"${gross_return_dollars:,.0f} - ${annual_loan_payment:,.0f} = ${net_return_dollars:,.0f}",
            "result": f"${net_return_dollars:,.0f}/year ({net_return_pct:+.2f}% net)",
            "value_usd": round(net_return_dollars, 2),
            "value_pct": round(net_return_pct, 2),
        })
    else:
        steps.append({
            "step": 5,
            "title": "Net Annual Return (No Loan)",
            "explanation": "Since you're using only savings, gross return = net return.",
            "formula": f"${gross_return_dollars:,.0f} (no loan to repay)",
            "result": f"${gross_return_dollars:,.0f}/year ({real_roi * 100:+.2f}% net)",
            "value_usd": round(gross_return_dollars, 2),
            "value_pct": round(real_roi * 100, 2),
        })

    # Conclusion
    conclusion = ""
    if y1_net > 0 and net_return_dollars < 0:
        conclusion = (
            f"📊 Two views of this business:\n\n"
            f"1️⃣ As a BUSINESS: It generates ${y1_net:,.0f}/year cash flow in Year 1 — "
            f"that's positive, the business is healthy.\n\n"
            f"2️⃣ As an INVESTMENT: After inflation and loan amortization, you lose "
            f"${abs(net_return_dollars):,.0f}/year ({net_return_pct:+.2f}%) on your "
            f"${total_capital:,.0f} capital.\n\n"
            f"💡 To improve: Reduce the loan amount or wait until you have more savings."
        )
    elif y1_net < 0 and abs(y1_net) / total_capital > 0.10:
        y1_loss_pct = abs(y1_net) / total_capital * 100
        conclusion = (
            f"⚠️ This business loses ${abs(y1_net):,.0f} in Year 1 — that's "
            f"{y1_loss_pct:.1f}% of your capital.\n\n"
            f"This is UNSUSTAINABLE for a side hustle. You'd need to cover this loss from "
            f"your salary or other savings.\n\n"
            f"💡 Recommendations:\n"
            f"• Reduce loan amount (lower interest cost)\n"
            f"• Choose smaller-scale business (less capital required)\n"
            f"• Or wait until you can commit more weekly hours to grow revenue faster"
        )
    elif net_return_dollars > 0:
        conclusion = (
            f"✅ This strategy is genuinely profitable. After inflation and loan payments, "
            f"you generate ${net_return_dollars:,.0f}/year in real purchasing power "
            f"({net_return_pct:+.2f}% return on capital)."
        )
    else:
        conclusion = (
            f"⚠️ This strategy loses ${abs(net_return_dollars):,.0f}/year after inflation and "
            f"loan amortization. Consider reducing loan or increasing savings before proceeding."
        )

    return {
        "steps": steps,
        "summary": {
            "total_capital": round(total_capital, 2),
            "nominal_return_pct": round(expected_return * 100, 2),
            "real_return_pct": round(real_roi * 100, 2),
            "inflation_pct": round(inflation_pct, 2),
            "gross_return_dollars": round(gross_return_dollars, 2),
            "annual_loan_payment": round(annual_loan_payment, 2),
            "net_return_dollars": round(net_return_dollars, 2),
            "net_return_pct": round(net_return_pct, 2),
        },
        "conclusion": conclusion,
    }


# ─────────────────────────────────
# ✅ v5.2.5 MAIN VALIDATOR
# ─────────────────────────────────
def validate_business_output(data: dict, user=None, config: dict = None) -> dict:
    max_return = _calculate_max_return(user)

    if config:
        mode = _detect_mode(config)
        if mode == "cash":
            default_risk, default_stability = 0.4, 0.7
        elif mode == "loan":
            default_risk, default_stability = 0.55, 0.55
        else:
            default_risk, default_stability = 0.5, 0.6
        loan_payment_annual = _calculate_loan_payment(
            config.get("loan_amount", 0),
            config.get("interest_rate", 0),
            config.get("loan_years", 0)
        )["annual_payment"]
        total_capital = config.get("loan_amount", 0) + config.get("savings_to_use", 0)
    else:
        default_risk, default_stability = 0.5, 0.5
        loan_payment_annual = 0
        total_capital = 0

    title = safe_str(data.get("title"), "Business opportunity")
    if config:
        mode = _detect_mode(config)
        marker = {"cash": "[Cash-Only]", "loan": "[Loan-Funded]", "mixed": "[Mixed]"}[mode]
        if not (title.startswith("[Cash") or title.startswith("[Loan") or title.startswith("[Mixed")):
            title = f"{marker} {title}"

    # ⭐ v5.2.5 NEW: Validate business type with hours-aware fallback
    valid_types = set(BUSINESS_TYPE_DEFAULTS.keys())
    type_value = safe_str(data.get("type"), "services").lower()
    if type_value not in valid_types:
        type_value = "services"

    # Hours-aware re-validation: force fallback if user can't handle this type
    if user:
        try:
            hours_value = user.professional.weekly_hours.value
            acceptable = _get_acceptable_types_for_hours(hours_value)
            if type_value not in acceptable:
                type_value = _fallback_type_for_hours(hours_value)
        except (AttributeError, KeyError):
            pass

    unit_econ = _validate_unit_economics(data)
    rescaled_alloc = _rescale_allocation_to_capital(data.get("allocation") or {}, total_capital)
    projections = _recompute_projections(data, unit_econ, loan_payment_annual)

    derived_return = _derive_expected_return_from_projections(
        projections, total_capital, max_return
    )

    derived_status = _determine_status_from_projections(projections, total_capital)

    scenarios = _validate_scenarios(data, derived_return)
    break_even = _validate_break_even(data, unit_econ)
    market_context = _validate_market_context(data)

    calc_breakdown = _build_calculation_breakdown(
        user, config, projections, derived_return, loan_payment_annual, total_capital
    )

    return {
        "agent": "business",
        "title": title,
        "type": type_value,  # ⭐ v5.2.5 NEW
        "description": safe_str(
            data.get("description"),
            "A business venture leveraging user's skills and available capital."
        ),
        "allocation": rescaled_alloc,
        "expected_return": derived_return,
        "risk": round(clamp(data.get("risk"), 0, 1, default_risk), 4),
        "stability": round(clamp(data.get("stability"), 0, 1, default_stability), 4),
        "market_context": market_context,
        "unit_economics": unit_econ,
        "projections": projections,
        "scenarios": scenarios,
        "break_even": break_even,
        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), []),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "6-12 months"),
        "calculation_breakdown": calc_breakdown,
        "derived_status_override": derived_status,
    }


# ─────────────────────────────────
# 🚀 MAIN AGENT FUNCTION
# ─────────────────────────────────
async def run_business_agent(user, config: dict) -> dict:
    if config is None:
        config = {
            "loan_amount": 0, "loan_years": 0,
            "savings_to_use": user.financial.savings, "interest_rate": 0,
        }

    raw, rag_chunk_ids = await generate_business_idea_llm(user, config)
    result = validate_business_output(raw, user=user, config=config)
    result["rag_sources"] = rag_chunk_ids

    result["funding_mode"] = _detect_mode(config)
    result["loan_amount"] = config.get("loan_amount", 0)
    result["loan_years"] = config.get("loan_years", 0)
    result["savings_used"] = config.get("savings_to_use", 0)
    result["interest_rate"] = config.get("interest_rate", 0)
    result["total_capital"] = config.get("loan_amount", 0) + config.get("savings_to_use", 0)

    return result