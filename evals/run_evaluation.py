"""
evals/run_evaluation.py

Runs all validation profiles against the live /analyze endpoint, measures:
  • Strategy selection accuracy
  • Status consistency per agent (business, real_estate, stock)
  • Business type adherence (hours-aware filtering)
  • RAG drift (Palo Alto $3M+ anti-pattern)
  • Latency (mean, p50, p95, max)
  • Token cost (estimated USD)

Generates:
  • EVALUATION_REPORT.md (human-readable)
  • results/{timestamp}.json (raw per-profile data)

Usage:
  # Backend must be running first:
  #   make backend  (in another terminal)

  # Then:
  uv run python evals/run_evaluation.py

  # Or via Makefile:
  make eval
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

# Add project root to path so we can import from app/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evals.metrics import (  # noqa: E402
    AggregateMetrics,
    ProfileResult,
    aggregate,
    estimate_cost,
    evaluate_profile,
)


# ──────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────
BACKEND_URL = os.getenv("CALIFORNIACFO_URL", "http://localhost:8000")
ANALYZE_ENDPOINT = "/analyze"
TIMEOUT_SEC = 180.0  # 3 minutes per request (full analysis can take ~30-60s)

EVALS_DIR = Path(__file__).resolve().parent
PROFILES_FILE = EVALS_DIR / "validation_profiles.json"
RESULTS_DIR = EVALS_DIR / "results"
REPORT_FILE = EVALS_DIR / "EVALUATION_REPORT.md"


# ──────────────────────────────────────────────────
# TOKEN ESTIMATION (since /analyze doesn't return usage directly)
# ──────────────────────────────────────────────────
def estimate_tokens_from_strings(*texts: str) -> int:
    """Rough estimate: 1 token ≈ 4 chars for English."""
    total_chars = sum(len(t) for t in texts if t)
    return total_chars // 4


def extract_tokens_from_response(
    request_body: dict, response: dict
) -> tuple[int, int]:
    """
    Estimate input/output tokens from a /analyze cycle.

    Real token usage is not exposed by orchestrator. We estimate by:
      • INPUT: JSON-serialized request × 4 agents (business, real_estate, stock, judge)
              + RAG context (~2000 tokens per agent for retrieved chunks)
      • OUTPUT: JSON-serialized response (judge + 3 strategies)
    """
    # Input: request body + estimated system prompts + RAG context
    request_str = json.dumps(request_body, ensure_ascii=False)
    request_tokens = estimate_tokens_from_strings(request_str)
    # 4 LLM calls (3 agents + 1 judge), each gets ~2000 token system+RAG context
    estimated_input = request_tokens + (4 * 2500)

    # Output: full response is what LLMs produced
    response_str = json.dumps(response, ensure_ascii=False)
    estimated_output = estimate_tokens_from_strings(response_str)

    return estimated_input, estimated_output


# ──────────────────────────────────────────────────
# CORE RUNNER
# ──────────────────────────────────────────────────
async def run_single_profile(
    client: httpx.AsyncClient, profile: dict
) -> ProfileResult:
    """Run /analyze for one profile, evaluate result, return ProfileResult."""
    profile_id = profile["id"]
    profile_name = profile["name"]
    expected = profile.get("expected", {})
    request_body = profile["input"]

    print(f"  ▸ {profile_name} ...", end="", flush=True)
    start = time.perf_counter()

    try:
        response = await client.post(
            f"{BACKEND_URL}{ANALYZE_ENDPOINT}",
            json=request_body,
            timeout=TIMEOUT_SEC,
        )
        elapsed = time.perf_counter() - start

        if response.status_code != 200:
            print(f" ✗ HTTP {response.status_code}")
            return ProfileResult(
                profile_id=profile_id,
                profile_name=profile_name,
                success=False,
                error=f"HTTP {response.status_code}: {response.text[:200]}",
                latency_sec=round(elapsed, 2),
            )

        response_json = response.json()
        input_tokens, output_tokens = extract_tokens_from_response(
            request_body, response_json
        )

        result = evaluate_profile(
            profile_id=profile_id,
            profile_name=profile_name,
            expected=expected,
            response=response_json,
            latency_sec=elapsed,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        # Pretty result indicator
        flags = []
        if result.winner_correct: flags.append("W✓")
        else: flags.append(f"W✗({result.winner_actual})")
        if result.business_status_correct: flags.append("B✓")
        else: flags.append(f"B✗({result.business_status_actual})")
        if result.real_estate_status_correct: flags.append("R✓")
        else: flags.append(f"R✗({result.real_estate_status_actual})")
        if result.stock_status_correct: flags.append("S✓")
        else: flags.append(f"S✗({result.stock_status_actual})")
        if result.drift_check_passed: flags.append("D✓")
        else: flags.append("D✗")

        print(f" {elapsed:5.1f}s  {' '.join(flags)}  ~${result.cost_usd:.4f}")

        return result

    except httpx.TimeoutException:
        elapsed = time.perf_counter() - start
        print(f" ✗ TIMEOUT after {elapsed:.1f}s")
        return ProfileResult(
            profile_id=profile_id,
            profile_name=profile_name,
            success=False,
            error=f"Timeout after {TIMEOUT_SEC}s",
            latency_sec=round(elapsed, 2),
        )
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f" ✗ ERROR: {type(e).__name__}: {str(e)[:80]}")
        return ProfileResult(
            profile_id=profile_id,
            profile_name=profile_name,
            success=False,
            error=f"{type(e).__name__}: {e}",
            latency_sec=round(elapsed, 2),
        )


async def check_backend_alive(client: httpx.AsyncClient) -> bool:
    """Verify backend is reachable before running profiles."""
    try:
        r = await client.get(f"{BACKEND_URL}/health", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False


async def run_evaluation(
    profiles_to_run: list[str] | None = None,
    fast_mode: bool = False,
) -> tuple[list[ProfileResult], AggregateMetrics]:
    """
    Run evaluation on all profiles (or a subset).

    Args:
        profiles_to_run: Optional list of profile IDs to run (e.g. ["truck_driver_sd"])
        fast_mode: If True, only runs first profile (for smoke testing)

    Returns:
        (per-profile results, aggregate metrics)
    """
    # Load profiles
    with PROFILES_FILE.open() as f:
        data = json.load(f)
    profiles = data["profiles"]

    if fast_mode:
        profiles = profiles[:1]
        print("⚡ FAST MODE: running 1 profile only")
    elif profiles_to_run:
        profiles = [p for p in profiles if p["id"] in profiles_to_run]
        print(f"🎯 Running {len(profiles)} selected profiles: {profiles_to_run}")

    if not profiles:
        print("❌ No profiles to run!")
        return [], aggregate([])

    print(f"\n{'='*78}")
    print(f"CaliforniaCFO Evaluation — {len(profiles)} profile(s)")
    print(f"Backend: {BACKEND_URL}")
    print(f"{'='*78}\n")

    # Check backend alive
    async with httpx.AsyncClient() as client:
        alive = await check_backend_alive(client)
        if not alive:
            print(f"❌ Backend not reachable at {BACKEND_URL}")
            print(f"   Run: make backend")
            sys.exit(1)
        print(f"✓ Backend healthy\n")

        # Run all profiles sequentially (parallel would overwhelm LLM rate limits)
        print(f"Legend: W=Winner, B=Business, R=RealEstate, S=Stock, D=Drift\n")
        results: list[ProfileResult] = []
        for profile in profiles:
            r = await run_single_profile(client, profile)
            results.append(r)

    # Aggregate
    agg = aggregate(results)

    return results, agg


# ──────────────────────────────────────────────────
# REPORT WRITER
# ──────────────────────────────────────────────────
def format_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def format_metric_row(label: str, value: str, target: str = "") -> str:
    """Format a metric line for the markdown report."""
    if target:
        return f"| {label} | {value} | {target} |"
    return f"| {label} | {value} |"


def write_report(
    results: list[ProfileResult],
    agg: AggregateMetrics,
    output_path: Path,
) -> None:
    """Write human-readable Markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: list[str] = []
    lines.append(f"# CaliforniaCFO Evaluation Report")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}  ")
    lines.append(f"**Backend:** `{BACKEND_URL}`  ")
    lines.append(f"**Profiles run:** {agg.total_profiles}  ")
    lines.append(f"**Successful:** {agg.successful_profiles} / {agg.total_profiles}  ")
    lines.append("")

    # ─── EXECUTIVE SUMMARY ───
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("| Metric | Value | Target |")
    lines.append("|---|---|---|")
    lines.append(format_metric_row(
        "**Winner Selection Accuracy**",
        format_pct(agg.winner_accuracy),
        "≥ 80%",
    ))
    lines.append(format_metric_row(
        "**Overall Status Accuracy (3 agents avg)**",
        format_pct(agg.overall_status_accuracy),
        "≥ 75%",
    ))
    lines.append(format_metric_row(
        "**Business Type Adherence** (hours-aware filtering)",
        format_pct(agg.business_type_accuracy),
        "≥ 90%",
    ))
    lines.append(format_metric_row(
        "**RAG Drift Pass Rate** (no Palo Alto $3M+ anti-pattern)",
        format_pct(agg.drift_check_pass_rate),
        "100%",
    ))
    lines.append(format_metric_row(
        "**Mean Latency**",
        f"{agg.latency_mean:.1f}s",
        "≤ 60s",
    ))
    lines.append(format_metric_row(
        "**P95 Latency**",
        f"{agg.latency_p95:.1f}s",
        "≤ 90s",
    ))
    lines.append(format_metric_row(
        "**Avg Cost per Request**",
        f"${agg.cost_per_request_mean_usd:.4f}",
        "≤ $0.20",
    ))
    lines.append("")

    # ─── PER-AGENT BREAKDOWN ───
    lines.append("## Per-Agent Status Accuracy")
    lines.append("")
    lines.append("| Agent | Accuracy |")
    lines.append("|---|---|")
    lines.append(f"| Business | {format_pct(agg.business_status_accuracy)} |")
    lines.append(f"| Real Estate | {format_pct(agg.real_estate_status_accuracy)} |")
    lines.append(f"| Stock | {format_pct(agg.stock_status_accuracy)} |")
    lines.append("")

    # ─── PERFORMANCE ───
    lines.append("## Performance Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Latency mean | {agg.latency_mean:.2f}s |")
    lines.append(f"| Latency p50 | {agg.latency_p50:.2f}s |")
    lines.append(f"| Latency p95 | {agg.latency_p95:.2f}s |")
    lines.append(f"| Latency max | {agg.latency_max:.2f}s |")
    lines.append(f"| Total input tokens | {agg.total_input_tokens:,} |")
    lines.append(f"| Total output tokens | {agg.total_output_tokens:,} |")
    lines.append(f"| Total cost | ${agg.total_cost_usd:.4f} |")
    lines.append(f"| Cost per request | ${agg.cost_per_request_mean_usd:.4f} |")
    lines.append("")

    # ─── PER-PROFILE DETAILS ───
    lines.append("## Per-Profile Results")
    lines.append("")
    lines.append("| Profile | Winner | Biz Status | RE Status | Stock Status | Drift | Latency | Cost |")
    lines.append("|---|---|---|---|---|---|---|---|")

    for r in results:
        if not r.success:
            lines.append(
                f"| ❌ {r.profile_name} | ERROR: {(r.error or '')[:50]} | - | - | - | - | "
                f"{r.latency_sec:.1f}s | - |"
            )
            continue

        winner_cell = (
            f"✓ {r.winner_actual}"
            if r.winner_correct
            else f"✗ got `{r.winner_actual}`, expected {r.winner_expected}"
        )
        biz_cell = (
            f"✓ {r.business_status_actual}"
            if r.business_status_correct
            else f"✗ {r.business_status_actual}"
        )
        re_cell = (
            f"✓ {r.real_estate_status_actual}"
            if r.real_estate_status_correct
            else f"✗ {r.real_estate_status_actual}"
        )
        stock_cell = (
            f"✓ {r.stock_status_actual}"
            if r.stock_status_correct
            else f"✗ {r.stock_status_actual}"
        )
        drift_cell = "✓" if r.drift_check_passed else "✗"

        lines.append(
            f"| {r.profile_name} | {winner_cell} | {biz_cell} | {re_cell} | {stock_cell} | "
            f"{drift_cell} | {r.latency_sec:.1f}s | ${r.cost_usd:.4f} |"
        )

    lines.append("")

    # ─── DRIFT DETAILS ───
    drift_issues = [r for r in results if r.success and not r.drift_check_passed]
    if drift_issues:
        lines.append("## ⚠️ Drift Issues Detected")
        lines.append("")
        for r in drift_issues:
            lines.append(f"- **{r.profile_name}**: {r.drift_check_detail}")
        lines.append("")

    # ─── METHODOLOGY ───
    lines.append("## Methodology")
    lines.append("")
    lines.append("**Validation set:** 8 California-representative profiles covering "
                 "demographics (truck driver → film producer), regions (Bay Area, LA, SD, "
                 "Sacramento, Inland Empire), labor capacity (0-5h → 30+h), and sectors "
                 "(Tech, Healthcare, Entertainment, etc).")
    lines.append("")
    lines.append("**Metrics computed:**")
    lines.append("")
    lines.append("1. **Winner Selection Accuracy** — Does the judge agent's recommendation "
                 "match the set of plausible winners for this profile?")
    lines.append("2. **Status Accuracy per agent** — Is each agent's status "
                 "(profitable / marginal / not_profitable / rejected) within the expected range?")
    lines.append("3. **Business Type Adherence** — Critical hours-aware filter: 0-5h profiles "
                 "must NOT get high-labor businesses (services, e-commerce); they get passive_income.")
    lines.append("4. **RAG Drift Check** — Did the real estate agent stay within plausible "
                 "property values? Catches the historical `Palo Alto $3.2M` anti-pattern.")
    lines.append("5. **Latency** — End-to-end /analyze request time (3 parallel agents + judge).")
    lines.append("6. **Cost** — Token usage estimated from request/response JSON sizes "
                 f"+ assumed RAG context (4 × 2500 input tokens), priced at OpenRouter rates "
                 f"(${3.00}/1M input, ${15.00}/1M output for Claude 3.5 Sonnet).")
    lines.append("")

    lines.append("**Honesty note:** Token counts are *estimated* (the orchestrator doesn't "
                 "expose `usage` field per-call). Real costs may differ by ±30%.")
    lines.append("")

    # Write
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 Report written: {output_path}")


def write_raw_results(results: list[ProfileResult], output_dir: Path) -> Path:
    """Save raw per-profile results as JSON for later analysis."""
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"results_{timestamp}.json"

    payload = {
        "timestamp": datetime.now().isoformat(),
        "backend_url": BACKEND_URL,
        "profiles": [
            {
                "profile_id": r.profile_id,
                "profile_name": r.profile_name,
                "success": r.success,
                "error": r.error,
                "winner_correct": r.winner_correct,
                "winner_actual": r.winner_actual,
                "winner_expected": r.winner_expected,
                "business_status_correct": r.business_status_correct,
                "business_status_actual": r.business_status_actual,
                "real_estate_status_correct": r.real_estate_status_correct,
                "real_estate_status_actual": r.real_estate_status_actual,
                "stock_status_correct": r.stock_status_correct,
                "stock_status_actual": r.stock_status_actual,
                "business_type_correct": r.business_type_correct,
                "business_type_actual": r.business_type_actual,
                "drift_check_passed": r.drift_check_passed,
                "drift_check_detail": r.drift_check_detail,
                "latency_sec": r.latency_sec,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cost_usd": r.cost_usd,
            }
            for r in results
        ],
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return output_path


# ──────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run CaliforniaCFO evaluation suite",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run only the first profile (smoke test, ~30-60s)",
    )
    parser.add_argument(
        "--profile",
        action="append",
        help="Run specific profile(s) by ID (can be used multiple times)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating EVALUATION_REPORT.md",
    )
    args = parser.parse_args()

    profiles_to_run = args.profile if args.profile else None

    # Run async event loop
    results, agg = asyncio.run(
        run_evaluation(profiles_to_run=profiles_to_run, fast_mode=args.fast)
    )

    if not results:
        return 1

    # Print summary to console
    print(f"\n{'='*78}")
    print(f"AGGREGATE METRICS")
    print(f"{'='*78}")
    print(f"  Profiles run:                {agg.total_profiles}")
    print(f"  Successful:                  {agg.successful_profiles}")
    print(f"  Failed:                      {agg.failed_profiles}")
    print()
    print(f"  Winner accuracy:             {format_pct(agg.winner_accuracy)}")
    print(f"  Business status accuracy:    {format_pct(agg.business_status_accuracy)}")
    print(f"  Real estate status accuracy: {format_pct(agg.real_estate_status_accuracy)}")
    print(f"  Stock status accuracy:       {format_pct(agg.stock_status_accuracy)}")
    print(f"  Business type accuracy:      {format_pct(agg.business_type_accuracy)}")
    print(f"  Overall status accuracy:     {format_pct(agg.overall_status_accuracy)}")
    print(f"  Drift pass rate:             {format_pct(agg.drift_check_pass_rate)}")
    print()
    print(f"  Latency (mean):              {agg.latency_mean:.1f}s")
    print(f"  Latency (p95):               {agg.latency_p95:.1f}s")
    print(f"  Latency (max):               {agg.latency_max:.1f}s")
    print()
    print(f"  Total tokens (input):        {agg.total_input_tokens:,}")
    print(f"  Total tokens (output):       {agg.total_output_tokens:,}")
    print(f"  Total cost:                  ${agg.total_cost_usd:.4f}")
    print(f"  Cost per request (mean):     ${agg.cost_per_request_mean_usd:.4f}")
    print(f"{'='*78}\n")

    # Write artifacts
    raw_path = write_raw_results(results, RESULTS_DIR)
    print(f"📁 Raw results: {raw_path}")

    if not args.no_report:
        write_report(results, agg, REPORT_FILE)

    # Exit code: 0 if all critical metrics pass, 1 otherwise
    if agg.successful_profiles < agg.total_profiles:
        print("\n⚠️  Some profiles failed (HTTP errors). See report for details.")
        return 1
    if agg.winner_accuracy < 0.5:
        print("\n⚠️  Winner accuracy below 50%. Quality regression?")
        return 1
    if agg.drift_check_pass_rate < 1.0:
        print("\n⚠️  RAG drift detected. Check report.")
        return 1

    print("\n✅ All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
