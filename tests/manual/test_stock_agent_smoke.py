"""Quick smoke test for refactored stock agent."""
import asyncio
from app.models.user import UserInput
from app.agents.stock_agent import run_stock_agent

user_data = {
    "personal": {"age": 32},
    "location": {"region": "BAY_AREA", "city": "San Francisco"},
    "financial": {
        "income": 15000, "expenses": 5000, "monthly_debt": 800,
        "savings": 80000, "currency": "USD"
    },
    "professional": {
        "sector": "Technology", "profession": "Software Engineer",
        "employment_status": "full-time", "interests": ["investing"],
        "prior_experience": "", "weekly_hours": "5-15",
        "equity_compensation": "RSU (Restricted Stock Units)"
    },
    "preferences": {"risk_profile": "medium", "horizon": "5-8"}
}

user = UserInput(**user_data)


async def main():
    # 1. CASH ($60k savings, no margin)
    print("\n" + "=" * 60)
    print("MODE 1: CASH-ONLY ($60k savings)")
    print("=" * 60)
    cash_config = {
        "loan_amount": 0,
        "loan_years": 0,
        "savings_to_use": 60000,
        "interest_rate": 0,
    }
    cash_result = await run_stock_agent(user, cash_config)
    print(f"Title:           {cash_result['title']}")
    print(f"Mode:            {cash_result['funding_mode']}")
    print(f"Total capital:   ${cash_result['total_capital']:,}")
    print(f"Expected return: {cash_result['expected_return']:.2%}")
    print(f"Risk:            {cash_result['risk']:.2f}")
    print(f"Stability:       {cash_result['stability']:.2f}")
    print(f"Allocation:      {cash_result['allocation']}")
    print(f"RAG sources:     {cash_result['rag_sources']}")

    # 2. MARGIN ($40k margin + $40k savings)
    print("\n" + "=" * 60)
    print("MODE 2: MARGIN ($40k margin + $40k savings)")
    print("=" * 60)
    margin_config = {
        "loan_amount": 40000,
        "loan_years": 5,
        "savings_to_use": 40000,
        "interest_rate": 0.08,
    }
    margin_result = await run_stock_agent(user, margin_config)
    print(f"Title:           {margin_result['title']}")
    print(f"Mode:            {margin_result['funding_mode']}")
    print(f"Total capital:   ${margin_result['total_capital']:,}")
    print(f"Expected return: {margin_result['expected_return']:.2%}")
    print(f"Risk:            {margin_result['risk']:.2f}  (>=0.6 forced)")
    print(f"Stability:       {margin_result['stability']:.2f}  (<=0.6 forced)")
    print(f"Allocation:      {margin_result['allocation']}")
    print(f"RAG sources:     {margin_result['rag_sources']}")

    # 3. MARGIN with LTV OVERFLOW ($60k margin + $40k savings — should auto-cap)
    print("\n" + "=" * 60)
    print("MODE 3: MARGIN with LTV cap ($60k margin requested + $40k savings)")
    print("=" * 60)
    overflow_config = {
        "loan_amount": 60000,  # Higher than savings
        "loan_years": 5,
        "savings_to_use": 40000,
        "interest_rate": 0.08,
    }
    overflow_result = await run_stock_agent(user, overflow_config)
    print(f"Title:           {overflow_result['title']}")
    print(f"Loan amount:     ${overflow_result['loan_amount']:,}  (auto-capped from $60k to $40k)")
    print(f"LTV capped:      {overflow_result.get('ltv_capped', False)}")
    print(f"LTV warning:     {overflow_result.get('ltv_warning', 'none')}")


asyncio.run(main())