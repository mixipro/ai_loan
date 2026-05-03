from app.services.orchestrator import run_pipeline


def test_run_pipeline_returns_expected_shape(base_user):
    result = run_pipeline(base_user)

    assert result["status"] == "Pipeline working"
    assert "summary" in result


def test_run_pipeline_calculates_disposable_income(base_user):
    result = run_pipeline(base_user)

    assert result["summary"]["income"] == 1500
    assert result["summary"]["expenses"] == 500
    assert result["summary"]["disposable_income"] == 1000


def test_run_pipeline_preserves_location_and_savings(base_user):
    result = run_pipeline(base_user)

    assert result["summary"]["country"] == base_user.location.country
    assert result["summary"]["city"] == "Belgrade"
    assert result["summary"]["savings"] == 5000


def test_run_pipeline_works_with_high_income_user(high_income_user):
    result = run_pipeline(high_income_user)

    assert result["summary"]["country"] == high_income_user.location.country
    assert result["summary"]["city"] == "Berlin"
    assert result["summary"]["disposable_income"] == 2500
