import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --- Manufacturing data sources -------------------------------------------------


class HistoricalIssue(Base):
    __tablename__ = "historical_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[str] = mapped_column(String, unique=True)
    occurred_at: Mapped[str] = mapped_column(String)
    station: Mapped[str] = mapped_column(String)
    symptom: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str] = mapped_column(Text)
    resolution: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, default=list)


class FmeaEntry(Base):
    __tablename__ = "fmea_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    component: Mapped[str] = mapped_column(String)
    failure_mode: Mapped[str] = mapped_column(String)
    effect: Mapped[str] = mapped_column(Text)
    cause: Mapped[str] = mapped_column(Text)
    severity: Mapped[int] = mapped_column(Integer)
    occurrence: Mapped[int] = mapped_column(Integer)
    detection: Mapped[int] = mapped_column(Integer)
    rpn: Mapped[int] = mapped_column(Integer)


class WirelistEntry(Base):
    __tablename__ = "wirelist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    connector: Mapped[str] = mapped_column(String)
    pin: Mapped[str] = mapped_column(String)
    signal: Mapped[str] = mapped_column(String)
    from_ref: Mapped[str] = mapped_column(String)
    to_ref: Mapped[str] = mapped_column(String)


class BomEntry(Base):
    __tablename__ = "bom_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    part_number: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    revision: Mapped[str] = mapped_column(String)
    supplier: Mapped[str] = mapped_column(String)
    notes: Mapped[str] = mapped_column(Text, default="")


class FirmwareConfig(Base):
    __tablename__ = "firmware_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    station: Mapped[str] = mapped_column(String)
    config_key: Mapped[str] = mapped_column(String)
    value: Mapped[str] = mapped_column(String)
    version: Mapped[str] = mapped_column(String)


class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_id: Mapped[str] = mapped_column(String, unique=True)
    station: Mapped[str] = mapped_column(String)
    timestamp: Mapped[str] = mapped_column(String)
    measurements: Mapped[dict] = mapped_column(JSON, default=dict)
    pass_fail: Mapped[str] = mapped_column(String)
    notes: Mapped[str] = mapped_column(Text, default="")


class SlackMessage(Base):
    __tablename__ = "slack_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel: Mapped[str] = mapped_column(String)
    thread_ts: Mapped[str] = mapped_column(String)
    author: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text)
    ts: Mapped[str] = mapped_column(String)


# --- Agent runs ------------------------------------------------------------------


class TriageRun(Base):
    __tablename__ = "triage_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, unique=True, default=_uuid)
    symptom: Mapped[str] = mapped_column(Text)
    station: Mapped[str] = mapped_column(String)
    test_id: Mapped[str] = mapped_column(String, default="")

    status: Mapped[str] = mapped_column(String, default="pending")  # pending|running|complete|failed
    severity: Mapped[str] = mapped_column(String, default="")
    category: Mapped[str] = mapped_column(String, default="")
    routing_team: Mapped[str] = mapped_column(String, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    rationale: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class RcaRun(Base):
    __tablename__ = "rca_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, unique=True, default=_uuid)
    triage_run_id: Mapped[str] = mapped_column(String, default="")

    symptom: Mapped[str] = mapped_column(Text)
    station: Mapped[str] = mapped_column(String)
    test_id: Mapped[str] = mapped_column(String, default="")

    status: Mapped[str] = mapped_column(String, default="pending")  # pending|running|complete|failed
    summary: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    hypotheses: Mapped[list["Hypothesis"]] = relationship(
        back_populates="rca_run", cascade="all, delete-orphan", order_by="Hypothesis.rank"
    )


class Hypothesis(Base):
    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rca_run_id: Mapped[int] = mapped_column(ForeignKey("rca_runs.id"))
    rank: Mapped[int] = mapped_column(Integer, default=0)

    description: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[list] = mapped_column(JSON, default=list)  # [{type, id, snippet}]

    suggested_workaround: Mapped[str] = mapped_column(Text, default="")
    workaround_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    feedback: Mapped[str] = mapped_column(String, default="pending")  # pending|confirmed|rejected
    feedback_notes: Mapped[str] = mapped_column(Text, default="")

    rca_run: Mapped["RcaRun"] = relationship(back_populates="hypotheses")
