"""
tests/unit/test_evaluation_suite.py

Verifies that the evaluation suite (evals/) is structurally sound:
- validation_profiles.json is valid JSON
- All profiles have required fields
- Profile inputs match Pydantic models
- Metrics module is importable
"""

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EVALS_DIR = PROJECT_ROOT / "evals"
PROFILES_FILE = EVALS_DIR / "validation_profiles.json"


@pytest.fixture(scope="module")
def profiles_data() -> dict:
    """Load validation_profiles.json once for all tests."""
    if not PROFILES_FILE.exists():
        pytest.skip(f"evals/ not installed at {PROFILES_FILE}")
    with PROFILES_FILE.open() as f:
        return json.load(f)


class TestValidationProfilesStructure:
    def test_file_is_valid_json(self, profiles_data):
        assert isinstance(profiles_data, dict)

    def test_has_version(self, profiles_data):
        assert "version" in profiles_data
        assert profiles_data["version"]

    def test_has_profiles_array(self, profiles_data):
        assert "profiles" in profiles_data
        assert isinstance(profiles_data["profiles"], list)

    def test_has_at_least_5_profiles(self, profiles_data):
        """Need representative sample of California demographics."""
        assert len(profiles_data["profiles"]) >= 5

    def test_profile_ids_are_unique(self, profiles_data):
        ids = [p["id"] for p in profiles_data["profiles"]]
        assert len(ids) == len(set(ids)), "Duplicate profile IDs!"


class TestProfileRequiredFields:
    """Every profile needs these top-level fields."""

    def test_each_profile_has_id_name_input_expected(self, profiles_data):
        for p in profiles_data["profiles"]:
            assert "id" in p, f"Profile missing id: {p}"
            assert "name" in p, f"Profile missing name: {p['id']}"
            assert "input" in p, f"Profile missing input: {p['id']}"
            assert "expected" in p, f"Profile missing expected: {p['id']}"

    def test_each_input_has_user_and_config(self, profiles_data):
        for p in profiles_data["profiles"]:
            assert "user" in p["input"], (
                f"Profile {p['id']} missing input.user"
            )
            assert "config" in p["input"], (
                f"Profile {p['id']} missing input.config"
            )

    def test_each_user_has_required_sections(self, profiles_data):
        required = {
            "personal",
            "location",
            "financial",
            "professional",
            "preferences",
        }
        for p in profiles_data["profiles"]:
            present = set(p["input"]["user"].keys())
            missing = required - present
            assert not missing, (
                f"Profile {p['id']} missing user sections: {missing}"
            )


class TestProfilesValidateAgainstModels:
    """Profile inputs must construct valid UserInput objects."""

    def test_all_profiles_construct_valid_user_input(self, profiles_data):
        from app.models.user import UserInput

        for p in profiles_data["profiles"]:
            try:
                UserInput(**p["input"]["user"])
            except Exception as e:
                pytest.fail(
                    f"Profile {p['id']} failed Pydantic validation: {e}"
                )


class TestExpectedOutcomesFormat:
    """Expected outcomes should be lists (for set-membership checks)."""

    def test_winner_agent_is_list(self, profiles_data):
        for p in profiles_data["profiles"]:
            wa = p["expected"].get("winner_agent")
            if wa is not None:
                assert isinstance(wa, list), (
                    f"Profile {p['id']} winner_agent must be list"
                )
                assert len(wa) > 0, (
                    f"Profile {p['id']} winner_agent list is empty"
                )

    def test_status_fields_are_lists_when_present(self, profiles_data):
        status_keys = [
            "business_status",
            "real_estate_status",
            "stock_status",
        ]
        for p in profiles_data["profiles"]:
            for key in status_keys:
                val = p["expected"].get(key)
                if val is not None:
                    assert isinstance(val, list), (
                        f"Profile {p['id']}.{key} must be list, got {type(val)}"
                    )


class TestMetricsModule:
    def test_metrics_module_importable(self):
        from evals import metrics
        assert metrics is not None

    def test_estimate_cost_returns_float(self):
        from evals.metrics import estimate_cost
        cost = estimate_cost(input_tokens=1000, output_tokens=500)
        assert isinstance(cost, float)
        assert cost > 0

    def test_percentile_calculation(self):
        from evals.metrics import percentile
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert percentile(vals, 0.5) == pytest.approx(3.0)
        assert percentile(vals, 1.0) == pytest.approx(5.0)
        assert percentile(vals, 0.0) == pytest.approx(1.0)

    def test_percentile_empty_list(self):
        from evals.metrics import percentile
        assert percentile([], 0.5) == 0.0


class TestRunnerModule:
    def test_runner_importable(self):
        """The runner should import without side effects."""
        from evals import run_evaluation
        assert hasattr(run_evaluation, "run_evaluation")
        assert hasattr(run_evaluation, "main")
