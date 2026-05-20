# CaliforniaCFO Evaluation Report

**Generated:** 2026-05-20 07:03:29  
**Backend:** `http://localhost:8000`  
**Profiles run:** 8  
**Successful:** 8 / 8  

## Executive Summary

| Metric | Value | Target |
|---|---|---|
| **Winner Selection Accuracy** | 100.0% | ≥ 80% |
| **Overall Status Accuracy (3 agents avg)** | 95.8% | ≥ 75% |
| **Business Type Adherence** (hours-aware filtering) | 100.0% | ≥ 90% |
| **RAG Drift Pass Rate** (no Palo Alto $3M+ anti-pattern) | 100.0% | 100% |
| **Mean Latency** | 35.0s | ≤ 60s |
| **P95 Latency** | 59.9s | ≤ 90s |
| **Avg Cost per Request** | $0.1414 | ≤ $0.20 |

## Per-Agent Status Accuracy

| Agent | Accuracy |
|---|---|
| Business | 100.0% |
| Real Estate | 87.5% |
| Stock | 100.0% |

## Performance Metrics

| Metric | Value |
|---|---|
| Latency mean | 35.03s |
| Latency p50 | 37.45s |
| Latency p95 | 59.87s |
| Latency max | 62.24s |
| Total input tokens | 81,657 |
| Total output tokens | 59,060 |
| Total cost | $1.1310 |
| Cost per request | $0.1414 |

## Per-Profile Results

| Profile | Winner | Biz Status | RE Status | Stock Status | Drift | Latency | Cost |
|---|---|---|---|---|---|---|---|
| Truck Driver — San Diego | ✓ stock | ✓ not_profitable | ✓ marginal | ✓ profitable | ✓ | 41.6s | $0.1524 |
| Doctor — Bay Area (high income) | ✓ stock | ✓ not_profitable | ✓ not_profitable | ✓ profitable | ✓ | 15.9s | $0.1566 |
| Software Engineer — San Francisco | ✓ business | ✓ marginal | ✗ ? | ✓ marginal | ✓ | 40.1s | $0.1277 |
| Retired Couple — Sacramento | ✓ stock | ✓ not_profitable | ✓ marginal | ✓ profitable | ✓ | 34.8s | $0.1503 |
| Startup Founder — San Francisco | ✓ stock | ✓ not_profitable | ✓ ? | ✓ marginal | ✓ | 15.8s | $0.1335 |
| Nurse — Los Angeles | ✓ stock | ✓ marginal | ✓ ? | ✓ profitable | ✓ | 14.3s | $0.1302 |
| Teacher — Inland Empire | ✓ stock | ✓ not_profitable | ✓ ? | ✓ profitable | ✓ | 55.5s | $0.1291 |
| Film Producer — Los Angeles | ✓ business | ✓ profitable | ✓ not_profitable | ✓ marginal | ✓ | 62.2s | $0.1510 |

## Methodology

**Validation set:** 8 California-representative profiles covering demographics (truck driver → film producer), regions (Bay Area, LA, SD, Sacramento, Inland Empire), labor capacity (0-5h → 30+h), and sectors (Tech, Healthcare, Entertainment, etc).

**Metrics computed:**

1. **Winner Selection Accuracy** — Does the judge agent's recommendation match the set of plausible winners for this profile?
2. **Status Accuracy per agent** — Is each agent's status (profitable / marginal / not_profitable / rejected) within the expected range?
3. **Business Type Adherence** — Critical hours-aware filter: 0-5h profiles must NOT get high-labor businesses (services, e-commerce); they get passive_income.
4. **RAG Drift Check** — Did the real estate agent stay within plausible property values? Catches the historical `Palo Alto $3.2M` anti-pattern.
5. **Latency** — End-to-end /analyze request time (3 parallel agents + judge).
6. **Cost** — Token usage estimated from request/response JSON sizes + assumed RAG context (4 × 2500 input tokens), priced at OpenRouter rates ($3.0/1M input, $15.0/1M output for Claude 3.5 Sonnet).

**Honesty note:** Token counts are *estimated* (the orchestrator doesn't expose `usage` field per-call). Real costs may differ by ±30%.
