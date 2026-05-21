# app/agents/judge_agent.py
"""
Judge Agent v5.2.1 — UNIFIED COMPARISON METRICS.

v5.2.1 FIX:
  - Adds Y3 COMPARABLE RETURN to prompt (apples-to-apples metric)
    - Business: net_cash_flow (operating profit)
    - Real Estate: total_return (cash + equity + appreciation)  ← CRITICAL
    - Stock: net_return (dividends + appreciation - margin)
  - Adds CRITICAL warning in prompt about fair comparison
    (prevents judge from comparing RE.cash_flow to Stock.net_return)

v5.2 RETAINED:
  - Rich prompt with all agent v5.2 data
  - Structured detailed_explanation (6 fields)
  - 4 comparison_charts (SVG-ready specs)
"""

import logging
from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import parse_llm_json, safe_str, safe_list, call_llm_with_retry
from app.core.california_config import REGION_DATA
from app.utils.logger import log_llm_interaction

logger = logging.getLogger(__name__)

PROFILE_WEIGHTS = {
    "low": {"roi": 0.50, "stability": 0.35, "risk_penalty": 0.15},
    "medium": {"roi": 0.70, "stability": 0.20, "risk_penalty": 0.10},
    "high": {"roi": 0.85, "stability": 0.08, "risk_penalty": 0.07},
}

AGENT_COLORS = {
    "business": "#2563eb",
    "real_estate": "#16a34a",
    "stock": "#ea580c",
}

AGENT_DISPLAY_NAMES = {
    "business": "Business",
    "real_estate": "Real Estate",
    "stock": "Stocks/REIT",
}


def personalized_score(strategy: dict, profile: str) -> float:
    weights = PROFILE_WEIGHTS.get(profile, PROFILE_WEIGHTS["medium"])
    roi = strategy.get("net_return", strategy.get("real_return", 0))
    stability = strategy.get("stability", 0.5)
    risk = strategy.get("risk", 0.5)
    score = (
            roi * weights["roi"] +
            stability * weights["stability"] +
            (1 - risk) * weights["risk_penalty"]
    )
    return round(score, 4)


def _status_tier(strategy: dict) -> int:
    status = strategy.get("status", "not_profitable")
    if strategy.get("rejected"):
        return 3
    return {"profitable": 0, "marginal": 1, "not_profitable": 2}.get(status, 2)


def select_best_strategy(strategies: list, profile: str) -> dict | None:
    if not strategies:
        return None

    for s in strategies:
        s["personalized_score"] = personalized_score(s, profile)

    valid = [s for s in strategies if not s.get("rejected") and not s.get("error")]
    if not valid:
        return None

    by_tier = {0: [], 1: [], 2: []}
    for s in valid:
        tier = _status_tier(s)
        if tier in by_tier:
            by_tier[tier].append(s)

    chosen_tier = None
    for tier in (0, 1, 2):
        if by_tier[tier]:
            chosen_tier = tier
            break

    if chosen_tier is None:
        return None

    tier_strategies = sorted(
        by_tier[chosen_tier],
        key=lambda x: x["personalized_score"],
        reverse=True
    )
    chosen = tier_strategies[0]

    tier_label = {0: "profitable", 1: "marginal", 2: "not_profitable"}[chosen_tier]
    chosen["winning_tier"] = tier_label

    if chosen_tier == 1:
        chosen["tier_note"] = (
            "Selected the best MARGINAL strategy. No strategy was clearly profitable; "
            "consider adjusting your loan amounts or savings allocation to improve net returns."
        )
    elif chosen_tier == 2:
        chosen["loan_recommendation"] = "AVOID_LOAN"
        chosen["tier_note"] = (
            "⚠️ ALL strategies show NEGATIVE net returns with the current loan structure. "
            "Recommended: reduce loan amounts, increase savings allocation, "
            "or wait until financial situation improves."
        )

    return chosen


# ─────────────────────────────────
# ⭐ v5.2.1 NEW — UNIFIED COMPARABLE RETURN
# ─────────────────────────────────
def _get_y3_comparable_return(s: dict) -> tuple[float, str]:
    """
    Returns (y3_total_annual_return, explanation) for fair comparison.

    Apples-to-apples metric per agent:
      - Business: net_cash_flow (revenue - costs - loan)
      - Real Estate: total_return (cash flow + principal + appreciation)
      - Stock: net_return (dividends + appreciation - margin interest)
    """
    agent = s.get("agent", "")
    projections = s.get("projections") or {}
    y3 = projections.get("year_3", {})

    if agent == "business":
        value = y3.get("net_cash_flow", 0)
        explanation = "operating profit (revenue - costs - loan)"
    elif agent == "real_estate":
        value = y3.get("total_return", 0)
        explanation = "TOTAL RETURN (cash flow + principal + appreciation)"
    elif agent == "stock":
        value = y3.get("net_return", 0)
        explanation = "net return (dividends + appreciation - margin cost)"
    else:
        value = 0
        explanation = "unknown"

    return value, explanation


# ─────────────────────────────────
# 📝 RICH STRATEGY SUMMARY (v5.2.1)
# ─────────────────────────────────
def _format_strategy_for_prompt(s: dict) -> str:
    agent = s.get("agent", "unknown").upper()
    title = s.get("title", "N/A")
    description = s.get("description", "N/A")[:200]
    status = s.get("status", "N/A").upper()
    net_return_pct = s.get("net_return", 0) * 100
    net_return_dollars = s.get("net_return_dollars", 0)
    total_capital = s.get("total_capital", 0)

    # ⭐ v5.2.1: Unified Y3 comparable return
    y3_comparable, y3_explanation = _get_y3_comparable_return(s)
    y3_comparable_pct = (y3_comparable / total_capital * 100) if total_capital > 0 else 0

    loan_info = s.get("loan_info", {})
    loan_section = ""
    if s.get("uses_loan"):
        loan_section = (
            f"- 🏦 Loan: ${loan_info.get('amount', 0):,.0f} @ "
            f"{loan_info.get('rate', 0) * 100:.2f}% × {s.get('loan_years', 0)}yr\n"
            f"- 📉 Annual loan payment: ${s.get('annual_payment', 0):,.0f}\n"
        )

    projections = s.get("projections") or {}
    proj_section = ""
    if projections:
        if agent == "BUSINESS":
            y1 = projections.get("year_1", {})
            y3 = projections.get("year_3", {})
            y5 = projections.get("year_5", {})
            proj_section = (
                f"\n📈 5-YEAR PROJECTIONS:\n"
                f"  Year 1: revenue ${y1.get('revenue', 0):,.0f}, "
                f"net cash flow ${y1.get('net_cash_flow', 0):+,.0f}\n"
                f"  Year 3: revenue ${y3.get('revenue', 0):,.0f}, "
                f"net cash flow ${y3.get('net_cash_flow', 0):+,.0f}\n"
                f"  Year 5: revenue ${y5.get('revenue', 0):,.0f}, "
                f"net cash flow ${y5.get('net_cash_flow', 0):+,.0f}\n"
            )
        elif agent == "REAL_ESTATE":
            y1 = projections.get("year_1", {})
            y3 = projections.get("year_3", {})
            y5 = projections.get("year_5", {})
            proj_section = (
                f"\n📈 5-YEAR PROJECTIONS (REAL ESTATE):\n"
                f"  Year 1: rental ${y1.get('rental_income', 0):,.0f}, "
                f"cash flow ${y1.get('cash_flow', 0):+,.0f}, "
                f"TOTAL ${y1.get('total_return', 0):+,.0f}\n"
                f"  Year 3: cash flow ${y3.get('cash_flow', 0):+,.0f}, "
                f"appreciation ${y3.get('appreciation', 0):+,.0f}, "
                f"TOTAL ${y3.get('total_return', 0):+,.0f}\n"
                f"  Year 5: TOTAL ${y5.get('total_return', 0):+,.0f}\n"
                f"  ⚠️ NOTE: For real estate, USE 'TOTAL' for comparison, NOT 'cash flow'\n"
            )
        elif agent == "STOCK":
            y1 = projections.get("year_1", {})
            y3 = projections.get("year_3", {})
            y5 = projections.get("year_5", {})
            proj_section = (
                f"\n📈 5-YEAR PROJECTIONS (STOCK):\n"
                f"  Year 1: dividend ${y1.get('dividend_income', 0):,.0f}, "
                f"appreciation ${y1.get('price_appreciation', 0):,.0f}, "
                f"net ${y1.get('net_return', 0):+,.0f}\n"
                f"  Year 3: net ${y3.get('net_return', 0):+,.0f}\n"
                f"  Year 5: net ${y5.get('net_return', 0):+,.0f}\n"
            )

    scenarios = s.get("scenarios") or {}
    scenarios_section = ""
    if scenarios:
        best = scenarios.get("best_case", {})
        base = scenarios.get("base_case", {})
        worst = scenarios.get("worst_case", {})
        best_val = best.get("total_roi_pct", best.get("annual_return_pct", 0))
        base_val = base.get("total_roi_pct", base.get("annual_return_pct", 0))
        worst_val = worst.get("total_roi_pct", worst.get("annual_return_pct", 0))
        scenarios_section = (
            f"\n🎯 SCENARIOS:\n"
            f"  Best: +{best_val:.1f}%  |  Base: {base_val:+.1f}%  |  Worst: {worst_val:+.1f}%\n"
        )

    break_even = s.get("break_even") or {}
    be_section = ""
    if break_even:
        months = break_even.get("months_to_breakeven")
        years = break_even.get("years_to_breakeven")
        if months:
            be_section = f"\n⚖️ BREAK-EVEN: Month {months}\n"
        elif years:
            be_section = f"\n⚖️ BREAK-EVEN: Year {years} (equity > down payment)\n"

    mc = s.get("market_context") or s.get("property_market_context") or {}
    mc_section = ""
    if mc:
        if agent == "BUSINESS":
            mc_section = (
                f"\n📊 MARKET: {mc.get('industry_growth_rate_pct', 0):+.1f}%/yr growth, "
                f"competitors: {', '.join(mc.get('key_competitors', [])[:3])}\n"
            )
        elif agent == "REAL_ESTATE":
            mc_section = (
                f"\n📊 PROPERTY MARKET: median ${mc.get('median_property_value_usd', 0):,}, "
                f"rent ${mc.get('median_rent_monthly_usd', 0):,}/mo, "
                f"appreciation {mc.get('appreciation_rate_pct_5yr', 0):.1f}%/yr\n"
            )
        elif agent == "STOCK":
            mc_section = (
                f"\n📊 MARKET: regime {mc.get('market_regime', 'neutral').upper()}, "
                f"VIX {mc.get('vix_level', 18):.0f}, "
                f"CA cap gains tax {mc.get('ca_capital_gains_tax_pct', 13.3):.1f}%\n"
            )

    mcr = s.get("margin_call_risk") or {}
    mcr_section = ""
    if mcr and mcr.get("margin_call_probability", 0) > 0:
        mcr_section = (
            f"\n🚨 MARGIN CALL RISK: {mcr['margin_call_probability'] * 100:.0f}% probability, "
            f"{mcr.get('expected_severity_loss', 0) * 100:.0f}% severity\n"
        )

    calc = s.get("calculation_breakdown") or {}
    calc_section = ""
    if calc and calc.get("summary"):
        summary = calc["summary"]
        if "nominal_return_pct" in summary and "real_return_pct" in summary:
            calc_section = (
                f"\n🧮 CALC: nominal {summary.get('nominal_return_pct', 0):+.2f}% → "
                f"real (after inflation) {summary.get('real_return_pct', 0):+.2f}%"
            )

    # ⭐ v5.2.1: Highlighted unified comparable metric
    comparable_section = (
        f"\n⭐ Y3 COMPARABLE RETURN: ${y3_comparable:+,.0f} "
        f"({y3_comparable_pct:+.2f}% of capital) "
        f"[= {y3_explanation}]"
    )

    return f"""
{agent}:
- Title: {title}
- Description: {description}
- Status: {status}  |  Real return: {s.get('real_return', 0) * 100:.2f}%
- 💰 Total capital: ${total_capital:,.0f}
{loan_section}- 🎯 NET annual return (after loan + inflation): ${net_return_dollars:,.0f}/yr ({net_return_pct:+.2f}%)
{comparable_section}
- Risk: {s.get('risk', 0.5):.2f}, Stability: {s.get('stability', 0.5):.2f}
- Personalized score: {s.get('personalized_score', 0)}
{proj_section}{scenarios_section}{be_section}{mc_section}{mcr_section}{calc_section}
"""


# ─────────────────────────────────
# 📝 v5.2.1 EXPLANATION PROMPT
# ─────────────────────────────────
def build_explanation_prompt(user, loan: dict, all_strategies: list, chosen: dict) -> str:
    strategies_text = "\n".join(_format_strategy_for_prompt(s) for s in all_strategies)

    interests_text = (
        ", ".join(user.professional.interests)
        if user.professional.interests
        else "Not specified"
    )

    region = user.location.region
    region_data = REGION_DATA[region]
    chosen_net_return_pct = chosen.get("net_return", 0) * 100
    chosen_net_return_usd = chosen.get("net_return_dollars", 0)
    winning_tier = chosen.get("winning_tier", "unknown")

    if winning_tier == "profitable":
        tier_instruction = (
            "The chosen strategy is PROFITABLE. Explain why it's the best of profitable options."
        )
    elif winning_tier == "marginal":
        tier_instruction = (
            "The chosen strategy is MARGINAL. Be HONEST: no strategy is clearly profitable, "
            "but this one is the safest bet. Suggest user reconsider loan amounts."
        )
    else:
        tier_instruction = (
            "⚠️ NO strategy is profitable with current loan structure. "
            "Be DIRECT: STRONGLY recommend user reduce loans or wait."
        )

    return f"""
You are a senior California financial advisor providing a DETAILED, HONEST recommendation.

USER PROFILE:
- Age: {user.personal.age}  |  Region: {region_data['display_name']}, California
- City: {user.location.city}  |  Profession: {user.professional.profession}
- Sector: {user.professional.sector.value}  |  Interests: {interests_text}
- Weekly hours: {user.professional.weekly_hours.value}
- Monthly income: ${user.financial.income}  |  Savings: ${user.financial.savings}
- Risk tolerance: {user.preferences.risk_profile.value}  |  Horizon: {user.preferences.horizon.value}

🌴 CALIFORNIA CONTEXT:
- State tax up to 13.3%  |  Prop 13 (real estate)  |  QSBS (tech equity)
- Capital gains: highest in nation (no LT preferential rate)
- Region: {region_data['display_name']} — industries: {', '.join(region_data['primary_industries'])}

═══════════════════════════════════════════════════════════════
⭐ CRITICAL — FAIR COMPARISON RULE:
═══════════════════════════════════════════════════════════════
When comparing strategies, USE THE "⭐ Y3 COMPARABLE RETURN" METRIC SHOWN BELOW.
This is the apples-to-apples annual value generated by each strategy:
  - Business: operating profit (revenue - costs - loan)
  - Real Estate: TOTAL return (cash + equity + appreciation)  ← INCLUDES APPRECIATION
  - Stock: net return (dividends + appreciation - margin)

⚠️ DO NOT compare Real Estate's "cash flow" to Stock's "net return" — that's apples-to-oranges.
Real Estate's cash flow alone DOES NOT include equity buildup or appreciation, which
make up most of real estate returns. Always use the ⭐ COMPARABLE RETURN.

When stating winner, ALWAYS reference the ⭐ Y3 COMPARABLE RETURN in dollar amounts.
═══════════════════════════════════════════════════════════════

ALL STRATEGIES (with v5.2 data — projections, scenarios, market):
═══════════════════════════════════════════════════════════════
{strategies_text}

═══════════════════════════════════════════════════════════════
🏆 CHOSEN: {chosen['agent']} — {chosen.get('title')}
- 🎯 NET return: {chosen_net_return_pct:+.2f}% (${chosen_net_return_usd:,.0f}/year)
- Status: {chosen.get('status', 'N/A').upper()}  |  Winning tier: {winning_tier.upper()}
═══════════════════════════════════════════════════════════════

⚠️ TIER CONTEXT:
{tier_instruction}

YOUR TASK — Generate STRUCTURED detailed explanation (JSON):

{{
  "headline": "ONE sentence: why this strategy wins (use $$ amounts from ⭐ COMPARABLE RETURN)",

  "why_chosen": "3-4 sentences explaining specifically WHY this strategy beats alternatives. Reference its Y3 COMPARABLE RETURN in dollars. Use concrete numbers.",

  "comparative_analysis": "3-4 sentences DIRECTLY comparing to OTHER strategies using ⭐ Y3 COMPARABLE RETURN. Example: 'Real Estate generates $22,652/yr Y3 vs Stock $8,158/yr vs Business $7,454/yr — RE wins on absolute return because of equity buildup and appreciation.'",

  "risk_analysis": "2-3 sentences on worst-case scenarios. Reference scenarios.worst_case. Mention CA risks (earthquake/wildfire for RE; CA tax for stock; market saturation for business).",

  "california_angle": "2 sentences on CA-specific advantages relevant to chosen strategy: Prop 13 for RE, CA capital gains for stock, LLC tax for business.",

  "action_plan": [
    "STEP 1: Specific first action",
    "STEP 2: Concrete second action",
    "STEP 3: 90-day milestone"
  ],

  "reasoning": "Summary 5-7 sentences (backwards compat)",
  "next_step": "ONE concrete next action (backwards compat)",
  "comparison": "Short summary using ⭐ Y3 COMPARABLE RETURN (backwards compat)"
}}

⚠️ RULES:
- ALWAYS use ⭐ Y3 COMPARABLE RETURN values when comparing
- For RE, mention TOTAL return (cash + equity + appreciation), not just cash flow
- Use CONCRETE $$ amounts, not vague language
- If tier is marginal/not_profitable, BE HONEST — recommend reducing loan
- California-specific advice MUST be relevant to chosen strategy
- action_plan: each step ACTIONABLE within 90 days
- Return ONLY valid JSON, no markdown fences
"""


# ─────────────────────────────────
# ⭐ v5.2 — COMPARISON CHARTS
# ─────────────────────────────────
def build_comparison_charts(strategies: list) -> dict:
    valid = [s for s in strategies if not s.get("rejected") and not s.get("error")]

    if not valid:
        return {
            "return_chart": None,
            "cashflow_chart": None,
            "risk_chart": None,
            "timeline_chart": None,
        }

    return_chart = {
        "type": "bar",
        "title": "Net Annual Return Comparison",
        "subtitle": "After inflation and loan amortization",
        "y_axis_label": "Net Return (%)",
        "data": [
            {
                "label": AGENT_DISPLAY_NAMES.get(s["agent"], s["agent"]),
                "value": round(s.get("net_return", 0) * 100, 2),
                "color": AGENT_COLORS.get(s["agent"], "#888"),
                "formatted": f"{s.get('net_return', 0) * 100:+.2f}%",
                "absolute_usd": s.get("net_return_dollars", 0),
            }
            for s in valid
        ],
    }

    cashflow_series = []
    for s in valid:
        projections = s.get("projections") or {}
        if not projections:
            continue

        if s["agent"] == "business":
            y1 = projections.get("year_1", {}).get("net_cash_flow", 0)
            y3 = projections.get("year_3", {}).get("net_cash_flow", 0)
            y5 = projections.get("year_5", {}).get("net_cash_flow", 0)
        elif s["agent"] == "real_estate":
            y1 = projections.get("year_1", {}).get("total_return", 0)
            y3 = projections.get("year_3", {}).get("total_return", 0)
            y5 = projections.get("year_5", {}).get("total_return", 0)
        elif s["agent"] == "stock":
            y1 = projections.get("year_1", {}).get("net_return", 0)
            y3 = projections.get("year_3", {}).get("net_return", 0)
            y5 = projections.get("year_5", {}).get("net_return", 0)
        else:
            continue

        cashflow_series.append({
            "name": AGENT_DISPLAY_NAMES.get(s["agent"], s["agent"]),
            "color": AGENT_COLORS.get(s["agent"], "#888"),
            "data": [round(y1, 2), round(y3, 2), round(y5, 2)],
            "formatted": [f"${y1:+,.0f}", f"${y3:+,.0f}", f"${y5:+,.0f}"],
        })

    cashflow_chart = {
        "type": "line",
        "title": "5-Year Comparable Return Projection",
        "subtitle": "Apples-to-apples Y1/Y3/Y5 (RE uses TOTAL return)",
        "x_axis_label": "Year",
        "y_axis_label": "Annual Return ($)",
        "categories": ["Year 1", "Year 3", "Year 5"],
        "series": cashflow_series,
    } if cashflow_series else None

    risk_chart = {
        "type": "scatter",
        "title": "Risk vs Stability Profile",
        "subtitle": "Lower-left = ideal (low risk, high stability)",
        "x_axis_label": "Risk Level",
        "y_axis_label": "Stability",
        "data": [
            {
                "label": AGENT_DISPLAY_NAMES.get(s["agent"], s["agent"]),
                "x": round(s.get("risk", 0.5) * 100, 1),
                "y": round(s.get("stability", 0.5) * 100, 1),
                "color": AGENT_COLORS.get(s["agent"], "#888"),
                "size": max(8, min(20, abs(s.get("net_return", 0)) * 200)),
            }
            for s in valid
        ],
    }

    timeline_data = []
    for s in valid:
        break_even = s.get("break_even") or {}
        if "months_to_breakeven" in break_even and break_even["months_to_breakeven"]:
            months = break_even["months_to_breakeven"]
            label_suffix = f"{months} months"
        elif "years_to_breakeven" in break_even and break_even["years_to_breakeven"]:
            months = break_even["years_to_breakeven"] * 12
            label_suffix = f"{break_even['years_to_breakeven']} years"
        else:
            months = break_even.get("months_to_breakeven", 12)
            label_suffix = f"{months} months"

        timeline_data.append({
            "label": AGENT_DISPLAY_NAMES.get(s["agent"], s["agent"]),
            "value": months,
            "color": AGENT_COLORS.get(s["agent"], "#888"),
            "formatted": label_suffix,
        })

    timeline_data.sort(key=lambda x: x["value"])

    timeline_chart = {
        "type": "horizontal_bar",
        "title": "Time to Break-Even",
        "subtitle": "Shorter is better (faster to recoup capital)",
        "x_axis_label": "Months",
        "data": timeline_data,
    }

    return {
        "return_chart": return_chart,
        "cashflow_chart": cashflow_chart,
        "risk_chart": risk_chart,
        "timeline_chart": timeline_chart,
    }


# ─────────────────────────────────
# 🤖 GENERATE EXPLANATION (v5.2.1)
# ─────────────────────────────────
async def generate_explanation(
    user,
    loan: dict,
    all_strategies: list,
    chosen: dict
) -> dict:

    prompt = build_explanation_prompt(
        user,
        loan,
        all_strategies,
        chosen
    )

    agent_name = "judge"

    try:
        # 🤖 LLM call
        data = await call_llm_with_retry(
            llm_call=lambda: call_llm(prompt),
            agent_name=agent_name
        )

        # 📝 success logging
        log_llm_interaction(
            agent=agent_name,
            prompt=prompt,
            raw_response=str(data),
            parsed_response=data,
            success=True
        )

        return {
            "headline": safe_str(data.get("headline"))[:200],
            "why_chosen": safe_str(data.get("why_chosen"))[:600],
            "comparative_analysis": safe_str(data.get("comparative_analysis"))[:600],
            "risk_analysis": safe_str(data.get("risk_analysis"))[:400],
            "california_angle": safe_str(data.get("california_angle"))[:300],
            "action_plan": safe_list(data.get("action_plan"), [])[:3],
            "reasoning": safe_str(data.get("reasoning")),
            "next_step": safe_str(data.get("next_step")),
            "comparison": safe_str(data.get("comparison")),
        }

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

        logger.error(f"Judge LLM failed after retries, using fallback: {e}")

        region = user.location.region
        region_name = REGION_DATA[region]["display_name"]
        net_return_pct = chosen.get('net_return', 0) * 100
        winning_tier = chosen.get("winning_tier", "unknown")
        agent_name = chosen.get("agent", "unknown")
        display_name = AGENT_DISPLAY_NAMES.get(agent_name, agent_name)

        # Comparable return for chosen
        chosen_y3_comparable, _ = _get_y3_comparable_return(chosen)

        if winning_tier == "profitable":

            headline = (
                f"{display_name} is profitable with "
                f"${chosen_y3_comparable:+,.0f} Y3 comparable return."
            )

            why_chosen = (
                f"This {agent_name} strategy in {region_name} "
                f"delivers consistent positive returns. "
                f"It outperforms other available strategies "
                f"on the comparable return metric."
            )

        elif winning_tier == "marginal":

            headline = (
                f"{display_name} is marginal at "
                f"{net_return_pct:+.2f}% — best available option."
            )

            why_chosen = (
                f"All strategies show only marginal returns "
                f"with your current loan structure. "
                f"Consider reducing loan amounts to improve returns."
            )

        else:

            headline = (
                f"⚠️ All strategies unprofitable. "
                f"{display_name} loses the least."
            )

            why_chosen = (
                f"With your current configuration, "
                f"ALL strategies are unprofitable. "
                f"STRONGLY recommend reducing loan amounts "
                f"before proceeding."
            )

        comparative = ""

        for s in all_strategies:

            if s.get("rejected") or s.get("agent") == agent_name:
                continue

            other_y3, _ = _get_y3_comparable_return(s)

            other_name = AGENT_DISPLAY_NAMES.get(
                s.get("agent"),
                s.get("agent")
            )

            comparative += (
                f"{other_name}: "
                f"${other_y3:+,.0f} Y3 comparable. "
            )

        return {
            "headline": headline,

            "why_chosen": why_chosen,

            "comparative_analysis": (
                f"Compared to other strategies: {comparative}"
                if comparative
                else "Other strategies were rejected or had similar returns."
            ),

            "risk_analysis": (
                f"Worst-case scenario shows potential downside. "
                f"Risk: {chosen.get('risk', 0.5):.2f}, "
                f"Stability: {chosen.get('stability', 0.5):.2f}."
            ),

            "california_angle": (
                f"California-specific factors apply: "
                f"state tax up to 13.3%, "
                f"region-specific factors for {region_name}."
            ),

            "action_plan": (
                chosen.get("next_steps", [])[:3]
                or [
                    "Reduce loan amount",
                    "Re-run analysis",
                    "Consult advisor"
                ]
            ),

            "reasoning": why_chosen,

            "next_step": (
                chosen.get(
                    'next_steps',
                    ['Reduce loan amount and re-run analysis.']
                )[0]
                if chosen.get('next_steps')
                else "Reduce loan amount and re-run analysis."
            ),

            "comparison": "Strategies ranked by tier, then score.",

            "llm_error": str(e)
        }
# ─────────────────────────────────
# 🚀 MAIN (v5.2.1)
# ─────────────────────────────────
async def run_judge_agent(user, loan: dict, strategies: list) -> dict:
    profile = user.preferences.risk_profile.value

    chosen = select_best_strategy(strategies, profile)

    if chosen is None:
        return {
            "recommended": None,
            "reasoning": "No valid strategies available — all were rejected.",
            "next_step": "Adjust your configuration and re-run the analysis.",
            "comparison": "",
            "profile_used": profile,
            "detailed_explanation": None,
            "comparison_charts": build_comparison_charts(strategies),
        }

    explanation = await generate_explanation(user, loan, strategies, chosen)
    charts = build_comparison_charts(strategies)

    return {
        "recommended": chosen,
        "reasoning": explanation["reasoning"],
        "next_step": explanation["next_step"],
        "comparison": explanation["comparison"],
        "profile_used": profile,
        "detailed_explanation": {
            "headline": explanation["headline"],
            "why_chosen": explanation["why_chosen"],
            "comparative_analysis": explanation["comparative_analysis"],
            "risk_analysis": explanation["risk_analysis"],
            "california_angle": explanation["california_angle"],
            "action_plan": explanation["action_plan"],
        },
        "comparison_charts": charts,
        **({"llm_error": explanation["llm_error"]} if "llm_error" in explanation else {})
    }
