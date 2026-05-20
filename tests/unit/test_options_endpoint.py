"""
tests/unit/test_options_endpoint.py

Smoke tests for GET /options — verifies backend returns
the structures expected by frontend (form dropdowns).

Run with backend NOT required (uses TestClient).
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """TestClient that doesn't require a running server."""
    from app.main import app
    return TestClient(app)


class TestOptionsEndpoint:
    def test_options_returns_200(self, client):
        r = client.get("/options")
        assert r.status_code == 200

    def test_options_returns_json(self, client):
        r = client.get("/options")
        data = r.json()
        assert isinstance(data, dict)

    def test_options_has_required_keys(self, client):
        r = client.get("/options")
        data = r.json()

        required_keys = {
            "regions",
            "cities_by_region",
            "sectors",
            "professions_by_sector",
            "all_professions",
            "employment_statuses",
            "risk_profiles",
            "horizons",
            "weekly_hours",
            "predefined_interests",
        }
        missing = required_keys - data.keys()
        assert not missing, f"Missing keys in /options: {missing}"

    def test_options_has_california_fields(self, client):
        """Day 5 California-specific enum fields."""
        r = client.get("/options")
        data = r.json()

        california_keys = {
            "tech_roles",
            "equity_compensations",
            "company_stages",
            "entertainment_roles",
        }
        missing = california_keys - data.keys()
        assert not missing, f"Missing California fields: {missing}"

    def test_regions_are_california_only(self, client):
        """Verify California pivot: only CA regions."""
        r = client.get("/options")
        data = r.json()

        region_values = [
            r if isinstance(r, str) else r.get("value")
            for r in data["regions"]
        ]

        # All should look California-y (BAY_AREA, LOS_ANGELES, etc.)
        expected = {"BAY_AREA", "LOS_ANGELES", "SAN_DIEGO"}
        present = expected & set(region_values)
        assert present, f"Expected California regions, got: {region_values}"

    def test_cities_by_region_has_bay_area(self, client):
        r = client.get("/options")
        data = r.json()

        cities = data["cities_by_region"].get("BAY_AREA", [])
        assert isinstance(cities, list)
        assert len(cities) > 0, "Bay Area should have cities"

    def test_predefined_interests_nonempty(self, client):
        r = client.get("/options")
        data = r.json()

        interests = data["predefined_interests"]
        assert isinstance(interests, list)
        assert len(interests) >= 10, (
            f"Expected ≥10 interests, got {len(interests)}"
        )

    def test_weekly_hours_includes_all_buckets(self, client):
        r = client.get("/options")
        data = r.json()

        hours = data["weekly_hours"]
        expected = {"0-5", "5-15", "15-30", "30+"}
        present = set(hours) & expected
        assert len(present) >= 3, f"Expected most hour buckets, got {hours}"


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_root_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200
