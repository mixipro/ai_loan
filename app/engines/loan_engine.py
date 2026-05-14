# app/engines/loan_engine.py

"""
California / US multi-loan-type calculator.
Supports per-strategy loans: business, mortgage, margin, personal.
"""

from app.engines.interest_engine import LOAN_TYPES


def calculate_loan_offer(
    user,
    risk: dict,
    interest: dict,
    loan_type: str = "personal"
) -> dict:
    """
    Calculates maximum loan offer for given loan type.
    """
    if loan_type not in LOAN_TYPES:
        return {"approved": False, "reason": f"Unsupported loan type: {loan_type}"}

    loan_config = LOAN_TYPES[loan_type]

    income = user.financial.income
    expenses = user.financial.expenses
    monthly_debt = user.financial.monthly_debt
    savings = user.financial.savings

    disposable = income - expenses

    if disposable <= 0:
        return {"approved": False, "reason": "No disposable income"}

    # 🏦 DTI LIMIT (varies by loan type)
    dti_limit = loan_config["dti_limit"]
    max_monthly_payment = income * dti_limit
    available_payment = max_monthly_payment - monthly_debt

    if available_payment <= 0:
        return {"approved": False, "reason": "Existing debt exceeds DTI limit"}

    # 📅 LOAN DURATION
    years = loan_config["default_years"]
    months = years * 12

    # 💸 INTEREST
    annual_rate = interest["interest_rate"]
    monthly_rate = annual_rate / 12

    # 📊 MAX LOAN AMOUNT (PV formula)
    if monthly_rate == 0:
        loan_amount = available_payment * months
    else:
        numerator = available_payment * ((1 + monthly_rate) ** months - 1)
        denominator = monthly_rate * ((1 + monthly_rate) ** months)
        loan_amount = numerator / denominator

    loan_amount = max(0, loan_amount)

    # 📉 RISK ADJUSTMENT
    level = risk["level"]
    if level == "high_risk":
        loan_amount *= 0.7
    elif level == "medium_risk":
        loan_amount *= 0.85

    # ⭐ NEW: LTV (Loan-to-Value) check for margin loans
    # Margin: max 50% LTV of savings (broker rules)
    if loan_type == "margin":
        max_margin = savings * 0.5  # 50% LTV
        loan_amount = min(loan_amount, max_margin)

    # ⭐ NEW: Mortgage requires 20% down payment minimum
    if loan_type == "mortgage":
        # Mortgage max = 4x savings (savings = 20% down payment)
        max_mortgage = savings * 4.0
        loan_amount = min(loan_amount, max_mortgage)

    # 🔁 RECALCULATE ACTUAL PAYMENT
    if monthly_rate == 0:
        actual_payment = loan_amount / months
    else:
        actual_payment = (
            loan_amount * monthly_rate * ((1 + monthly_rate) ** months)
            / ((1 + monthly_rate) ** months - 1)
        )

    # 💰 TOTAL COST CALCULATIONS
    total_paid = actual_payment * months
    total_interest = total_paid - loan_amount
    annual_payment = actual_payment * 12

    return {
        "approved": True,
        "loan_type": loan_type,
        "loan_description": loan_config["description"],
        "max_loan_amount": round(loan_amount, 2),
        "monthly_payment": round(actual_payment, 2),
        "annual_payment": round(annual_payment, 2),
        "max_allowed_payment": round(available_payment, 2),
        "loan_years": years,
        "interest_rate": annual_rate,
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "dti_used": round((actual_payment + monthly_debt) / income, 3),
        "country": "US",
        "region": user.location.region.value,
    }


def calculate_all_strategy_loans(user, risk: dict, all_rates: dict) -> dict:
    """
    Calculates loan offers for ALL strategy types.
    Returns dict: {strategy_name: loan_offer}
    """
    return {
        "business":     calculate_loan_offer(user, risk, all_rates["business"],  "business"),
        "real_estate":  calculate_loan_offer(user, risk, all_rates["mortgage"],  "mortgage"),
        "stock_margin": calculate_loan_offer(user, risk, all_rates["margin"],    "margin"),
        "personal":     calculate_loan_offer(user, risk, all_rates["personal"],  "personal"),
    }


def calculate_custom_loan(
    loan_amount: float,
    loan_years: int,
    annual_rate: float,
    user,
    risk: dict,
    loan_type: str = "personal",
) -> dict:
    """
    Custom loan calculation for simulator.
    """
    if loan_type not in LOAN_TYPES:
        return {"approved": False, "reason": f"Unsupported loan type: {loan_type}"}

    loan_config = LOAN_TYPES[loan_type]
    income = user.financial.income
    monthly_debt = user.financial.monthly_debt
    region = user.location.region.value

    dti_limit = loan_config["dti_limit"]
    max_monthly_payment = income * dti_limit
    available_payment = max_monthly_payment - monthly_debt

    max_loan_years = loan_config["max_years"]

    if loan_amount == 0:
        return {
            "approved": True,
            "loan_amount": 0,
            "monthly_payment": 0,
            "annual_payment": 0,
            "loan_years": 0,
            "interest_rate": 0,
            "total_paid": 0,
            "total_interest": 0,
            "country": "US",
            "region": region,
            "loan_type": loan_type,
            "scenario": "no_loan",
        }

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
                f"Monthly payment (${round(monthly_payment, 2)}) exceeds DTI buffer "
                f"(${round(available_payment, 2)}). Reduce loan or extend period."
            )
        }

    total_paid = monthly_payment * months
    total_interest = total_paid - loan_amount
    annual_payment = monthly_payment * 12

    return {
        "approved": True,
        "loan_amount": round(loan_amount, 2),
        "monthly_payment": round(monthly_payment, 2),
        "annual_payment": round(annual_payment, 2),
        "loan_years": loan_years,
        "interest_rate": annual_rate,
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "country": "US",
        "region": region,
        "loan_type": loan_type,
        "scenario": "custom_loan",
    }