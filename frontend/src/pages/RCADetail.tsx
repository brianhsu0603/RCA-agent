import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, RcaRun } from "../api/client";
import HypothesisCard from "../components/HypothesisCard";

export default function RCADetail() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<RcaRun | null>(null);
  const [rerunning, setRerunning] = useState(false);
  const navigate = useNavigate();
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  async function refresh() {
    if (!runId) return;
    setRun(await api.getRca(runId));
  }

  async function handleRerun() {
    if (!run) return;
    setRerunning(true);
    try {
      const accepted = await api.createRca({
        symptom: run.symptom,
        station: run.station,
        test_id: run.test_id,
        triage_run_id: run.triage_run_id,
      });
      // Guard against navigating back to this run's page if the user has
      // already left it while this request was in flight (e.g. clicked
      // "Re-run RCA" then immediately clicked back to the triage queue).
      if (isMountedRef.current) {
        navigate(`/rca/${accepted.run_id}`);
      }
    } finally {
      if (isMountedRef.current) {
        setRerunning(false);
      }
    }
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
        {(run.status === "complete" || run.status === "failed") && (
          <button onClick={handleRerun} disabled={rerunning}>
            {rerunning ? "Starting new run..." : "Re-run RCA"}
          </button>
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
