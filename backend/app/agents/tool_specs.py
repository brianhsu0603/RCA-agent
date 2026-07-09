"""Anthropic tool-use JSON schemas.

Each agent gets a set of read tools (one per manufacturing data source) plus a
single "terminal" tool it must call to deliver its final structured answer -
submit_triage_result for the triage agent, submit_rca_report for the RCA agent.
Forcing the answer through a schema-validated tool call (rather than parsing free
text) is what makes confidence scores and evidence citations reliable.
"""

SEARCH_HISTORICAL_ISSUES = {
    "name": "search_historical_issues",
    "description": "Full-text search over past resolved manufacturing issues (symptom, root cause, resolution, tags).",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "keywords describing the symptom or suspected cause"},
        },
        "required": ["query"],
    },
}

GET_FMEA = {
    "name": "get_fmea",
    "description": "Search the FMEA (Failure Mode and Effects Analysis) table by component name or failure mode keywords.",
    "input_schema": {
        "type": "object",
        "properties": {
            "component_or_failure_mode": {"type": "string"},
        },
        "required": ["component_or_failure_mode"],
    },
}

GET_WIRELIST = {
    "name": "get_wirelist",
    "description": "Look up wirelist / net connectivity entries for a given connector designator (e.g. 'J4').",
    "input_schema": {
        "type": "object",
        "properties": {
            "connector": {"type": "string"},
        },
        "required": ["connector"],
    },
}

GET_BOM = {
    "name": "get_bom",
    "description": "Search the bill of materials by part number or keyword. Returns all known revisions so revision changes (e.g. supplier ECNs) are visible.",
    "input_schema": {
        "type": "object",
        "properties": {
            "part_number_or_keyword": {"type": "string"},
        },
        "required": ["part_number_or_keyword"],
    },
}

GET_FIRMWARE_CONFIG = {
    "name": "get_firmware_config",
    "description": "Look up firmware/test-station configuration values for a given station, optionally filtered by config key keyword.",
    "input_schema": {
        "type": "object",
        "properties": {
            "station": {"type": "string"},
            "key_query": {"type": "string", "description": "optional keyword to filter config_key"},
        },
        "required": ["station"],
    },
}

GET_DIAGNOSTICS = {
    "name": "get_diagnostics",
    "description": "Look up test-station diagnostic records: pass a specific test_id, or a station to see recent records from that station.",
    "input_schema": {
        "type": "object",
        "properties": {
            "test_id": {"type": "string", "description": "exact test id, if known"},
            "station": {"type": "string", "description": "station name, used when test_id is not known"},
        },
    },
}

SEARCH_SLACK = {
    "name": "search_slack",
    "description": "Full-text search over engineering Slack channels for relevant discussion (e.g. supplier changes, fixture wear, calibration issues).",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
        },
        "required": ["query"],
    },
}

SUBMIT_TRIAGE_RESULT = {
    "name": "submit_triage_result",
    "description": "Deliver the final triage result. Call this exactly once you have enough evidence to classify the failure.",
    "input_schema": {
        "type": "object",
        "properties": {
            "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            "category": {"type": "string", "description": "short failure category, e.g. 'connector/mechanical', 'firmware/config', 'test-station'"},
            "routing_team": {"type": "string", "description": "team to route to, e.g. 'Process Engineering', 'NPI', 'Test Engineering'"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"},
        },
        "required": ["severity", "category", "routing_team", "confidence", "rationale"],
    },
}

SUBMIT_RCA_REPORT = {
    "name": "submit_rca_report",
    "description": "Deliver the final RCA report as a ranked list of hypotheses. Call this exactly once you have gathered sufficient evidence.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "1-2 sentence overview of the investigation"},
            "hypotheses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "the candidate root cause"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "reasoning": {"type": "string", "description": "why this evidence supports this hypothesis"},
                        "evidence_refs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "evidence_id values returned by tool calls, e.g. 'hist:ISS-088'",
                        },
                        "suggested_workaround": {"type": "string"},
                        "workaround_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": [
                        "description",
                        "confidence",
                        "reasoning",
                        "evidence_refs",
                        "suggested_workaround",
                        "workaround_confidence",
                    ],
                },
            },
        },
        "required": ["summary", "hypotheses"],
    },
}

TRIAGE_TOOLS = [
    GET_DIAGNOSTICS,
    SEARCH_HISTORICAL_ISSUES,
    SUBMIT_TRIAGE_RESULT,
]

RCA_TOOLS = [
    SEARCH_HISTORICAL_ISSUES,
    GET_FMEA,
    GET_WIRELIST,
    GET_BOM,
    GET_FIRMWARE_CONFIG,
    GET_DIAGNOSTICS,
    SEARCH_SLACK,
    SUBMIT_RCA_REPORT,
]
