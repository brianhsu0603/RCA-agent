"""Generic Claude tool-use loop shared by the triage and RCA agents.

The loop keeps calling the model, executing any requested tools, and feeding
results back until the model calls the designated "terminal" tool (its way of
saying "here is my final structured answer"). That terminal call's input is
returned as-is for the caller to validate against a Pydantic schema.
"""

import json
from typing import Any, Callable

import anthropic

from app.config import settings

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

ToolExecutor = Callable[..., Any]


class AgentDidNotFinishError(RuntimeError):
    pass


def run_agent_loop(
    *,
    model: str,
    system_prompt: str,
    user_message: str,
    tools: list[dict],
    tool_executors: dict[str, ToolExecutor],
    terminal_tool_name: str,
    max_iterations: int = 8,
) -> dict:
    messages: list[dict] = [{"role": "user", "content": user_message}]

    for _ in range(max_iterations):
        response = _client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            # Model responded with text only and didn't call the terminal tool -
            # nudge it to finish rather than silently returning nothing useful.
            messages.append(
                {
                    "role": "user",
                    "content": f"Please call {terminal_tool_name} now with your final answer.",
                }
            )
            continue

        terminal_input = None
        tool_results = []
        for block in tool_use_blocks:
            if block.name == terminal_tool_name:
                terminal_input = block.input
                continue
            executor = tool_executors.get(block.name)
            if executor is None:
                result = {"error": f"unknown tool {block.name}"}
            else:
                try:
                    result = executor(**block.input)
                except Exception as e:  # noqa: BLE001 - surface to the model, don't crash the run
                    result = {"error": str(e)}
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                }
            )

        if terminal_input is not None:
            return terminal_input

        messages.append({"role": "user", "content": tool_results})

    raise AgentDidNotFinishError(
        f"Agent did not call {terminal_tool_name} within {max_iterations} iterations"
    )
