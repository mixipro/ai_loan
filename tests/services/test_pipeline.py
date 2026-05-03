from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_interest_rate
from app.engines.loan_engine import calculate_loan_offer


def run_pipeline(user):
    risk = calculate_risk_score(user)
    interest = calculate_interest_rate(risk, user.location.country.value)
    loan = calculate_loan_offer(user, risk, interest)

    return risk, interest, loan


def test_pipeline_success(base_user):
    risk, interest, loan = run_pipeline(base_user)

    assert loan["approved"] is True
    assert loan["max_loan_amount"] > 0
    assert loan["monthly_payment"] > 0
    assert interest["interest_rate"] > 0
    assert risk["level"] in ["low_risk", "medium_risk", "high_risk"]


def test_pipeline_rejected(low_income_user):
    risk, interest, loan = run_pipeline(low_income_user)

    assert loan["approved"] is False


def test_pipeline_high_income(high_income_user):
    risk, interest, loan = run_pipeline(high_income_user)

    assert loan["approved"] is True
    assert loan["max_loan_amount"] > 10000
