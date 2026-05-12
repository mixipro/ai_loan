# app/agents/stock_agent.py

from app.agents._common import (
    parse_llm_json, clamp, safe_list, safe_str, safe_dict,
    call_llm_with_tools
)
from app.agents._tools import STOCK_TOOLS
from app.core.california_config import REGION_DATA

HOURS_STOCK_DESCRIPTIONS = {
    "0-5": "Less than 5h/week (PASSIVE — set-and-forget ETFs only)",
    "5-15": "5-15h/week (LIGHT — quarterly rebalancing, mostly passive)",
    "15-30": "15-30h/week (MODERATE — monthly review, some sector rotation)",
    "30+": "30+h/week (HEAVY — active monitoring, advanced strategies)"
}


def build_prompt(user, loan: dict) -> str:
    total_capital = user.financial.savings

    if loan.get("approved"):
        total_capital += loan.get("max_loan_amount", 0)

    hours_desc = HOURS_STOCK_DESCRIPTIONS.get(
        user.professional.weekly_hours.value,
        "Unknown availability"
    )

    # ⭐ California context
    region_data = REGION_DATA[user.location.region]

    # Check for QSBS opportunity (tech equity)
    qsbs_note = ""
    if user.professional.equity_compensation:
        from app.models.user import EquityCompensation
        if user.professional.equity_compensation in (
                EquityCompensation.ISO,
                EquityCompensation.FOUNDER_STOCK,
                EquityCompensation.MIXED,
        ):
            qsbs_note = (
                "\n⚠️ USER HAS EQUITY COMPENSATION — they may qualify for QSBS "
                "(Section 1202) exclusion: up to $10M federal+state tax-free on startup exit. "
                "Consider mentioning portfolio diversification away from employer stock."
            )

    return f"""
You are a senior California-aware portfolio manager and stock market strategist.

USER PROFILE:
- Age: {user.personal.age}
- Region: {region_data['display_name']} (California, USA)
- City: {user.location.city}
- Currency: USD
- Weekly hours available: {hours_desc}
- Cost of living: {region_data['cost_of_living_index']}x national average

FINANCIAL DATA:
- Total available capital: ${round(total_capital, 2)} USD

LOAN CONDITIONS:
- Approved: {loan.get("approved")}
- Interest rate: {loan.get("interest_rate")}

PREFERENCES:
- Risk tolerance: {user.preferences.risk_profile.value}
- Investment horizon: {user.preferences.horizon.value} years

🌴 CALIFORNIA TAX CONTEXT:
- California treats capital gains as ORDINARY INCOME (up to 13.3% state)
- For high earners, total tax on gains: federal 20% + state 13.3% = 33.3%
- Tax-advantaged accounts (401k, Roth IRA, HSA) crucial for CA residents
- California municipal bonds: DOUBLE tax-free (federal + state)
{qsbs_note}

═══════════════════════════════════════════════════════════
🛠️ MANDATORY WORKFLOW (DO NOT SKIP):
═══════════════════════════════════════════════════════════

STEP 1: Call `calculate_stock_allocation` tool with:
        risk_profile="{user.preferences.risk_profile.value}"
        horizon="{user.preferences.horizon.value}"
        → This returns the EXACT ETF allocation percentages.

STEP 2: Call `calculate_expected_return` tool with the same parameters.
        → This returns EXACT expected_return, risk, and stability values.

STEP 3: Use the tool results in your JSON output:
        - allocation = exactly what calculate_stock_allocation returned
        - expected_return, risk, stability = exactly what calculate_expected_return returned

DO NOT make up your own numbers. The tools provide historically-accurate values.

═══════════════════════════════════════════════════════════

YOUR TASK:
Generate a portfolio strategy that:
- Uses tool-provided allocation (DO NOT modify percentages)
- Uses tool-provided metrics (DO NOT modify return/risk/stability)
- Mentions California tax efficiency where relevant (Roth IRA, CA muni bonds, QSBS)
- Adds creative, personalized: title, description, pros, cons, next_steps

REQUIRED FIELDS:
1. title — short portfolio name (e.g., "California Tax-Aware Growth Portfolio")
2. description — what this portfolio invests in and California angle (2-3 sentences)
3. allocation — EXACTLY from calculate_stock_allocation tool
4. expected_return — EXACTLY from calculate_expected_return tool
5. risk — EXACTLY from calculate_expected_return tool
6. stability — EXACTLY from calculate_expected_return tool
7. pros — 3 advantages (BE CREATIVE, mention CA-specific benefits if relevant)
8. cons — 2 risks (BE CREATIVE)
9. next_steps — 3 concrete actions (broker, account type — prefer Roth IRA for CA residents, first ETFs)
10. time_to_profit — realistic horizon

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- DO NOT change tool-provided numbers
- BE CREATIVE in title, description, pros, cons, next_steps

FORMAT:
{{
  "agent": "stock",
  "title": "...",
  "description": "...",
  "allocation": {{
    "VOO": "40%",
    "VXUS": "30%",
    ...
  }},
  "expected_return": 0.08,
  "risk": 0.5,
  "stability": 0.6,
  "pros": ["...", "...", "..."],
  "cons": ["...", "..."],
  "next_steps": ["...", "...", "..."],
  "time_to_profit": "..."
}}
"""


async def generate_stock_strategy_llm(user, loan: dict) -> dict:
    prompt = build_prompt(user, loan)

    return await call_llm_with_tools(
        prompt=prompt,
        tools=STOCK_TOOLS,
        agent_name="stock"
    )


def validate_stock_output(data: dict) -> dict:
    return {
        "agent": "stock",
        "title": safe_str(data.get("title"), "Diversified ETF Portfolio"),
        "description": safe_str(
            data.get("description"),
            "A diversified portfolio of ETFs balancing growth and stability."
        ),
        "allocation": safe_dict(data.get("allocation"), {
            "VOO": "40%",
            "VXUS": "30%",
            "BND": "20%",
            "Cash reserve": "10%",
        }),
        "expected_return": clamp(data.get("expected_return"), 0.01, 0.2, 0.07),
        "risk": clamp(data.get("risk"), 0, 1, 0.5),
        "stability": clamp(data.get("stability"), 0, 1, 0.6),
        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), []),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "3-5 years"),
    }


async def run_stock_agent(user, loan: dict) -> dict:
    raw = await generate_stock_strategy_llm(user, loan)
    return validate_stock_output(raw)
