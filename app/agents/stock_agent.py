# app/agents/stock_agent.py
"""
Unified Stock Agent v5.2 — TRANSPARENT + REALISTIC.

v5.2 NEW (defense-grade):
  1. portfolio_composition  : asset classes + tickers + weights + expected returns
  2. market_context         : market regime, VIX, CA capital gains tax
  3. projections (Y1/Y3/Y5) : dividend income + price appreciation + margin cost
  4. scenarios              : best/base/worst with appreciation + dividend + total ROI
  5. break_even             : months to recover from drawdown
  6. margin_call_risk       : probability + severity (stock-specific)
  7. calculation_breakdown  : step-by-step transparent math
  8. derived_status_override: status from projections (not just net_return)

Strategy types:
  etf_diversified, dividend_focused, tech_growth, reit_etf, covered_call

Strict requirements (from v4.0):
  - margin loan capped at 50% LTV (loan ≤ savings)
"""

from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import (
    parse_llm_json, clamp, safe_list, safe_str, safe_dict,
    call_llm_with_retry
)
from app.core.california_config import REGION_DATA
from app.engines.inflation_engine import real_return, AgentType
from app.rag.retriever import retrieve


# ─────────────────────────────────
# 📚 RAG CONTEXT BUILDER
# ─────────────────────────────────
def _build_rag_context(user) -> tuple[str, list]:
    region = user.location.region.value
    sector = user.professional.sector.value
    interests = ", ".join(user.professional.interests) if user.professional.interests else ""

    primary_query = f"California {region} stocks investing ETF portfolio {interests}"
    secondary_query = f"California capital gains tax stocks dividends {sector}"

    stock_chunks = retrieve(primary_query, top_k=2, category_filter="stock")
    tax_chunks = retrieve(secondary_query, top_k=1, category_filter="tax")
    all_chunks = stock_chunks + tax_chunks

    if not all_chunks:
        return "", []

    context_parts = ["📚 RELEVANT CALIFORNIA STOCK/INVESTING KNOWLEDGE BASE:\n"]
    for i, chunk in enumerate(all_chunks, 1):
        context_parts.append(
            f"\n═══ Knowledge {i}: {chunk['id']} "
            f"(relevance: {chunk['similarity_score'] * 100:.0f}%) ═══\n"
            f"Category: {chunk['category']} | Sources: {chunk.get('sources', 'N/A')}\n\n"
            f"{chunk['content'][:800]}\n"
        )

    return "\n".join(context_parts), [c['id'] for c in all_chunks]


# ─────────────────────────────────
# 📊 STRATEGY TYPE DEFAULTS
# ─────────────────────────────────
STRATEGY_TYPE_DEFAULTS = {
    "etf_diversified": {
        "blended_return_pct": 8.0,
        "dividend_yield_pct": 2.0,
        "expense_ratio_pct": 0.10,
        "volatility_pct": 15,
        "expected_return_typical": 0.08,
    },
    "dividend_focused": {
        "blended_return_pct": 7.0,
        "dividend_yield_pct": 3.5,        # Higher yield
        "expense_ratio_pct": 0.08,
        "volatility_pct": 12,             # Lower volatility
        "expected_return_typical": 0.07,
    },
    "tech_growth": {
        "blended_return_pct": 12.0,       # Higher return
        "dividend_yield_pct": 0.5,        # Low yield
        "expense_ratio_pct": 0.20,        # QQQ etc.
        "volatility_pct": 22,             # Higher volatility
        "expected_return_typical": 0.10,
    },
    "reit_etf": {
        "blended_return_pct": 8.0,
        "dividend_yield_pct": 4.0,        # REITs pay high dividends
        "expense_ratio_pct": 0.12,
        "volatility_pct": 18,
        "expected_return_typical": 0.075,
    },
    "covered_call": {
        "blended_return_pct": 8.5,
        "dividend_yield_pct": 6.5,        # Premium income
        "expense_ratio_pct": 0.35,        # Active strategy
        "volatility_pct": 14,
        "expected_return_typical": 0.075,
    },
}


# ─────────────────────────────────
# 🔧 HELPERS
# ─────────────────────────────────
def _validate_stock_config(config: dict) -> tuple[bool, str, dict]:
    """Validates and AUTO-CAPS stock config (50% LTV)."""
    loan_amount = config.get("loan_amount", 0)
    savings_to_use = config.get("savings_to_use", 0)

    if loan_amount > 0 and savings_to_use == 0:
        return False, (
            "Margin loan requires savings collateral. "
            "Set savings_to_use > 0 to use margin, or use cash-only strategy."
        ), config

    # Auto-cap margin at 50% LTV
    capped_config = dict(config)
    if loan_amount > savings_to_use:
        capped_config["loan_amount"] = savings_to_use
        # Note: this is a soft cap, not an error

    return True, "", capped_config


def _calculate_margin_interest(loan_amount: float, rate: float) -> float:
    """Annual margin interest cost."""
    if loan_amount <= 0 or rate <= 0:
        return 0
    return round(loan_amount * rate, 2)


# ─────────────────────────────────
# 🎯 v5.2 PROMPT BUILDER
# ─────────────────────────────────
def build_prompt(user, config: dict, rag_context: str = "") -> str:
    loan_amount = config.get("loan_amount", 0)
    loan_years = config.get("loan_years", 5)
    savings_to_use = config.get("savings_to_use", 0)
    interest_rate = config.get("interest_rate", 0.065)

    total_capital = loan_amount + savings_to_use
    uses_margin = loan_amount > 0
    annual_margin_cost = _calculate_margin_interest(loan_amount, interest_rate)

    region = user.location.region
    region_data = REGION_DATA[region]

    interests_text = ", ".join(user.professional.interests) if user.professional.interests else "Not specified"
    experience_text = user.professional.prior_experience or "No prior investing experience"
    hours_value = user.professional.weekly_hours.value

    sector = user.professional.sector.value

    if uses_margin:
        capital_section = f"""📈 FUNDING MODE: MARGIN-LEVERAGED
- Margin loan: ${loan_amount:,.0f} @ {interest_rate * 100:.2f}% (annual)
- Savings collateral: ${savings_to_use:,.0f}
- LTV: {(loan_amount / total_capital * 100):.1f}% (max 50% enforced)
- Total invested: ${total_capital:,.0f}
- ANNUAL MARGIN COST: ${annual_margin_cost:,.0f}"""
        title_marker = "[Margin]"
        mode = "margin"
    else:
        capital_section = f"""💰 FUNDING MODE: CASH-ONLY
- Savings invested: ${savings_to_use:,.0f}
- Total invested: ${total_capital:,.0f}
- No margin interest burden"""
        title_marker = "[Cash-Only]"
        mode = "cash"

    return f"""
You are a senior California stock investment advisor with deep knowledge of CA capital gains tax.

⚠️ MATHEMATICAL CONSISTENCY MANDATORY. Numbers will be auto-verified.

USER PROFILE:
- Age: {user.personal.age} | Region: {region_data['display_name']} | Sector: {sector}
- Interests: {interests_text}
- Prior experience: {experience_text}
- Weekly hours: {hours_value}
- Income: ${user.financial.income:,}/mo | Savings: ${user.financial.savings:,}

{capital_section}

PREFERENCES: {user.preferences.risk_profile.value} risk, {user.preferences.horizon.value} yr horizon

{rag_context}

🌴 CALIFORNIA-SPECIFIC (CRITICAL):
═══════════════════════════════════════════════════════════════
- CA Capital Gains Tax: up to 13.3% (no LT preferential rate, unlike federal)
- Federal LT capital gains: 15-20% for high earners
- TOTAL TAX BURDEN: ~28-37% on stock gains (highest in nation)
- Wash sale rule: 30 day window
- {region_data['display_name']}: COL {region_data['cost_of_living_index']}x

═══════════════════════════════════════════════════════════════
📊 STRATEGY TYPE SELECTION:
═══════════════════════════════════════════════════════════════
Choose ONE that fits user profile and capital ${total_capital:,.0f}:

  - "etf_diversified"   → Broad market ETFs (VOO, VTI, VXUS) — 8%, low vol
  - "dividend_focused"  → Dividend ETFs (SCHD, VYM) — 7%, stable income
  - "tech_growth"       → Tech ETFs (QQQ, VGT) — 12%, high volatility
  - "reit_etf"          → REIT ETFs (VNQ, REM) — 8%, real estate exposure
  - "covered_call"      → Income ETFs (JEPI, JEPQ) — 7.5%, premium income

═══════════════════════════════════════════════════════════════
🔢 v5.2 MATH RULES — REALISTIC PROJECTIONS
═══════════════════════════════════════════════════════════════

RULE 1: portfolio_composition asset_classes MUST sum to 100% weight
  Example: VOO 40% + QQQ 25% + VNQ 20% + BND 15% = 100%

RULE 2: blended_expected_return = SUM(weight_i × return_i)
  Example: (40% × 8%) + (25% × 12%) + (20% × 7%) + (15% × 4%) = 8.0%

RULE 3: Year 1 projections:
  - dividend_income = total_capital × dividend_yield
  - price_appreciation = total_capital × (blended_return - dividend_yield)
  - margin_interest_cost = -loan_amount × margin_rate
  - ca_capital_gains_tax = 0 (assume reinvested, no realization)
  - net_return = dividend + appreciation + margin_cost

RULE 4: Year 3/5 — same formula, but capital grows (compounding):
  - Y3 capital = Y1 capital × (1 + blended_return)^2
  - Y5 capital = Y1 capital × (1 + blended_return)^4

RULE 5: Scenarios reflect STOCK realities:
  - best_case: Bull market, 15-20% appreciation
  - base_case: Average market, matches blended_return
  - worst_case: Bear market, NEGATIVE (-15 to -25%)

RULE 6: margin_call_risk MANDATORY if margin > 0:
  - At 25% drawdown, broker may issue margin call
  - probability based on portfolio volatility
  - severity: typical forced sale loses 30%

═══════════════════════════════════════════════════════════════
📝 OUTPUT FORMAT (STRICT JSON, no markdown):
═══════════════════════════════════════════════════════════════

{{
  "agent": "stock",
  "title": "{title_marker} ...",
  "type": "etf_diversified",
  "description": "3-4 sentences. {region_data['display_name']}-specific. Mention CA tax impact.",

  "allocation": {{
    "stocks_etfs": 0,
    "bonds": 0,
    "reits": 0,
    "cash_reserve": 0,
    "international": 0
  }},

  "expected_return": 0.08,
  "risk": 0.45,
  "stability": 0.60,

  "portfolio_composition": {{
    "asset_classes": [
      {{"name": "S&P 500 ETF", "ticker": "VOO", "weight_pct": 40, "expected_return_pct": 8}},
      {{"name": "Tech Growth", "ticker": "QQQ", "weight_pct": 25, "expected_return_pct": 12}},
      {{"name": "REIT ETF", "ticker": "VNQ", "weight_pct": 20, "expected_return_pct": 7}},
      {{"name": "Bonds", "ticker": "BND", "weight_pct": 15, "expected_return_pct": 4}}
    ],
    "blended_expected_return_pct": 8.1,
    "dividend_yield_pct": 2.5,
    "expense_ratio_pct": 0.10
  }},

  "market_context": {{
    "market_regime": "neutral",
    "sp500_yoy_change_pct": 10,
    "vix_level": 18,
    "ca_capital_gains_tax_pct": 13.3,
    "expected_volatility_pct": 15
  }},

  "projections": {{
    "year_1": {{
      "dividend_income": 0,
      "price_appreciation": 0,
      "margin_interest_cost": {-annual_margin_cost:.0f},
      "ca_capital_gains_tax": 0,
      "net_return": 0
    }},
    "year_3": {{
      "dividend_income": 0,
      "price_appreciation": 0,
      "margin_interest_cost": {-annual_margin_cost:.0f},
      "ca_capital_gains_tax": 0,
      "net_return": 0
    }},
    "year_5": {{
      "dividend_income": 0,
      "price_appreciation": 0,
      "margin_interest_cost": {-annual_margin_cost:.0f},
      "ca_capital_gains_tax": 0,
      "net_return": 0
    }}
  }},

  "scenarios": {{
    "best_case": {{
      "price_appreciation_pct": 18,
      "dividend_yield_pct": 3,
      "total_roi_pct": 21,
      "narrative": "Bull market + earnings growth"
    }},
    "base_case": {{
      "price_appreciation_pct": 6,
      "dividend_yield_pct": 2.5,
      "total_roi_pct": 8.5,
      "narrative": "Average California market conditions"
    }},
    "worst_case": {{
      "price_appreciation_pct": -20,
      "dividend_yield_pct": 2,
      "total_roi_pct": -18,
      "narrative": "Bear market + margin call risk"
    }}
  }},

  "break_even": {{
    "months_to_breakeven": 12,
    "drawdown_recovery_months": 24,
    "explanation": "Months until portfolio recovers from typical 20% drawdown."
  }},

  "margin_call_risk": {{
    "margin_call_probability": {0.15 if uses_margin else 0},
    "trigger_drawdown_pct": 25,
    "expected_severity_loss": {0.30 if uses_margin else 0},
    "explanation": "{'At 25% portfolio drawdown, broker may force liquidation.' if uses_margin else 'No margin used — no margin call risk.'}"
  }},

  "pros": ["...", "...", "..."],
  "cons": ["...", "..."],
  "next_steps": ["...", "...", "..."],
  "time_to_profit": "..."
}}
"""


# ─────────────────────────────────
# 🤖 LLM CALL
# ─────────────────────────────────
async def generate_stock_strategy_llm(user, config: dict) -> tuple[dict, list]:
    rag_context, rag_chunk_ids = _build_rag_context(user)
    prompt = build_prompt(user, config, rag_context=rag_context)
    uses_margin = config.get("loan_amount", 0) > 0
    agent_name = "stock_margin" if uses_margin else "stock_cash"
    response = await call_llm_with_retry(
        llm_call=lambda: call_llm(prompt),
        agent_name=agent_name
    )
    return response, rag_chunk_ids


# ─────────────────────────────────
# ✅ v5.2 VALIDATORS
# ─────────────────────────────────
def _rescale_allocation_to_capital(allocation: dict, target_total: float) -> dict:
    """Rescale allocation to match target_total."""
    if target_total <= 0:
        return allocation
    keys = ["stocks_etfs", "bonds", "reits", "cash_reserve", "international"]
    for k in keys:
        if k not in allocation:
            allocation[k] = 0
        try:
            allocation[k] = max(0, float(allocation[k]))
        except (TypeError, ValueError):
            allocation[k] = 0

    current_sum = sum(allocation[k] for k in keys)
    if current_sum == 0:
        # Default 60/15/10/5/10 split
        allocation["stocks_etfs"] = round(target_total * 0.60, 2)
        allocation["bonds"] = round(target_total * 0.15, 2)
        allocation["reits"] = round(target_total * 0.10, 2)
        allocation["cash_reserve"] = round(target_total * 0.05, 2)
        allocation["international"] = round(target_total * 0.10, 2)
        return allocation

    ratio = target_total / current_sum
    for k in keys:
        allocation[k] = round(allocation[k] * ratio, 2)
    new_sum = sum(allocation[k] for k in keys)
    allocation["cash_reserve"] = round(allocation["cash_reserve"] + (target_total - new_sum), 2)
    return allocation


def _validate_portfolio_composition(data: dict, type_value: str) -> dict:
    pc = data.get("portfolio_composition") or {}
    defaults = STRATEGY_TYPE_DEFAULTS.get(type_value, STRATEGY_TYPE_DEFAULTS["etf_diversified"])

    asset_classes = pc.get("asset_classes") or []
    # Validate and normalize weights to sum to 100%
    valid_classes = []
    total_weight = 0
    for ac in asset_classes[:6]:  # max 6 classes
        if not isinstance(ac, dict):
            continue
        weight = clamp(ac.get("weight_pct"), 0, 100, 0)
        if weight <= 0:
            continue
        valid_classes.append({
            "name": safe_str(ac.get("name"), "Asset Class")[:80],
            "ticker": safe_str(ac.get("ticker"), "")[:10],
            "weight_pct": round(weight, 1),
            "expected_return_pct": round(clamp(ac.get("expected_return_pct"), -10, 25, 7), 1),
        })
        total_weight += weight

    # If weights don't sum to 100%, normalize
    if valid_classes and abs(total_weight - 100) > 1:
        if total_weight > 0:
            for ac in valid_classes:
                ac["weight_pct"] = round(ac["weight_pct"] * 100 / total_weight, 1)

    if not valid_classes:
        # Default composition based on type
        if type_value == "tech_growth":
            valid_classes = [
                {"name": "Tech ETF", "ticker": "QQQ", "weight_pct": 60, "expected_return_pct": 12},
                {"name": "S&P 500", "ticker": "VOO", "weight_pct": 30, "expected_return_pct": 8},
                {"name": "Bonds", "ticker": "BND", "weight_pct": 10, "expected_return_pct": 4},
            ]
        elif type_value == "dividend_focused":
            valid_classes = [
                {"name": "Dividend ETF", "ticker": "SCHD", "weight_pct": 60, "expected_return_pct": 7},
                {"name": "S&P 500", "ticker": "VOO", "weight_pct": 25, "expected_return_pct": 8},
                {"name": "REIT ETF", "ticker": "VNQ", "weight_pct": 15, "expected_return_pct": 7},
            ]
        elif type_value == "reit_etf":
            valid_classes = [
                {"name": "REIT ETF", "ticker": "VNQ", "weight_pct": 60, "expected_return_pct": 8},
                {"name": "Mortgage REIT", "ticker": "REM", "weight_pct": 20, "expected_return_pct": 9},
                {"name": "S&P 500", "ticker": "VOO", "weight_pct": 20, "expected_return_pct": 8},
            ]
        else:
            valid_classes = [
                {"name": "S&P 500 ETF", "ticker": "VOO", "weight_pct": 50, "expected_return_pct": 8},
                {"name": "International", "ticker": "VXUS", "weight_pct": 20, "expected_return_pct": 7},
                {"name": "Bonds", "ticker": "BND", "weight_pct": 20, "expected_return_pct": 4},
                {"name": "REIT", "ticker": "VNQ", "weight_pct": 10, "expected_return_pct": 7},
            ]

    # Compute blended return from weights
    blended = sum(
        (ac["weight_pct"] / 100) * ac["expected_return_pct"]
        for ac in valid_classes
    )

    return {
        "asset_classes": valid_classes,
        "blended_expected_return_pct": round(blended, 2),
        "dividend_yield_pct": round(clamp(
            pc.get("dividend_yield_pct"), 0, 10, defaults["dividend_yield_pct"]
        ), 2),
        "expense_ratio_pct": round(clamp(
            pc.get("expense_ratio_pct"), 0, 2, defaults["expense_ratio_pct"]
        ), 2),
    }


def _validate_market_context(data: dict) -> dict:
    mc = data.get("market_context") or {}
    regime = safe_str(mc.get("market_regime"), "neutral").lower()
    if regime not in ("bull", "neutral", "bear"):
        regime = "neutral"

    return {
        "market_regime": regime,
        "sp500_yoy_change_pct": round(clamp(mc.get("sp500_yoy_change_pct"), -40, 40, 10), 1),
        "vix_level": round(clamp(mc.get("vix_level"), 8, 80, 18), 1),
        "ca_capital_gains_tax_pct": round(clamp(mc.get("ca_capital_gains_tax_pct"), 0, 20, 13.3), 1),
        "expected_volatility_pct": round(clamp(mc.get("expected_volatility_pct"), 5, 50, 15), 1),
    }


def _recompute_projections(
    data: dict,
    portfolio_comp: dict,
    config: dict,
) -> dict:
    """Recompute Y1/Y3/Y5 from portfolio composition + margin cost."""
    loan_amount = config.get("loan_amount", 0)
    interest_rate = config.get("interest_rate", 0.065)
    total_capital = loan_amount + config.get("savings_to_use", 0)

    blended_return = portfolio_comp["blended_expected_return_pct"] / 100
    dividend_yield = portfolio_comp["dividend_yield_pct"] / 100
    expense_ratio = portfolio_comp["expense_ratio_pct"] / 100

    annual_margin_cost = _calculate_margin_interest(loan_amount, interest_rate)

    def _build_year(year_n: int) -> dict:
        # Capital compounds over time (reinvested)
        capital_at_year = total_capital * ((1 + blended_return - expense_ratio) ** (year_n - 1))

        # Dividend income (annual)
        dividend_income = round(capital_at_year * dividend_yield, 2)

        # Price appreciation (capital gain that year)
        price_appreciation = round(capital_at_year * (blended_return - dividend_yield - expense_ratio), 2)

        # Margin interest cost (fixed annual, unless paid down)
        margin_cost = round(-annual_margin_cost, 2)

        # CA capital gains tax (assume reinvested, no realization)
        # Only applies if user sells; we assume hold strategy
        ca_tax = 0

        net_return = round(dividend_income + price_appreciation + margin_cost + ca_tax, 2)

        return {
            "dividend_income": dividend_income,
            "price_appreciation": price_appreciation,
            "margin_interest_cost": margin_cost,
            "ca_capital_gains_tax": ca_tax,
            "net_return": net_return,
        }

    return {
        "year_1": _build_year(1),
        "year_3": _build_year(3),
        "year_5": _build_year(5),
    }


def _validate_scenarios(data: dict, base_return: float) -> dict:
    """
    ⭐ v5.2.2 BUG #5 FIX:
    Enforces total_roi_pct = price_appreciation_pct + dividend_yield_pct.
    Previously LLM could hallucinate inconsistent values.
    Now total is ALWAYS computed from the parts.
    """
    sc = data.get("scenarios") or {}
    base_pct = round(base_return * 100, 1)

    def _v(key, default_appr, default_div, narrative_default):
        item = sc.get(key) or {}
        appr_pct = round(clamp(item.get("price_appreciation_pct"), -40, 40, default_appr), 1)
        div_pct = round(clamp(item.get("dividend_yield_pct"), 0, 10, default_div), 1)

        # ⭐ v5.2.2: ALWAYS compute total = appr + div (don't trust LLM math)
        total_roi = round(appr_pct + div_pct, 1)

        return {
            "price_appreciation_pct": appr_pct,
            "dividend_yield_pct": div_pct,
            "total_roi_pct": total_roi,
            "narrative": safe_str(item.get("narrative"), narrative_default)[:300],
        }

    best = _v("best_case", 18, 3, "Bull market + earnings growth")
    base = _v("base_case", 6, 2.5, "Average California market conditions")
    worst = _v("worst_case", -20, 2, "Bear market + correction")

    # Enforce hierarchy
    if best["total_roi_pct"] <= base["total_roi_pct"] + 3:
        best["price_appreciation_pct"] = round(base["price_appreciation_pct"] + 10, 1)
        best["total_roi_pct"] = round(best["price_appreciation_pct"] + best["dividend_yield_pct"], 1)

    if worst["total_roi_pct"] >= base["total_roi_pct"] - 3:
        worst["price_appreciation_pct"] = round(base["price_appreciation_pct"] - 15, 1)
        worst["total_roi_pct"] = round(worst["price_appreciation_pct"] + worst["dividend_yield_pct"], 1)

    return {"best_case": best, "base_case": base, "worst_case": worst}


def _validate_break_even(data: dict, market_ctx: dict) -> dict:
    be = data.get("break_even") or {}
    volatility = market_ctx.get("expected_volatility_pct", 15)

    # Higher volatility → longer recovery
    months_default = max(6, int(volatility * 1.5))

    return {
        "months_to_breakeven": int(clamp(be.get("months_to_breakeven"), 1, 60, 12)),
        "drawdown_recovery_months": int(clamp(be.get("drawdown_recovery_months"), 1, 60, months_default)),
        "explanation": safe_str(
            be.get("explanation"),
            f"Months until portfolio recovers from typical 20% drawdown. "
            f"Higher volatility ({volatility:.0f}%) = longer recovery."
        )[:300],
    }


def _validate_margin_call_risk(data: dict, config: dict, market_ctx: dict) -> dict:
    """Compute margin call risk based on volatility and LTV."""
    mcr = data.get("margin_call_risk") or {}
    loan_amount = config.get("loan_amount", 0)
    savings_to_use = config.get("savings_to_use", 0)

    if loan_amount <= 0 or savings_to_use <= 0:
        return {
            "margin_call_probability": 0,
            "trigger_drawdown_pct": 0,
            "expected_severity_loss": 0,
            "explanation": "No margin used — no margin call risk.",
        }

    ltv = loan_amount / (loan_amount + savings_to_use)
    volatility = market_ctx.get("expected_volatility_pct", 15) / 100

    # Probability roughly: 2× LTV × volatility (rough heuristic)
    # Higher LTV + higher vol = higher probability
    raw_prob = 2 * ltv * volatility
    probability = round(min(0.50, max(0.01, raw_prob)), 3)

    return {
        "margin_call_probability": probability,
        "trigger_drawdown_pct": round(clamp(mcr.get("trigger_drawdown_pct"), 10, 50, 25), 1),
        "expected_severity_loss": round(clamp(mcr.get("expected_severity_loss"), 0, 1, 0.30), 3),
        "explanation": safe_str(
            mcr.get("explanation"),
            f"With {ltv * 100:.0f}% LTV and {volatility * 100:.0f}% volatility, "
            f"there's ~{probability * 100:.0f}% chance broker issues margin call at "
            f"25% drawdown. Forced sale typically loses 30% of position value."
        )[:300],
    }


def _build_allocation_from_composition(portfolio_comp: dict, target_total: float) -> dict:
    """
    ⭐ v5.2.2 BUG #3 FIX:
    Maps portfolio_composition.asset_classes to allocation buckets.

    PRE: VOO 40% + QQQ 25% + VNQ 20% + BND 15% → allocation $0 za bonds/reits
    POSLE: stocks_etfs $650 + reits $200 + bonds $150 (correct mapping)

    Mapping rules (by ticker / asset name):
      - stocks_etfs:  VOO, VTI, SPY, QQQ, VGT, SCHD, VYM, JEPI, JEPQ
      - bonds:        BND, AGG, BIV, BNDX (anything bond/treasury)
      - reits:        VNQ, REM, IYR (anything REIT)
      - international: VXUS, VEU, IXUS, EFA, VWO
      - cash_reserve: cash, money market
    """
    if target_total <= 0:
        return {
            "stocks_etfs": 0, "bonds": 0, "reits": 0,
            "cash_reserve": 0, "international": 0
        }

    asset_classes = portfolio_comp.get("asset_classes", [])
    allocation = {
        "stocks_etfs": 0.0,
        "bonds": 0.0,
        "reits": 0.0,
        "cash_reserve": 0.0,
        "international": 0.0,
    }

    BOND_KEYWORDS = ["bond", "treasury", "agg", "bnd", "tlt", "tip", "bil"]
    REIT_KEYWORDS = ["reit", "vnq", "rem", "iyr", "real estate"]
    INTL_KEYWORDS = ["international", "vxus", "veu", "ixus", "efa", "emerging", "vwo"]
    CASH_KEYWORDS = ["cash", "money market", "mmkt", "reserve"]

    # If no asset_classes (LLM didn't provide), fall back to default distribution
    if not asset_classes:
        allocation["stocks_etfs"] = round(target_total * 0.60, 2)
        allocation["bonds"] = round(target_total * 0.15, 2)
        allocation["reits"] = round(target_total * 0.10, 2)
        allocation["cash_reserve"] = round(target_total * 0.05, 2)
        allocation["international"] = round(target_total * 0.10, 2)
        return allocation

    for ac in asset_classes:
        weight_pct = ac.get("weight_pct", 0)
        if weight_pct <= 0:
            continue
        dollar_amount = target_total * (weight_pct / 100)

        ticker = (ac.get("ticker", "") or "").lower()
        name = (ac.get("name", "") or "").lower()
        combined = f"{ticker} {name}"

        # Classify into bucket
        if any(kw in combined for kw in BOND_KEYWORDS):
            allocation["bonds"] += dollar_amount
        elif any(kw in combined for kw in REIT_KEYWORDS):
            allocation["reits"] += dollar_amount
        elif any(kw in combined for kw in INTL_KEYWORDS):
            allocation["international"] += dollar_amount
        elif any(kw in combined for kw in CASH_KEYWORDS):
            allocation["cash_reserve"] += dollar_amount
        else:
            # Default to stocks_etfs (VOO, QQQ, sector ETFs, dividend ETFs)
            allocation["stocks_etfs"] += dollar_amount

    # Round each bucket
    for k in allocation:
        allocation[k] = round(allocation[k], 2)

    # Reconcile rounding errors — adjust stocks_etfs to make sum match exactly
    current_sum = sum(allocation.values())
    diff = target_total - current_sum
    if abs(diff) > 0.5:
        allocation["stocks_etfs"] = round(allocation["stocks_etfs"] + diff, 2)

    return allocation

# ─────────────────────────────────
# ⭐ v5.2 NEW — DERIVED RETURN + STATUS + CALC BREAKDOWN
# ─────────────────────────────────
def _derive_expected_return_from_projections(
    projections: dict,
    total_capital: float,
    type_value: str,
) -> float:
    """Average net_return over Y1-Y3 / capital, capped at type-typical max."""
    if total_capital <= 0:
        return 0.0

    defaults = STRATEGY_TYPE_DEFAULTS.get(type_value, STRATEGY_TYPE_DEFAULTS["etf_diversified"])
    max_for_type = defaults["expected_return_typical"] * 1.5

    y1 = projections.get("year_1", {}).get("net_return", 0)
    y3 = projections.get("year_3", {}).get("net_return", 0)
    avg_return = (y1 + y3) / 2

    raw_roi = avg_return / total_capital
    return round(max(-0.20, min(raw_roi, max_for_type)), 4)


def _determine_status_from_projections(
        projections: dict,
        total_capital: float,
        config: dict = None,
) -> str:
    """
    ⭐ v5.2.2 BUG #1 FIX:
    Status now considers FULL margin loan amortization impact.

    PRE: agent saw +5.61% Y3 ROI → "profitable",
         but investment_engine added loan amortization → final -12.67%
    POSLE: status considers BOTH projections AND amortization burden

    Logic:
      - NOT_PROFITABLE if margin loan exists and Y3 ROI after FULL amortization < -2%
      - PROFITABLE if Y1 ROI > 2% AND Y3 ROI > 4% (margin-aware)
      - MARGINAL if Y1 OR Y3 net > 0
      - NOT_PROFITABLE otherwise
    """
    if total_capital <= 0:
        return "not_profitable"

    y1_net = projections.get("year_1", {}).get("net_return", 0)
    y3_net = projections.get("year_3", {}).get("net_return", 0)
    y1_dividend = projections.get("year_1", {}).get("dividend_income", 0)
    y1_appreciation = projections.get("year_1", {}).get("price_appreciation", 0)

    y1_roi = y1_net / total_capital
    y3_roi = y3_net / total_capital

    # ⭐ v5.2.2 NEW: If margin loan used, check TRUE amortization burden
    if config is not None:
        loan_amount = config.get("loan_amount", 0)
        interest_rate = config.get("interest_rate", 0)
        loan_years = config.get("loan_years", 5)

        if loan_amount > 0 and interest_rate > 0 and loan_years > 0:
            # Compute amortized annual payment (investment_engine uses this)
            months = loan_years * 12
            monthly_rate = interest_rate / 12
            try:
                monthly_pmt = (
                        loan_amount * monthly_rate * ((1 + monthly_rate) ** months) /
                        (((1 + monthly_rate) ** months) - 1)
                )
                annual_amort = monthly_pmt * 12
            except (ValueError, ZeroDivisionError):
                annual_amort = loan_amount * interest_rate

            # Margin interest already in projections, but engine may add full amortization
            # Check TRUE net assuming full amortization is applied
            margin_interest_in_proj = abs(projections.get("year_3", {}).get("margin_interest_cost", 0))
            y1_gross = y1_dividend + y1_appreciation
            true_y1_net = y1_gross - annual_amort  # after FULL amortization (worst case)

            # If even Y1 gross can't cover amortization, NOT profitable
            if true_y1_net < -total_capital * 0.05:
                return "not_profitable"

            # Adjust Y3 ROI estimate for amortization
            extra_burden = annual_amort - margin_interest_in_proj
            true_y3_net = y3_net - extra_burden
            true_y3_roi = true_y3_net / total_capital

            if true_y3_roi < -0.02:
                return "not_profitable"
            if true_y3_roi < 0.02:
                return "marginal"

    # Standard logic (cash-only or low-impact margin scenarios)
    if y1_roi > 0.02 and y3_roi > 0.04:
        return "profitable"
    elif y1_net > 0 or y3_net > 0:
        return "marginal"
    else:
        return "not_profitable"


def _build_calculation_breakdown(
    user,
    config: dict,
    portfolio_comp: dict,
    market_ctx: dict,
    projections: dict,
    margin_call_risk: dict,
    expected_return: float,
    total_capital: float,
) -> dict:
    """Step-by-step transparent calculation for stocks."""
    loan_amount = config.get("loan_amount", 0)
    savings_to_use = config.get("savings_to_use", 0)
    interest_rate = config.get("interest_rate", 0)
    annual_margin_cost = _calculate_margin_interest(loan_amount, interest_rate)
    uses_margin = loan_amount > 0

    currency = user.financial.currency.value
    y1 = projections.get("year_1", {})
    y3 = projections.get("year_3", {})

    blended_return = portfolio_comp["blended_expected_return_pct"] / 100
    dividend_yield = portfolio_comp["dividend_yield_pct"] / 100
    expense_ratio = portfolio_comp["expense_ratio_pct"] / 100
    ca_tax = market_ctx["ca_capital_gains_tax_pct"]

    # Inflation
    try:
        agent_type = AgentType("stock")
        real_roi = real_return(
            nominal_return=expected_return,
            agent=agent_type,
            currency=currency
        )
        inflation_pct = round((expected_return - real_roi) * 100, 2)
    except Exception:
        real_roi = expected_return * 0.70
        inflation_pct = round(expected_return * 30, 2)

    steps = [
        {
            "step": 1,
            "title": "Your Capital",
            "explanation": (
                f"Total capital invested in the portfolio. "
                f"{'Includes margin loan from broker.' if uses_margin else 'All from your savings.'}"
            ),
            "formula": (
                f"${savings_to_use:,.0f} (savings) + ${loan_amount:,.0f} (margin)"
                if uses_margin
                else f"${savings_to_use:,.0f} (savings only)"
            ),
            "result": f"${total_capital:,.0f}",
            "value_usd": round(total_capital, 2),
        },
    ]

    # Step 2: Portfolio composition
    composition_str = ", ".join([
        f"{ac['ticker']}: {ac['weight_pct']:.0f}%"
        for ac in portfolio_comp["asset_classes"][:5]
    ])

    steps.append({
        "step": 2,
        "title": "Portfolio Composition + Blended Return",
        "explanation": (
            "Your portfolio combines multiple asset classes. The blended return is "
            "the weighted average of each asset's expected return."
        ),
        "formula": composition_str,
        "result": f"{portfolio_comp['blended_expected_return_pct']:.2f}% blended return (before fees)",
        "value_pct": round(portfolio_comp["blended_expected_return_pct"], 2),
    })

    # Step 3: Dividend income
    y1_dividend = y1.get("dividend_income", 0)
    steps.append({
        "step": 3,
        "title": "Annual Dividend Income",
        "explanation": (
            f"Dividend ETFs pay you cash each quarter. "
            f"Your portfolio's blended dividend yield is {dividend_yield * 100:.2f}%."
        ),
        "formula": f"${total_capital:,.0f} × {dividend_yield * 100:.2f}% = ${y1_dividend:,.0f}",
        "result": f"+${y1_dividend:,.0f}/year",
        "value_usd": round(y1_dividend, 2),
    })

    # Step 4: Price appreciation
    y1_appreciation = y1.get("price_appreciation", 0)
    appreciation_pct = (blended_return - dividend_yield - expense_ratio) * 100
    steps.append({
        "step": 4,
        "title": "Annual Price Appreciation",
        "explanation": (
            "Stock prices grow over time. After subtracting dividends paid out and "
            f"expense ratio ({expense_ratio * 100:.2f}%), price grows at "
            f"~{appreciation_pct:.2f}%/year."
        ),
        "formula": (
            f"${total_capital:,.0f} × ({blended_return * 100:.2f}% blended - "
            f"{dividend_yield * 100:.2f}% div - {expense_ratio * 100:.2f}% expense)"
        ),
        "result": f"+${y1_appreciation:,.0f}/year",
        "value_usd": round(y1_appreciation, 2),
    })

    # Step 5: Margin interest cost (only if margin used)
    if uses_margin:
        steps.append({
            "step": 5,
            "title": "Margin Interest Cost",
            "explanation": (
                f"Your broker charges interest on the margin loan. "
                f"At {interest_rate * 100:.2f}% on ${loan_amount:,.0f}, "
                f"this is a fixed annual cost regardless of market performance."
            ),
            "formula": f"${loan_amount:,.0f} × {interest_rate * 100:.2f}%",
            "result": f"-${annual_margin_cost:,.0f}/year",
            "value_usd": round(-annual_margin_cost, 2),
            "note": (
                f"⚠️ Margin call risk: At 25% drawdown, broker may force liquidation. "
                f"Estimated probability: {margin_call_risk['margin_call_probability'] * 100:.0f}%"
            ),
        })

    # Step 6: CA capital gains tax (when realized)
    steps.append({
        "step": 6 if uses_margin else 5,
        "title": "California Capital Gains Tax (when realized)",
        "explanation": (
            "California has the HIGHEST capital gains tax in the US. Unlike federal "
            f"(15-20% long-term), CA taxes gains as ordinary income (up to {ca_tax:.1f}%). "
            "Total tax burden when you SELL: ~30-37%. "
            "We assume buy-and-hold (no realization), so tax = $0 until sale."
        ),
        "formula": f"If you sell: gain × ~30% (Federal LT + CA {ca_tax:.1f}%)",
        "result": "$0 if held (recommended) | ~30% if sold short-term",
        "value_usd": 0,
        "note": "💡 Tax-efficient strategy: Hold long-term, harvest losses, use tax-advantaged accounts.",
    })

    # Step 7: Net annual return
    y1_net = y1.get("net_return", 0)
    y1_roi = (y1_net / total_capital * 100) if total_capital > 0 else 0
    steps.append({
        "step": 7 if uses_margin else 6,
        "title": "Net Annual Return (Year 1)",
        "explanation": (
            "Sum of all flows: dividends + appreciation - margin cost - tax. "
            "This is your TRUE annual return."
        ),
        "formula": (
            f"${y1_dividend:,.0f} (div) + ${y1_appreciation:,.0f} (appr) "
            f"{'- $' + str(int(annual_margin_cost)) + ' (margin)' if uses_margin else ''}"
        ),
        "result": f"${y1_net:,.0f}/year ({y1_roi:+.2f}% net)",
        "value_usd": round(y1_net, 2),
        "value_pct": round(y1_roi, 2),
    })

    # Step 8: Inflation
    steps.append({
        "step": 8 if uses_margin else 7,
        "title": "Inflation-Adjusted (Real) Return",
        "explanation": (
            "Money loses purchasing power. California inflation typically "
            f"~{inflation_pct:.1f}%/year. Stocks are partially inflation-protected "
            "(companies raise prices, dividends grow)."
        ),
        "formula": f"{expected_return * 100:.2f}% nominal - {inflation_pct:.2f}% inflation",
        "result": f"{real_roi * 100:+.2f}% real annual return",
        "value_pct": round(real_roi * 100, 2),
    })

    # Conclusion
    y3_net = y3.get("net_return", 0)
    y3_roi = (y3_net / total_capital) if total_capital > 0 else 0

    if y1_roi > 2 and y3_roi > 0.04:
        if uses_margin:
            conclusion = (
                f"✅ This margin strategy is profitable IF market cooperates.\n\n"
                f"📊 Year 1 outlook:\n"
                f"• Dividend income: ${y1_dividend:,.0f}\n"
                f"• Price appreciation: ${y1_appreciation:,.0f}\n"
                f"• Margin cost: -${annual_margin_cost:,.0f}\n"
                f"• Net: ${y1_net:,.0f} ({y1_roi:+.2f}%)\n\n"
                f"⚠️ RISK: {margin_call_risk['margin_call_probability'] * 100:.0f}% chance of margin call. "
                f"Bear market with 25% drawdown could trigger forced liquidation."
            )
        else:
            conclusion = (
                f"✅ This is a solid cash-only investment.\n\n"
                f"📊 Year 1 outlook:\n"
                f"• Dividend income: ${y1_dividend:,.0f}\n"
                f"• Price appreciation: ${y1_appreciation:,.0f}\n"
                f"• Net: ${y1_net:,.0f} ({y1_roi:+.2f}%)\n\n"
                f"💡 Tax efficiency: Hold long-term to avoid CA's high capital gains tax."
            )
    elif y1_net > 0:
        conclusion = (
            f"⚠️ Marginal returns. Y1 net: ${y1_net:,.0f} ({y1_roi:+.2f}%).\n\n"
            f"This may not justify the risk. Consider:\n"
            f"• Lower-cost ETFs (reduce expense_ratio)\n"
            f"• {'Reduce margin loan to lower interest cost' if uses_margin else 'Stay course — long-term compounds'}\n"
            f"• Tax-loss harvesting in down years"
        )
    else:
        conclusion = (
            f"❌ Negative projected returns at current configuration.\n\n"
            f"Year 1 net: ${y1_net:,.0f} ({y1_roi:+.2f}%)\n\n"
            f"💡 Options:\n"
            f"{'• Eliminate margin loan — interest cost exceeds returns' if uses_margin else '• Choose more aggressive strategy (tech_growth)'}\n"
            f"• Reduce expense ratio (use index ETFs like VOO, not active funds)\n"
            f"• Increase time horizon — stocks need 5+ years to compound"
        )

    return {
        "steps": steps,
        "summary": {
            "total_capital": round(total_capital, 2),
            "blended_return_pct": round(portfolio_comp["blended_expected_return_pct"], 2),
            "dividend_yield_pct": round(dividend_yield * 100, 2),
            "annual_dividend": round(y1_dividend, 2),
            "annual_appreciation": round(y1_appreciation, 2),
            "annual_margin_cost": round(annual_margin_cost, 2),
            "nominal_return_pct": round(expected_return * 100, 2),
            "real_return_pct": round(real_roi * 100, 2),
            "inflation_pct": round(inflation_pct, 2),
        },
        "conclusion": conclusion,
    }


# ─────────────────────────────────
# ✅ MAIN VALIDATOR (v5.2)
# ─────────────────────────────────
def validate_stock_output(data: dict, user=None, config: dict = None) -> dict:
    # Type validation
    valid_types = {"etf_diversified", "dividend_focused", "tech_growth", "reit_etf", "covered_call"}
    type_value = safe_str(data.get("type"), "etf_diversified")
    if type_value not in valid_types:
        type_value = "etf_diversified"

    defaults = STRATEGY_TYPE_DEFAULTS[type_value]

    # Risk/stability per type
    if type_value == "tech_growth":
        default_risk, default_stability = 0.60, 0.45
    elif type_value == "dividend_focused":
        default_risk, default_stability = 0.35, 0.70
    elif type_value == "covered_call":
        default_risk, default_stability = 0.40, 0.65
    else:
        default_risk, default_stability = 0.45, 0.60

    # Capital info
    if config:
        loan_amount = config.get("loan_amount", 0)
        savings_to_use = config.get("savings_to_use", 0)
        # Auto-cap loan at 50% LTV
        if loan_amount > savings_to_use:
            loan_amount = savings_to_use
        total_capital = loan_amount + savings_to_use
        uses_margin = loan_amount > 0
    else:
        loan_amount = 0
        savings_to_use = 0
        total_capital = 0
        uses_margin = False

    # Title with mode prefix
    title = safe_str(data.get("title"), "Stock portfolio strategy")
    marker = "[Margin]" if uses_margin else "[Cash-Only]"
    if not (title.startswith("[Margin") or title.startswith("[Cash")):
        title = f"{marker} {title}"

    # ⭐ v5.2.2 VALIDATION CHAIN
    portfolio_comp = _validate_portfolio_composition(data, type_value)
    #     # ⭐ v5.2.2 BUG #3 FIX: Build allocation FROM composition (not from LLM)
    rescaled_alloc = _build_allocation_from_composition(portfolio_comp, total_capital)
    market_context = _validate_market_context(data)

    # Recompute projections from portfolio composition
    projections = _recompute_projections(data, portfolio_comp, config or {})

    # ⭐ v5.2 NEW: Derive expected_return from projections
    derived_return = _derive_expected_return_from_projections(
        projections, total_capital, type_value
    )

    # ⭐ v5.2 NEW: Determine status from projections
    derived_status = _determine_status_from_projections(projections, total_capital, config or {})

    scenarios = _validate_scenarios(data, derived_return)
    break_even = _validate_break_even(data, market_context)
    margin_call_risk = _validate_margin_call_risk(data, config or {}, market_context)

    # ⭐ v5.2 NEW: Calculation breakdown
    calc_breakdown = _build_calculation_breakdown(
        user, config or {}, portfolio_comp, market_context, projections,
        margin_call_risk, derived_return, total_capital
    )

    return {
        "agent": "stock",
        "title": title,
        "type": type_value,
        "description": safe_str(
            data.get("description"),
            "A California-aware stock portfolio strategy."
        ),
        "allocation": rescaled_alloc,
        "expected_return": derived_return,
        "risk": round(clamp(data.get("risk"), 0, 1, default_risk), 4),
        "stability": round(clamp(data.get("stability"), 0, 1, default_stability), 4),

        # ⭐ v5.2 NEW FIELDS
        "portfolio_composition": portfolio_comp,
        "market_context": market_context,
        "projections": projections,
        "scenarios": scenarios,
        "break_even": break_even,
        "margin_call_risk": margin_call_risk,
        "calculation_breakdown": calc_breakdown,
        "derived_status_override": derived_status,

        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), []),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "12-24 months"),
    }


# ─────────────────────────────────
# 🚀 MAIN AGENT FUNCTION
# ─────────────────────────────────
async def run_stock_agent(user, config: dict) -> dict:
    """v5.2 stock agent with realistic projections + transparent breakdown."""
    if config is None:
        config = {
            "loan_amount": 0, "loan_years": 0,
            "savings_to_use": user.financial.savings, "interest_rate": 0,
        }

    # Validate config (auto-cap margin)
    is_valid, reason, capped_config = _validate_stock_config(config)
    if not is_valid:
        return {
            "agent": "stock",
            "rejected": True,
            "rejection_reason": reason,
            "title": "Stock — Strategy Rejected",
            "description": f"Stock strategy was not generated. {reason}",
            "type": "rejected",
            "allocation": {},
            "expected_return": 0, "risk": 0, "stability": 0,
            "pros": [], "cons": [reason],
            "next_steps": [
                "Adjust savings allocation to at least match margin loan amount",
                "Or use cash-only strategy (no margin)",
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

    # Run LLM with capped config
    raw, rag_chunk_ids = await generate_stock_strategy_llm(user, capped_config)
    result = validate_stock_output(raw, user=user, config=capped_config)
    result["rag_sources"] = rag_chunk_ids

    # Embed config metadata
    uses_margin = capped_config.get("loan_amount", 0) > 0
    result["funding_mode"] = "margin" if uses_margin else "cash"
    result["loan_amount"] = capped_config.get("loan_amount", 0)
    result["loan_years"] = capped_config.get("loan_years", 0)
    result["savings_used"] = capped_config.get("savings_to_use", 0)
    result["interest_rate"] = capped_config.get("interest_rate", 0)
    result["total_capital"] = capped_config.get("loan_amount", 0) + capped_config.get("savings_to_use", 0)
    result["rejected"] = False

    return result