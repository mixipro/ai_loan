# app/services/orchestrator.py

import asyncio
import logging

from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_all_loan_rates, calculate_interest_rate
from app.engines.loan_engine import calculate_all_strategy_loans, calculate_custom_loan
from app.engines.investment_engine import get_best_investments

from app.agents.stock_agent import run_stock_agent_cash, run_stock_agent_margin
from app.agents.business_agent import run_business_agent, run_business_agent_cash  # ⭐ NEW import
from app.agents.real_estate_agent import run_real_estate_agent
from app.agents.judge_agent import run_judge_agent

logger = logging.getLogger(__name__)


# ─────────────────────────
# 🚀 RUN ALL AGENTS — PARALLEL (5 agents now!)
# ─────────────────────────
async def run_all_agents(user, strategy_loans: dict) -> list:
    """
    Runs 5 agents in parallel via asyncio.gather.
    Each agent gets its OWN loan type (business, mortgage, none, margin).

    ⭐ NEW: business_cash agent provides bootstrap alternative
    """
    business_loan = strategy_loans["business"]
    mortgage_loan = strategy_loans["real_estate"]
    margin_loan = strategy_loans["stock_margin"]

    agent_definitions = [
        ("business", lambda: run_business_agent(user, business_loan)),
        ("business_cash", lambda: run_business_agent_cash(user)),  # ⭐ NEW
        ("real_estate", lambda: run_real_estate_agent(user, mortgage_loan)),
        ("stock_cash", lambda: run_stock_agent_cash(user)),
        ("stock_margin", lambda: run_stock_agent_margin(user, margin_loan)),
    ]

    logger.info(
        "Launching 5 agents in parallel "
        "(business, business_cash, real_estate, stock_cash, stock_margin)..."
    )

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
            })
        else:
            logger.info(f"Agent '{name}' completed successfully")
            results.append(result)

    return results


# ─────────────────────────
# 📝 BUILD RISK EXPLANATION (unchanged)
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
# 🚀 MAIN PIPELINE — ASYNC
# ─────────────────────────
async def run_pipeline(user) -> dict:
    """
    Main system flow (async):
    user → risk → ALL loan rates (5) → strategy loans (4) → 5 agents PARALLEL →
    investment eval (per-strategy real amortization) → judge → result
    """
    logger.info("=" * 50)
    logger.info("Pipeline started (California system v3.1 — 5-agent multi-loan)")
    logger.info("=" * 50)

    # 1️⃣ RISK
    logger.info("Step 1: calculating risk score")
    risk = calculate_risk_score(user)
    logger.info(
        f"Region: {risk['region_display_name']} | "
        f"Risk level: {risk['level']} | "
        f"Creditworthiness: {risk['creditworthiness']} | "
        f"Score: {risk['adjusted_score']}"
    )

    # 2️⃣ ALL INTEREST RATES (5 types)
    logger.info("Step 2: calculating ALL loan interest rates (5 types)")
    all_rates = calculate_all_loan_rates(risk)
    for loan_type, rate_data in all_rates.items():
        logger.info(f"  {loan_type}: {rate_data['interest_rate'] * 100:.2f}%")

    interest = all_rates["personal"]

    # 3️⃣ STRATEGY LOANS (4 strategies)
    logger.info("Step 3: calculating per-strategy loan offers")
    strategy_loans = calculate_all_strategy_loans(user, risk, all_rates)

    for strategy_name, loan_data in strategy_loans.items():
        if loan_data["approved"]:
            logger.info(
                f"  {strategy_name}: ${loan_data['max_loan_amount']:,.0f} "
                f"@ {loan_data['interest_rate'] * 100:.2f}% "
                f"({loan_data['loan_years']}y)"
            )
        else:
            logger.warning(f"  {strategy_name}: REJECTED - {loan_data.get('reason')}")

    loan = strategy_loans["personal"]

    # 4️⃣ AGENTS — ASYNC PARALLEL (5 agents)
    logger.info("Step 4: running 5 investment agents in parallel")
    agents_results = await run_all_agents(user, strategy_loans)
    logger.info(f"Agents returned {len(agents_results)} strategies")

    # 5️⃣ INVESTMENT EVALUATION (per-strategy real amortization)
    logger.info("Step 5: evaluating + ranking strategies (real amortization)")
    ranked = get_best_investments(user, agents_results, strategy_loans)

    for r in ranked:
        logger.info(
            f"  {r['agent']}: net_return={r['net_return'] * 100:.2f}%, "
            f"status={r['status']}, score={r['score']}"
        )

    # 6️⃣ JUDGE — ASYNC
    logger.info("Step 6: judge agent — selecting best strategy")
    judgment = await run_judge_agent(user, loan, ranked)

    if judgment.get("recommended"):
        logger.info(
            f"Judge recommended: {judgment['recommended'].get('agent', 'unknown')} "
            f"(profile: {judgment.get('profile_used', 'unknown')})"
        )

    user_risk_pref = user.preferences.risk_profile.value
    logger.info("Pipeline finished")

    return {
        "user_summary": _build_user_summary(user),
        "risk": _build_risk_section(user, risk),
        "interest": interest,
        "loan": loan,
        "loans": strategy_loans,
        "all_rates": all_rates,
        "strategies": ranked,
        "recommendation": judgment.get("recommended"),
        "reasoning": judgment.get("reasoning", ""),
        "next_step": judgment.get("next_step", ""),
        "comparison": judgment.get("comparison", ""),
        "profile_used": judgment.get("profile_used", user_risk_pref),
    }


# ─────────────────────────
# 🚀 SIMULATION PIPELINE (PRESERVED!)
# ─────────────────────────
async def run_simulation_pipeline(user, simulation_choice) -> dict:
    """
    Custom calculator: user chooses loan params and savings allocation.
    Uses PERSONAL loan type for backward compat with simulator UI.
    """
    logger.info("=" * 50)
    logger.info("Simulation pipeline started (California system)")
    logger.info(f"User chose: loan={simulation_choice.loan_amount}, "
                f"years={simulation_choice.loan_years}, "
                f"savings_to_invest={simulation_choice.savings_to_invest}")
    logger.info("=" * 50)

    # 1️⃣ RISK + INTEREST
    risk = calculate_risk_score(user)
    interest = calculate_interest_rate(risk, loan_type="personal")
    annual_rate = interest["interest_rate"]

    # 2️⃣ CUSTOM LOAN
    logger.info("Step 2: calculating custom loan")
    loan = calculate_custom_loan(
        loan_amount=simulation_choice.loan_amount,
        loan_years=simulation_choice.loan_years,
        annual_rate=annual_rate,
        user=user,
        risk=risk,
        loan_type="personal",
    )

    if not loan["approved"]:
        return {
            "user_summary": _build_user_summary(user),
            "risk": _build_risk_section(user, risk),
            "interest": interest,
            "loan": loan,
            "simulation_request": simulation_choice.model_dump(),
            "error": "Simulation parameters invalid",
            "strategies": [],
            "recommendation": None,
        }

    # 3️⃣ ADAPT USER
    adapted_user = user.model_copy(deep=True)
    adapted_user.financial.savings = int(simulation_choice.savings_to_invest)

    # 4️⃣ BUILD SHARED LOAN FOR ALL STRATEGIES
    custom_loan_obj = {
        "approved": loan["loan_amount"] > 0,
        "max_loan_amount": loan["loan_amount"],
        "monthly_payment": loan["monthly_payment"],
        "annual_payment": loan.get("annual_payment", loan["monthly_payment"] * 12),
        "interest_rate": loan["interest_rate"],
        "loan_years": loan["loan_years"],
        "loan_type": "personal",
        "total_paid": loan.get("total_paid", 0),
        "total_interest": loan.get("total_interest", 0),
    }

    simulation_strategy_loans = {
        "business": custom_loan_obj,
        "real_estate": custom_loan_obj,
        "stock_margin": custom_loan_obj,
        "personal": custom_loan_obj,
    }

    # 5️⃣ AGENTS
    logger.info("Step 5: running agents with custom parameters")
    agents_results = await run_all_agents(adapted_user, simulation_strategy_loans)

    # 6️⃣ INVESTMENT EVALUATION
    ranked = get_best_investments(adapted_user, agents_results, simulation_strategy_loans)

    # 7️⃣ JUDGE
    logger.info("Step 7: judge agent")
    judgment = await run_judge_agent(adapted_user, custom_loan_obj, ranked)

    user_risk_pref = user.preferences.risk_profile.value
    saved_buffer = user.financial.savings - simulation_choice.savings_to_invest
    total_invested = simulation_choice.savings_to_invest + simulation_choice.loan_amount

    return {
        "user_summary": _build_user_summary(user),
        "risk": _build_risk_section(user, risk),
        "interest": interest,
        "loan": loan,
        "simulation": {
            "user_chose": {
                "loan_amount": simulation_choice.loan_amount,
                "loan_years": simulation_choice.loan_years,
                "savings_to_invest": simulation_choice.savings_to_invest,
            },
            "calculated": {
                "monthly_payment": loan["monthly_payment"],
                "total_paid": loan["total_paid"],
                "total_interest": loan["total_interest"],
                "total_capital_invested": round(total_invested, 2),
                "savings_kept_as_buffer": round(saved_buffer, 2),
            },
            "scenario": loan["scenario"],
        },
        "strategies": ranked,
        "recommendation": judgment.get("recommended"),
        "reasoning": judgment.get("reasoning", ""),
        "next_step": judgment.get("next_step", ""),
        "comparison": judgment.get("comparison", ""),
        "profile_used": judgment.get("profile_used", user_risk_pref),
    }


# ─────────────────────────
# 🛠️ HELPERS (preserved)
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