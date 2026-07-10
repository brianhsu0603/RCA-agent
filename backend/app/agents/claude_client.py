"""Generic Claude tool-use loop shared by the triage and RCA agents.

The loop keeps calling the model, executing any requested tools, and feeding
results back until the model calls the designated "terminal" tool (its way of
saying "here is my final structured answer"). That terminal call's input is
returned as-is for the caller to validate against a Pydantic schema.
"""

import json
import logging
from typing import Any, Callable

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

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

    for iteration in range(1, max_iterations + 1):
        logger.info("agent loop iteration=%d/%d model=%s", iteration, max_iterations, model)
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
            logger.info("model returned no tool calls on iteration=%d, nudging to finish", iteration)
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
            logger.info("tool call: %s(%s)", block.name, block.input)
            executor = tool_executors.get(block.name)
            if executor is None:
                logger.error("model requested unknown tool: %s", block.name)
                result = {"error": f"unknown tool {block.name}"}
            else:
                try:
                    result = executor(**block.input)
                except Exception as e:  # noqa: BLE001 - surface to the model, don't crash the run
                    logger.error("tool %s(%s) raised: %s", block.name, block.input, e)
                    result = {"error": str(e)}
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                }
            )

        if terminal_input is not None:
            logger.info("agent called terminal tool %s after %d iteration(s)", terminal_tool_name, iteration)
            return terminal_input

        messages.append({"role": "user", "content": tool_results})

    logger.error("agent did not call %s within %d iterations", terminal_tool_name, max_iterations)
    raise AgentDidNotFinishError(
        f"Agent did not call {terminal_tool_name} within {max_iterations} iterations"
    )
