"""Exercises the read tools against the same seed data the app ships with
(app/data/*.json, loaded by app/ingestion/seed.py) - see conftest.py.
"""

from app.agents import tools


def test_search_historical_issues_finds_seeded_usb_c_issue(db_session):
    results = tools.search_historical_issues(db_session, "USB-C connector reflow")
    assert any(r["issue_id"] == "ISS-101" for r in results)
    assert results[0]["evidence_id"].startswith("hist:")


def test_search_historical_issues_no_match_returns_empty(db_session):
    results = tools.search_historical_issues(db_session, "zzz-nonexistent-keyword-zzz")
    assert results == []


def test_get_wirelist_filters_by_connector(db_session):
    results = tools.get_wirelist(db_session, "J4")
    assert results
    assert all(r["connector"] == "J4" for r in results)
    assert results[0]["evidence_id"] == f"wire:J4-{results[0]['pin']}"


def test_get_wirelist_unknown_connector_returns_empty(db_session):
    assert tools.get_wirelist(db_session, "does-not-exist") == []
