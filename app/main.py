# app/main.py

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.routes import router
from app.api.loan_offers import router as loan_offers_router

# ─────────────────────────
# 🪵 LOGGER
# ─────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ─────────────────────────
# 🚀 APP
# ─────────────────────────
app = FastAPI(
    title="CaliforniaCFO — AI Financial Advisor",
    description=(
        "Multi-agent financial decision system specialized for California. "
        "Combines deterministic engines, live market data (Phase 2), "
        "and RAG-based California expert knowledge (Phase 3)."
    ),
    version="3.0.0"
)

# CORS (development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router)
app.include_router(loan_offers_router)

# ─────────────────────────
# 🌐 FRONTEND
# ─────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ─────────────────────────
# ❤️ HEALTH CHECK
# ─────────────────────────
@app.get("/health")
def health():
    return {
        "status": "running",
        "system": "CaliforniaCFO",
        "version": "3.0.0",
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
