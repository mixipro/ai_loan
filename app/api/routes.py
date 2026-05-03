from fastapi import APIRouter
from app.models.user import UserInput

from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_interest_rate
from app.engines.loan_engine import calculate_loan_offer


router = APIRouter()


@router.post("/analyze")
def analyze_user(user: UserInput):
    # 1️⃣ risk
    risk = calculate_risk_score(user)

    # 2️⃣ interest
    country = user.location.country.value
    interest = calculate_interest_rate(risk, country)

    # 3️⃣ loan
    loan = calculate_loan_offer(user, risk, interest)

    return {
        "risk": risk,
        "interest": interest,
        "loan": loan
    }