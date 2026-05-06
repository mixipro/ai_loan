# app/agents/judge_agent.py

from app.services.llm_service import call_llm
from app.agents._common import parse_llm_json, safe_str


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


def select_best_strategy(strategies: list, profile: str) -> dict:
    if not strategies:
        return None

    profitable = [s for s in strategies if s.get("status") == "profitable"]
    candidates = profitable if profitable else strategies

    for s in candidates:
        s["personalized_score"] = personalized_score(s, profile)

    ranked = sorted(candidates, key=lambda x: x["personalized_score"], reverse=True)
    return ranked[0]


def build_explanation_prompt(user, loan: dict, all_strategies: list, chosen: dict) -> str:
    """
    Bogatiji prompt — koristi nova polja iz agenata (title, description, pros/cons, allocation).
    """
    # Detaljno opiši sve strategije sa novim poljima
    strategies_text = ""
    for s in all_strategies:
        strategies_text += f"""
{s['agent'].upper()}:
- Title: {s.get('title', 'N/A')}
- Description: {s.get('description', 'N/A')}
- Real return: {s['real_return']*100:.2f}%
- Risk: {s['risk']}, Stability: {s['stability']}
- Status: {s.get('status', 'N/A')}
- Pros: {', '.join(s.get('pros', []))}
- Cons: {', '.join(s.get('cons', []))}
"""

    return f"""
You are a senior financial advisor. Explain to the user WHY this specific strategy 
is the best fit for their profile, using natural and persuasive language.

USER PROFILE:
- Age: {user.personal.age}
- Country: {user.location.country.value}
- Profession: {user.professional.profession.value}
- Monthly income: {user.financial.income} {user.financial.currency.value}
- Savings: {user.financial.savings}
- Risk tolerance: {user.preferences.risk_profile.value}
- Investment horizon: {user.preferences.horizon.value} years

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
1. Why "{chosen.get('title')}" matches user's risk tolerance ({user.preferences.risk_profile.value})
2. Why it suits investment horizon ({user.preferences.horizon.value} years)
3. Specifically why it was preferred over the other 2 strategies (compare directly)
4. What the user should expect financially in concrete numbers
5. The first concrete step they should take this week

Write in second person ("you should...", "your profile..."). Be specific, not generic.

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- reasoning: 5-7 sentences, persuasive and specific
- next_step: ONE concrete action (not a list)
- comparison: short comparison summary (1-2 sentences explaining trade-offs)

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
        raw = await call_llm(prompt)
        data = parse_llm_json(raw)
        return {
            "reasoning": safe_str(data.get("reasoning")),
            "next_step": safe_str(data.get("next_step")),
            "comparison": safe_str(data.get("comparison"))
        }
    except Exception as e:
        # 🛡️ FALLBACK — bogatiji nego pre
        return {
            "reasoning": (
                f"Based on your {user.preferences.risk_profile.value} risk tolerance "
                f"and {user.preferences.horizon.value} year horizon, "
                f"the {chosen['agent']} strategy ('{chosen.get('title', 'N/A')}') "
                f"offers the best balance of return ({chosen['real_return']*100:.1f}%) "
                f"and stability ({chosen['stability']*100:.0f}%). "
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
        }

    explanation = await generate_explanation(user, loan, strategies, chosen)

    return {
        "recommended": chosen,
        "reasoning": explanation["reasoning"],
        "next_step": explanation["next_step"],
        "comparison": explanation["comparison"],   # ⭐ NOVO
        "profile_used": profile,
        **({"llm_error": explanation["llm_error"]} if "llm_error" in explanation else {})
    }