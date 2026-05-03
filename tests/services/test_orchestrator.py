from app.models.user import UserInput
from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_interest_rate
from app.engines.loan_engine import calculate_loan_offer


def test_full_pipeline():
    user = UserInput(
        personal={"age": 30},
        location={"country": "RS", "city": "Belgrade"},
        financial={
            "income": 1500,
            "expenses": 500,
            "debt": 100,
            "savings": 5000,
            "currency": "EUR"
        },
        professional={
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "full-time"
        },
        preferences={
            "risk_profile": "medium",
            "horizon": "3-5"
        }
    )

    risk = calculate_risk_score(user)
    interest = calculate_interest_rate(risk, user.location.country.value)
    loan = calculate_loan_offer(user, risk, interest)

    assert loan["approved"] is True
    assert loan["max_loan_amount"] > 0
    assert loan["monthly_payment"] > 0
    assert interest["interest_rate"] > 0
    assert risk["level"] in ["low_risk", "medium_risk", "high_risk"]