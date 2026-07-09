import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, RcaRun } from "../api/client";
import HypothesisCard from "../components/HypothesisCard";

export default function RCADetail() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<RcaRun | null>(null);

  async function refresh() {
    if (!runId) return;
    setRun(await api.getRca(runId));
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(() => {
      if (run?.status === "pending" || run?.status === "running" || !run) {
        refresh();
      }
    }, 2000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId, run?.status]);

  if (!run) return <p>Loading...</p>;

  return (
    <div className="rca-page">
      <Link to="/" className="back-link">
        ← Triage queue
      </Link>

      <section className="card">
        <h2>RCA run</h2>
        <p>
          <strong>Station:</strong> {run.station} &nbsp; <strong>Test ID:</strong>{" "}
          {run.test_id || "—"}
        </p>
        <p>
          <strong>Symptom:</strong> {run.symptom}
        </p>
        <p>
          <span className={`status-badge ${run.status}`}>{run.status}</span>
        </p>
        {run.status === "complete" && <p className="summary">{run.summary}</p>}
        {run.status === "failed" && <p className="error-text">{run.error}</p>}
        {(run.status === "pending" || run.status === "running") && (
          <p className="pending-text">Agent is investigating - gathering evidence across data sources...</p>
        )}
      </section>

      {run.hypotheses.length > 0 && (
        <section>
          <h2>Ranked hypotheses</h2>
          {run.hypotheses.map((h) => (
            <HypothesisCard key={h.id} runId={run.run_id} hypothesis={h} onFeedbackSubmitted={refresh} />
          ))}
        </section>
      )}
    </div>
  );
}
