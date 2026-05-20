"""Print output of all 3 modes."""
import asyncio
from app.models.user import UserInput
from app.agents.business_agent import run_business_agent

user_data = {
    "personal": {"age": 32},
    "location": {"region": "BAY_AREA", "city": "San Francisco"},
    "financial": {
        "income": 15000, "expenses": 5000, "monthly_debt": 800,
        "savings": 80000, "currency": "USD"
    },
    "professional": {
        "sector": "Technology", "profession": "Software Engineer",
        "employment_status": "full-time", "interests": ["technology"],
        "prior_experience": "", "weekly_hours": "5-15"
    },
    "preferences": {"risk_profile": "medium", "horizon": "5-8"}
}

user = UserInput(**user_data)


async def main():
    for mode_name, config in [
        ("CASH", {"loan_amount": 0, "loan_years": 0, "savings_to_use": 50000, "interest_rate": 0}),
        ("LOAN", {"loan_amount": 100000, "loan_years": 7, "savings_to_use": 0, "interest_rate": 0.07}),
        ("MIXED", {"loan_amount": 50000, "loan_years": 7, "savings_to_use": 30000, "interest_rate": 0.07}),
    ]:
        result = await run_business_agent(user, config)
        print(f"\n{'='*60}")
        print(f"MODE: {mode_name}")
        print(f"{'='*60}")
        print(f"Title:           {result['title']}")
        print(f"Mode:            {result['funding_mode']}")
        print(f"Total capital:   ${result['total_capital']:,}")
        print(f"Loan amount:     ${result['loan_amount']:,}")
        print(f"Savings used:    ${result['savings_used']:,}")
        print(f"Expected return: {result['expected_return']:.2%}")
        print(f"Risk:            {result['risk']:.2f}")
        print(f"Stability:       {result['stability']:.2f}")
        print(f"RAG sources:     {result['rag_sources']}")
        print(f"Description:     {result['description'][:100]}...")


asyncio.run(main())