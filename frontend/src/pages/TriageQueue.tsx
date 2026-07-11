import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, TriageRun } from "../api/client";

const STATIONS = ["FCT-2", "FCT-1", "ICT-1"];

export default function TriageQueue() {
  const [symptom, setSymptom] = useState(
    "Intermittent USB-C continuity fail on CC1 line, batch B-2026-19."
  );
  const [station, setStation] = useState(STATIONS[0]);
  const [testId, setTestId] = useState("FCT2-88213");
  const [submitting, setSubmitting] = useState(false);
  const [runs, setRuns] = useState<TriageRun[]>([]);
  const [rcaLaunching, setRcaLaunching] = useState<string | null>(null);
  const navigate = useNavigate();

  async function refresh() {
    setRuns(await api.listTriage());
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.createTriage({ symptom, station, test_id: testId });
      await refresh();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRunRca(run: TriageRun) {
    setRcaLaunching(run.run_id);
    try {
      const accepted = await api.createRca({
        symptom: run.symptom,
        station: run.station,
        test_id: run.test_id,
        triage_run_id: run.run_id,
      });
      navigate(`/rca/${accepted.run_id}`);
    } finally {
      setRcaLaunching(null);
    }
  }

  return (
    <div className="triage-page">
      <section className="card">
        <h2>Report a failure</h2>
        <form onSubmit={handleSubmit} className="triage-form">
          <label>
            Station
            <select value={station} onChange={(e) => setStation(e.target.value)}>
              {STATIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label>
            Test ID (optional)
            <input value={testId} onChange={(e) => setTestId(e.target.value)} placeholder="e.g. FCT2-88213" />
          </label>
          <label>
            Symptom
            <textarea
              value={symptom}
              onChange={(e) => setSymptom(e.target.value)}
              rows={3}
              required
            />
          </label>
          <button type="submit" disabled={submitting}>
            {submitting ? "Submitting..." : "Submit for triage"}
          </button>
        </form>
      </section>

      <section className="card">
        <h2>Triage queue</h2>
        <table className="runs-table">
          <thead>
            <tr>
              <th>Station</th>
              <th>Symptom</th>
              <th>Status</th>
              <th>Severity</th>
              <th>Category</th>
              <th>Routing</th>
              <th>Confidence</th>
              <th>RCA Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.run_id}>
                <td>{run.station}</td>
                <td className="symptom-cell">{run.symptom}</td>
                <td>
                  <span className={`status-badge ${run.status}`}>{run.status}</span>
                </td>
                <td>{run.severity}</td>
                <td>{run.category}</td>
                <td>{run.routing_team}</td>
                <td>{run.status === "complete" ? `${Math.round(run.confidence * 100)}%` : "—"}</td>
                <td>
                  {run.status === "complete" ? (
                    <span className={`status-badge ${run.rca_status ?? "pending"}`}>
                      {run.rca_status ?? "pending"}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td>
                  {run.status === "complete" && run.rca_run_id && (
                    <button onClick={() => navigate(`/rca/${run.rca_run_id}`)}>
                      View Result
                    </button>
                  )}
                  {run.status === "complete" && !run.rca_run_id && (
                    <button
                      onClick={() => handleRunRca(run)}
                      disabled={rcaLaunching === run.run_id}
                    >
                      {rcaLaunching === run.run_id ? "Launching..." : "Run RCA"}
                    </button>
                  )}
                  {run.status === "failed" && <span className="error-text">{run.error}</span>}
                </td>
              </tr>
            ))}
            {runs.length === 0 && (
              <tr>
                <td colSpan={9} className="empty-row">
                  No triage runs yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
