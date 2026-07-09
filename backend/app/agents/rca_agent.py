from functools import partial

from sqlalchemy.orm import Session

from app.agents import tools
from app.agents.claude_client import run_agent_loop
from app.agents.prompts import RCA_SYSTEM_PROMPT
from app.agents.tool_specs import RCA_TOOLS
from app.config import settings
from app.schemas import RcaReport


def run_rca(
    db: Session,
    symptom: str,
    station: str,
    test_id: str,
    triage_context: str = "",
) -> RcaReport:
    user_message = (
        f"Station: {station}\n"
        f"Test ID: {test_id or 'unknown'}\n"
        f"Reported symptom: {symptom}\n"
        + (f"\nPrior triage classification: {triage_context}\n" if triage_context else "")
        + "\nInvestigate the root cause and produce a ranked hypothesis report."
    )

    tool_executors = {
        "search_historical_issues": partial(tools.search_historical_issues, db),
        "get_fmea": partial(tools.get_fmea, db),
        "get_wirelist": partial(tools.get_wirelist, db),
        "get_bom": partial(tools.get_bom, db),
        "get_firmware_config": partial(tools.get_firmware_config, db),
        "get_diagnostics": partial(tools.get_diagnostics, db),
        "search_slack": partial(tools.search_slack, db),
    }

    result = run_agent_loop(
        model=settings.rca_model,
        system_prompt=RCA_SYSTEM_PROMPT,
        user_message=user_message,
        tools=RCA_TOOLS,
        tool_executors=tool_executors,
        terminal_tool_name="submit_rca_report",
        max_iterations=settings.max_agent_iterations,
    )

    return RcaReport.model_validate(result)
