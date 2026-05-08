# app/main.py

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.routes import router

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
    title="AI Investment & Loan Advisor",
    description="Multi-agent financial decision system",
    version="2.0.0"
)

# CORS (još uvek korisno za development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes (POSLE setup-a)
app.include_router(router)

# ─────────────────────────
# 🌐 FRONTEND
# ─────────────────────────
# Putanja do frontend foldera (relativna od ovog fajla)
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# ⭐ Root endpoint vraća index.html
@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")

# ⭐ Mount-uje sve ostale fajlove iz frontend foldera
# (CSS, JS, slike — ako kasnije budeš dodavao)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ─────────────────────────
# ❤️ HEALTH CHECK
# ─────────────────────────
@app.get("/health")
def health():
    return {"status": "running"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)