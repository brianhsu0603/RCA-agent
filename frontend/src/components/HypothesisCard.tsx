import { useState } from "react";
import type { Hypothesis } from "../api/client";
import { api } from "../api/client";
import ConfidenceBar from "./ConfidenceBar";

interface Props {
  runId: string;
  hypothesis: Hypothesis;
  onFeedbackSubmitted: () => void;
}

export default function HypothesisCard({ runId, hypothesis, onFeedbackSubmitted }: Props) {
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function sendFeedback(feedback: "confirmed" | "rejected") {
    setSubmitting(true);
    try {
      await api.submitFeedback(runId, hypothesis.id, feedback, notes);
      onFeedbackSubmitted();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card hypothesis-card">
      <div className="hypothesis-header">
        <span className="rank-badge">#{hypothesis.rank}</span>
        <h3>{hypothesis.description}</h3>
      </div>

      <ConfidenceBar value={hypothesis.confidence} label="Root cause confidence" />

      <p className="reasoning">{hypothesis.reasoning}</p>

      {hypothesis.evidence.length > 0 && (
        <div className="evidence-list">
          <span className="evidence-label">Evidence:</span>
          <ul>
            {hypothesis.evidence.map((e) => (
              <li key={e.id}>
                <code>{e.id}</code>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="workaround">
        <strong>Suggested workaround:</strong>
        <p>{hypothesis.suggested_workaround}</p>
        <ConfidenceBar value={hypothesis.workaround_confidence} label="Workaround confidence" />
      </div>

      <div className="feedback-row">
        {hypothesis.feedback === "pending" ? (
          <>
            <input
              type="text"
              placeholder="optional notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
            <button disabled={submitting} onClick={() => sendFeedback("confirmed")}>
              Confirm
            </button>
            <button disabled={submitting} onClick={() => sendFeedback("rejected")} className="secondary">
              Reject
            </button>
          </>
        ) : (
          <span className={`feedback-badge ${hypothesis.feedback}`}>
            Engineer marked: {hypothesis.feedback}
            {hypothesis.feedback_notes ? ` — ${hypothesis.feedback_notes}` : ""}
          </span>
        )}
      </div>
    </div>
  );
}
