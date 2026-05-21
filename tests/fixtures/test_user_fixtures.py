from app.models.analyze import AnalyzeConfig
from app.models.user import UserInput
from tests.fixtures import user_fixtures

LEGACY_TOP_LEVEL_LOCATION_FIELDS = {"country"}
LEGACY_FINANCIAL_FIELDS = {"debt"}


def test_all_user_fixture_payloads_are_valid_user_inputs():
    for payload in user_fixtures.VALID_USER_PAYLOADS:
        user = UserInput(**payload)

        assert user.location.region.value == payload["location"]["region"]
        assert user.location.city == payload["location"]["city"]
        assert user.financial.currency.value == "USD"
        assert user.financial.expenses < user.financial.income
        assert len(user.professional.interests) <= 4


def test_user_fixture_payloads_use_current_california_schema_only():
    for payload in user_fixtures.VALID_USER_PAYLOADS:
        assert not (LEGACY_TOP_LEVEL_LOCATION_FIELDS & payload["location"].keys())
        assert not (LEGACY_FINANCIAL_FIELDS & payload["financial"].keys())
        assert "region" in payload["location"]
        assert "monthly_debt" in payload["financial"]
        assert payload["financial"]["currency"] == "USD"


def test_clone_payload_returns_independent_mutable_copy():
    original = user_fixtures.BAY_AREA_TECH_USER_PAYLOAD
    cloned = user_fixtures.clone_payload(original)

    cloned["financial"]["income"] = 1
    cloned["professional"]["interests"].append("robotics")

    assert original["financial"]["income"] == 28000
    assert original["professional"]["interests"] == [
        "ai/ml",
        "investing",
        "programming",
        "startups",
    ]


def test_analyze_config_fixture_is_valid_and_covers_all_strategies():
    config = AnalyzeConfig(**user_fixtures.VALID_ANALYZE_CONFIG_PAYLOAD)

    assert set(config.model_dump().keys()) == {"business", "real_estate", "stock"}
    assert config.business.loan_years == 7
    assert config.real_estate.loan_years == 30
    assert config.stock.loan_amount <= config.stock.savings_to_use
    assert config.real_estate.savings_to_use >= 0.20 * (
            config.real_estate.loan_amount + config.real_estate.savings_to_use
    )


def test_fixture_module_exports_expected_data_constants():
    assert user_fixtures.BAY_AREA_TECH_USER_PAYLOAD in user_fixtures.VALID_USER_PAYLOADS
    assert user_fixtures.SACRAMENTO_LOW_RISK_USER_PAYLOAD in user_fixtures.VALID_USER_PAYLOADS
    assert user_fixtures.LOS_ANGELES_ENTERTAINMENT_USER_PAYLOAD in user_fixtures.VALID_USER_PAYLOADS
    assert "VALID_ANALYZE_CONFIG_PAYLOAD" in user_fixtures.__all__
