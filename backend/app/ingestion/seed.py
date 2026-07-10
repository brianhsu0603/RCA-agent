"""Loads the bundled mock manufacturing data sources into Postgres on first boot.

Real deployments would replace this with connectors into the actual PLM/MES/FMEA
systems (see app/ingestion/slack_ingest.py for the pattern used for a live source).
Each table is only populated if empty, so this is safe to run on every container start.
"""

import json
import logging
from pathlib import Path

from sqlalchemy import text

from app.db import Base, SessionLocal, engine
from app.models import (
    BomEntry,
    Diagnostic,
    FirmwareConfig,
    FmeaEntry,
    HistoricalIssue,
    SlackMessage,
    WirelistEntry,
)

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Arbitrary constant used as a Postgres advisory lock key so that the backend
# and worker containers - which both run this on startup - don't race on
# `create_all` against a fresh database (concurrent CREATE TABLE can throw
# duplicate-key errors on Postgres' internal catalog).
_SEED_LOCK_KEY = 875_309


def _load(name: str) -> list[dict]:
    with open(DATA_DIR / name) as f:
        return json.load(f)


def seed() -> None:
    logger.info("acquiring seed advisory lock")
    with engine.connect() as conn:
        conn.execute(text("SELECT pg_advisory_lock(:key)"), {"key": _SEED_LOCK_KEY})
        try:
            Base.metadata.create_all(bind=engine)
            _seed_rows()
        except Exception:
            logger.exception("seeding failed")
            raise
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": _SEED_LOCK_KEY})
    logger.info("seed complete")


def _seed_rows() -> None:
    db = SessionLocal()
    try:
        for model, filename in (
            (HistoricalIssue, "historical_issues.json"),
            (FmeaEntry, "fmea.json"),
            (WirelistEntry, "wirelist.json"),
            (BomEntry, "bom.json"),
            (FirmwareConfig, "firmware_config.json"),
            (Diagnostic, "diagnostics.json"),
            (SlackMessage, "slack_threads.json"),
        ):
            if db.query(model).count() == 0:
                rows = _load(filename)
                db.add_all(model(**row) for row in rows)
                logger.info("seeded %d rows into %s", len(rows), model.__tablename__)
            else:
                logger.info("%s already populated, skipping", model.__tablename__)

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    from app.logging_config import setup_logging

    setup_logging()
    seed()
