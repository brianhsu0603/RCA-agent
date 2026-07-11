from datetime import datetime

from pydantic import BaseModel, Field

# --- Requests ---------------------------------------------------------------


class TriageRequest(BaseModel):
    symptom: str
    station: str
    test_id: str = ""


class RcaRequest(BaseModel):
    symptom: str
    station: str
    test_id: str = ""
    triage_run_id: str = ""


class FeedbackRequest(BaseModel):
    feedback: str = Field(pattern="^(confirmed|rejected)$")
    notes: str = ""


# --- Responses ----------------------------------------------------------------


class RunAccepted(BaseModel):
    run_id: str
    status: str


class TriageRunOut(BaseModel):
    run_id: str
    symptom: str
    station: str
    test_id: str
    status: str
    severity: str
    category: str
    routing_team: str
    confidence: float
    rationale: str
    error: str
    created_at: datetime
    updated_at: datetime
    rca_run_id: str | None = None
    rca_status: str | None = None

    class Config:
        from_attributes = True


class EvidenceRef(BaseModel):
    type: str
    id: str
    snippet: str = ""


class HypothesisOut(BaseModel):
    id: int
    rank: int
    description: str
    confidence: float
    reasoning: str
    evidence: list[EvidenceRef]
    suggested_workaround: str
    workaround_confidence: float
    feedback: str
    feedback_notes: str

    class Config:
        from_attributes = True


class RcaRunOut(BaseModel):
    run_id: str
    triage_run_id: str
    symptom: str
    station: str
    test_id: str
    status: str
    summary: str
    error: str
    created_at: datetime
    updated_at: datetime
    hypotheses: list[HypothesisOut]

    class Config:
        from_attributes = True


# --- Agent-internal structured outputs (used as the "terminal tool" schema) --


class TriageResult(BaseModel):
    severity: str = Field(description="one of: low, medium, high, critical")
    category: str = Field(
        description="short failure category, e.g. 'connector/mechanical', 'firmware/config', 'test-station'"
    )
    routing_team: str = Field(
        description="team this should be routed to, e.g. 'Process Engineering', 'NPI', 'Test Engineering'"
    )
    confidence: float = Field(ge=0, le=1)
    rationale: str


class HypothesisIn(BaseModel):
    description: str
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    evidence_refs: list[str] = Field(description="evidence ids returned by tool calls, e.g. 'hist:ISS-042'")
    suggested_workaround: str
    workaround_confidence: float = Field(ge=0, le=1)


class RcaReport(BaseModel):
    summary: str
    hypotheses: list[HypothesisIn]
