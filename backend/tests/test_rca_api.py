from app.models import Hypothesis, RcaRun
from app.tasks import run_rca_task


def test_create_rca_run_enqueues_task(client, monkeypatch):
    monkeypatch.setattr(run_rca_task, "delay", lambda run_id: None)

    resp = client.post("/api/rca", json={"symptom": "won't boot", "station": "FCT-2"})

    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


def test_get_rca_run_not_found(client):
    resp = client.get("/api/rca/does-not-exist")
    assert resp.status_code == 404


def test_submit_feedback_updates_hypothesis(client, db_session, monkeypatch):
    monkeypatch.setattr(run_rca_task, "delay", lambda run_id: None)

    create_resp = client.post("/api/rca", json={"symptom": "x", "station": "FCT-1"})
    run_id = create_resp.json()["run_id"]

    run = db_session.query(RcaRun).filter(RcaRun.run_id == run_id).first()
    hyp = Hypothesis(rca_run_id=run.id, rank=1, description="cold solder joint", confidence=0.5)
    db_session.add(hyp)
    db_session.commit()
    db_session.refresh(hyp)

    resp = client.post(
        f"/api/rca/{run_id}/hypotheses/{hyp.id}/feedback",
        json={"feedback": "confirmed", "notes": "looks right"},
    )

    assert resp.status_code == 200
    db_session.refresh(hyp)
    assert hyp.feedback == "confirmed"
    assert hyp.feedback_notes == "looks right"


def test_submit_feedback_rejects_invalid_value(client, monkeypatch):
    monkeypatch.setattr(run_rca_task, "delay", lambda run_id: None)

    create_resp = client.post("/api/rca", json={"symptom": "x", "station": "FCT-1"})
    run_id = create_resp.json()["run_id"]

    resp = client.post(f"/api/rca/{run_id}/hypotheses/999/feedback", json={"feedback": "maybe"})

    assert resp.status_code == 422


def test_submit_feedback_unknown_hypothesis_404s(client, monkeypatch):
    monkeypatch.setattr(run_rca_task, "delay", lambda run_id: None)

    create_resp = client.post("/api/rca", json={"symptom": "x", "station": "FCT-1"})
    run_id = create_resp.json()["run_id"]

    resp = client.post(
        f"/api/rca/{run_id}/hypotheses/999999/feedback", json={"feedback": "confirmed"}
    )

    assert resp.status_code == 404
