from app.models.user import UserInput
from app.agents.business_agent import run_business_agent


user = UserInput(
    personal={"age": 40},
    location={"country": "RU", "city": "Moscow"},
    financial={
        "income": 20000,
        "expenses": 4000,
        "debt": 2000,
        "savings": 100000,
        "currency": "EUR"
    },
    professional={
        "sector": "Real Estate",
        "profession": "Real Estate Investor",
        "employment_status": "self-employed",

    },
    preferences={
        "risk_profile": "medium",
        "horizon": "8+"
    }
)

loan = {
    "approved": True,
    "max_loan_amount": 1000000,
    "interest_rate": 0.02,
    "monthly_payment": 12755,
    "loan_years": 7
}

result = run_business_agent(user, loan)

print("\n🔥 RESULT:\n")
print(result)