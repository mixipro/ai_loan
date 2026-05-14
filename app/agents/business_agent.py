# app/agents/business_agent.py

from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import parse_llm_json, clamp, safe_list, safe_str, safe_dict, call_llm_with_retry
from app.core.california_config import REGION_DATA
from app.rag.retriever import retrieve  # ⭐ RAG retriever


# ─────────────────────────────────
# 📚 RAG CONTEXT BUILDER
# ─────────────────────────────────
def _build_rag_context(user, business_loan: dict) -> tuple[str, list]:
    """
    Retrieves California-specific business knowledge based on user profile.

    Returns:
        (formatted_context_text, list_of_chunk_ids)
    """
    region = user.location.region.value
    profession = user.professional.profession.value
    sector = user.professional.sector.value
    interests = ", ".join(user.professional.interests) if user.professional.interests else ""

    # Build semantic query combining region + profession + interests
    primary_query = f"California {region} {sector} {profession} business {interests}"
    secondary_query = f"California {sector} business tax LLC franchise"

    # Retrieve from business + tax categories
    business_chunks = retrieve(primary_query, top_k=2, category_filter="business")
    tax_chunks = retrieve(secondary_query, top_k=1, category_filter="tax")

    all_chunks = business_chunks + tax_chunks

    if not all_chunks:
        return "", []

    # Build LLM-ready context
    context_parts = ["📚 RELEVANT CALIFORNIA BUSINESS KNOWLEDGE BASE:\n"]
    for i, chunk in enumerate(all_chunks, 1):
        context_parts.append(
            f"\n═══ Knowledge {i}: {chunk['id']} "
            f"(relevance: {chunk['similarity_score'] * 100:.0f}%) ═══\n"
            f"Category: {chunk['category']} | Sources: {chunk.get('sources', 'N/A')}\n\n"
            f"{chunk['content'][:800]}\n"  # Truncate long chunks
        )

    context_text = "\n".join(context_parts)
    chunk_ids = [c['id'] for c in all_chunks]

    return context_text, chunk_ids

# ─────────────────────────────────
# 📊 WEEKLY HOURS CONFIGURATION
# ─────────────────────────────────
HOURS_DESCRIPTIONS = {
    "0-5": "Less than 5h/week (PASSIVE — needs automation, hands-off operation)",
    "5-15": "5-15h/week (LIGHT — weekend/evening side hustle, productized service)",
    "15-30": "15-30h/week (MODERATE — serious side business, can take some calls)",
    "30+": "30+h/week (HEAVY — can run full operation, scaling business)"
}

# ⭐ BUG #3 FIX: Realistic returns for serious commitment
# Previous caps were too conservative (Founder at 15% couldn't beat cash 13%)
# New caps reflect real CA market: serious businesses CAN target higher returns
HOURS_RETURN_CAP = {
    "0-5": {"max": 0.07, "label": "passive (3-7% realistic)"},
    "5-15": {"max": 0.12, "label": "light effort (7-12% realistic)"},  # ⭐ was 0.10
    "15-30": {"max": 0.16, "label": "moderate (10-16% realistic)"},  # ⭐ was 0.13
    "30+": {"max": 0.20, "label": "full commitment (15-20% realistic)"},  # ⭐ was 0.15
}

# ⭐ BUG #3 FIX: Horizon adjustment
# Early-stage businesses (1-3yr) target higher growth (acquisition/exit)
# Mature businesses (8+yr) settle at steady-state returns
HORIZON_RETURN_MODIFIER = {
    "1-3": 1.20,  # Early stage: aim higher (e.g. 20% × 1.2 = 24% capped at 25%)
    "3-5": 1.10,  # Growth stage
    "5-8": 1.00,  # Established
    "8+": 0.85,  # Mature: lower steady state
}


def _calculate_max_return(user) -> float:
    """
    Calculates max realistic expected_return based on hours + horizon.
    Used by both prompt building and post-validation clamping.
    """
    if user is None:
        return 0.15

    hours_value = user.professional.weekly_hours.value
    horizon_value = user.preferences.horizon.value

    base_max = HOURS_RETURN_CAP.get(hours_value, {"max": 0.10})["max"]
    modifier = HORIZON_RETURN_MODIFIER.get(horizon_value, 1.0)

    # Absolute ceiling 25% (no business sustainably returns more than this)
    return min(base_max * modifier, 0.25)


# ─────────────────────────────────
# 🎯 BUILD PROMPT (with loan)
# ─────────────────────────────────
def build_prompt(user, business_loan: dict, rag_context: str = "") -> str:
    """
    Builds prompt for business agent (with business loan + RAG context).
    """
    total_capital = user.financial.savings
    if business_loan.get("approved"):
        total_capital += business_loan.get("max_loan_amount", 0)

    region = user.location.region
    region_data = REGION_DATA[region]
    primary_industries = ", ".join(region_data["primary_industries"])

    interests_text = (
        ", ".join(user.professional.interests)
        if user.professional.interests
        else "Not specified"
    )
    experience_text = user.professional.prior_experience or "No prior business experience"

    hours_value = user.professional.weekly_hours.value
    hours_desc = HOURS_DESCRIPTIONS.get(hours_value, "Unknown availability")

    # ⭐ Calculate max_return using new horizon-adjusted formula
    max_return = _calculate_max_return(user)
    hours_cap = HOURS_RETURN_CAP.get(hours_value, {"max": 0.10, "label": "moderate"})
    return_label = hours_cap["label"]

    tech_role = (
        user.professional.tech_role.value
        if user.professional.tech_role
        else "N/A"
    )
    equity = (
        user.professional.equity_compensation.value
        if user.professional.equity_compensation
        else "N/A"
    )

    loan_rate_pct = business_loan.get("interest_rate", 0) * 100
    loan_amount = business_loan.get("max_loan_amount", 0)
    loan_years = business_loan.get("loan_years", 7)
    monthly_payment = business_loan.get("monthly_payment", 0)
    total_paid = business_loan.get("total_paid", 0)
    total_interest = business_loan.get("total_interest", 0)

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
- Total available capital (savings + business loan): ${round(total_capital, 2)} USD
- Cost of living index: {region_data['cost_of_living_index']}x US average

🏦 BUSINESS LOAN CONDITIONS (specific for this strategy):
- Loan type: BUSINESS LOAN (NOT personal — terms specific to business financing)
- Approved: {business_loan.get("approved")}
- Max loan amount: ${loan_amount} USD
- Interest rate: {loan_rate_pct:.2f}% APR
- Loan term: {loan_years} years
- Monthly payment: ${monthly_payment}
- 💰 REAL COST: User pays ${total_paid} total over {loan_years} years
  (interest alone: ${total_interest})
- This means user must generate enough revenue to cover ${monthly_payment}/month JUST for loan service!

PREFERENCES:
- Risk tolerance: {user.preferences.risk_profile.value}
- Investment horizon: {user.preferences.horizon.value} years
- Primary goal: PROFIT (maximize income, build sustainable revenue)

{rag_context}

🌴 CALIFORNIA BUSINESS CONTEXT:
- LLC franchise tax: $800/year minimum (mandatory, even for $0 revenue)
- California state income tax: progressive up to 13.3% (highest in US)
- {region_data['display_name']} specifics:
  * Cost of living: {region_data['cost_of_living_index']}x national average
  * Strong industries: {primary_industries}
  * Real estate context: median home ${region_data['median_home_price']:,}
- Consider tax implications: California treats capital gains as ordinary income
- If software/SaaS in Bay Area: highest concentration of YC + VCs in world

🚨 CRITICAL EXPECTED RETURN RULES (NON-NEGOTIABLE):

The user has {hours_desc}.
Maximum REALISTIC expected_return: {max_return:.2f} ({return_label}, horizon-adjusted)

DO NOT EXCEED {max_return:.2f} expected_return under any circumstances.

Reasoning (hours-based base):
- 0-5h/week: Passive businesses (dropshipping, affiliate, simple SaaS) → 3-7%
- 5-15h/week: Side hustles in California's competitive market → 7-12%
- 15-30h/week: Serious side businesses → 10-16%
- 30+h/week: Full-time founders chasing growth → 15-20%

Horizon adjustment applied:
- 1-3 years: ×1.20 (early stage potential, can target higher with exit goal)
- 3-5 years: ×1.10 (growth stage)
- 5-8 years: ×1.00 (established business)
- 8+ years: ×0.85 (mature, steady-state)

⚠️ Be REALISTIC given:
- California's competitive market
- LLC fees + state tax (13.3%)
- Customer acquisition costs
- {loan_rate_pct:.2f}% loan eats into margins
- ${monthly_payment}/month loan payment must be covered FIRST

🚨 IF user has 0-5h/week: BUSINESS IS LIKELY NOT VIABLE.
   Propose a TRULY passive option (affiliate, course sales) at 3-7%.
   Be HONEST about time constraint.

YOUR TASK:
Propose ONE specific, realistic California-aware business idea that:
1. Matches REGION (Bay Area=tech, LA=entertainment, SD=biotech, CV=agriculture, etc.)
2. Combines PROFESSION + INTERESTS with regional opportunity
3. Fits ${round(total_capital, 2)} capital
4. RESPECTS WEEKLY HOURS (most important!)
5. Considers California costs
6. Aligns with risk ({user.preferences.risk_profile.value}) and horizon ({user.preferences.horizon.value})

REQUIRED FIELDS:
1. title — short business name/concept
2. description — 2-3 sentences, California-aware
3. allocation — capital split, must sum to ${round(total_capital, 2)}, reserve ≥ 10%
4. expected_return — annual decimal (MAX {max_return:.2f})
5. risk — 0–1
6. stability — 0–1
7. pros — 3 advantages
8. cons — 2 honest risks
9. next_steps — 3 concrete actions
10. time_to_profit — realistic timeframe

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- All monetary amounts in USD
- expected_return MUST be ≤ {max_return:.2f}
- Allocation sum ≈ ${round(total_capital, 2)} USD

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
  "expected_return": {max_return:.2f},
  "risk": 0.5,
  "stability": 0.7,
  "pros": ["...", "...", "..."],
  "cons": ["...", "..."],
  "next_steps": ["...", "...", "..."],
  "time_to_profit": "..."
}}
"""


# ─────────────────────────────────
# 🎯 BUILD PROMPT — CASH ONLY (no loan)
# ⭐ NEW: For business_cash strategy
# ─────────────────────────────────
def build_prompt_cash(user, rag_context: str = "") -> str:
    """
    Builds prompt for business agent with NO LOAN (cash-only strategy).
    """
    total_capital = user.financial.savings  # cash only

    region = user.location.region
    region_data = REGION_DATA[region]
    primary_industries = ", ".join(region_data["primary_industries"])

    interests_text = (
        ", ".join(user.professional.interests)
        if user.professional.interests
        else "Not specified"
    )
    experience_text = user.professional.prior_experience or "No prior business experience"

    hours_value = user.professional.weekly_hours.value
    hours_desc = HOURS_DESCRIPTIONS.get(hours_value, "Unknown availability")

    max_return = _calculate_max_return(user)
    hours_cap = HOURS_RETURN_CAP.get(hours_value, {"max": 0.10, "label": "moderate"})
    return_label = hours_cap["label"]

    tech_role = user.professional.tech_role.value if user.professional.tech_role else "N/A"
    equity = user.professional.equity_compensation.value if user.professional.equity_compensation else "N/A"

    return f"""
You are a senior California business strategist proposing a CASH-FUNDED business (no loan).

Your task is to propose ONE realistic California-aware business idea that uses ONLY the user's savings.

USER PROFILE:
- Age: {user.personal.age}
- Region: {region_data['display_name']} ({region.value})
- City: {user.location.city}
- Primary regional industries: {primary_industries}
- Profession: {user.professional.profession.value}
- Sector: {user.professional.sector.value}
- Tech role: {tech_role}, Equity: {equity}
- Interests: {interests_text}
- Experience: {experience_text}
- Weekly hours: {hours_desc}

💰 CASH-ONLY CAPITAL (NO LOAN):
- Available: ${user.financial.savings} USD from savings
- This is CONSERVATIVE bootstrap: no debt, no monthly loan burden, no personal guarantee
- Lower-risk approach: business failure won't leave user in debt
- Scale must fit savings — smaller startup, more bootstrap-friendly

PREFERENCES:
- Risk: {user.preferences.risk_profile.value}
- Horizon: {user.preferences.horizon.value} years

🌴 CALIFORNIA CONTEXT:
- LLC franchise tax: $800/year minimum
- State income tax up to 13.3%
- {region_data['display_name']}: COL {region_data['cost_of_living_index']}x

🚨 EXPECTED RETURN RULES:
The user has {hours_desc}.
Maximum REALISTIC expected_return: {max_return:.2f} ({return_label}, horizon-adjusted)
DO NOT EXCEED {max_return:.2f}.

⭐ CASH-ONLY ADVANTAGE: No loan payment burden means MORE of revenue goes to profit.
   This makes cash businesses MORE attractive than loan-funded for smaller scales.

YOUR TASK:
Propose ONE bootstrap-style California business idea that:
1. Fits ${user.financial.savings} USD capital (smaller scale than loan-funded)
2. Matches region + profession + interests
3. RESPECTS WEEKLY HOURS
4. Can start lean and grow organically
5. Examples: dropshipping, content business, productized service, micro-SaaS, 
   consulting, online course, niche e-commerce

REQUIRED FIELDS (return ONLY JSON):
{{
  "agent": "business_cash",
  "title": "[Cash-Only] ...",
  "description": "2-3 sentences emphasizing bootstrap approach + California angle",
  "allocation": {{
    "initial_investment": 0,
    "working_capital": 0,
    "marketing_budget": 0,
    "reserve": 0
  }},
  "expected_return": {max_return:.2f},
  "risk": 0.4,
  "stability": 0.7,
  "pros": ["No loan burden — full profit retained", "...", "..."],
  "cons": ["Limited initial scale", "..."],
  "next_steps": ["File LLC", "...", "..."],
  "time_to_profit": "..."
}}

STRICT RULES:
- Allocation must sum to ${user.financial.savings} USD
- Reserve ≥ 15% (cash-only needs bigger safety net since no loan to fall back on)
- expected_return ≤ {max_return:.2f}
- "agent" field MUST be "business_cash"
"""


# ─────────────────────────────────
# 🤖 LLM CALL (with loan)
# ─────────────────────────────────
async def generate_business_idea_llm(user, business_loan: dict) -> tuple[dict, list]:
    """
    Generates business idea using LLM with RAG context + retry logic.
    Returns: (llm_response, rag_chunk_ids)
    """
    # ⭐ Step 1: Retrieve California knowledge
    rag_context, rag_chunk_ids = _build_rag_context(user, business_loan)

    # Step 2: Build prompt with RAG context injected
    prompt = build_prompt(user, business_loan, rag_context=rag_context)

    # Step 3: LLM call
    response = await call_llm_with_retry(
        llm_call=lambda: call_llm(prompt),
        agent_name="business"
    )

    return response, rag_chunk_ids

# ─────────────────────────────────
# 🤖 LLM CALL (cash only)
# ⭐ NEW
# ─────────────────────────────────
async def generate_business_cash_idea_llm(user) -> tuple[dict, list]:
    """
    Generates business idea using LLM with NO loan (cash-only) + RAG.
    Returns: (llm_response, rag_chunk_ids)
    """
    # ⭐ RAG: use empty business_loan dict since we don't need loan info
    no_loan = {"approved": False, "max_loan_amount": 0, "interest_rate": 0}
    rag_context, rag_chunk_ids = _build_rag_context(user, no_loan)

    prompt = build_prompt_cash(user, rag_context=rag_context)

    response = await call_llm_with_retry(
        llm_call=lambda: call_llm(prompt),
        agent_name="business_cash"
    )

    return response, rag_chunk_ids


# ─────────────────────────────────
# ✅ VALIDATE OUTPUT (with hard cap)
# ⭐ Now uses _calculate_max_return for horizon-adjusted cap
# ─────────────────────────────────
def validate_business_output(data: dict, user=None) -> dict:
    """
    Validates business agent output and applies post-validation clamps.
    Uses horizon-adjusted max_return (HOURS_RETURN_CAP × HORIZON_RETURN_MODIFIER).
    """
    # ⭐ BUG #3 FIX: Use horizon-adjusted max_return
    max_return = _calculate_max_return(user)

    raw_return = data.get("expected_return", 0.10)
    capped_return = clamp(raw_return, 0.01, max_return, 0.07)

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
        "expected_return": capped_return,
        "risk": round(clamp(data.get("risk"), 0, 1, 0.5), 4),
        "stability": round(clamp(data.get("stability"), 0, 1, 0.5), 4),
        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), []),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "6-12 months"),
    }


# ─────────────────────────────────
# ✅ VALIDATE OUTPUT — CASH variant
# ⭐ NEW
# ─────────────────────────────────
def validate_business_cash_output(data: dict, user=None) -> dict:
    """Same validation as regular business, but with agent='business_cash'."""
    max_return = _calculate_max_return(user)
    raw_return = data.get("expected_return", 0.08)
    # ⭐ BUG #7 FIX: Round to avoid float precision artifacts
    capped_return = round(clamp(raw_return, 0.01, max_return, 0.07), 4)

    title = safe_str(data.get("title"), "Cash-Only Business")
    # Ensure title has cash marker
    if not title.startswith("[Cash"):
        title = f"[Cash-Only] {title}"

    return {
        "agent": "business_cash",  # ⭐ Different agent name
        "title": title,
        "description": safe_str(
            data.get("description"),
            "A bootstrap business venture using only savings — no loan burden."
        ),
        "allocation": safe_dict(data.get("allocation"), {
            "initial_investment": 0,
            "working_capital": 0,
            "marketing_budget": 0,
            "reserve": 0,
        }),
        "expected_return": capped_return,
        "risk": round(clamp(data.get("risk"), 0, 1, 0.4), 4),
        "stability": round(clamp(data.get("stability"), 0, 1, 0.7), 4),
        "pros": safe_list(data.get("pros"), ["No loan burden — full profit retained"]),
        "cons": safe_list(data.get("cons"), ["Limited initial scale"]),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "6-12 months"),
    }


# ─────────────────────────────────
# 🚀 MAIN AGENT FUNCTION (with loan)
# ─────────────────────────────────
async def run_business_agent(user, business_loan: dict) -> dict:
    """Business agent with business loan + RAG context."""
    raw, rag_chunk_ids = await generate_business_idea_llm(user, business_loan)
    result = validate_business_output(raw, user=user)
    result["rag_sources"] = rag_chunk_ids  # ⭐ Transparency: which chunks were used
    return result

# ─────────────────────────────────
# 🚀 MAIN AGENT FUNCTION — CASH ONLY
# ⭐ NEW
# ─────────────────────────────────
async def run_business_agent_cash(user) -> dict:
    """
    Business agent funded by savings only — NO loan + RAG context.
    ⭐ Provides bootstrap alternative for users with sufficient savings.
    """
    # ⭐ BUG FIX: generate_business_cash_idea_llm returns tuple (response, chunk_ids)
    raw, rag_chunk_ids = await generate_business_cash_idea_llm(user)
    result = validate_business_cash_output(raw, user=user)
    result["rag_sources"] = rag_chunk_ids  # ⭐ Transparency
    return result