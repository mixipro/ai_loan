# tests/test_phase1.py

"""
Quick validation test for Phase 1 — California Foundation.
Run from project root: python tests/test_phase1.py
"""

import sys

sys.path.insert(0, ".")

from app.core.california_config import (
    REGION_DATA, CaliforniaRegion,
    get_all_california_cities, find_region_for_city,
    get_city_real_estate_data,
)
from app.engines.california_tax_engine import (
    calculate_total_income_tax,
    calculate_qsbs_benefit,
    calculate_property_tax_prop13,
    analyze_california_tax_situation,
)


def test_region_data():
    print("=" * 60)
    print("TEST 1: Region Data")
    print("=" * 60)

    print(f"Total regions: {len(REGION_DATA)}")
    print(f"Total cities: {len(get_all_california_cities())}")

    # Verify all 8 regions
    assert len(REGION_DATA) == 8, f"Expected 8 regions, got {len(REGION_DATA)}"
    print("✅ 8 regions confirmed")

    # Verify city lookups
    sf_region = find_region_for_city("San Francisco")
    assert sf_region == CaliforniaRegion.BAY_AREA, f"SF should be BAY_AREA, got {sf_region}"
    print(f"✅ San Francisco → {sf_region.value}")

    la_region = find_region_for_city("Beverly Hills")
    assert la_region == CaliforniaRegion.LOS_ANGELES
    print(f"✅ Beverly Hills → {la_region.value}")

    sd_region = find_region_for_city("La Jolla")
    assert sd_region == CaliforniaRegion.SAN_DIEGO
    print(f"✅ La Jolla → {sd_region.value}")

    print()


def test_city_real_estate():
    print("=" * 60)
    print("TEST 2: City Real Estate Data")
    print("=" * 60)

    # Test premium city (has override)
    pa_data = get_city_real_estate_data("Palo Alto", CaliforniaRegion.BAY_AREA)
    print(f"Palo Alto: ${pa_data['price_per_sqft']}/sqft, ${pa_data['rent_2br']}/mo 2BR rent")
    print(f"   Source: {pa_data['source']}")

    # Test non-premium city (region average)
    rc_data = get_city_real_estate_data("Rancho Cordova", CaliforniaRegion.SACRAMENTO)
    print(f"Rancho Cordova: ${rc_data['price_per_sqft']}/sqft, ${rc_data['rent_2br']}/mo 2BR rent")
    print(f"   Source: {rc_data['source']}")

    assert pa_data['source'] == 'city_specific'
    assert rc_data['source'] == 'region_average'
    print("✅ City overrides work correctly")
    print()


def test_income_tax():
    print("=" * 60)
    print("TEST 3: Income Tax Calculation")
    print("=" * 60)

    # Test 1: Tech worker $180k
    result = calculate_total_income_tax(180000)
    print(f"Income $180k:")
    print(f"   State tax: ${result['state_tax']:,.0f}")
    print(f"   Federal tax: ${result['federal_tax']:,.0f}")
    print(f"   Total tax: ${result['total_tax']:,.0f}")
    print(f"   Effective rate: {result['effective_rate'] * 100:.1f}%")
    print(f"   Marginal rate: {result['marginal_rate'] * 100:.1f}%")
    print(f"   Take home: ${result['after_tax_income']:,.0f}")

    # Test 2: Million dollar earner (triggers mental health tax)
    result_high = calculate_total_income_tax(1_500_000)
    print(f"\nIncome $1.5M:")
    print(f"   Effective rate: {result_high['effective_rate'] * 100:.1f}%")
    print(f"   Marginal rate: {result_high['marginal_rate'] * 100:.1f}%")
    print(f"   Note: Mental Health Tax (+1%) applies on income > $1M")
    print()


def test_qsbs():
    print("=" * 60)
    print("TEST 4: QSBS Exclusion (Startup Exit)")
    print("=" * 60)

    # Test 1: $2M exit, 6 years holding (qualifies)
    qsbs = calculate_qsbs_benefit(
        sale_proceeds=2_000_000,
        cost_basis=1000,
        holding_years=6
    )
    print(f"$2M exit, 6 years holding:")
    print(f"   Qualifies: {qsbs['qualifies']}")
    print(f"   Capital gain: ${qsbs['capital_gain']:,.0f}")
    print(f"   Tax WITHOUT QSBS: ${qsbs['tax_without_qsbs']:,.0f}")
    print(f"   Tax WITH QSBS: ${qsbs['tax_with_qsbs']:,.0f}")
    print(f"   💰 Savings: ${qsbs['savings']:,.0f}")

    # Test 2: $15M exit (above $10M cap)
    qsbs_big = calculate_qsbs_benefit(
        sale_proceeds=15_000_000,
        cost_basis=1000,
        holding_years=7
    )
    print(f"\n$15M exit, 7 years (above $10M cap):")
    print(f"   Excluded: ${qsbs_big['excluded_amount']:,.0f}")
    print(f"   Taxable (over $10M): ${qsbs_big['taxable_amount']:,.0f}")
    print(f"   💰 Savings: ${qsbs_big['savings']:,.0f}")

    # Test 3: 3 years (doesn't qualify)
    qsbs_short = calculate_qsbs_benefit(
        sale_proceeds=500_000,
        cost_basis=1000,
        holding_years=3
    )
    print(f"\n$500k exit, 3 years (DOESN'T qualify):")
    print(f"   Qualifies: {qsbs_short['qualifies']}")
    print(f"   Reason: {qsbs_short['reason']}")
    print(f"   Advice: {qsbs_short['advice']}")
    print()


def test_prop13():
    print("=" * 60)
    print("TEST 5: Prop 13 Property Tax")
    print("=" * 60)

    # Test 1: 10 years ownership
    p13_10 = calculate_property_tax_prop13(
        purchase_price=600_000,
        years_owned=10
    )
    print(f"$600k purchase, 10 years owned:")
    print(f"   Assessed value: ${p13_10['assessed_value']:,.0f}")
    print(f"   Market value: ${p13_10['market_value_estimate']:,.0f}")
    print(f"   Annual tax: ${p13_10['annual_tax']:,.0f}")
    print(f"   New buyer would pay: ${p13_10['new_buyer_would_pay']:,.0f}")
    print(f"   💰 Annual savings: ${p13_10['annual_savings_vs_new_buyer']:,.0f}")

    # Test 2: 30 years (huge savings)
    p13_30 = calculate_property_tax_prop13(
        purchase_price=300_000,
        years_owned=30
    )
    print(f"\n$300k purchase, 30 years owned:")
    print(f"   Annual savings: ${p13_30['annual_savings_vs_new_buyer']:,.0f}")
    print(f"   30-year cumulative savings: ${p13_30['annual_savings_vs_new_buyer'] * 30:,.0f}")
    print()


def test_full_analysis():
    print("=" * 60)
    print("TEST 6: Full California Tax Analysis")
    print("=" * 60)

    # Mid-level professional
    analysis = analyze_california_tax_situation(150_000)
    print(f"Income $150k analysis:")
    print(f"   Effective rate: {analysis['effective_rate'] * 100:.1f}%")
    print(f"   Recommendations:")
    for rec in analysis['recommendations']:
        print(f"     • {rec}")

    # High earner
    print()
    analysis_high = analyze_california_tax_situation(750_000)
    print(f"Income $750k analysis:")
    print(f"   Effective rate: {analysis_high['effective_rate'] * 100:.1f}%")
    print(f"   Recommendations:")
    for rec in analysis_high['recommendations']:
        print(f"     • {rec}")
    print()


if __name__ == "__main__":
    print("\n🌴 PHASE 1 VALIDATION — California Foundation\n")

    try:
        test_region_data()
        test_city_real_estate()
        test_income_tax()
        test_qsbs()
        test_prop13()
        test_full_analysis()

        print("=" * 60)
        print("✅ ALL TESTS PASSED — Phase 1.1 ready!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)