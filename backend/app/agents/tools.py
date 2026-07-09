"""Data-access functions exposed to the agents as tools.

Each function queries one manufacturing data source and returns a list of dicts
shaped like {"evidence_id": ..., **fields}. The evidence_id is what the agent is
asked to cite in its final hypotheses, so the UI can link a claim back to the
underlying record. Search-style tools use Postgres full-text search (to_tsvector /
plainto_tsquery) - sufficient for this scaffold's data volume; swap for pgvector +
embeddings if semantic recall over much larger corpora becomes necessary.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    BomEntry,
    Diagnostic,
    FirmwareConfig,
    FmeaEntry,
    HistoricalIssue,
    SlackMessage,
    WirelistEntry,
)


def _fts(column_expr, query: str):
    tsvector = func.to_tsvector("english", column_expr)
    tsquery = func.plainto_tsquery("english", query)
    return tsvector.op("@@")(tsquery), func.ts_rank(tsvector, tsquery)


def search_historical_issues(db: Session, query: str, top_k: int = 5) -> list[dict]:
    combined = func.concat_ws(
        " ", HistoricalIssue.symptom, HistoricalIssue.root_cause, HistoricalIssue.resolution
    )
    match, rank = _fts(combined, query)
    rows = (
        db.query(HistoricalIssue)
        .filter(match)
        .order_by(rank.desc())
        .limit(top_k)
        .all()
    )
    return [
        {
            "evidence_id": f"hist:{r.issue_id}",
            "issue_id": r.issue_id,
            "occurred_at": r.occurred_at,
            "station": r.station,
            "symptom": r.symptom,
            "root_cause": r.root_cause,
            "resolution": r.resolution,
            "tags": r.tags,
        }
        for r in rows
    ]


def get_fmea(db: Session, component_or_failure_mode: str, top_k: int = 5) -> list[dict]:
    combined = func.concat_ws(" ", FmeaEntry.component, FmeaEntry.failure_mode, FmeaEntry.cause)
    match, rank = _fts(combined, component_or_failure_mode)
    rows = db.query(FmeaEntry).filter(match).order_by(rank.desc()).limit(top_k).all()
    return [
        {
            "evidence_id": f"fmea:{r.code}",
            "component": r.component,
            "failure_mode": r.failure_mode,
            "effect": r.effect,
            "cause": r.cause,
            "severity": r.severity,
            "occurrence": r.occurrence,
            "detection": r.detection,
            "rpn": r.rpn,
        }
        for r in rows
    ]


def get_wirelist(db: Session, connector: str) -> list[dict]:
    rows = (
        db.query(WirelistEntry)
        .filter(WirelistEntry.connector.ilike(f"%{connector}%"))
        .all()
    )
    return [
        {
            "evidence_id": f"wire:{r.connector}-{r.pin}",
            "connector": r.connector,
            "pin": r.pin,
            "signal": r.signal,
            "from_ref": r.from_ref,
            "to_ref": r.to_ref,
        }
        for r in rows
    ]


def get_bom(db: Session, part_number_or_keyword: str) -> list[dict]:
    combined = func.concat_ws(" ", BomEntry.part_number, BomEntry.description, BomEntry.notes)
    match, rank = _fts(combined, part_number_or_keyword)
    rows = (
        db.query(BomEntry)
        .filter(match | BomEntry.part_number.ilike(f"%{part_number_or_keyword}%"))
        .order_by(rank.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "evidence_id": f"bom:{r.part_number}-rev{r.revision}",
            "part_number": r.part_number,
            "description": r.description,
            "revision": r.revision,
            "supplier": r.supplier,
            "notes": r.notes,
        }
        for r in rows
    ]


def get_firmware_config(db: Session, station: str, key_query: str = "") -> list[dict]:
    q = db.query(FirmwareConfig).filter(FirmwareConfig.station.ilike(f"%{station}%"))
    if key_query:
        q = q.filter(FirmwareConfig.config_key.ilike(f"%{key_query}%"))
    rows = q.all()
    return [
        {
            "evidence_id": f"cfg:{r.code}",
            "station": r.station,
            "config_key": r.config_key,
            "value": r.value,
            "version": r.version,
        }
        for r in rows
    ]


def get_diagnostics(db: Session, test_id: str = "", station: str = "", limit: int = 5) -> list[dict]:
    if test_id:
        q = db.query(Diagnostic).filter(Diagnostic.test_id == test_id)
    else:
        q = db.query(Diagnostic).filter(Diagnostic.station.ilike(f"%{station}%")).limit(limit)
    rows = q.all()
    return [
        {
            "evidence_id": f"diag:{r.test_id}",
            "test_id": r.test_id,
            "station": r.station,
            "timestamp": r.timestamp,
            "measurements": r.measurements,
            "pass_fail": r.pass_fail,
            "notes": r.notes,
        }
        for r in rows
    ]


def search_slack(db: Session, query: str, top_k: int = 5) -> list[dict]:
    match, rank = _fts(SlackMessage.text, query)
    rows = db.query(SlackMessage).filter(match).order_by(rank.desc()).limit(top_k).all()
    return [
        {
            "evidence_id": f"slack:{r.channel}:{r.ts}",
            "channel": r.channel,
            "author": r.author,
            "text": r.text,
            "ts": r.ts,
        }
        for r in rows
    ]
