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


def _build_qsbs_note(user) -> str:
    """Returns QSBS-relevant note if user has equity compensation."""
    if not user.professional.equity_compensation:
        return ""

    from app.models.user import EquityCompensation
    if user.professional.equity_compensation in (
            EquityCompensation.ISO,
            EquityCompensation.FOUNDER_STOCK,
            EquityCompensation.MIXED,
    ):
        return (
            "\n⚠️ USER HAS EQUITY COMPENSATION — they may qualify for QSBS "
            "(Section 1202) exclusion: up to $10M federal+state tax-free on startup exit. "
            "Consider mentioning portfolio diversification away from employer stock."
        )
    return ""


# ═══════════════════════════════════════════════════════════
# 📊 STOCK CASH AGENT — Conservative, uses savings only
# ═══════════════════════════════════════════════════════════

def build_prompt_cash(user) -> str:
    """
    Cash-only stock portfolio.
    Uses user's risk_profile directly (no leverage amplification).
    """
    total_capital = user.financial.savings  # cash only — NO LOAN

    hours_desc = HOURS_STOCK_DESCRIPTIONS.get(
        user.professional.weekly_hours.value,
        "Unknown availability"
    )

    region_data = REGION_DATA[user.location.region]
    qsbs_note = _build_qsbs_note(user)

    return f"""
You are a senior California-aware portfolio manager specializing in CASH-FUNDED stock portfolios.

USER PROFILE:
- Age: {user.personal.age}
- Region: {region_data['display_name']} (California, USA)
- City: {user.location.city}
- Currency: USD
- Weekly hours available: {hours_desc}
- Cost of living: {region_data['cost_of_living_index']}x national average

💰 INVESTMENT CAPITAL (CASH ONLY — NO LOAN):
- Available from savings: ${user.financial.savings} USD
- This is CONSERVATIVE strategy: no leverage, no margin call risk
- Capital deployed = exactly user's savings

PREFERENCES:
- Risk tolerance: {user.preferences.risk_profile.value}
- Investment horizon: {user.preferences.horizon.value} years

🌴 CALIFORNIA TAX CONTEXT:
- California treats capital gains as ORDINARY INCOME (up to 13.3% state)
- For high earners: federal 20% + state 13.3% = 33.3% total tax on gains
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
Generate a CASH-FUNDED portfolio strategy that:
- Uses tool-provided allocation (DO NOT modify percentages)
- Uses tool-provided metrics (DO NOT modify return/risk/stability)
- Mentions California tax efficiency (Roth IRA, CA muni bonds, QSBS where relevant)
- Emphasizes CONSERVATIVE approach (no leverage, no margin)

REQUIRED FIELDS:
1. title — short portfolio name (e.g., "California Tax-Aware Cash Portfolio")
2. description — what this portfolio invests in (2-3 sentences, emphasize cash-funded)
3. allocation — EXACTLY from calculate_stock_allocation tool
4. expected_return — EXACTLY from calculate_expected_return tool
5. risk — EXACTLY from calculate_expected_return tool
6. stability — EXACTLY from calculate_expected_return tool
7. pros — 3 advantages (mention CA-specific benefits + no-leverage safety)
8. cons — 2 risks (BE CREATIVE)
9. next_steps — 3 concrete actions (prefer Roth IRA for CA residents)
10. time_to_profit — realistic horizon

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- DO NOT change tool-provided numbers
- "agent" field MUST be "stock_cash"

FORMAT:
{{
  "agent": "stock_cash",
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


async def generate_stock_cash_strategy_llm(user) -> dict:
    prompt = build_prompt_cash(user)
    return await call_llm_with_tools(
        prompt=prompt,
        tools=STOCK_TOOLS,
        agent_name="stock_cash"
    )


def validate_stock_cash_output(data: dict) -> dict:
    return {
        "agent": "stock_cash",
        "title": safe_str(data.get("title"), "Cash-Funded ETF Portfolio"),
        "description": safe_str(
            data.get("description"),
            "A diversified portfolio of ETFs funded entirely from savings (no leverage)."
        ),
        "allocation": safe_dict(data.get("allocation"), {
            "VOO": "40%",
            "VXUS": "30%",
            "BND": "20%",
            "Cash reserve": "10%",
        }),
        "expected_return": clamp(data.get("expected_return"), 0.01, 0.15, 0.07),
        "risk": clamp(data.get("risk"), 0, 1, 0.5),
        "stability": clamp(data.get("stability"), 0, 1, 0.6),
        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), []),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "3-5 years"),
    }


async def run_stock_agent_cash(user) -> dict:
    """Cash-funded stock portfolio (no loan, no leverage)."""
    raw = await generate_stock_cash_strategy_llm(user)
    return validate_stock_cash_output(raw)


# ═══════════════════════════════════════════════════════════
# 📈 STOCK MARGIN AGENT — Leveraged, uses margin loan
# ═══════════════════════════════════════════════════════════

# ⭐ Margin agent uses MORE AGGRESSIVE allocation
# We bump risk_profile one level up (low→medium, medium→high)
# because margin investing IS inherently leveraged risk
MARGIN_RISK_AMPLIFIER = {
    "low": "medium",  # Conservative + margin = medium effective risk
    "medium": "high",  # Medium + margin = high effective risk
    "high": "high",  # Already aggressive
}


def build_prompt_margin(user, margin_loan: dict) -> str:
    """
    Leveraged stock portfolio using margin loan.
    Bumps risk_profile one level up for allocation tool (margin amplifies risk).
    """
    total_capital = user.financial.savings
    if margin_loan.get("approved"):
        total_capital += margin_loan.get("max_loan_amount", 0)

    hours_desc = HOURS_STOCK_DESCRIPTIONS.get(
        user.professional.weekly_hours.value,
        "Unknown availability"
    )

    region_data = REGION_DATA[user.location.region]
    qsbs_note = _build_qsbs_note(user)

    # ⭐ Margin amplifies risk — use bumped profile for allocation
    user_risk = user.preferences.risk_profile.value
    effective_risk_profile = MARGIN_RISK_AMPLIFIER.get(user_risk, "medium")

    # Margin loan details
    margin_amount = margin_loan.get("max_loan_amount", 0)
    margin_rate = margin_loan.get("interest_rate", 0)
    margin_rate_pct = margin_rate * 100
    margin_monthly = margin_loan.get("monthly_payment", 0)

    # Warning based on user profile
    risk_warning = ""
    if user_risk == "low":
        risk_warning = "\n🚨 CRITICAL WARNING: User selected LOW risk tolerance. Margin investing is GENERALLY INAPPROPRIATE. Emphasize this in cons. Suggest cash strategy instead."
    elif user_risk == "medium":
        risk_warning = "\n⚠️ NOTE: User selected MEDIUM risk. Margin amplifies risk — be conservative in allocation."

    return f"""
You are a senior California-aware portfolio manager specializing in LEVERAGED stock portfolios (MARGIN LOANS).

USER PROFILE:
- Age: {user.personal.age}
- Region: {region_data['display_name']} (California, USA)
- City: {user.location.city}
- Currency: USD
- Weekly hours available: {hours_desc}
- Cost of living: {region_data['cost_of_living_index']}x national average

📈 MARGIN LOAN CONDITIONS (LEVERAGED INVESTING):
- Approved: {margin_loan.get("approved")}
- Type: MARGIN LOAN from broker (Robinhood, Schwab, IBKR)
- Max margin: ${margin_amount} USD (capped at 50% LTV of savings)
- Interest rate: {margin_rate_pct:.2f}% APR (variable, can change)
- Term: CALLABLE — broker can force liquidation if portfolio drops below maintenance margin (~25%)
- Monthly interest: ~${margin_monthly}

💰 TOTAL CAPITAL WITH MARGIN:
- Savings: ${user.financial.savings} USD
- Margin loan: ${margin_amount} USD
- Total deployable: ${round(total_capital, 2)} USD
- ⚠️ LEVERAGE: {round(total_capital / max(user.financial.savings, 1), 2)}x your savings

🚨 MARGIN CALL RISK (CRITICAL):
- If portfolio value drops, broker demands more cash OR forces liquidation at LOSS
- Volatile stocks (QQQ, ARKK) increase margin call probability
- High volatility + leverage = potential for TOTAL LOSS of savings
- Interest rate is VARIABLE — can rise during high inflation

PREFERENCES:
- User-stated risk tolerance: {user_risk}
- ⭐ Effective risk for allocation (with leverage): {effective_risk_profile}
  (margin amplifies risk — we use one level up for allocation)
- Investment horizon: {user.preferences.horizon.value} years
{risk_warning}

🌴 CALIFORNIA TAX CONTEXT:
- California treats capital gains as ORDINARY INCOME (up to 13.3% state)
- ⭐ Investment interest expense on margin loan MAY be tax-deductible (consult CPA)
{qsbs_note}

═══════════════════════════════════════════════════════════
🛠️ MANDATORY WORKFLOW (DO NOT SKIP):
═══════════════════════════════════════════════════════════

STEP 1: Call `calculate_stock_allocation` tool with:
        risk_profile="{effective_risk_profile}"          ⭐ NOTE: BUMPED for leverage
        horizon="{user.preferences.horizon.value}"
        → Returns the EXACT ETF allocation percentages.

STEP 2: Call `calculate_expected_return` tool with the same parameters.
        → Returns EXACT expected_return, risk, and stability values.

STEP 3: Use tool results in your JSON output (DO NOT modify numbers).

═══════════════════════════════════════════════════════════

YOUR TASK:
Generate a MARGIN-LEVERAGED portfolio strategy that:
- Uses tool-provided allocation (with bumped risk profile — accounts for leverage)
- Uses tool-provided metrics (DO NOT modify)
- HONESTLY mentions margin call risk in cons
- Mentions tax deductibility of margin interest
- If user has LOW risk tolerance: cons MUST explicitly say "margin is inappropriate for low-risk investors"

REQUIRED FIELDS:
1. title — short portfolio name (e.g., "Leveraged California Growth Portfolio")
2. description — leveraged strategy (2-3 sentences, mention {round(total_capital / max(user.financial.savings, 1), 1)}x leverage)
3. allocation — EXACTLY from calculate_stock_allocation tool
4. expected_return — EXACTLY from calculate_expected_return tool
5. risk — EXACTLY from calculate_expected_return tool (min 0.6 for margin)
6. stability — EXACTLY from calculate_expected_return tool (max 0.6 for margin)
7. pros — 3 advantages (amplified returns if market goes up)
8. cons — MUST INCLUDE: 
   - "Margin call risk if market drops 20%+"
   - "Variable interest rate can rise"
   - At least one more
9. next_steps — 3 concrete actions (open margin account, understand maintenance margin)
10. time_to_profit — realistic horizon

STRICT RULES:
- Return ONLY valid JSON, no markdown fences
- DO NOT change tool-provided numbers
- "agent" field MUST be "stock_margin"
- risk MUST be ≥ 0.6 (margin is inherently risky)
- stability MUST be ≤ 0.6 (margin is volatile)

FORMAT:
{{
  "agent": "stock_margin",
  "title": "...",
  "description": "...",
  "allocation": {{
    "VOO": "50%",
    "BND": "25%",
    ...
  }},
  "expected_return": 0.09,
  "risk": 0.7,
  "stability": 0.5,
  "pros": ["...", "...", "..."],
  "cons": ["Margin call risk if market drops 20%+", "Variable interest rate", "..."],
  "next_steps": ["...", "...", "..."],
  "time_to_profit": "..."
}}
"""


async def generate_stock_margin_strategy_llm(user, margin_loan: dict) -> dict:
    prompt = build_prompt_margin(user, margin_loan)
    return await call_llm_with_tools(
        prompt=prompt,
        tools=STOCK_TOOLS,
        agent_name="stock_margin"
    )


def validate_stock_margin_output(data: dict) -> dict:
    return {
        "agent": "stock_margin",
        "title": safe_str(data.get("title"), "Leveraged ETF Portfolio (Margin)"),
        "description": safe_str(
            data.get("description"),
            "A leveraged portfolio using margin loan to amplify exposure (high risk, high reward)."
        ),
        "allocation": safe_dict(data.get("allocation"), {
            "VOO": "50%",
            "BND": "25%",
            "VXUS": "20%",
            "Cash reserve": "5%",
        }),
        "expected_return": clamp(data.get("expected_return"), 0.01, 0.18, 0.09),
        # ⭐ Margin: force risk min 0.6, stability max 0.6
        "risk": clamp(data.get("risk"), 0.6, 1, 0.7),
        "stability": clamp(data.get("stability"), 0, 0.6, 0.5),
        "pros": safe_list(data.get("pros"), []),
        "cons": safe_list(data.get("cons"), [
            "Margin call risk if portfolio drops 20%+",
            "Variable interest rate can rise"
        ]),
        "next_steps": safe_list(data.get("next_steps"), []),
        "time_to_profit": safe_str(data.get("time_to_profit"), "3-5 years"),
    }


async def run_stock_agent_margin(user, margin_loan: dict) -> dict:
    """Margin-leveraged stock portfolio (uses broker margin loan)."""
    raw = await generate_stock_margin_strategy_llm(user, margin_loan)
    return validate_stock_margin_output(raw)


# ═══════════════════════════════════════════════════════════
# 🔄 LEGACY COMPATIBILITY
# Keeps old `run_stock_agent(user, loan)` working if anything still calls it
# ═══════════════════════════════════════════════════════════

async def run_stock_agent(user, loan: dict = None) -> dict:
    """
    Legacy entry point — defaults to cash strategy.
    Kept for backward compatibility with code that may still call run_stock_agent.
    """
    return await run_stock_agent_cash(user)


# Legacy prompt function name (in case anything imports it)
def build_prompt(user, loan: dict) -> str:
    """Legacy: defaults to cash prompt."""
    return build_prompt_cash(user)


# Legacy validation name
def validate_stock_output(data: dict) -> dict:
    """Legacy: defaults to cash validation, normalizes agent field to 'stock'."""
    result = validate_stock_cash_output(data)
    result["agent"] = "stock"  # Legacy normalization
    return result


# Legacy generate function
async def generate_stock_strategy_llm(user, loan: dict) -> dict:
    """Legacy: defaults to cash generation."""
    return await generate_stock_cash_strategy_llm(user)