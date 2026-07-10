import pytest
from pydantic import ValidationError

from app.schemas import FeedbackRequest, HypothesisIn, RcaReport, TriageResult


def test_feedback_request_accepts_confirmed():
    req = FeedbackRequest(feedback="confirmed")
    assert req.notes == ""


def test_feedback_request_accepts_rejected_with_notes():
    req = FeedbackRequest(feedback="rejected", notes="disagree with this")
    assert req.notes == "disagree with this"


def test_feedback_request_rejects_invalid_value():
    with pytest.raises(ValidationError):
        FeedbackRequest(feedback="maybe")


def test_triage_result_confidence_must_be_within_0_and_1():
    with pytest.raises(ValidationError):
        TriageResult(severity="high", category="x", routing_team="y", confidence=1.5, rationale="z")


def test_rca_report_holds_ranked_hypotheses():
    report = RcaReport(
        summary="summary",
        hypotheses=[
            HypothesisIn(
                description="cold solder joint",
                confidence=0.7,
                reasoning="matches historical issue ISS-101",
                evidence_refs=["hist:ISS-101"],
                suggested_workaround="rework affected units",
                workaround_confidence=0.4,
            )
        ],
    )
    assert report.hypotheses[0].confidence == 0.7
    assert report.hypotheses[0].evidence_refs == ["hist:ISS-101"]
