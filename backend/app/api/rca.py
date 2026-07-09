from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Hypothesis, RcaRun
from app.schemas import FeedbackRequest, RcaRequest, RcaRunOut, RunAccepted
from app.tasks import run_rca_task

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
        raise HTTPException(status_code=404, detail="rca run not found")
    return run


@router.post("/{run_id}/hypotheses/{hypothesis_id}/feedback")
def submit_feedback(
    run_id: str, hypothesis_id: int, req: FeedbackRequest, db: Session = Depends(get_db)
):
    run = db.query(RcaRun).filter(RcaRun.run_id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="rca run not found")

    hyp = (
        db.query(Hypothesis)
        .filter(Hypothesis.id == hypothesis_id, Hypothesis.rca_run_id == run.id)
        .first()
    )
    if hyp is None:
        raise HTTPException(status_code=404, detail="hypothesis not found")

    hyp.feedback = req.feedback
    hyp.feedback_notes = req.notes
    db.commit()
    return {"status": "ok"}
