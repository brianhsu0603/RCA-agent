import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.logging_config import setup_logging
from app.sentry_init import init_sentry

setup_logging()
init_sentry()

from app.api import health, rca, triage  # noqa: E402
from app.config import settings  # noqa: E402

logger = logging.getLogger(__name__)

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


@app.on_event("startup")
def check_config() -> None:
    logger.info("RCA & Triage Agent starting up (triage_model=%s, rca_model=%s)", settings.triage_model, settings.rca_model)
    if not settings.anthropic_api_key:
        logger.critical(
            "ANTHROPIC_API_KEY is not set - every triage/RCA run will fail. Set it in .env and restart."
        )
