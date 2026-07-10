import json
import logging
from functools import partial

from sqlalchemy.orm import Session

from app.agents import tools
from app.agents.claude_client import run_agent_loop
from app.agents.prompts import RCA_SYSTEM_PROMPT
from app.agents.tool_specs import RCA_TOOLS
from app.config import settings
from app.schemas import RcaReport

logger = logging.getLogger(__name__)


def _parse_json_list(raw: str) -> list:
    """Parse a string that's supposed to hold a JSON array of objects, but may
    instead be a single well-formed array, a bare object, or several JSON
    objects concatenated back-to-back with no enclosing brackets (and possibly
    no separating commas) - all observed from submit_rca_report calls with many
    hypotheses."""
    raw = raw.strip()
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    items: list = []
    idx = 0
    while idx < len(raw):
        while idx < len(raw) and raw[idx] in " \t\n\r,":
            idx += 1
        if idx >= len(raw):
            break
        obj, end = decoder.raw_decode(raw, idx)
        items.append(obj)
        idx = end
    return items


def _normalize_rca_result(result: dict) -> dict:
    """Defensively unwrap fields the model occasionally double-encodes as JSON
    strings instead of native arrays - observed on submit_rca_report calls with
    many hypotheses, where the nested "hypotheses" array (and sometimes a
    hypothesis's "evidence_refs") comes back JSON-stringified rather than as an
    actual list even though the tool schema declares them as arrays."""
    hypotheses = result.get("hypotheses")
    if isinstance(hypotheses, str):
        logger.warning("model returned hypotheses as a JSON string, not a list - unwrapping")
        hypotheses = _parse_json_list(hypotheses)

    normalized = []
    for h in hypotheses:
        if isinstance(h, dict) and isinstance(h.get("evidence_refs"), str):
            h = {**h, "evidence_refs": _parse_json_list(h["evidence_refs"])}
        normalized.append(h)

    return {**result, "hypotheses": normalized}


def run_rca(
    db: Session,
    symptom: str,
    station: str,
    test_id: str,
    triage_context: str = "",
) -> RcaReport:
    logger.info("running rca agent station=%s test_id=%s", station, test_id or "unknown")
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

    validated = RcaReport.model_validate(_normalize_rca_result(result))
    logger.info(
        "rca agent finished station=%s hypothesis_count=%d", station, len(validated.hypotheses)
    )
    return validated
