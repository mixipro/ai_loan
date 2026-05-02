# app/engines/risk_engine.py

from app.models.user import UserInput
from app.core.country_config import COUNTRY_RISK


def calculate_risk_score(user: UserInput) -> dict:
    score = 0

    # ─────────────────────────
    # 💰 DISPOSABLE INCOME
    # ─────────────────────────
    income = user.financial.income
    expenses = user.financial.expenses
    disposable = income - expenses

    if disposable > 1000:
        score += 3
    elif disposable > 500:
        score += 2
    else:
        score += 1

    # ─────────────────────────
    # 💰 SAVINGS
    # ─────────────────────────
    savings = user.financial.savings

    if savings > 20000:
        score += 3
    elif savings > 5000:
        score += 2
    elif savings > 2000:
        score += 1
    else:
        score += 0

    # ─────────────────────────
    # 📉 DEBT RATIO
    # ─────────────────────────
    debt = user.financial.debt
    debt_ratio = debt / income if income > 0 else 1

    if debt_ratio < 0.2:
        score += 3
    elif debt_ratio < 0.5:
        score += 2
    elif debt_ratio < 0.7:
        score += 0
    else:
        score += -1

    # ─────────────────────────
    # 💼 EMPLOYMENT STATUS
    # ─────────────────────────
    status = user.professional.employment_status

    if status.name == "FULL_TIME":
        score += 3
    elif status.name in ["PART_TIME", "SELF_EMPLOYED"]:
        score += 2
    elif status.name == "FREELANCER":
        score += 1
    else:  # unemployed, student, retired
        score += -1

    # ─────────────────────────
    # 👤 AGE
    # ─────────────────────────
    age = user.personal.age

    if 25 <= age <= 55:
        score += 2
    elif 25 < age <= 64:
        score += 1
    else:
        score += 0

    # ─────────────────────────
    # ⚙️ USER RISK PREFERENCE
    # ─────────────────────────
    pref = user.preferences.risk_profile

    if pref.name == "LOW":
        score += 1
    elif pref.name == "MEDIUM":
        score += 2
    else:
        score += 3

    # ─────────────────────────
    # 🌍 COUNTRY FACTOR
    # ─────────────────────────
    country = user.location.country.value
    country_factor = COUNTRY_RISK.get(country, 1.0)

    adjusted_score = score * (1 / country_factor)

    # ─────────────────────────
    # 🔥 FINAL RISK LEVEL
    # ─────────────────────────
    if adjusted_score >= 12:
        level = "low_risk"
    elif adjusted_score >= 8:
        level = "medium_risk"
    else:
        level = "high_risk"

    # ─────────────────────────
    # 📊 OUTPUT
    # ─────────────────────────
    return {
        "base_score": score,
        "adjusted_score": round(adjusted_score, 2),
        "level": level,
        "country": country,
        "country_factor": country_factor,
        "disposable_income": disposable,
        "debt_ratio": round(debt_ratio, 2)
    }