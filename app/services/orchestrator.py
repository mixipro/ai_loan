# app/services/orchestrator.py

import asyncio
import logging

from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_interest_rate
from app.engines.loan_engine import calculate_loan_offer
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
    """
    Pokreće sva tri agenta PARALELNO preko asyncio.gather.
    return_exceptions=True znači da exception JEDNOG agenta ne ruši ostale.
    """
    agent_definitions = [
        ("stock", run_stock_agent),
        ("business", run_business_agent),
        ("real_estate", run_real_estate_agent),
    ]

    logger.info("Launching agents in parallel...")

    # 🚀 Paralelno pokretanje
    tasks = [agent_fn(user, loan) for _, agent_fn in agent_definitions]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 🛡️ Mapiranje rezultata + fallback za exception-e
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
# 🚀 FINAL PIPELINE — ASYNC
# ─────────────────────────
async def run_pipeline(user) -> dict:
    """
    Glavni tok sistema (async):
    user → risk → interest → loan → [agents PARALLEL] → investment eval → judge → result
    """
    logger.info("=" * 50)
    logger.info("Pipeline started")
    logger.info("=" * 50)

    # ─────────────────────────
    # 1️⃣ RISK (sync — matematika)
    # ─────────────────────────
    logger.info("Step 1: calculating risk score")
    risk = calculate_risk_score(user)
    logger.info(f"Risk level: {risk['level']} (score: {risk['adjusted_score']})")

    # ─────────────────────────
    # 2️⃣ INTEREST (sync — matematika)
    # ─────────────────────────
    logger.info("Step 2: calculating interest rate")
    country = user.location.country.value
    interest = calculate_interest_rate(risk, country)
    logger.info(f"Interest rate: {interest['interest_rate']}")

    # ─────────────────────────
    # 3️⃣ LOAN (sync — matematika)
    # ─────────────────────────
    logger.info("Step 3: calculating loan offer")
    loan = calculate_loan_offer(user, risk, interest)

    if loan["approved"]:
        logger.info(f"Loan approved: {loan['max_loan_amount']} ({loan['loan_years']}y)")
    else:
        logger.warning(f"Loan rejected: {loan.get('reason')}")

    # ─────────────────────────
    # 4️⃣ AGENTS — ASYNC PARALLEL ⭐
    # ─────────────────────────
    logger.info("Step 4: running investment agents in parallel")
    agents_results = await run_all_agents(user, loan)   # ⭐ await
    logger.info(f"Agents returned {len(agents_results)} strategies")

    # ─────────────────────────
    # 5️⃣ INVESTMENT EVALUATION (sync — matematika)
    # ─────────────────────────
    logger.info("Step 5: evaluating + ranking strategies")
    ranked = get_best_investments(user, agents_results, loan)

    # ─────────────────────────
    # 6️⃣ JUDGE — ASYNC ⭐
    # ─────────────────────────
    logger.info("Step 6: judge agent — selecting best strategy")
    judgment = await run_judge_agent(user, loan, ranked)   # ⭐ await

    if judgment["recommended"]:
        logger.info(
            f"Judge recommended: {judgment['recommended']['agent']} "
            f"(profile: {judgment['profile_used']})"
        )

    # ─────────────────────────
    # 📊 OUTPUT
    # ─────────────────────────
    logger.info("Pipeline finished")

    return {
        "user_summary": {
            "country": country,
            "city": user.location.city,
            "age": user.personal.age,
            "income": user.financial.income,
            "expenses": user.financial.expenses,
            "savings": user.financial.savings,
            "currency": user.financial.currency.value,
            "risk_profile": user.preferences.risk_profile.value,
            "horizon": user.preferences.horizon.value,
        },
        "risk": risk,
        "interest": interest,
        "loan": loan,
        "strategies": ranked,
        "recommendation": judgment["recommended"],
        "reasoning": judgment["reasoning"],
        "next_step": judgment["next_step"],
        "profile_used": judgment["profile_used"],
    }