"""Quick smoke test for refactored real estate agent."""
import asyncio
from app.models.user import UserInput
from app.agents.real_estate_agent import run_real_estate_agent

user_data = {
    "personal": {"age": 32},
    "location": {"region": "BAY_AREA", "city": "Oakland"},
    "financial": {
        "income": 15000, "expenses": 5000, "monthly_debt": 800,
        "savings": 80000, "currency": "USD"
    },
    "professional": {
        "sector": "Technology", "profession": "Software Engineer",
        "employment_status": "full-time", "interests": ["real estate"],
        "prior_experience": "", "weekly_hours": "5-15"
    },
    "preferences": {"risk_profile": "medium", "horizon": "8+"}
}

user = UserInput(**user_data)


async def main():
    # 1. VALID — Mortgage $400k + Savings $100k (20% down)
    print("\n" + "=" * 70)
    print("TEST 1: VALID Direct Property ($400k mortgage + $100k down = 20%)")
    print("=" * 70)
    valid_config = {
        "loan_amount": 400000,
        "loan_years": 30,
        "savings_to_use": 100000,
        "interest_rate": 0.055,
    }
    result1 = await run_real_estate_agent(user, valid_config)
    print(f"Rejected:        {result1.get('rejected', False)}")
    print(f"Title:           {result1['title']}")
    print(f"Type:            {result1.get('type', 'N/A')}")
    print(f"Total capital:   ${result1['total_capital']:,}")
    print(f"Down %:          {result1.get('down_payment_pct', 0):.1%}")
    print(f"Expected return: {result1['expected_return']:.2%}")
    print(f"Risk:            {result1['risk']:.2f}")
    print(f"Stability:       {result1['stability']:.2f}")

    # 2. REJECTED — No mortgage (loan=0)
    print("\n" + "=" * 70)
    print("TEST 2: REJECT — Cash-only attempt (loan=0)")
    print("=" * 70)
    no_loan_config = {
        "loan_amount": 0,
        "loan_years": 0,
        "savings_to_use": 80000,
        "interest_rate": 0,
    }
    result2 = await run_real_estate_agent(user, no_loan_config)
    print(f"Rejected:        {result2.get('rejected', False)}")
    print(f"Title:           {result2['title']}")
    print(f"Reason:          {result2.get('rejection_reason', 'N/A')}")

    # 3. REJECTED — Down payment too low (10%)
    print("\n" + "=" * 70)
    print("TEST 3: REJECT — Down payment only 10% (below 20% min)")
    print("=" * 70)
    low_down_config = {
        "loan_amount": 450000,
        "loan_years": 30,
        "savings_to_use": 50000,  # 50k / 500k = 10%
        "interest_rate": 0.055,
    }
    result3 = await run_real_estate_agent(user, low_down_config)
    print(f"Rejected:        {result3.get('rejected', False)}")
    print(f"Title:           {result3['title']}")
    print(f"Reason:          {result3.get('rejection_reason', 'N/A')}")

    # 4. VALID — Exactly 20% (edge case)
    print("\n" + "=" * 70)
    print("TEST 4: VALID — Edge case (exactly 20%)")
    print("=" * 70)
    edge_config = {
        "loan_amount": 320000,
        "loan_years": 30,
        "savings_to_use": 80000,  # 80k / 400k = 20%
        "interest_rate": 0.055,
    }
    result4 = await run_real_estate_agent(user, edge_config)
    print(f"Rejected:        {result4.get('rejected', False)}")
    print(f"Title:           {result4['title']}")
    print(f"Type:            {result4.get('type', 'N/A')}")
    print(f"Down %:          {result4.get('down_payment_pct', 0):.1%}")


asyncio.run(main())