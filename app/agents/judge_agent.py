# app/agents/judge_agent.py

import logging
from app.services.llm_service import call_llm_text as call_llm
from app.agents._common import parse_llm_json, safe_str, call_llm_with_retry

logger = logging.getLogger(__name__)


# ─────────────────────────
# 🎯 PROFILE WEIGHTS
# ─────────────────────────
PROFILE_WEIGHTS = {
    "low": {
        "roi": 0.2,
        "stability": 0.6,
        "risk_penalty": 0.2
    },
    "medium": {
        "roi": 0.5,
        "stability": 0.3,
        "risk_penalty": 0.2
    },
    "high": {
        "roi": 0.7,
        "stability": 0.1,
        "risk_penalty": 0.2
    }
}


def personalized_score(strategy: dict, profile: str) -> float:
    weights = PROFILE_WEIGHTS.get(profile, PROFILE_WEIGHTS["medium"])

    roi = strategy["real_return"]
    stability = strategy["stability"]
    risk = strategy["risk"]

    score = (
            roi * weights["roi"] +
            stability * weights["stability"] +
            (1 - risk) * weights["risk_penalty"]
    )

    return round(score, 4)


def select_best_strategy(strategies, profile):
    if not strategies:
        return None

    profitable = [s for s in strategies if s.get("status") == "profitable"]

    if not profitable:
        # ⚠️ NIJEDNA NIJE PROFITABILNA SA KREDITOM
        all_with_score = strategies.copy()
        for s in all_with_score:
            s["personalized_score"] = personalized_score(s, profile)
        ranked = sorted(all_with_score, key=lambda x: x["personalized_score"], reverse=True)
        chosen = ranked[0]
        chosen["loan_recommendation"] = "AVOID_LOAN"
        chosen["warning"] = (
            "No strategy is profitable with the current loan. "
            "Consider investing only with savings (without loan)."
        )
        return chosen

    # ✅ NORMALAN SLUČAJ — ima profitabilnih strategija
    for s in profitable:
        s["personalized_score"] = personalized_score(s, profile)

    ranked = sorted(profitable, key=lambda x: x["personalized_score"], reverse=True)
    return ranked[0]


def build_explanation_prompt(user, loan: dict, all_strategies: list, chosen: dict) -> str:
    """
    Bogatiji prompt — koristi nova polja iz agenata + nove user kontekste.
    Naglašava razdvajanje 'investment risk' od 'creditworthiness'.
    """
    strategies_text = ""
    for s in all_strategies:
        strategies_text += f"""
{s['agent'].upper()}:
- Title: {s.get('title', 'N/A')}
- Description: {s.get('description', 'N/A')}
- Real return: {s['real_return'] * 100:.2f}%
- Net return (after loan interest): {s.get('net_return', 0) * 100:.2f}%
- Risk: {s['risk']}, Stability: {s['stability']}
- Status: {s.get('status', 'N/A')}
- Pros: {', '.join(s.get('pros', []))}
- Cons: {', '.join(s.get('cons', []))}
"""

    interests_text = (
        ", ".join(user.professional.interests)
        if user.professional.interests
        else "Not specified"
    )

    return f"""
You are a senior financial advisor. Explain to the user WHY this specific strategy 
is the best fit for their profile, using natural and persuasive language.

USER PROFILE:
- Age: {user.personal.age}
- Country: {user.location.country.value}
- Profession: {user.professional.profession.value}
- Interests: {interests_text}
- Weekly hours available: {user.professional.weekly_hours.value}
- Monthly income: {user.financial.income} {user.financial.currency.value}
- Savings: {user.financial.savings}
- Investment risk tolerance: {user.preferences.risk_profile.value} (user's PREFERENCE for portfolio risk)
- Investment horizon: {user.preferences.horizon.value} years

⚠️ IMPORTANT CONCEPT:
"Investment risk tolerance" (user's preference for portfolio risk) and 
"creditworthiness" (bank-side rating affecting loan terms) are EVALUATED INDEPENDENTLY.
A user can be highly creditworthy (good loan terms) while preferring conservative investments.
Always honor the user's stated risk tolerance for investment selection.
DO NOT confuse these two dimensions in your reasoning.

LOAN CONDITIONS:
- Approved: {loan.get("approved")}
- Max loan: {loan.get("max_loan_amount")}
- Interest rate: {loan.get("interest_rate")}

ALL STRATEGIES EVALUATED:
{strategies_text}

CHOSEN STRATEGY: {chosen['agent']}
- Title: {chosen.get('title')}
- Personalized score: {chosen.get('personalized_score', chosen['score'])}

YOUR TASK:
Write a personalized recommendation in 5-7 sentences explaining:
1. Why "{chosen.get('title')}" matches user's INVESTMENT risk tolerance ({user.preferences.risk_profile.value})
2. Why it suits investment horizon ({user.preferences.horizon.value} years)
3. How it fits weekly hours availability ({user.professional.weekly_hours.value}) and interests ({interests_text})
4. Specifically why it was preferred over the other 2 strategies (compare directly using net_return)
5. What the user should expect financially in concrete numbers (use NET return after loan interest)
6. The first concrete step they should take this week

Write in second person ("you should...", "your profile..."). Be specific, not generic.

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- reasoning: 5-7 sentences, persuasive and specific
- next_step: ONE concrete action (not a list)
- comparison: short comparison summary (1-2 sentences explaining trade-offs)
- Use NET return (after loan interest) when discussing real profitability

FORMAT:
{{
  "reasoning": "...",
  "next_step": "...",
  "comparison": "..."
}}
"""


async def generate_explanation(user, loan: dict, all_strategies: list, chosen: dict) -> dict:
    """
    Generiše LLM eksplanaciju sa retry-jem.
    Ako svi pokušaji propadnu → vraća fallback eksplanaciju.
    """
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

        return {
            "reasoning": (
                f"Based on your {user.preferences.risk_profile.value} investment risk tolerance "
                f"and {user.preferences.horizon.value} year horizon, "
                f"the {chosen['agent']} strategy ('{chosen.get('title', 'N/A')}') "
                f"offers the best balance of return ({chosen['real_return'] * 100:.1f}%) "
                f"and stability ({chosen['stability'] * 100:.0f}%). "
                f"This was preferred over alternatives because of your profile weighting."
            ),
            "next_step": (
                chosen.get('next_steps', ['Research this strategy further.'])[0]
                if chosen.get('next_steps') else
                f"Consider allocating capital to the {chosen['agent']} strategy."
            ),
            "comparison": "Other strategies were viable but ranked lower for your profile.",
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