"""Shared fixtures.

Tests run against a real Postgres (see app/agents/tools.py's docstring on why -
full-text search is Postgres-specific, so SQLite can't stand in). Each test
gets its own transaction that's rolled back afterward, so tests can't see each
other's writes; the reference tables (historical issues, wirelist, etc.) are
seeded once per session from the same fixtures the app seeds itself with.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db import engine, get_db
from app.ingestion.seed import seed
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _seeded_database():
    seed()


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: (yield db_session)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
