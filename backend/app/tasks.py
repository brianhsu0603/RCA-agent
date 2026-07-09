from app.agents.rca_agent import run_rca
from app.agents.triage_agent import run_triage
from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import Hypothesis, RcaRun, TriageRun


@celery_app.task(name="app.tasks.run_triage_task")
def run_triage_task(triage_run_id: str) -> None:
    db = SessionLocal()
    try:
        run = db.query(TriageRun).filter(TriageRun.run_id == triage_run_id).first()
        if run is None:
            return
        run.status = "running"
        db.commit()

        try:
            result = run_triage(db, run.symptom, run.station, run.test_id)
            run.severity = result.severity
            run.category = result.category
            run.routing_team = result.routing_team
            run.confidence = result.confidence
            run.rationale = result.rationale
            run.status = "complete"
        except Exception as e:  # noqa: BLE001 - persist failure so the UI can show it
            run.status = "failed"
            run.error = str(e)
        db.commit()
    finally:
        db.close()


@celery_app.task(name="app.tasks.run_rca_task")
def run_rca_task(rca_run_id: str) -> None:
    db = SessionLocal()
    try:
        run = db.query(RcaRun).filter(RcaRun.run_id == rca_run_id).first()
        if run is None:
            return
        run.status = "running"
        db.commit()

        triage_context = ""
        if run.triage_run_id:
            triage = db.query(TriageRun).filter(TriageRun.run_id == run.triage_run_id).first()
            if triage is not None and triage.status == "complete":
                triage_context = (
                    f"severity={triage.severity}, category={triage.category}, "
                    f"rationale={triage.rationale}"
                )

        try:
            result = run_rca(db, run.symptom, run.station, run.test_id, triage_context)
            run.summary = result.summary
            for rank, h in enumerate(
                sorted(result.hypotheses, key=lambda h: h.confidence, reverse=True), start=1
            ):
                db.add(
                    Hypothesis(
                        rca_run_id=run.id,
                        rank=rank,
                        description=h.description,
                        confidence=h.confidence,
                        reasoning=h.reasoning,
                        evidence=[{"type": ref.split(":", 1)[0], "id": ref} for ref in h.evidence_refs],
                        suggested_workaround=h.suggested_workaround,
                        workaround_confidence=h.workaround_confidence,
                    )
                )
            run.status = "complete"
        except Exception as e:  # noqa: BLE001 - persist failure so the UI can show it
            run.status = "failed"
            run.error = str(e)
        db.commit()
    finally:
        db.close()
