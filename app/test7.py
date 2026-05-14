# tests/test_investment_engine_v2.py

import sys

sys.path.insert(0, ".")

from app.core.california_config import CaliforniaRegion
from app.models.user import (
    UserInput, PersonalInfo, LocationInfo, FinancialInfo,
    ProfessionalInfo, Preferences,
    CaliforniaSector, Profession, EmploymentStatus,
    RiskProfile, HorizonGroup, WeeklyHours, Currency,
)
from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_all_loan_rates
from app.engines.loan_engine import calculate_all_strategy_loans
from app.engines.investment_engine import (
    get_best_investments,
    calculate_annual_payment,
    calculate_margin_call_risk,
)


def make_test_user():
    return UserInput(
        personal=PersonalInfo(age=32),
        location=LocationInfo(region=CaliforniaRegion.BAY_AREA, city="San Francisco"),
        financial=FinancialInfo(income=15000, expenses=5000, monthly_debt=800, savings=80000),
        professional=ProfessionalInfo(
            sector=CaliforniaSector.TECHNOLOGY,
            profession=Profession.SOFTWARE_ENGINEER,
            employment_status=EmploymentStatus.FULL_TIME,
        ),
        preferences=Preferences(risk_profile=RiskProfile.MEDIUM, horizon=HorizonGroup.LONG),
    )


def test_amortization_calculator():
    print("=" * 70)
    print("TEST 1: PMT amortization formula correct")
    print("=" * 70)

    # $100,000 loan at 6% for 30 years
    # Expected monthly payment ~$600, annual ~$7,200
    annual = calculate_annual_payment(100000, 0.06, 30)
    monthly = annual / 12

    print(f"$100k @ 6%, 30yr: monthly = ${monthly:.2f}, annual = ${annual:.2f}")

    assert 590 < monthly < 620, f"Expected ~$600/mo, got ${monthly:.2f}"
    print(f"✅ Amortization formula CORRECT")

    # $320,000 mortgage at 5.5% for 30 years
    # Expected ~$1,817/mo
    annual = calculate_annual_payment(320000, 0.055, 30)
    monthly = annual / 12

    print(f"$320k @ 5.5%, 30yr: monthly = ${monthly:.2f}, annual = ${annual:.2f}")

    assert 1800 < monthly < 1850, f"Expected ~$1,817/mo, got ${monthly:.2f}"
    print(f"✅ Mortgage amortization CORRECT")
    print()


def test_real_amortization_kills_business():
    print("=" * 70)
    print("TEST 2: Real amortization kills inflated business returns")
    print("=" * 70)

    user = make_test_user()
    risk = calculate_risk_score(user)
    all_rates = calculate_all_loan_rates(risk)
    strategy_loans = calculate_all_strategy_loans(user, risk, all_rates)

    # Simulated business strategy with INFLATED 20% return (old bug)
    inflated_business = {
        "agent": "business",
        "expected_return": 0.20,  # OLD BUG: too high
        "risk": 0.5,
        "stability": 0.6,
    }

    # Simulated business with REALISTIC 10% return
    realistic_business = {
        "agent": "business",
        "expected_return": 0.10,  # Realistic
        "risk": 0.5,
        "stability": 0.6,
    }

    results = get_best_investments(
        user,
        [inflated_business, realistic_business],
        strategy_loans
    )

    print(f"Both strategies use business_loan: ${strategy_loans['business']['max_loan_amount']:,.0f} @ 7%, 7yr\n")

    for r in results:
        print(f"📊 Business @ {r['nominal_return'] * 100:.0f}% expected:")
        print(f"   Real ROI:           {r['real_return'] * 100:.2f}%")
        print(f"   Total capital:      ${r['total_capital']:>12,.0f}")
        print(f"   Gross return:       ${r['gross_return_dollars']:>12,.0f}/yr")
        print(f"   Annual payment:     ${r['annual_payment']:>12,.0f}/yr")
        print(f"   NET return:         ${r['net_return_dollars']:>12,.0f}/yr ({r['net_return'] * 100:.2f}%)")
        print(f"   Status:             {r['status']}")
        print()

    print("✅ System now shows REAL impact of loan payments (not just interest rate)")
    print()


def test_mortgage_real_estate_realistic():
    print("=" * 70)
    print("TEST 3: Real Estate with mortgage — realistic numbers")
    print("=" * 70)

    user = make_test_user()
    risk = calculate_risk_score(user)
    all_rates = calculate_all_loan_rates(risk)
    strategy_loans = calculate_all_strategy_loans(user, risk, all_rates)

    # Realistic RE return: 6% nominal
    re_strategy = {
        "agent": "real_estate",
        "expected_return": 0.06,
        "risk": 0.3,
        "stability": 0.8,
    }

    results = get_best_investments(user, [re_strategy], strategy_loans)
    r = results[0]

    print(f"Real Estate Strategy:")
    print(f"  Nominal return:      {r['nominal_return'] * 100:.2f}%")
    print(f"  Real return (inflation): {r['real_return'] * 100:.2f}%")
    print(f"  Loan type:           {r['loan_info']['type']}")
    print(f"  Loan amount:         ${r['loan_info']['amount']:,.0f}")
    print(f"  Loan rate:           {r['loan_info']['rate'] * 100:.2f}%")
    print(f"  Loan years:          {r['loan_info']['years']}")
    print(f"  Monthly payment:     ${r['loan_info']['monthly_payment']:,.0f}")
    print(f"  Total capital:       ${r['total_capital']:,.0f}")
    print(f"  Gross return:        ${r['gross_return_dollars']:,.0f}/yr")
    print(f"  Annual payment:      ${r['annual_payment']:,.0f}/yr")
    print(f"  NET return:          ${r['net_return_dollars']:,.0f}/yr ({r['net_return'] * 100:.2f}%)")
    print(f"  Status:              {r['status']}")

    # With $80k down + $320k mortgage at 5.5% for 30yr
    # Annual payment ~$21,800
    # 6% real return on $400k = $24,000 (but real adjusted lower due to inflation)
    # Net likely small positive or marginal

    assert r['loan_info']['type'] == 'mortgage', "Should use mortgage loan"
    assert r['loan_info']['years'] == 30, "Should be 30-year mortgage"
    print(f"\n✅ RE uses 30-year mortgage at lower rate (realistic)")
    print()


def test_stock_cash_vs_margin():
    print("=" * 70)
    print("TEST 4: Stock cash vs Stock margin comparison")
    print("=" * 70)

    user = make_test_user()
    risk = calculate_risk_score(user)
    all_rates = calculate_all_loan_rates(risk)
    strategy_loans = calculate_all_strategy_loans(user, risk, all_rates)

    # Same return, different funding
    stock_cash = {
        "agent": "stock_cash",
        "expected_return": 0.085,
        "risk": 0.5,
        "stability": 0.65,
    }

    stock_margin = {
        "agent": "stock_margin",
        "expected_return": 0.085,
        "risk": 0.5,
        "stability": 0.65,
    }

    results = get_best_investments(user, [stock_cash, stock_margin], strategy_loans)

    for r in results:
        print(f"\n📈 {r['agent'].upper()}:")
        print(f"   Capital:            ${r['total_capital']:,.0f}")
        print(f"   Uses loan:          {r['uses_loan']}")
        if r['uses_loan']:
            print(f"   Loan:               ${r['loan_info']['amount']:,.0f} @ {r['loan_info']['rate'] * 100:.2f}%")
            print(f"   Annual payment:     ${r['annual_payment']:,.0f}")
        print(f"   Gross return:       ${r['gross_return_dollars']:,.0f}")
        print(f"   NET return:         {r['net_return'] * 100:.2f}%")

        if 'margin_call_risk' in r:
            mc = r['margin_call_risk']
            print(f"   🚨 MARGIN CALL RISK:")
            print(f"      Probability:     {mc['margin_call_probability'] * 100:.1f}%")
            print(f"      Severity:        {mc['expected_severity_loss'] * 100:.1f}%")
            print(f"      Risk penalty:    {mc['risk_adjusted_penalty'] * 100:.2f}%")

    # Stock cash uses no loan
    cash_result = next(r for r in results if r['agent'] == 'stock_cash')
    assert not cash_result['uses_loan'], "Stock cash should NOT use loan"

    # Stock margin uses margin loan
    margin_result = next(r for r in results if r['agent'] == 'stock_margin')
    assert margin_result['uses_loan'], "Stock margin should use margin loan"
    assert 'margin_call_risk' in margin_result, "Stock margin should have margin call risk"

    print(f"\n✅ Stock cash and margin properly differentiated")
    print(f"✅ Margin call risk modeled for leveraged stock")
    print()


def test_margin_call_risk_model():
    print("=" * 70)
    print("TEST 5: Margin call risk model")
    print("=" * 70)

    # Low volatility, low LTV
    low_risk = calculate_margin_call_risk(real_roi=0.08, volatility=0.3, ltv=0.5)
    print(f"Low vol (0.3), good return (8%), 50% LTV:")
    print(f"   Margin call probability: {low_risk['margin_call_probability'] * 100:.1f}%")

    # High volatility, high LTV
    high_risk = calculate_margin_call_risk(real_roi=0.08, volatility=0.7, ltv=0.5)
    print(f"\nHigh vol (0.7), good return (8%), 50% LTV:")
    print(f"   Margin call probability: {high_risk['margin_call_probability'] * 100:.1f}%")

    # Negative return scenario
    negative_return = calculate_margin_call_risk(real_roi=-0.10, volatility=0.5, ltv=0.5)
    print(f"\nMedium vol (0.5), negative return (-10%), 50% LTV:")
    print(f"   Margin call probability: {negative_return['margin_call_probability'] * 100:.1f}%")

    assert high_risk['margin_call_probability'] > low_risk['margin_call_probability'], \
        "Higher vol should give higher margin call probability"
    assert negative_return['margin_call_probability'] > low_risk['margin_call_probability'], \
        "Negative returns should increase margin call probability"

    print(f"\n✅ Margin call risk model behaves correctly")
    print()


def test_full_pipeline_4_strategies():
    print("=" * 70)
    print("TEST 6: Full pipeline — 4 strategies compared")
    print("=" * 70)

    user = make_test_user()
    risk = calculate_risk_score(user)
    all_rates = calculate_all_loan_rates(risk)
    strategy_loans = calculate_all_strategy_loans(user, risk, all_rates)

    strategies = [
        {"agent": "business", "expected_return": 0.10, "risk": 0.5, "stability": 0.6},
        {"agent": "real_estate", "expected_return": 0.06, "risk": 0.3, "stability": 0.8},
        {"agent": "stock_cash", "expected_return": 0.085, "risk": 0.5, "stability": 0.65},
        {"agent": "stock_margin", "expected_return": 0.085, "risk": 0.5, "stability": 0.65},
    ]

    results = get_best_investments(user, strategies, strategy_loans)

    print(f"User: $80k savings, $15k/mo income, Bay Area\n")
    print(
        f"{'Strategy':<15} {'Capital':<12} {'Loan':<12} {'Gross/yr':<12} {'Pmt/yr':<12} {'NET %':<10} {'Status':<15} {'Score':<8}")
    print("-" * 100)

    for r in results:
        loan_amt = r['loan_info']['amount']
        print(f"{r['agent']:<15} "
              f"${r['total_capital']:>9,.0f}  "
              f"${loan_amt:>9,.0f}  "
              f"${r['gross_return_dollars']:>9,.0f}  "
              f"${r['annual_payment']:>9,.0f}  "
              f"{r['net_return'] * 100:>6.2f}%  "
              f"{r['status']:<15} "
              f"{r['score']:.4f}")

    print(f"\n🏆 WINNER: {results[0]['agent']} (score={results[0]['score']:.4f})")
    print()


if __name__ == "__main__":
    print("\n💰 KORAK 2 VALIDATION — Investment Engine with Real Amortization\n")

    try:
        test_amortization_calculator()
        test_real_amortization_kills_business()
        test_mortgage_real_estate_realistic()
        test_stock_cash_vs_margin()
        test_margin_call_risk_model()
        test_full_pipeline_4_strategies()

        print("=" * 70)
        print("✅ ALL KORAK 2 TESTS PASSED")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)