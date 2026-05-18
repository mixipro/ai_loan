# app/services/orchestrator.py
"""
Orchestrator — runs 3 strategy agents in parallel with user-specified config.

NEW FLOW (v4.0):
  1. User submits profile + per-strategy config (from /loan-offers slider UI)
  2. Risk engine computes profile (for transparency / reporting)
  3. Three agents run in parallel:
     - business_agent(user, config.business)
     - real_estate_agent(user, config.real_estate)
     - stock_agent(user, config.stock)
  4. Each agent uses its OWN loan_amount + savings_to_use from config
  5. Investment engine computes net return per strategy
  6. Judge agent selects best (skipping rejected strategies)

REMOVED:
  - 5-agent system (business + business_cash + RE + stock_cash + stock_margin)
  - /simulate endpoint (replaced by config in /analyze)
"""

import asyncio
import logging

from app.engines.risk_engine import calculate_risk_score
from app.engines.investment_engine import get_best_investments

from app.agents.stock_agent import run_stock_agent
from app.agents.business_agent import run_business_agent
from app.agents.real_estate_agent import run_real_estate_agent
from app.agents.judge_agent import run_judge_agent

logger = logging.getLogger(__name__)


# ─────────────────────────
# 🚀 RUN 3 AGENTS — PARALLEL
# ─────────────────────────
async def run_all_agents(user, config: dict) -> list:
    """
    Runs 3 agents in parallel via asyncio.gather.
    Each agent receives its OWN config from the /loan-offers slider UI.

    Args:
        user: UserInput
        config: {
            "business":    {loan_amount, loan_years, savings_to_use, interest_rate},
            "real_estate": {loan_amount, loan_years, savings_to_use, interest_rate},
            "stock":       {loan_amount, loan_years, savings_to_use, interest_rate}
        }
    """
    business_config = config.get("business", {})
    real_estate_config = config.get("real_estate", {})
    stock_config = config.get("stock", {})

    agent_definitions = [
        ("business", lambda: run_business_agent(user, business_config)),
        ("real_estate", lambda: run_real_estate_agent(user, real_estate_config)),
        ("stock", lambda: run_stock_agent(user, stock_config)),
    ]

    logger.info("Launching 3 agents in parallel (business, real_estate, stock)...")

    tasks = [agent_fn() for _, agent_fn in agent_definitions]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for (name, _), result in zip(agent_definitions, raw_results):
        if isinstance(result, Exception):
            logger.error(f"Agent '{name}' failed: {result}")
            results.append({
                "agent": name,
                "title": f"[{name} agent unavailable]",
                "description": f"Agent error: {str(result)[:200]}",
                "expected_return": 0.05,
                "risk": 0.5,
                "stability": 0.5,
                "allocation": {},
                "pros": [],
                "cons": [f"Agent failed: {str(result)[:100]}"],
                "next_steps": [],
                "time_to_profit": "N/A",
                "error": str(result),
                "rejected": True,
                "rejection_reason": f"Agent execution error: {str(result)[:200]}",
            })
        else:
            if result.get("rejected"):
                logger.warning(
                    f"Agent '{name}' REJECTED strategy: "
                    f"{result.get('rejection_reason', 'unknown reason')}"
                )
            else:
                logger.info(f"Agent '{name}' completed successfully")
            results.append(result)

    return results


# ─────────────────────────
# 📝 BUILD RISK EXPLANATION
# ─────────────────────────
def build_risk_explanation(user_risk_pref: str, creditworthiness: str) -> str:
    base = (
        f"You selected '{user_risk_pref.upper()}' risk tolerance for INVESTMENTS. "
        f"Your financial profile rates as '{creditworthiness.upper()}' CREDITWORTHINESS "
        f"(this affects your loan terms, not investment selection). "
        f"These two dimensions are evaluated independently."
    )

    if user_risk_pref == "low" and creditworthiness == "high":
        base += (
            " 📊 Note: Your strong financial profile would qualify you for aggressive "
            "strategies, but we honored your conservative preference."
        )
    elif user_risk_pref == "high" and creditworthiness == "low":
        base += (
            " ⚠️ Note: Your financial profile is fragile, so even though you prefer "
            "aggressive strategies, you'll face higher loan rates and stricter limits."
        )

    return base


# ─────────────────────────
# 🔧 BUILD STRATEGY LOAN OBJECT FROM CONFIG
# (for investment_engine compatibility)
# ─────────────────────────
def _build_strategy_loans_from_config(config: dict) -> dict:
    """
    Converts user config into strategy_loans format expected by investment_engine.

    Maintains the same shape that legacy investment_engine expects, so we don't
    have to refactor it (just adapts our config to its input format).
    """
    def _to_loan_obj(strategy_config: dict, loan_type: str) -> dict:
        loan_amount = strategy_config.get("loan_amount", 0)
        loan_years = strategy_config.get("loan_years", 0)
        rate = strategy_config.get("interest_rate", 0)

        # Compute monthly_payment / annual_payment / total_paid using amortization
        if loan_amount > 0 and rate > 0 and loan_years > 0:
            months = loan_years * 12
            monthly_rate = rate / 12
            monthly_payment = (
                loan_amount * monthly_rate * ((1 + monthly_rate) ** months) /
                (((1 + monthly_rate) ** months) - 1)
            )
            annual_payment = monthly_payment * 12
            total_paid = monthly_payment * months
            total_interest = total_paid - loan_amount
        else:
            monthly_payment = 0
            annual_payment = 0
            total_paid = 0
            total_interest = 0

        return {
            "approved": loan_amount > 0,
            "max_loan_amount": loan_amount,
            "loan_amount": loan_amount,
            "interest_rate": rate,
            "loan_years": loan_years,
            "monthly_payment": round(monthly_payment, 2),
            "annual_payment": round(annual_payment, 2),
            "total_paid": round(total_paid, 2),
            "total_interest": round(total_interest, 2),
            "loan_type": loan_type,
            "savings_to_use": strategy_config.get("savings_to_use", 0),
        }

    stock_loan = _to_loan_obj(config.get("stock", {}), "margin")
    return {
        "business": _to_loan_obj(config.get("business", {}), "business"),
        "real_estate": _to_loan_obj(config.get("real_estate", {}), "mortgage"),
        "stock_margin": stock_loan,
        "stock": stock_loan,  # ⭐ Alias for new unified agent name
    }


# ─────────────────────────
# 🚀 MAIN PIPELINE — ASYNC
# ─────────────────────────
async def run_pipeline(user, config: dict) -> dict:
    """
    Main system flow (async):
      user + config → risk → 3 agents in parallel → investment eval → judge → result

    Args:
        user: UserInput (validated Pydantic)
        config: {
            "business":    {loan_amount, loan_years, savings_to_use, interest_rate},
            "real_estate": {loan_amount, loan_years, savings_to_use, interest_rate},
            "stock":       {loan_amount, loan_years, savings_to_use, interest_rate}
        }
    """
    logger.info("=" * 50)
    logger.info("Pipeline started (CaliforniaCFO v4.0 — 3-agent config-driven)")
    logger.info("=" * 50)

    # 1️⃣ RISK (for transparency / reporting only — config already has rates)
    logger.info("Step 1: calculating risk score for reporting")
    risk = calculate_risk_score(user)
    logger.info(
        f"Region: {risk['region_display_name']} | "
        f"Risk level: {risk['level']} | "
        f"Creditworthiness: {risk['creditworthiness']} | "
        f"Score: {risk['adjusted_score']}"
    )

    # 2️⃣ Log user config
    logger.info("Step 2: user-configured capital allocation:")
    for strategy_name in ("business", "real_estate", "stock"):
        s_config = config.get(strategy_name, {})
        loan_amt = s_config.get("loan_amount", 0)
        savings = s_config.get("savings_to_use", 0)
        logger.info(
            f"  {strategy_name}: loan=${loan_amt:,.0f}, "
            f"savings=${savings:,.0f}, "
            f"total=${loan_amt + savings:,.0f}"
        )

    # 3️⃣ BUILD STRATEGY LOAN OBJECTS (compatibility shim for investment_engine)
    strategy_loans = _build_strategy_loans_from_config(config)

    # 4️⃣ AGENTS — ASYNC PARALLEL (3 agents)
    logger.info("Step 4: running 3 investment agents in parallel")
    agents_results = await run_all_agents(user, config)
    logger.info(f"Agents returned {len(agents_results)} strategy results")

    # 5️⃣ INVESTMENT EVALUATION (skip rejected strategies)
    logger.info("Step 5: evaluating + ranking strategies (real amortization)")
    valid_strategies = [r for r in agents_results if not r.get("rejected")]
    rejected_strategies = [r for r in agents_results if r.get("rejected")]

    if valid_strategies:
        ranked = get_best_investments(user, valid_strategies, strategy_loans)
    else:
        ranked = []
        logger.warning("No valid strategies to rank (all rejected)")

    # Append rejected ones at the end (so frontend can show them)
    ranked = ranked + rejected_strategies

    for r in ranked:
        if r.get("rejected"):
            logger.warning(f"  {r['agent']}: REJECTED — {r.get('rejection_reason', 'unknown')}")
        else:
            logger.info(
                f"  {r['agent']}: net_return={r.get('net_return', 0) * 100:.2f}%, "
                f"status={r.get('status', 'unknown')}, "
                f"score={r.get('score', 0)}"
            )

    # 6️⃣ JUDGE — ASYNC (skip if no valid strategies)
    logger.info("Step 6: judge agent — selecting best strategy")

    # Build placeholder "loan" object for judge (uses business loan as primary)
    primary_loan = strategy_loans["business"]

    if valid_strategies:
        judgment = await run_judge_agent(user, primary_loan, [r for r in ranked if not r.get("rejected")])

        if judgment.get("recommended"):
            logger.info(
                f"Judge recommended: {judgment['recommended'].get('agent', 'unknown')} "
                f"(profile: {judgment.get('profile_used', 'unknown')})"
            )
    else:
        judgment = {
            "recommended": None,
            "reasoning": "All strategies were rejected based on your configuration. "
                         "Please adjust your loan amounts or savings allocation.",
            "next_step": "Review the rejection reasons for each strategy and reconfigure.",
            "comparison": "",
            "profile_used": user.preferences.risk_profile.value,
        }

    user_risk_pref = user.preferences.risk_profile.value
    logger.info("Pipeline finished")

    return {
        "user_summary": _build_user_summary(user),
        "risk": _build_risk_section(user, risk),
        "config": config,
        "loans": strategy_loans,
        "strategies": ranked,
        "recommendation": judgment.get("recommended"),
        "reasoning": judgment.get("reasoning", ""),
        "next_step": judgment.get("next_step", ""),
        "comparison": judgment.get("comparison", ""),
        "profile_used": judgment.get("profile_used", user_risk_pref),
        "rejected_count": len(rejected_strategies),
        "detailed_explanation": judgment.get("detailed_explanation"),  # ✅ FIXED
        "comparison_charts": judgment.get("comparison_charts"),         # ✅ FIXED
    }

# ─────────────────────────
# 🛠️ HELPERS
# ─────────────────────────
def _build_user_summary(user) -> dict:
    return {
        "region": user.location.region.value,
        "city": user.location.city,
        "country": "US",
        "age": user.personal.age,
        "income": user.financial.income,
        "expenses": user.financial.expenses,
        "monthly_debt": user.financial.monthly_debt,
        "savings": user.financial.savings,
        "currency": user.financial.currency.value,
        "risk_profile": user.preferences.risk_profile.value,
        "horizon": user.preferences.horizon.value,
    }


def _build_risk_section(user, risk: dict) -> dict:
    user_risk_pref = user.preferences.risk_profile.value
    creditworthiness = risk.get("creditworthiness", "medium")
    risk_explanation = build_risk_explanation(user_risk_pref, creditworthiness)

    return {
        "creditworthiness": creditworthiness,
        "explanation": risk_explanation,
        "score": risk["adjusted_score"],
        "level": risk["level"],
        "region": risk["region"],
        "region_display_name": risk["region_display_name"],
        "region_factor": risk["region_factor"],
        "cost_of_living_index": risk["cost_of_living_index"],
        "real_disposable_income": risk["real_disposable_income"],
        "real_savings": risk["real_savings"],
        "industry_adjustment": risk["industry_adjustment"],
        "equity_bonus": risk["equity_bonus"],
        "disposable_income": risk["disposable_income"],
        "debt_ratio": risk["debt_ratio"],
        "base_score": risk["base_score"],
        "country": "US",
        "country_factor": risk["region_factor"],
    }