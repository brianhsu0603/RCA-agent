from app.tasks import run_triage_task


def test_create_triage_run_enqueues_task(client, monkeypatch):
    enqueued = {}
    monkeypatch.setattr(run_triage_task, "delay", lambda run_id: enqueued.setdefault("run_id", run_id))

    resp = client.post("/api/triage", json={"symptom": "won't boot", "station": "FCT-2", "test_id": "T-1"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert enqueued["run_id"] == body["run_id"]


def test_get_triage_run_not_found(client):
    resp = client.get("/api/triage/does-not-exist")
    assert resp.status_code == 404


def test_list_and_get_triage_run_roundtrip(client, monkeypatch):
    monkeypatch.setattr(run_triage_task, "delay", lambda run_id: None)

    create_resp = client.post("/api/triage", json={"symptom": "x", "station": "FCT-1"})
    run_id = create_resp.json()["run_id"]

    list_resp = client.get("/api/triage")
    assert any(r["run_id"] == run_id for r in list_resp.json())

    get_resp = client.get(f"/api/triage/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["run_id"] == run_id
    assert get_resp.json()["status"] == "pending"
