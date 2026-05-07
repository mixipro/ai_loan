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
    max_monthly_payment = income * 0.35

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
    # 📊 STEP 1: KOLIKI KREDIT MOŽE PRIMITI
    # (anuitetna formula: rata → kredit)
    # ─────────────────────────
    if monthly_rate == 0:
        loan_amount = available_payment * months
    else:
        numerator = available_payment * ((1 + monthly_rate) ** months - 1)
        denominator = monthly_rate * ((1 + monthly_rate) ** months)
        loan_amount = numerator / denominator

    loan_amount = max(0, loan_amount)

    # ─────────────────────────
    # 📉 STEP 2: REALNA KOREKCIJA PO RIZIKU
    # banka smanjuje iznos kredita za rizičnije klijente
    # ─────────────────────────
    level = risk["level"]

    if level == "high_risk":
        loan_amount *= 0.7
    elif level == "medium_risk":
        loan_amount *= 0.85
    # low_risk ostaje isto

    # ─────────────────────────
    # 🔁 STEP 3: PRERAČUNAJ STVARNU RATU
    # (anuitetna formula: kredit → rata)
    # nakon korekcije, rata MORA biti manja
    # ─────────────────────────
    if monthly_rate == 0:
        actual_payment = loan_amount / months
    else:
        actual_payment = (
            loan_amount * monthly_rate * ((1 + monthly_rate) ** months)
            / ((1 + monthly_rate) ** months - 1)
        )

    # ─────────────────────────
    # 📊 OUTPUT
    # ─────────────────────────
    return {
        "approved": True,
        "max_loan_amount": round(loan_amount, 2),
        "monthly_payment": round(actual_payment, 2),       # ← sad je tačno
        "max_allowed_payment": round(available_payment, 2), # ← bonus: max koji korisnik MOŽE plaćati
        "loan_years": years,
        "interest_rate": annual_rate,
        "country": country
    }