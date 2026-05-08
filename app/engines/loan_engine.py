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
    monthly_debt = user.financial.monthly_debt

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
    available_payment = max_monthly_payment - monthly_debt

    if available_payment <= 0:
        return {
            "approved": False,
            "reason": "Existing monthly debt too high"
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


# ─────────────────────────
# 🎯 CUSTOM LOAN CALCULATOR
# ─────────────────────────
def calculate_custom_loan(
        loan_amount: float,
        loan_years: int,
        annual_rate: float,
        user,
        risk: dict,
) -> dict:
    """
    Računa custom kredit prema korisnikovim izborima.
    Validira granice, vraća prilagođenu mesečnu ratu.

    Args:
        loan_amount: Koliko korisnik želi da uzme (0 = bez kredita)
        loan_years: Period otplate
        annual_rate: Kamata iz originalne /analyze (zaslužena)
        user: UserInput objekat
        risk: Output iz risk_engine

    Returns:
        dict sa simulation rezultatom ili greškom
    """
    income = user.financial.income
    monthly_debt = user.financial.monthly_debt
    country = user.location.country.value

    # Maksimumi (granice koje korisnik ne sme prekoračiti)
    max_monthly_payment = income * 0.35
    available_payment = max_monthly_payment - monthly_debt
    max_loan_years = COUNTRY_LOAN_YEARS.get(country, 5)

    # ─────────────────────────
    # 🚫 SCENARIJ: BEZ KREDITA
    # ─────────────────────────
    if loan_amount == 0:
        return {
            "approved": True,
            "loan_amount": 0,
            "monthly_payment": 0,
            "loan_years": 0,
            "interest_rate": 0,
            "total_paid": 0,
            "total_interest": 0,
            "country": country,
            "scenario": "no_loan"
        }

    # ─────────────────────────
    # 🔒 VALIDACIJA GRANICA
    # ─────────────────────────
    if loan_years > max_loan_years:
        return {
            "approved": False,
            "reason": f"loan_years ({loan_years}) prelazi maksimalnih {max_loan_years} za {country}"
        }

    months = loan_years * 12
    monthly_rate = annual_rate / 12

    # Računaj mesečnu ratu (anuitetna formula)
    if monthly_rate == 0:
        monthly_payment = loan_amount / months
    else:
        monthly_payment = (
                loan_amount * monthly_rate * ((1 + monthly_rate) ** months)
                / ((1 + monthly_rate) ** months - 1)
        )

    # Validacija: rata ne sme prekoračiti DTI buffer
    if monthly_payment > available_payment:
        return {
            "approved": False,
            "reason": (
                f"Mesečna rata ({round(monthly_payment, 2)}) prelazi tvoj DTI buffer "
                f"({round(available_payment, 2)}). Smanji iznos kredita ili produži period."
            )
        }

    total_paid = monthly_payment * months
    total_interest = total_paid - loan_amount

    return {
        "approved": True,
        "loan_amount": round(loan_amount, 2),
        "monthly_payment": round(monthly_payment, 2),
        "loan_years": loan_years,
        "interest_rate": annual_rate,
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "country": country,
        "scenario": "custom_loan"
    }