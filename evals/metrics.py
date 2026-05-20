"""
evals/metrics.py

Defines all metrics used to evaluate CaliforniaCFO output quality.

Metrics:
  1. Strategy Selection Accuracy  — Did the recommended winner match expectations?
  2. Strategy Status Consistency  — Did each agent's status match plausible range?
  3. Latency                       — How long did the analysis take?
  4. Token Cost                    — How many tokens used + estimated USD cost?
  5. Drift Check                   — Did RE avoid Palo Alto $3M+ anti-pattern?
"""

from dataclasses import dataclass, field
from typing import Any


# OpenRouter pricing for Claude 3.5 Sonnet (May 2026)
# Source: https://openrouter.ai/anthropic/claude-3.5-sonnet
PRICE_INPUT_PER_1M = 3.00   # $3.00 / 1M input tokens
PRICE_OUTPUT_PER_1M = 15.00 # $15.00 / 1M output tokens


@dataclass
class ProfileResult:
    """Single profile evaluation outcome."""
    profile_id: str
    profile_name: str
    success: bool                        # API call succeeded
    error: str | None = None             # If failed, why

    # Quality metrics
    winner_correct: bool = False
    winner_expected: list[str] = field(default_factory=list)
    winner_actual: str = ""

    business_status_correct: bool = False
    business_status_expected: list[str] = field(default_factory=list)
    business_status_actual: str = ""

    real_estate_status_correct: bool = False
    real_estate_status_expected: list[str] = field(default_factory=list)
    real_estate_status_actual: str = ""

    stock_status_correct: bool = False
    stock_status_expected: list[str] = field(default_factory=list)
    stock_status_actual: str = ""

    business_type_correct: bool = False
    business_type_expected: list[str] = field(default_factory=list)
    business_type_actual: str = ""

    drift_check_passed: bool = True
    drift_check_detail: str = ""

    # Performance metrics
    latency_sec: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

    # Raw response (for debugging)
    raw_response: dict[str, Any] | None = None


@dataclass
class AggregateMetrics:
    """Summary across all profiles."""
    total_profiles: int = 0
    successful_profiles: int = 0
    failed_profiles: int = 0

    # Accuracy (0.0-1.0)
    winner_accuracy: float = 0.0
    business_status_accuracy: float = 0.0
    real_estate_status_accuracy: float = 0.0
    stock_status_accuracy: float = 0.0
    business_type_accuracy: float = 0.0
    overall_status_accuracy: float = 0.0    # avg of 3 statuses
    drift_check_pass_rate: float = 0.0

    # Latency (seconds)
    latency_mean: float = 0.0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_max: float = 0.0

    # Cost (USD)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    cost_per_request_mean_usd: float = 0.0


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated USD cost for one request."""
    input_cost = (input_tokens / 1_000_000) * PRICE_INPUT_PER_1M
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M
    return round(input_cost + output_cost, 4)


def evaluate_profile(
    profile_id: str,
    profile_name: str,
    expected: dict[str, Any],
    response: dict[str, Any],
    latency_sec: float,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> ProfileResult:
    """
    Compare expected outcomes vs actual response from /analyze.

    Args:
        profile_id: Profile identifier (e.g. "truck_driver_sd")
        profile_name: Human-readable name
        expected: Dict from validation_profiles.json[profile].expected
        response: Full /analyze response JSON
        latency_sec: Time taken for full request
        input_tokens: Total input tokens used
        output_tokens: Total output tokens generated

    Returns:
        ProfileResult with all metric flags computed
    """
    result = ProfileResult(
        profile_id=profile_id,
        profile_name=profile_name,
        success=True,
        latency_sec=round(latency_sec, 2),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=estimate_cost(input_tokens, output_tokens),
        raw_response=response,
    )

    # Extract from response
    recommendation = response.get("recommendation") or {}
    strategies = response.get("strategies") or []

    strat_by_agent: dict[str, dict[str, Any]] = {
        s.get("agent", ""): s for s in strategies
    }

    business = strat_by_agent.get("business", {})
    real_estate = strat_by_agent.get("real_estate", {})
    stock = strat_by_agent.get("stock", {})

    # ─── 1. Winner agent ───
    winner_actual = recommendation.get("agent", "")
    winner_expected = expected.get("winner_agent", [])
    result.winner_actual = winner_actual
    result.winner_expected = winner_expected
    result.winner_correct = (
        winner_actual in winner_expected if winner_expected else True
    )

    # ─── 2. Business status ───
    business_status_actual = business.get("status", "?")
    business_status_expected = expected.get("business_status", [])
    result.business_status_actual = business_status_actual
    result.business_status_expected = business_status_expected
    result.business_status_correct = (
        business_status_actual in business_status_expected
        if business_status_expected
        else True
    )

    # ─── 3. Real Estate status ───
    re_status_actual = real_estate.get("status", "?")
    re_status_expected = expected.get("real_estate_status", [])
    result.real_estate_status_actual = re_status_actual
    result.real_estate_status_expected = re_status_expected
    result.real_estate_status_correct = (
        re_status_actual in re_status_expected
        if re_status_expected
        else True
    )

    # ─── 4. Stock status ───
    stock_status_actual = stock.get("status", "?")
    stock_status_expected = expected.get("stock_status", [])
    result.stock_status_actual = stock_status_actual
    result.stock_status_expected = stock_status_expected
    result.stock_status_correct = (
        stock_status_actual in stock_status_expected
        if stock_status_expected
        else True
    )

    # ─── 5. Business type (hours-aware filtering check) ───
    business_type_actual = business.get("type", "?")
    business_type_expected = expected.get("business_type", [])
    result.business_type_actual = business_type_actual
    result.business_type_expected = business_type_expected
    result.business_type_correct = (
        business_type_actual in business_type_expected
        if business_type_expected
        else True
    )

    # ─── 6. RAG drift check (RE price sanity) ───
    if expected.get("no_palo_alto_drift", False):
        property_value = (
            real_estate.get("property_economics", {}).get("purchase_price_usd", 0)
            or real_estate.get("property_market_context", {}).get("median_property_value_usd", 0)
            or 0
        )
        max_allowed = expected.get("property_value_max_usd", 5_000_000)
        if property_value > max_allowed:
            result.drift_check_passed = False
            result.drift_check_detail = (
                f"RE property value ${property_value:,} exceeds expected max ${max_allowed:,} "
                f"(possible Palo Alto $3M+ drift)"
            )
        else:
            result.drift_check_passed = True
            result.drift_check_detail = (
                f"RE property value ${property_value:,} ≤ ${max_allowed:,} ✓"
            )

    return result


def percentile(values: list[float], p: float) -> float:
    """Calculate percentile p (0.0-1.0) from a list of values."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def aggregate(results: list[ProfileResult]) -> AggregateMetrics:
    """Compute aggregate metrics from per-profile results."""
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    n_total = len(results)
    n_ok = len(successful)

    if n_ok == 0:
        return AggregateMetrics(
            total_profiles=n_total,
            successful_profiles=0,
            failed_profiles=len(failed),
        )

    # Accuracies
    winner_acc = sum(1 for r in successful if r.winner_correct) / n_ok
    biz_status_acc = sum(1 for r in successful if r.business_status_correct) / n_ok
    re_status_acc = sum(1 for r in successful if r.real_estate_status_correct) / n_ok
    stock_status_acc = sum(1 for r in successful if r.stock_status_correct) / n_ok
    biz_type_acc = sum(1 for r in successful if r.business_type_correct) / n_ok
    overall_status_acc = (biz_status_acc + re_status_acc + stock_status_acc) / 3
    drift_pass = sum(1 for r in successful if r.drift_check_passed) / n_ok

    # Latency
    latencies = [r.latency_sec for r in successful]
    latency_mean = sum(latencies) / len(latencies)

    # Cost
    total_in = sum(r.input_tokens for r in successful)
    total_out = sum(r.output_tokens for r in successful)
    total_cost = sum(r.cost_usd for r in successful)

    return AggregateMetrics(
        total_profiles=n_total,
        successful_profiles=n_ok,
        failed_profiles=len(failed),
        winner_accuracy=round(winner_acc, 3),
        business_status_accuracy=round(biz_status_acc, 3),
        real_estate_status_accuracy=round(re_status_acc, 3),
        stock_status_accuracy=round(stock_status_acc, 3),
        business_type_accuracy=round(biz_type_acc, 3),
        overall_status_accuracy=round(overall_status_acc, 3),
        drift_check_pass_rate=round(drift_pass, 3),
        latency_mean=round(latency_mean, 2),
        latency_p50=round(percentile(latencies, 0.5), 2),
        latency_p95=round(percentile(latencies, 0.95), 2),
        latency_max=round(max(latencies), 2),
        total_input_tokens=total_in,
        total_output_tokens=total_out,
        total_cost_usd=round(total_cost, 3),
        cost_per_request_mean_usd=round(total_cost / n_ok, 4),
    )
