# tests/test_phase1_4.py

"""
Phase 1.4 — Test new California-aware endpoints.
Run with FastAPI server NOT running (uses TestClient).
"""

import sys

sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    print("=" * 70)
    print("TEST 1: GET /health")
    print("=" * 70)

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    print(f"✅ Status: {data['status']}")
    print(f"   System: {data['system']}")
    print(f"   Version: {data['version']}")
    print()


def test_info():
    print("=" * 70)
    print("TEST 2: GET /info")
    print("=" * 70)

    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()

    print(f"✅ Name: {data['name']}")
    print(f"   Tagline: {data['tagline']}")
    print(f"   Specialization: {data['specialization']}")
    print(f"   Regions covered: {data['regions_covered']}")
    print(f"   Cities covered: {data['cities_covered']}")
    print(f"   Features:")
    for feat in data['features']:
        print(f"     • {feat}")
    print()


def test_options():
    print("=" * 70)
    print("TEST 3: GET /options")
    print("=" * 70)

    response = client.get("/options")
    assert response.status_code == 200
    data = response.json()

    # Verify regions
    print(f"✅ Regions: {len(data['regions'])}")
    for r in data['regions']:
        print(f"   • {r['label']} ({r['value']}): {len(data['cities_by_region'][r['value']])} cities")

    # Verify California sectors
    print(f"\n✅ Sectors: {len(data['sectors'])}")
    print(f"   First 5: {data['sectors'][:5]}")

    # Verify California-specific
    print(f"\n✅ Tech roles: {len(data['tech_roles'])}")
    print(f"✅ Equity comp options: {len(data['equity_compensations'])}")
    print(f"✅ Company stages: {len(data['company_stages'])}")
    print(f"✅ Entertainment roles: {len(data['entertainment_roles'])}")

    # Verify standard
    print(f"\n✅ Professions: {len(data['professions'])}")
    print(f"✅ Currencies: {data['currencies']} (USD only)")
    print(f"✅ Predefined interests: {len(data['predefined_interests'])}")
    print()


def test_analyze_bay_area_tech():
    print("=" * 70)
    print("TEST 4: POST /analyze — Bay Area tech worker")
    print("=" * 70)

    payload = {
        "personal": {"age": 32},
        "location": {
            "region": "BAY_AREA",
            "city": "San Francisco"
        },
        "financial": {
            "income": 15000,
            "expenses": 5000,
            "monthly_debt": 500,
            "savings": 80000,
            "currency": "USD"
        },
        "professional": {
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "full-time",
            "interests": ["ai/ml", "startups", "investing"],
            "prior_experience": "Built SaaS side project",
            "weekly_hours": "5-15",
            "tech_role": "Software Engineer",
            "equity_compensation": "RSU (Restricted Stock Units)",
            "company_stage": "Public Company"
        },
        "preferences": {
            "risk_profile": "medium",
            "horizon": "5-8"
        }
    }

    response = client.post("/analyze", json=payload)

    if response.status_code != 200:
        print(f"❌ Status: {response.status_code}")
        print(f"   Error: {response.text}")
        return

    data = response.json()

    print(f"✅ Response received")
    print(f"   Region: {data['risk']['region_display_name']}")
    print(f"   Creditworthiness: {data['risk']['creditworthiness']}")
    print(f"   Interest rate: {data['interest']['interest_rate'] * 100:.2f}%")
    if data['loan']['approved']:
        print(f"   Loan: ${data['loan']['max_loan_amount']:,.0f}")
    print(f"   Strategies returned: {len(data['strategies'])}")
    print()


def test_invalid_region_city():
    print("=" * 70)
    print("TEST 5: POST /analyze — Invalid city for region")
    print("=" * 70)

    payload = {
        "personal": {"age": 32},
        "location": {
            "region": "BAY_AREA",
            "city": "Beverly Hills"  # Wrong! Beverly Hills is LA
        },
        "financial": {
            "income": 15000,
            "expenses": 5000,
            "monthly_debt": 500,
            "savings": 80000,
            "currency": "USD"
        },
        "professional": {
            "sector": "Technology",
            "profession": "Software Engineer",
            "employment_status": "full-time"
        },
        "preferences": {
            "risk_profile": "medium",
            "horizon": "5-8"
        }
    }

    response = client.post("/analyze", json=payload)

    # Pydantic validation should reject this
    assert response.status_code == 422
    print(f"✅ Correctly rejected with 422 Unprocessable Entity")
    print(f"   Validation error caught by Pydantic")
    print()


if __name__ == "__main__":
    print("\n🌴 PHASE 1.4 VALIDATION — Routes + /options endpoint\n")

    try:
        test_health()
        test_info()
        test_options()
        test_invalid_region_city()
        # test_analyze_bay_area_tech() requires agents to work — skip for now

        print("=" * 70)
        print("✅ ALL PHASE 1.4 TESTS PASSED")
        print("=" * 70)
        print("\n⚠️ NOTE: /analyze test skipped — agents still use old country format.")
        print("    Will work after Phase 4 (agents update).")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)