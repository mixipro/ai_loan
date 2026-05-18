# app/agents/judge_agent.py

import logging
from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import parse_llm_json, safe_str, call_llm_with_retry
from app.core.california_config import REGION_DATA

logger = logging.getLogger(__name__)

PROFILE_WEIGHTS = {
    "low": {"roi": 0.2, "stability": 0.6, "risk_penalty": 0.2},
    "medium": {"roi": 0.5, "stability": 0.3, "risk_penalty": 0.2},
    "high": {"roi": 0.7, "stability": 0.1, "risk_penalty": 0.2},
}


def personalized_score(strategy: dict, profile: str) -> float:
    """
    Score based on NET return (after loan amortization), not just real return.
    """
    weights = PROFILE_WEIGHTS.get(profile, PROFILE_WEIGHTS["medium"])

    # ⭐ Use net_return (after loan payments) instead of real_return
    roi = strategy.get("net_return", strategy.get("real_return", 0))
    stability = strategy.get("stability", 0.5)
    risk = strategy.get("risk", 0.5)

    score = (
            roi * weights["roi"] +
            stability * weights["stability"] +
            (1 - risk) * weights["risk_penalty"]
    )

    return round(score, 4)


def select_best_strategy(strategies, profile):
    if not strategies:
        return None

    # Filter to profitable strategies first
    profitable = [s for s in strategies if s.get("status") == "profitable"]

    if not profitable:
        # All strategies unprofitable — recommend best of bad options
        all_with_score = strategies.copy()
        for s in all_with_score:
            s["personalized_score"] = personalized_score(s, profile)
        ranked = sorted(all_with_score, key=lambda x: x["personalized_score"], reverse=True)
        chosen = ranked[0]
        chosen["loan_recommendation"] = "AVOID_LOAN"
        chosen["warning"] = (
            "No strategy is profitable with the current loan structure. "
            "Consider investing only with savings (no loan) or accumulating more capital first."
        )
        return chosen

    for s in profitable:
        s["personalized_score"] = personalized_score(s, profile)

    ranked = sorted(profitable, key=lambda x: x["personalized_score"], reverse=True)
    return ranked[0]


def build_explanation_prompt(user, loan: dict, all_strategies: list, chosen: dict) -> str:
    """
    California-aware explanation prompt with NET RETURN focus.
    """

    # Build strategy summaries with REAL amortization details
    strategies_text = ""
    for s in all_strategies:
        loan_info = s.get("loan_info", {})
        margin_risk = s.get("margin_call_risk")

        strategies_text += f"""
{s['agent'].upper()}:
- Title: {s.get('title', 'N/A')}
- Description: {s.get('description', 'N/A')[:200]}
- Nominal return: {s.get('nominal_return', s.get('expected_return', 0)) * 100:.2f}%
- Real return (after inflation): {s.get('real_return', 0) * 100:.2f}%
- 💰 Total capital deployed: ${s.get('total_capital', 0):,.0f}
- 🏦 Loan type: {loan_info.get('type', 'N/A')} (${loan_info.get('amount', 0):,.0f} @ {loan_info.get('rate', 0) * 100:.2f}%)
- 📉 Annual loan payment: ${s.get('annual_payment', 0):,.0f}
- 💵 Gross annual return ($): ${s.get('gross_return_dollars', 0):,.0f}
- 🎯 NET annual return ($): ${s.get('net_return_dollars', 0):,.0f}/yr
- 🎯 NET return (%): {s.get('net_return', 0) * 100:.2f}%
- Risk: {s.get('risk', 0.5)}, Stability: {s.get('stability', 0.5)}
- Status: {s.get('status', 'N/A')}
- Pros: {', '.join(s.get('pros', []))}
- Cons: {', '.join(s.get('cons', []))}
"""
        if margin_risk:
            strategies_text += f"""- 🚨 MARGIN CALL RISK: {margin_risk['margin_call_probability'] * 100:.1f}% probability, {margin_risk['expected_severity_loss'] * 100:.1f}% severity
"""

    interests_text = (
        ", ".join(user.professional.interests)
        if user.professional.interests
        else "Not specified"
    )

    region = user.location.region
    region_data = REGION_DATA[region]

    # Chosen strategy details
    chosen_loan = chosen.get("loan_info", {})
    chosen_net_return_pct = chosen.get("net_return", 0) * 100
    chosen_net_return_usd = chosen.get("net_return_dollars", 0)

    return f"""
You are a senior California financial advisor. Explain why this specific strategy 
fits the user's California profile, using natural and persuasive language.

USER PROFILE:
- Age: {user.personal.age}
- Region: {region_data['display_name']} (California, USA)
- City: {user.location.city}
- Profession: {user.professional.profession.value}
- Sector: {user.professional.sector.value}
- Interests: {interests_text}
- Weekly hours available: {user.professional.weekly_hours.value}
- Monthly income: ${user.financial.income} USD
- Savings: ${user.financial.savings}
- Cost of living: {region_data['cost_of_living_index']}x national avg
- Investment risk tolerance: {user.preferences.risk_profile.value}
- Investment horizon: {user.preferences.horizon.value} years

⚠️ IMPORTANT CONCEPT:
"Investment risk tolerance" (user's preference for portfolio risk) and 
"creditworthiness" (bank-side rating affecting loan terms) are EVALUATED INDEPENDENTLY.

🌴 CALIFORNIA CONTEXT TO LEVERAGE:
- California state tax: progressive up to 13.3%
- Prop 13 benefit for real estate buyers (locked-in property tax)
- QSBS exclusion potential for tech equity (up to $10M tax-free)
- California muni bonds: DOUBLE tax-free (federal + state)
- Region: {region_data['display_name']} — strong industries: {', '.join(region_data['primary_industries'])}

🏦 MULTI-LOAN CONTEXT:
This system evaluates strategies with DIFFERENT loan types:
- BUSINESS loan: ~7%, 7yr term (for business strategies)
- MORTGAGE: ~5.5%, 30yr term (for real estate — much better terms!)
- MARGIN loan: ~8%, callable (for leveraged stock — RISKY)
- CASH only: No loan (for conservative stock investing)

Each strategy's NET return accounts for its SPECIFIC loan amortization (not just interest rate).

ALL STRATEGIES EVALUATED:
{strategies_text}

CHOSEN STRATEGY: {chosen['agent']}
- Title: {chosen.get('title')}
- 🎯 NET return: {chosen_net_return_pct:.2f}% (${chosen_net_return_usd:,.0f}/year)
- Personalized score: {chosen.get('personalized_score', chosen.get('score', 0))}
- Loan: {chosen_loan.get('type', 'N/A')} (${chosen_loan.get('amount', 0):,.0f})

YOUR TASK:
Write a personalized recommendation in 5-7 sentences explaining:
1. Why "{chosen.get('title')}" matches user's investment risk tolerance ({user.preferences.risk_profile.value})
2. Why it suits investment horizon ({user.preferences.horizon.value} years)
3. How it fits {region_data['display_name']} dynamics + interests ({interests_text})
4. Why preferred over alternatives — COMPARE USING NET RETURN (the real $$ they'll make/lose)
   Example: "Stock cash gives +5.2% net vs business -3.8% net after loan amortization"
5. California-specific advantage (Prop 13 / QSBS / muni bonds — whichever relevant)
6. First concrete step this week

⚠️ CRITICAL: When comparing strategies, use NET return (after loan amortization), 
NOT nominal return. A 20% nominal return that requires $50k/yr loan payment 
on $300k capital is WORSE than a 8% cash return on $80k.

Write in second person ("you should..."). Be specific, not generic.

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- reasoning: 5-7 sentences, persuasive and California-aware
- next_step: ONE concrete action
- comparison: short summary using NET returns

FORMAT:
{{
  "reasoning": "...",
  "next_step": "...",
  "comparison": "..."
}}
"""


async def generate_explanation(user, loan: dict, all_strategies: list, chosen: dict) -> dict:
    prompt = build_explanation_prompt(user, loan, all_strategies, chosen)

    try:
        data = await call_llm_with_retry(
            llm_call=lambda: call_llm(prompt),
            agent_name="judge"
        )

        return {
            "reasoning": safe_str(data.get("reasoning")),
            "next_step": safe_str(data.get("next_step")),
            "comparison": safe_str(data.get("comparison"))
        }

    except Exception as e:
        logger.error(f"Judge LLM failed after retries, using fallback: {e}")

        from app.core.california_config import REGION_DATA
        region = user.location.region
        region_name = REGION_DATA[region]["display_name"]

        net_return_pct = chosen.get('net_return', 0) * 100

        return {
            "reasoning": (
                f"Based on your {user.preferences.risk_profile.value} investment risk tolerance "
                f"and {user.preferences.horizon.value} year horizon in {region_name}, "
                f"the {chosen['agent']} strategy ('{chosen.get('title', 'N/A')}') "
                f"offers the best NET return ({net_return_pct:.2f}% after loan payments) "
                f"for your California profile."
            ),
            "next_step": (
                chosen.get('next_steps', ['Research this strategy further.'])[0]
                if chosen.get('next_steps') else
                f"Consider allocating capital to the {chosen['agent']} strategy."
            ),
            "comparison": "Other strategies were evaluated but ranked lower based on net returns after loan amortization.",
            "llm_error": str(e)
        }


async def run_judge_agent(user, loan: dict, strategies: list) -> dict:
    profile = user.preferences.risk_profile.value

    chosen = select_best_strategy(strategies, profile)

    if chosen is None:
        return {
            "recommended": None,
            "reasoning": "No valid strategies available.",
            "next_step": "Improve financial profile and try again.",
            "comparison": "",
            "profile_used": profile,
        }

    explanation = await generate_explanation(user, loan, strategies, chosen)

    return {
        "recommended": chosen,
        "reasoning": explanation["reasoning"],
        "next_step": explanation["next_step"],
        "comparison": explanation["comparison"],
        "profile_used": profile,
        **({"llm_error": explanation["llm_error"]} if "llm_error" in explanation else {})
    }
