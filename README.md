# CaliforniaCFO

> AI-powered California-focused investment advisor with multi-agent architecture, RAG knowledge base, and triple-validated financial projections.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Node 20 LTS](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)

---

## 🎯 Overview

CaliforniaCFO provides personalized investment recommendations across three asset classes — **business**, **real estate**, and **stocks** — tailored for California's unique tax landscape (Prop 13, capital gains, LLC fees) and regional markets (Bay Area, LA, San Diego, etc.).

**Key features:**

- **Multi-agent architecture** — independent specialists for each asset class, judged by a comparison agent
- **RAG knowledge base** — 51 curated California-specific chunks across business, tax, and real estate domains
- **Triple validation** — math consistency checks, LLM hallucination prevention, status-based downgrade chains
- **Profile-aware** — recommendations adapt to weekly hours, profession, region, risk tolerance
- **Transparent calculations** — step-by-step breakdown of every projection

---

## 🏗️ Architecture

```
ai_loan/
├── app/                      # Python backend (FastAPI + uv)
│   ├── agents/               # Business, Real Estate, Stock, Judge agents
│   ├── api/                  # HTTP routes
│   ├── core/                 # California config, profession catalog
│   ├── engines/              # Investment engine, inflation engine
│   ├── models/               # Pydantic models
│   ├── rag/                  # FAISS + sentence-transformers
│   └── services/             # LLM service, orchestrator
├── evals/                       
│   ├──results
├── frontend-react/           # ⭐ Modern React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
│── logs/
├── Makefile                  # Unified entry point
├── pyproject.toml            # Python deps (uv)
└── README.md
```

---

## 🚀 Quickstart

### Prerequisites

- **Python 3.12+** with [`uv`](https://docs.astral.sh/uv/) installed
- **Node 20 LTS** via [`nvm`](https://github.com/nvm-sh/nvm) (recommended)
- **OpenRouter API key** (or compatible LLM provider)

### Linux setup also if you use Windows need to change Makefile

```bash
# Install uv (if missing)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install nvm (if missing)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
```

### One-time setup

```bash
# Install all dependencies (backend + frontend)
make install

# Or step by step:
make install-backend    # uv sync
make install-frontend   # npm install in frontend-react/
```

### Run development servers

```bash
# Terminal 1 — backend (port 8000)
make backend

# Terminal 2 — React frontend (port 5173)
make frontend

# Open http://localhost:5173 in browser
```

Or with tmux split panes:

```bash
make dev-tmux
```

---

## 📦 Stack

### Backend

| Layer            | Tech                                  |
|------------------|---------------------------------------|
| Language         | Python 3.12                           |
| Framework        | FastAPI 0.136+                        |
| Package manager  | uv (modern, fast pip replacement)     |
| LLM client       | OpenRouter (configurable provider)    |
| Vector DB        | FAISS (CPU)                           |
| Embeddings       | sentence-transformers                 |
| Validation       | Pydantic v2                           |

### Frontend (React)

| Layer            | Tech                                  |
|------------------|---------------------------------------|
| Language         | TypeScript 5                          |
| Framework        | React 18                              |
| Build tool       | Vite 6                                |
| Routing          | React Router 6                        |
| State (server)   | TanStack Query                        |
| State (form)     | react-hook-form + zod                 |
| Styling          | Tailwind CSS 3 + shadcn/ui            |
| Charts           | Recharts                              |
| HTTP             | Axios                                 |

---

## 🔧 Available Commands

Run `make help` for full list:

```bash
make install        # Install all deps
make backend        # Run backend (:8000)
make frontend       # Run React frontend (:5173)
make dev            # Show parallel commands
make dev-tmux       # Run both in tmux split
make legacy         # Open legacy HTML frontend
make test           # Run all tests
make typecheck      # TypeScript typecheck
make lint           # Lint frontend
make build          # Production build frontend
make preview        # Preview production build
make clean          # Clean caches
make clean-deep     # Deep clean (node_modules + .venv)
make status         # Show project status
```

---

## 🧪 Testing

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend
```

---

## 📐 API

Backend exposes:

- `GET /options` — Dropdown values (regions, sectors, professions, interests)
- `POST /analyze` — Main analysis endpoint (accepts `user` + `config`, returns 3 strategies + judge)
- `GET /docs` — OpenAPI/Swagger UI

Example request body:

```json
{
  "user": {
    "personal": { "age": 38 },
    "location": { "region": "BAY_AREA", "city": "Palo Alto" },
    "financial": { "income": 35000, "expenses": 12000, "monthly_debt": 2000, "savings": 600000, "currency": "USD" },
    "professional": { "sector": "Healthcare", "profession": "Physician", "employment_status": "full-time", "interests": ["technology", "real estate"], "prior_experience": "...", "weekly_hours": "5-15" },
    "preferences": { "risk_profile": "low", "horizon": "8+" }
  },
  "config": {
    "business": { "loan_amount": 150000, "loan_years": 7, "savings_to_use": 150000, "interest_rate": 0.075 },
    "real_estate": { "loan_amount": 700000, "loan_years": 30, "savings_to_use": 200000, "interest_rate": 0.058 },
    "stock": { "loan_amount": 0, "loan_years": 0, "savings_to_use": 250000, "interest_rate": 0 }
  }
}
```

---

## 🎯 Project Status

**Version:** v5.2.5 — production-ready


Key validators in place:

- Business: 8-type taxonomy with hours-aware filtering
- Real Estate: segment-aware realism (counters RAG drift)
- Stocks: margin-aware status + scenarios validation
- Investment Engine: hybrid status logic, margin-loan interest-only
- Judge: Y3 comparable-return unified ranking

---
