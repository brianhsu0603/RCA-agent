export interface RunAccepted {
  run_id: string;
  status: string;
}

export interface TriageRun {
  run_id: string;
  symptom: string;
  station: string;
  test_id: string;
  status: string;
  severity: string;
  category: string;
  routing_team: string;
  confidence: number;
  rationale: string;
  error: string;
  created_at: string;
  updated_at: string;
  rca_run_id: string | null;
  rca_status: string | null;
}

export interface EvidenceRef {
  type: string;
  id: string;
  snippet: string;
}

export interface Hypothesis {
  id: number;
  rank: number;
  description: string;
  confidence: number;
  reasoning: string;
  evidence: EvidenceRef[];
  suggested_workaround: string;
  workaround_confidence: number;
  feedback: string;
  feedback_notes: string;
}

export interface RcaRun {
  run_id: string;
  triage_run_id: string;
  symptom: string;
  station: string;
  test_id: string;
  status: string;
  summary: string;
  error: string;
  created_at: string;
  updated_at: string;
  hypotheses: Hypothesis[];
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  createTriage: (body: { symptom: string; station: string; test_id: string }) =>
    fetch("/api/triage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => json<RunAccepted>(r)),

  listTriage: () => fetch("/api/triage").then((r) => json<TriageRun[]>(r)),

  getTriage: (runId: string) => fetch(`/api/triage/${runId}`).then((r) => json<TriageRun>(r)),

  createRca: (body: { symptom: string; station: string; test_id: string; triage_run_id: string }) =>
    fetch("/api/rca", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => json<RunAccepted>(r)),

  listRca: () => fetch("/api/rca").then((r) => json<RcaRun[]>(r)),

  getRca: (runId: string) => fetch(`/api/rca/${runId}`).then((r) => json<RcaRun>(r)),

  submitFeedback: (runId: string, hypothesisId: number, feedback: "confirmed" | "rejected", notes: string) =>
    fetch(`/api/rca/${runId}/hypotheses/${hypothesisId}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feedback, notes }),
    }).then((r) => json<{ status: string }>(r)),
};
