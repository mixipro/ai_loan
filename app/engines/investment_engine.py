# app/engines/investment_engine.py

from app.engines.inflation_engine import real_return, AgentType


# ─────────────────────────
# 🎯 SCORE FORMULA
# ─────────────────────────
def calculate_score(real_roi: float, risk: float, stability: float) -> float:
    """
    score = ROI * 0.5 + stability * 0.3 + (1 - risk) * 0.2
    """
    return round(
        real_roi * 0.5 +
        stability * 0.3 +
        (1 - risk) * 0.2,
        4
    )


# ─────────────────────────
# 🔍 CORE ENGINE
# ─────────────────────────
def evaluate_investments(user, agents_results: list, loan: dict) -> list:
    country = user.location.country.value
    currency = user.financial.currency.value

    results = []

    for agent_data in agents_results:
        agent_name = agent_data["agent"]
        nominal = agent_data["expected_return"]
        risk = agent_data.get("risk", 0.5)
        stability = agent_data.get("stability", 0.5)

        agent_type = AgentType(agent_name)

        # 📉 REAL ROI
        real_roi = real_return(
            nominal_return=nominal,
            agent=agent_type,
            country=country,
            currency=currency
        )

        # 🏦 LOAN-AWARE FILTER + NET RETURN
        if loan["approved"]:
            interest = loan["interest_rate"]
            net_return = real_roi - interest

            if real_roi < interest:
                status = "not_profitable"
            else:
                status = "profitable"
        else:
            net_return = real_roi
            status = "no_loan"

        # 🎯 SCORE
        score = calculate_score(real_roi, risk, stability)

        # ⭐ čuvamo SVA polja iz agenta + dodajemo numerička
        enriched = {
            **agent_data,
            "nominal_return": nominal,
            "real_return": real_roi,
            "net_return": round(net_return, 4),
            "score": score,
            "status": status,
        }

        results.append(enriched)

    return results


# ─────────────────────────
# 🏆 RANKING
# ─────────────────────────
def rank_investments(results: list) -> list:
    return sorted(results, key=lambda x: x["score"], reverse=True)


# ─────────────────────────
# 🚀 FINAL PIPELINE
# ─────────────────────────
def get_best_investments(user, agents_results: list, loan: dict) -> list:
    evaluated = evaluate_investments(user, agents_results, loan)
    ranked = rank_investments(evaluated)
    return ranked