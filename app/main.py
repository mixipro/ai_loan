# app/main.py

from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="AI Investment & Loan Advisor",
    description="Multi-agent financial decision system",
    version="1.0.0"
)

# register routes
app.include_router(router)


# health check (korisno za testove i Render)
@app.get("/")
def health():
    return {"status": "running"}