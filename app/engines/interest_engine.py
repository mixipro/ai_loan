# app/engines/interest_engine.py

from app.core.country_config import COUNTRY_INTEREST


def calculate_interest_rate(risk: dict, country: str) -> dict:
    """
    risk: output iz risk_engine
    country: ISO kod (RS, DE, US...)
    """

    # ─────────────────────────
    # 🔒 VALIDACIJA
    # ─────────────────────────
    if country not in COUNTRY_INTEREST:
        raise ValueError(f"Unsupported country: {country}")

    if "level" not in risk or "adjusted_score" not in risk:
        raise ValueError("Invalid risk input")

    # ─────────────────────────
    # 🌍 COUNTRY RANGE
    # ─────────────────────────
    min_rate, max_rate = COUNTRY_INTEREST[country]

    level = risk["level"]
    score = risk["adjusted_score"]

    # ─────────────────────────
    # 🎯 BASE (DISCRETE)
    # ─────────────────────────
    if level == "low_risk":
        base_rate = min_rate
    elif level == "medium_risk":
        base_rate = (min_rate + max_rate) / 2
    else:
        base_rate = max_rate

    # ─────────────────────────
    # 📈 CONTINUOUS MODEL (REALNOST)
    # ─────────────────────────
    # pretpostavljamo max score ≈ 15
    normalized = score / 15

    # clamp (za sigurnost)
    normalized = max(0, min(normalized, 1))

    # veći score → manja kamata
    score_rate = min_rate + (max_rate - min_rate) * (1 - normalized)

    # ─────────────────────────
    # ⚖️ BLEND MODEL
    # ─────────────────────────
    final_rate = (base_rate * 0.6) + (score_rate * 0.4)

    # dodatni clamp (sigurnost)
    final_rate = max(min_rate, min(final_rate, max_rate))

    # ─────────────────────────
    # 📊 OUTPUT
    # ─────────────────────────
    return {
        "interest_rate": round(final_rate, 4),
        "base_rate": round(base_rate, 4),
        "score_rate": round(score_rate, 4),
        "min_rate": min_rate,
        "max_rate": max_rate,
        "risk_level": level,
        "country": country,
        "score": score
    }