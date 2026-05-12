# app/engines/loan_engine.py

"""
California / US loan calculator.
USD-only system, uses standard US loan terms.
"""

# Standard loan periods for California / US
# Personal: 5 years, Mortgage: 30 years (handled separately)
US_DEFAULT_LOAN_YEARS = {
    "personal": 5,
    "mortgage": 30,
    "business": 7,
}


def calculate_loan_offer(user, risk: dict, interest: dict, loan_type: str = "personal") -> dict:
    """
    Calculates maximum loan offer for a California user.

    user: UserInput
    risk: output from risk_engine
    interest: output from interest_engine
    loan_type: "personal", "mortgage", or "business"
    """

    income = user.financial.income
    expenses = user.financial.expenses
    monthly_debt = user.financial.monthly_debt

    disposable = income - expenses

    # ─────────────────────────
    # 🔒 VALIDATION
    # ─────────────────────────
    if disposable <= 0:
        return {
            "approved": False,
            "reason": "No disposable income"
        }

    # ─────────────────────────
    # 🏦 MAX MONTHLY PAYMENT (DTI LOGIC)
    # ─────────────────────────
    # 35% DTI limit for US loans
    max_monthly_payment = income * 0.35
    available_payment = max_monthly_payment - monthly_debt

    if available_payment <= 0:
        return {
            "approved": False,
            "reason": "Existing monthly debt too high"
        }

    # ─────────────────────────
    # 🌴 LOAN DURATION (US default)
    # ─────────────────────────
    years = US_DEFAULT_LOAN_YEARS.get(loan_type, 5)
    months = years * 12

    # ─────────────────────────
    # 💸 INTEREST
    # ─────────────────────────
    annual_rate = interest["interest_rate"]
    monthly_rate = annual_rate / 12

    # ─────────────────────────
    # 📊 STEP 1: MAX LOAN AMOUNT
    # ─────────────────────────
    if monthly_rate == 0:
        loan_amount = available_payment * months
    else:
        numerator = available_payment * ((1 + monthly_rate) ** months - 1)
        denominator = monthly_rate * ((1 + monthly_rate) ** months)
        loan_amount = numerator / denominator

    loan_amount = max(0, loan_amount)

    # ─────────────────────────
    # 📉 STEP 2: RISK ADJUSTMENT
    # ─────────────────────────
    level = risk["level"]

    if level == "high_risk":
        loan_amount *= 0.7
    elif level == "medium_risk":
        loan_amount *= 0.85
    # low_risk stays the same

    # ─────────────────────────
    # 🔁 STEP 3: RECALCULATE ACTUAL PAYMENT
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
        "monthly_payment": round(actual_payment, 2),
        "max_allowed_payment": round(available_payment, 2),
        "loan_years": years,
        "interest_rate": annual_rate,
        "loan_type": loan_type,
        "country": "US",  # backward compat
        "region": user.location.region.value,
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
        loan_type: str = "personal",
) -> dict:
    """
    Custom loan calculation based on user choices.
    """
    income = user.financial.income
    monthly_debt = user.financial.monthly_debt
    region = user.location.region.value

    max_monthly_payment = income * 0.35
    available_payment = max_monthly_payment - monthly_debt
    max_loan_years = US_DEFAULT_LOAN_YEARS.get(loan_type, 5)

    # ─────────────────────────
    # 🚫 NO LOAN SCENARIO
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
            "country": "US",
            "region": region,
            "scenario": "no_loan"
        }

    # ─────────────────────────
    # 🔒 VALIDATION
    # ─────────────────────────
    if loan_years > max_loan_years:
        return {
            "approved": False,
            "reason": f"loan_years ({loan_years}) exceeds maximum {max_loan_years} for {loan_type} loans"
        }

    months = loan_years * 12
    monthly_rate = annual_rate / 12

    if monthly_rate == 0:
        monthly_payment = loan_amount / months
    else:
        monthly_payment = (
                loan_amount * monthly_rate * ((1 + monthly_rate) ** months)
                / ((1 + monthly_rate) ** months - 1)
        )

    if monthly_payment > available_payment:
        return {
            "approved": False,
            "reason": (
                f"Monthly payment ({round(monthly_payment, 2)}) exceeds your DTI buffer "
                f"({round(available_payment, 2)}). Reduce loan or extend period."
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
        "country": "US",
        "region": region,
        "scenario": "custom_loan"
    }