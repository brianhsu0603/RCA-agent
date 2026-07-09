from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, rca, triage
from app.config import settings

app = FastAPI(title="RCA & Triage Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(triage.router)
app.include_router(rca.router)
