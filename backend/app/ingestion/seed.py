"""Loads the bundled mock manufacturing data sources into Postgres on first boot.

Real deployments would replace this with connectors into the actual PLM/MES/FMEA
systems (see app/ingestion/slack_ingest.py for the pattern used for a live source).
Each table is only populated if empty, so this is safe to run on every container start.
"""

import json
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
    with engine.connect() as conn:
        conn.execute(text("SELECT pg_advisory_lock(:key)"), {"key": _SEED_LOCK_KEY})
        try:
            Base.metadata.create_all(bind=engine)
            _seed_rows()
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": _SEED_LOCK_KEY})


def _seed_rows() -> None:
    db = SessionLocal()
    try:
        if db.query(HistoricalIssue).count() == 0:
            db.add_all(HistoricalIssue(**row) for row in _load("historical_issues.json"))

        if db.query(FmeaEntry).count() == 0:
            db.add_all(FmeaEntry(**row) for row in _load("fmea.json"))

        if db.query(WirelistEntry).count() == 0:
            db.add_all(WirelistEntry(**row) for row in _load("wirelist.json"))

        if db.query(BomEntry).count() == 0:
            db.add_all(BomEntry(**row) for row in _load("bom.json"))

        if db.query(FirmwareConfig).count() == 0:
            db.add_all(FirmwareConfig(**row) for row in _load("firmware_config.json"))

        if db.query(Diagnostic).count() == 0:
            db.add_all(Diagnostic(**row) for row in _load("diagnostics.json"))

        if db.query(SlackMessage).count() == 0:
            db.add_all(SlackMessage(**row) for row in _load("slack_threads.json"))

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seed complete.")
