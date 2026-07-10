import logging
from functools import partial

from sqlalchemy.orm import Session

from app.agents import tools
from app.agents.claude_client import run_agent_loop
from app.agents.prompts import TRIAGE_SYSTEM_PROMPT
from app.agents.tool_specs import TRIAGE_TOOLS
from app.config import settings
from app.schemas import TriageResult

logger = logging.getLogger(__name__)


def run_triage(db: Session, symptom: str, station: str, test_id: str) -> TriageResult:
    logger.info("running triage agent station=%s test_id=%s", station, test_id or "unknown")
    user_message = (
        f"Station: {station}\n"
        f"Test ID: {test_id or 'unknown'}\n"
        f"Reported symptom: {symptom}\n\n"
        "Triage this failure."
    )

    tool_executors = {
        "get_diagnostics": partial(tools.get_diagnostics, db),
        "search_historical_issues": partial(tools.search_historical_issues, db),
    }

    result = run_agent_loop(
        model=settings.triage_model,
        system_prompt=TRIAGE_SYSTEM_PROMPT,
        user_message=user_message,
        tools=TRIAGE_TOOLS,
        tool_executors=tool_executors,
        terminal_tool_name="submit_triage_result",
        max_iterations=settings.max_agent_iterations,
    )

    validated = TriageResult.model_validate(result)
    logger.info(
        "triage agent finished station=%s severity=%s confidence=%.2f",
        station,
        validated.severity,
        validated.confidence,
    )
    return validated
