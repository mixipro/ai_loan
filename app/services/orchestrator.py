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
from app.engines.loan_engine import calculate_custom_loan

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
# 📝 BUILD RISK EXPLANATION
# ─────────────────────────
def build_risk_explanation(user_risk_pref: str, creditworthiness: str) -> str:
    """
    Generiše tekstualno objašnjenje razlike između investment risk tolerance
    i creditworthiness za korisnika.
    """
    base = (
        f"You selected '{user_risk_pref.upper()}' risk tolerance for INVESTMENTS. "
        f"Your financial profile rates as '{creditworthiness.upper()}' CREDITWORTHINESS "
        f"(this affects your loan terms, not investment selection). "
        f"These two dimensions are evaluated independently."
    )

    # Soft note kada se drastično razlikuju
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
    logger.info(
        f"Risk level: {risk['level']} | "
        f"Creditworthiness: {risk['creditworthiness']} | "
        f"Score: {risk['adjusted_score']}"
    )

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
    agents_results = await run_all_agents(user, loan)
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
    judgment = await run_judge_agent(user, loan, ranked)

    if judgment["recommended"]:
        logger.info(
            f"Judge recommended: {judgment['recommended']['agent']} "
            f"(profile: {judgment['profile_used']})"
        )

    # ─────────────────────────
    # 📝 BUILD RISK EXPLANATION ⭐ NOVO
    # ─────────────────────────
    user_risk_pref = user.preferences.risk_profile.value
    creditworthiness = risk.get("creditworthiness", "medium")
    risk_explanation = build_risk_explanation(user_risk_pref, creditworthiness)

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
            "monthly_debt": user.financial.monthly_debt,
            "savings": user.financial.savings,
            "currency": user.financial.currency.value,
            "risk_profile": user_risk_pref,  # user-ova preferencija
            "horizon": user.preferences.horizon.value,
        },
        "risk": {
            "creditworthiness": creditworthiness,  # ⭐ NOVO — bank-side rating
            "explanation": risk_explanation,  # ⭐ NOVO — objašnjenje razlike
            "score": risk["adjusted_score"],
            "level": risk["level"],  # backward compat
            "country": risk["country"],
            "country_factor": risk["country_factor"],
            "disposable_income": risk["disposable_income"],
            "debt_ratio": risk["debt_ratio"],
            "base_score": risk["base_score"],
        },
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
    """
    Custom kalkulator: korisnik bira parametre kredita i savings allokaciju.

    Tok:
    1. Risk + interest (kao i u /analyze — ne menja se po izboru)
    2. Custom loan calculation (sa korisnikovim izborima)
    3. Adapt user.savings na savings_to_invest
    4. Pokreni agente sa novim parametrima
    5. Investment evaluation
    6. Judge
    """
    logger.info("=" * 50)
    logger.info("Simulation pipeline started")
    logger.info(f"User chose: loan={simulation_choice.loan_amount}, "
                f"years={simulation_choice.loan_years}, "
                f"savings_to_invest={simulation_choice.savings_to_invest}")
    logger.info("=" * 50)

    # ─────────────────────────
    # 1️⃣ RISK + INTEREST (isti kao u /analyze)
    # ─────────────────────────
    risk = calculate_risk_score(user)
    country = user.location.country.value
    interest = calculate_interest_rate(risk, country)
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
        # 🚫 Custom loan ne prolazi validaciju
        return {
            "user_summary": _build_user_summary(user, country),
            "risk": _build_risk_section(user, risk),
            "interest": interest,
            "loan": loan,  # sadrži "reason"
            "simulation_request": simulation_choice.model_dump(),
            "error": "Simulation parameters invalid",
            "strategies": [],
            "recommendation": None,
        }

    # ─────────────────────────
    # 3️⃣ ADAPTIRAJ USER ZA SIMULACIJU
    # ─────────────────────────
    # Kreiraj kopiju user-a sa modifikovanim savings-om
    # (savings_to_invest = koliko zapravo ulaže, ostalo je rezerva)
    adapted_user = user.model_copy(deep=True)
    adapted_user.financial.savings = int(simulation_choice.savings_to_invest)

    logger.info(f"Adapted user: savings_to_invest={adapted_user.financial.savings}")

    # ─────────────────────────
    # 4️⃣ AGENTS — sa custom loan + adapted savings
    # ─────────────────────────
    # Konvertuj custom loan u format koji agenti očekuju
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
    creditworthiness = risk.get("creditworthiness", "medium")

    # Sačuvana ušteda (ne investirana)
    saved_buffer = user.financial.savings - simulation_choice.savings_to_invest
    total_invested = simulation_choice.savings_to_invest + simulation_choice.loan_amount

    return {
        "user_summary": _build_user_summary(user, country),
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
# 🛠️ HELPERS — refaktorisanje da ne dupliraju kod
# ─────────────────────────
def _build_user_summary(user, country: str) -> dict:
    return {
        "country": country,
        "city": user.location.city,
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
        "country": risk["country"],
        "country_factor": risk["country_factor"],
        "disposable_income": risk["disposable_income"],
        "debt_ratio": risk["debt_ratio"],
        "base_score": risk["base_score"],
    }
