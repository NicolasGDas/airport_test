# from __future__ import annotations
from fastapi import FastAPI
from app.middleware.timing import TimingMiddleware
from app.api.routers import ingest, analytics

app = FastAPI(title="Airports & Routes API (Layered)", version="0.1.0")

app.add_middleware(TimingMiddleware)

app.include_router(ingest.router)
app.include_router(analytics.router)

@app.get("/health")
def health():
    return {"status": "ok"}
