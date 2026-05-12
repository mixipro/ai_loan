# app/services/orchestrator.py

import asyncio
import logging

from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_interest_rate
from app.engines.loan_engine import calculate_loan_offer, calculate_custom_loan
from app.engines.investment_engine import get_best_investments

from app.agents.stock_agent import run_stock_agent
from app.agents.business_agent import run_business_agent
from app.agents.real_estate_agent import run_real_estate_agent
from app.agents.judge_agent import run_judge_agent

logger = logging.getLogger(__name__)


# ─────────────────────────
# 🚀 RUN ALL AGENTS — PARALLEL
# ─────────────────────────
async def run_all_agents(user, loan: dict) -> list:
    """Runs 3 agents in parallel via asyncio.gather."""
    agent_definitions = [
        ("stock", run_stock_agent),
        ("business", run_business_agent),
        ("real_estate", run_real_estate_agent),
    ]

    logger.info("Launching agents in parallel...")

    tasks = [agent_fn(user, loan) for _, agent_fn in agent_definitions]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for (name, _), result in zip(agent_definitions, raw_results):
        if isinstance(result, Exception):
            logger.error(f"Agent '{name}' failed: {result}")
            results.append({
                "agent": name,
                "strategy": f"[{name} agent unavailable]",
                "expected_return": 0.05,
                "risk": 0.5,
                "stability": 0.5,
                "error": str(result),
            })
        else:
            logger.info(f"Agent '{name}' completed successfully")
            results.append(result)

    return results


# ─────────────────────────
# 📝 BUILD RISK EXPLANATION
# ─────────────────────────
def build_risk_explanation(user_risk_pref: str, creditworthiness: str) -> str:
    """Generates explanation for risk tolerance vs creditworthiness."""
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
# 🚀 FINAL PIPELINE — ASYNC
# ─────────────────────────
async def run_pipeline(user) -> dict:
    """
    Main system flow (async):
    user → risk → interest → loan → [agents PARALLEL] → investment eval → judge → result
    """
    logger.info("=" * 50)
    logger.info("Pipeline started (California system)")
    logger.info("=" * 50)

    # ─────────────────────────
    # 1️⃣ RISK
    # ─────────────────────────
    logger.info("Step 1: calculating risk score")
    risk = calculate_risk_score(user)
    logger.info(
        f"Region: {risk['region_display_name']} | "
        f"Risk level: {risk['level']} | "
        f"Creditworthiness: {risk['creditworthiness']} | "
        f"Score: {risk['adjusted_score']}"
    )

    # ─────────────────────────
    # 2️⃣ INTEREST (California-aware, USD)
    # ─────────────────────────
    logger.info("Step 2: calculating interest rate")
    interest = calculate_interest_rate(risk, loan_type="personal")
    logger.info(f"Interest rate: {interest['interest_rate']}")

    # ─────────────────────────
    # 3️⃣ LOAN
    # ─────────────────────────
    logger.info("Step 3: calculating loan offer")
    loan = calculate_loan_offer(user, risk, interest)

    if loan["approved"]:
        logger.info(f"Loan approved: ${loan['max_loan_amount']} ({loan['loan_years']}y)")
    else:
        logger.warning(f"Loan rejected: {loan.get('reason')}")

    # ─────────────────────────
    # 4️⃣ AGENTS — ASYNC PARALLEL
    # ─────────────────────────
    logger.info("Step 4: running investment agents in parallel")
    agents_results = await run_all_agents(user, loan)
    logger.info(f"Agents returned {len(agents_results)} strategies")

    # ─────────────────────────
    # 5️⃣ INVESTMENT EVALUATION
    # ─────────────────────────
    logger.info("Step 5: evaluating + ranking strategies")
    ranked = get_best_investments(user, agents_results, loan)

    # ─────────────────────────
    # 6️⃣ JUDGE — ASYNC
    # ─────────────────────────
    logger.info("Step 6: judge agent — selecting best strategy")
    judgment = await run_judge_agent(user, loan, ranked)

    if judgment["recommended"]:
        logger.info(
            f"Judge recommended: {judgment['recommended']['agent']} "
            f"(profile: {judgment['profile_used']})"
        )

    # ─────────────────────────
    # 📝 BUILD RISK EXPLANATION
    # ─────────────────────────
    user_risk_pref = user.preferences.risk_profile.value
    creditworthiness = risk.get("creditworthiness", "medium")
    risk_explanation = build_risk_explanation(user_risk_pref, creditworthiness)

    # ─────────────────────────
    # 📊 OUTPUT
    # ─────────────────────────
    logger.info("Pipeline finished")

    return {
        "user_summary": _build_user_summary(user),
        "risk": _build_risk_section(user, risk),
        "interest": interest,
        "loan": loan,
        "strategies": ranked,
        "recommendation": judgment["recommended"],
        "reasoning": judgment["reasoning"],
        "next_step": judgment["next_step"],
        "profile_used": judgment.get("profile_used", user_risk_pref),
    }


# ─────────────────────────
# 🚀 SIMULATION PIPELINE
# ─────────────────────────
async def run_simulation_pipeline(user, simulation_choice) -> dict:
    """Custom calculator: user chooses loan params and savings allocation."""
    logger.info("=" * 50)
    logger.info("Simulation pipeline started (California system)")
    logger.info(f"User chose: loan={simulation_choice.loan_amount}, "
                f"years={simulation_choice.loan_years}, "
                f"savings_to_invest={simulation_choice.savings_to_invest}")
    logger.info("=" * 50)

    # ─────────────────────────
    # 1️⃣ RISK + INTEREST
    # ─────────────────────────
    risk = calculate_risk_score(user)
    interest = calculate_interest_rate(risk, loan_type="personal")
    annual_rate = interest["interest_rate"]

    # ─────────────────────────
    # 2️⃣ CUSTOM LOAN
    # ─────────────────────────
    logger.info("Step 2: calculating custom loan")
    loan = calculate_custom_loan(
        loan_amount=simulation_choice.loan_amount,
        loan_years=simulation_choice.loan_years,
        annual_rate=annual_rate,
        user=user,
        risk=risk
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

    # ─────────────────────────
    # 3️⃣ ADAPT USER
    # ─────────────────────────
    adapted_user = user.model_copy(deep=True)
    adapted_user.financial.savings = int(simulation_choice.savings_to_invest)

    logger.info(f"Adapted user: savings_to_invest={adapted_user.financial.savings}")

    # ─────────────────────────
    # 4️⃣ AGENTS
    # ─────────────────────────
    agent_loan = {
        "approved": loan["loan_amount"] > 0,
        "max_loan_amount": loan["loan_amount"],
        "monthly_payment": loan["monthly_payment"],
        "interest_rate": loan["interest_rate"],
        "loan_years": loan["loan_years"]
    }

    logger.info("Step 4: running agents with custom parameters")
    agents_results = await run_all_agents(adapted_user, agent_loan)

    # ─────────────────────────
    # 5️⃣ INVESTMENT EVALUATION
    # ─────────────────────────
    ranked = get_best_investments(adapted_user, agents_results, agent_loan)

    # ─────────────────────────
    # 6️⃣ JUDGE
    # ─────────────────────────
    logger.info("Step 6: judge agent")
    judgment = await run_judge_agent(adapted_user, agent_loan, ranked)

    # ─────────────────────────
    # 📊 OUTPUT
    # ─────────────────────────
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
        "recommendation": judgment["recommended"],
        "reasoning": judgment["reasoning"],
        "next_step": judgment["next_step"],
        "profile_used": judgment.get("profile_used", user_risk_pref),
    }


# ─────────────────────────
# 🛠️ HELPERS (California-aware)
# ─────────────────────────
def _build_user_summary(user) -> dict:
    """Builds user_summary with California region instead of country."""
    return {
        "region": user.location.region.value,
        "city": user.location.city,
        "country": "US",  # backward compat for downstream consumers
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
    """Builds risk section with California enrichments."""
    user_risk_pref = user.preferences.risk_profile.value
    creditworthiness = risk.get("creditworthiness", "medium")
    risk_explanation = build_risk_explanation(user_risk_pref, creditworthiness)

    return {
        "creditworthiness": creditworthiness,
        "explanation": risk_explanation,
        "score": risk["adjusted_score"],
        "level": risk["level"],

        # California enrichments
        "region": risk["region"],
        "region_display_name": risk["region_display_name"],
        "region_factor": risk["region_factor"],
        "cost_of_living_index": risk["cost_of_living_index"],
        "real_disposable_income": risk["real_disposable_income"],
        "real_savings": risk["real_savings"],
        "industry_adjustment": risk["industry_adjustment"],
        "equity_bonus": risk["equity_bonus"],

        # Standard outputs
        "disposable_income": risk["disposable_income"],
        "debt_ratio": risk["debt_ratio"],
        "base_score": risk["base_score"],

        # Backward compat
        "country": "US",
        "country_factor": risk["region_factor"],
    }