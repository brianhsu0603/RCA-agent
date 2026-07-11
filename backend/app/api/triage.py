import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import RcaRun, TriageRun
from app.schemas import RunAccepted, TriageRequest, TriageRunOut
from app.tasks import run_triage_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/triage", tags=["triage"])


def _attach_latest_rca(db: Session, runs: list[TriageRun]) -> list[TriageRun]:
    """Annotate each TriageRun with the most recently created RCA run (if any)
    for it, so the UI knows whether to offer "Run RCA" or "View Result"."""
    if not runs:
        return runs

    triage_ids = [r.run_id for r in runs]
    rca_runs = (
        db.query(RcaRun)
        .filter(RcaRun.triage_run_id.in_(triage_ids))
        .order_by(RcaRun.created_at.asc())
        .all()
    )
    latest_by_triage_id: dict[str, RcaRun] = {}
    for rca in rca_runs:
        latest_by_triage_id[rca.triage_run_id] = rca  # later ones overwrite, so last write wins

    for run in runs:
        latest = latest_by_triage_id.get(run.run_id)
        run.rca_run_id = latest.run_id if latest else None
        run.rca_status = latest.status if latest else None
    return runs


@router.post("", response_model=RunAccepted)
def create_triage_run(req: TriageRequest, db: Session = Depends(get_db)):
    run = TriageRun(symptom=req.symptom, station=req.station, test_id=req.test_id)
    db.add(run)
    db.commit()
    db.refresh(run)

    logger.info(
        "triage run created run_id=%s station=%s test_id=%s", run.run_id, run.station, run.test_id
    )
    run_triage_task.delay(run.run_id)

    return RunAccepted(run_id=run.run_id, status=run.status)


@router.get("", response_model=list[TriageRunOut])
def list_triage_runs(db: Session = Depends(get_db)):
    runs = db.query(TriageRun).order_by(TriageRun.created_at.desc()).limit(50).all()
    return _attach_latest_rca(db, runs)


@router.get("/{run_id}", response_model=TriageRunOut)
def get_triage_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(TriageRun).filter(TriageRun.run_id == run_id).first()
    if run is None:
        logger.warning("triage run not found run_id=%s", run_id)
        raise HTTPException(status_code=404, detail="triage run not found")
    _attach_latest_rca(db, [run])
    return run
