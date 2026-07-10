import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TriageRun
from app.schemas import RunAccepted, TriageRequest, TriageRunOut
from app.tasks import run_triage_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/triage", tags=["triage"])


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
    return runs


@router.get("/{run_id}", response_model=TriageRunOut)
def get_triage_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(TriageRun).filter(TriageRun.run_id == run_id).first()
    if run is None:
        logger.warning("triage run not found run_id=%s", run_id)
        raise HTTPException(status_code=404, detail="triage run not found")
    return run
