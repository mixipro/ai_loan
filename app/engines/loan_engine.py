# app/engines/loan_engine.py

from app.core.country_config import COUNTRY_LOAN_YEARS


def calculate_loan_offer(user, risk: dict, interest: dict) -> dict:
    """
    user: UserInput
    risk: output in risk_engine
    interest: output in interest_engine
    """

    income = user.financial.income
    expenses = user.financial.expenses
    debt = user.financial.debt

    disposable = income - expenses

    # ─────────────────────────
    # 🔒 VALIDACIJA
    # ─────────────────────────
    if disposable <= 0:
        return {
            "approved": False,
            "reason": "No disposable income"
        }

    # ─────────────────────────
    # 🏦 MAKSIMALNA RATA (DTI LOGIKA)
    # ─────────────────────────
    # max 30% od prihoda ide na kredit
    max_monthly_payment = income * 0.3

    # oduzmi postojeće obaveze
    available_payment = max_monthly_payment - debt

    if available_payment <= 0:
        return {
            "approved": False,
            "reason": "Existing debt too high"
        }

    # ─────────────────────────
    # 🌍 TRAJANJE KREDITA
    # ─────────────────────────
    country = user.location.country.value
    years = COUNTRY_LOAN_YEARS.get(country, 5)

    months = years * 12

    # ─────────────────────────
    # 💸 KAMATA
    # ─────────────────────────
    annual_rate = interest["interest_rate"]
    monthly_rate = annual_rate / 12

    # ─────────────────────────
    # 📊 FORMULA ZA KREDIT (ANUITET)
    # ─────────────────────────
    # M = P * r * (1+r)^n / ((1+r)^n - 1)
    # → računamo P (loan amount)

    if monthly_rate == 0:
        loan_amount = available_payment * months
    else:
        numerator = available_payment * ((1 + monthly_rate) ** months - 1)
        denominator = monthly_rate * ((1 + monthly_rate) ** months)

        loan_amount = numerator / denominator

    # sigurnosni clamp
    loan_amount = max(0, loan_amount)

    # ─────────────────────────
    # 📉 REALNA KOREKCIJA PO RIZIKU
    # ─────────────────────────
    level = risk["level"]

    if level == "high_risk":
        loan_amount *= 0.7
    elif level == "medium_risk":
        loan_amount *= 0.85
    # low_risk ostaje isto

    # ─────────────────────────
    # 📊 OUTPUT
    # ─────────────────────────
    return {
        "approved": True,
        "max_loan_amount": round(loan_amount, 2),
        "monthly_payment": round(available_payment, 2),
        "loan_years": years,
        "interest_rate": annual_rate,
        "country": country
    }