import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Hypothesis, RcaRun
from app.schemas import FeedbackRequest, RcaRequest, RcaRunOut, RunAccepted
from app.tasks import run_rca_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rca", tags=["rca"])


@router.post("", response_model=RunAccepted)
def create_rca_run(req: RcaRequest, db: Session = Depends(get_db)):
    run = RcaRun(
        symptom=req.symptom,
        station=req.station,
        test_id=req.test_id,
        triage_run_id=req.triage_run_id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    logger.info(
        "rca run created run_id=%s station=%s test_id=%s triage_run_id=%s",
        run.run_id,
        run.station,
        run.test_id,
        run.triage_run_id,
    )
    run_rca_task.delay(run.run_id)

    return RunAccepted(run_id=run.run_id, status=run.status)


@router.get("", response_model=list[RcaRunOut])
def list_rca_runs(db: Session = Depends(get_db)):
    runs = db.query(RcaRun).order_by(RcaRun.created_at.desc()).limit(50).all()
    return runs


@router.get("/{run_id}", response_model=RcaRunOut)
def get_rca_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(RcaRun).filter(RcaRun.run_id == run_id).first()
    if run is None:
        logger.warning("rca run not found run_id=%s", run_id)
        raise HTTPException(status_code=404, detail="rca run not found")
    return run


@router.post("/{run_id}/hypotheses/{hypothesis_id}/feedback")
def submit_feedback(
    run_id: str, hypothesis_id: int, req: FeedbackRequest, db: Session = Depends(get_db)
):
    run = db.query(RcaRun).filter(RcaRun.run_id == run_id).first()
    if run is None:
        logger.warning("rca run not found run_id=%s", run_id)
        raise HTTPException(status_code=404, detail="rca run not found")

    hyp = (
        db.query(Hypothesis)
        .filter(Hypothesis.id == hypothesis_id, Hypothesis.rca_run_id == run.id)
        .first()
    )
    if hyp is None:
        logger.warning("hypothesis not found run_id=%s hypothesis_id=%s", run_id, hypothesis_id)
        raise HTTPException(status_code=404, detail="hypothesis not found")

    hyp.feedback = req.feedback
    hyp.feedback_notes = req.notes
    db.commit()
    logger.info(
        "engineer feedback recorded run_id=%s hypothesis_id=%s feedback=%s",
        run_id,
        hypothesis_id,
        req.feedback,
    )
    return {"status": "ok"}
