# CaliforniaCFO Evaluation Suite

Quality measurement for the `/analyze` endpoint.

## What's measured

| Metric | What it catches |
|---|---|
| **Winner Selection Accuracy** | Judge agent picks plausible strategy for profile |
| **Status Accuracy** (per agent) | profitable / marginal / not_profitable / rejected within expected range |
| **Business Type Adherence** | Hours-aware filtering (0-5h → passive_income, NOT services) |
| **RAG Drift Pass Rate** | Catches the "Palo Alto $3.2M" drift anti-pattern |
| **Latency** (mean, p50, p95, max) | End-to-end /analyze response time |
| **Token Cost** | Estimated USD per request at OpenRouter rates |

## Validation set

8 California-representative profiles in `validation_profiles.json`:

1. **truck_driver_sd** — San Diego, 0-5h labor, $120k savings
2. **doctor_bay_area** — Bay Area, 5-15h, $600k savings (RAG drift trap)
3. **sw_engineer_sf** — SF, 30+h, $80k (low savings → RE rejected)
4. **retired_sacramento** — 0h, $400k (biz rejected)
5. **startup_founder_sf** — Palo Alto, 30+h, $50k (biz wins)
6. **nurse_la** — LA, 15-30h, $90k (balanced, no clear winner)
7. **teacher_inland_empire** — low risk, low savings, conservative
8. **film_producer_la** — Entertainment sector, freelancer, $300k

Each profile specifies `expected` outcomes (lists of acceptable values), so the
evaluator can pass even when there are multiple plausible answers.

## How to run

### Prerequisites

```bash
# Start the backend in another terminal
make backend
```

### Full evaluation (~5-10 minutes)

```bash
make eval
# OR directly:
uv run python evals/run_evaluation.py
```

### Smoke test (1 profile, ~30-60s)

```bash
make eval-fast
# OR:
uv run python evals/run_evaluation.py --fast
```

### Single profile

```bash
uv run python evals/run_evaluation.py --profile truck_driver_sd
```

### Multiple specific profiles

```bash
uv run python evals/run_evaluation.py \
    --profile truck_driver_sd \
    --profile doctor_bay_area
```

## Output

- **Console summary** — quick pass/fail per profile + aggregate
- **`EVALUATION_REPORT.md`** — human-readable Markdown report
- **`results/{timestamp}.json`** — raw per-profile data

## Exit codes

- `0` — All profiles ran, accuracy ≥ 50%, no drift
- `1` — HTTP errors / accuracy regression / drift detected

Use in CI to catch regressions.

## Methodology notes

**Token estimation is approximate.** The orchestrator does not currently expose
per-call `usage` from OpenRouter. We estimate by:

- **Input** = JSON-serialized request × 4 LLM calls + RAG context (~2500 tokens/agent)
- **Output** = JSON-serialized response

Real token usage may differ by ±30%. For exact cost tracking, hook into
`app/services/llm_service.py` to capture `response.json()["usage"]`.

**Multi-valued expectations.** Many profiles have *several* plausible winners
(e.g. for the Doctor, both `stock` and `real_estate` are reasonable). The
validator uses set membership — `actual in expected_list` — to avoid over-fitting.

## Adding a new profile

Edit `validation_profiles.json`:

```json
{
  "id": "your_profile_id",
  "name": "Human-readable name",
  "rationale": "Why this profile tests a specific behavior",
  "input": {
    "user": { ... },
    "config": { ... }
  },
  "expected": {
    "winner_agent": ["stock", "real_estate"],
    "business_status": ["profitable", "marginal"],
    "real_estate_status": ["profitable", "marginal"],
    "stock_status": ["profitable"],
    "business_type": ["passive_income"],
    "property_value_max_usd": 1000000,
    "no_palo_alto_drift": true
  }
}
```

All `expected.*_status` and `winner_agent` fields are **lists** — any of those
values counts as a pass. Omit a key to skip that check for this profile.
