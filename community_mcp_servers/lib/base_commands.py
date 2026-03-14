import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from .base_agent import BaseAgent, ensure_agent_initialized, stream_agent_response
from .state import RuntimeState
from .utils import (
    extract_message_text,
    sanitize_tool_name,
    _eprint,
)


__all__ = [
    "list_tools",
    "tool_info",
    "invoke_tool",
    "chat",
    "chat_loop",
    "sessions",
    "clear_session",
    "export_session",
    "health",
]


async def list_tools(state: RuntimeState, agent: BaseAgent) -> int:
    """List available MCP tools."""
    await ensure_agent_initialized(state, agent)
    if not state.tool_summaries:
        print("No tools available.")
        return 0

    for tool in state.tool_summaries:
        description = tool.get("description") or "(no description)"
        original_name = tool.get("original_name", "?")
        print(f"- {tool['name']} (original: {original_name}): {description}")
    return 0


async def tool_info(state: RuntimeState, agent: BaseAgent, tool_identifier: str) -> int:
    """Show detailed information about a specific tool."""
    await ensure_agent_initialized(state, agent)
    detail = _find_tool_detail(state, tool_identifier)
    if detail is None:
        _eprint(
            f"Tool '{tool_identifier}' not found. "
            "Run list-tools to see available IDs.",
        )
        return 1

    print(f"CLI name: {detail['name']}")
    print(f"Original name: {detail['original_name']}")
    if detail.get("description"):
        print(f"Description: {detail['description']}")
    metadata = detail.get("metadata") or {}
    if metadata:
        print("Metadata:")
        for key, value in metadata.items():
            print(f"  - {key}: {value}")
    args_schema = detail.get("args_schema")
    if args_schema:
        print("Args schema:", json.dumps(args_schema, indent=2))
    return 0


def _find_tool_detail(
    state: RuntimeState,
    identifier: str,
) -> dict[str, Any] | None:
    """Find tool details by identifier (sanitized or original name)."""
    normalized = sanitize_tool_name(identifier)
    if normalized in state.tool_details:
        return state.tool_details[normalized]
    for detail in state.tool_details.values():
        if detail.get("original_name") == identifier:
            return detail
    return None


async def invoke_tool(
    state: RuntimeState,
    agent: BaseAgent,
    tool_identifier: str,
    args_json: str | None = None,
) -> int:
    """Invoke a tool directly with provided arguments."""
    await ensure_agent_initialized(state, agent)
    detail = _find_tool_detail(state, tool_identifier)
    if detail is None:
        _eprint(
            f"Tool '{tool_identifier}' not found. "
            "Run list-tools to see available IDs.",
        )
        return 1

    tool = state.tool_map.get(detail["name"])
    if tool is None:
        _eprint(f"Tool '{tool_identifier}' is not loaded in the agent.")
        return 1

    arguments: dict[str, Any] = {}
    if args_json:
        try:
            parsed_args = json.loads(args_json)
        except json.JSONDecodeError as exc:
            _eprint(f"Failed to parse args JSON: {exc}")
            return 1
        if not isinstance(parsed_args, dict):
            print(
                "Tool arguments must be provided as a JSON object.",
                file=sys.stderr,
            )
            return 1
        arguments = parsed_args

    result = await tool.ainvoke(arguments)
    if isinstance(result, tuple) and len(result) == 2:
        text_part, artifacts = result
        if text_part:
            print(text_part)
        if artifacts:
            print(
                "Artifacts:",
                json.dumps([repr(a) for a in artifacts], indent=2),
            )
    else:
        print(result)
    return 0


async def chat(
    state: RuntimeState,
    agent: BaseAgent,
    message: str,
    session_id: str = "default",
) -> int:
    """Send a message to the agent and receive a response."""
    await ensure_agent_initialized(state, agent)

    human_message = HumanMessage(content=message)
    session_history = state.record_message(session_id, human_message)

    try:
        last_ai_message = await stream_agent_response(state, session_history)
        state.record_message(session_id, last_ai_message)
        print(extract_message_text(last_ai_message))
        return 0
    except RuntimeError as exc:
        state.pop_last_message(session_id)
        print(str(exc), file=sys.stderr)
        return 1


async def chat_loop(
    state: RuntimeState,
    agent: BaseAgent,
    session_id: str = "default",
    exit_command: str = "/exit",
    reset_command: str = "/reset",
    prompt_prefix: str | None = None,
) -> int:
    """Start an interactive chat session."""
    await ensure_agent_initialized(state, agent)

    normalized_exit = exit_command.strip().lower()
    normalized_reset = reset_command.strip().lower()
    prompt_template = prompt_prefix or f"[{session_id}]> "

    print("Interactive chat started. Type your message and press Enter.")
    print(
        "Use '{exit}' to quit and '{reset}' to clear the session.".format(
            exit=exit_command,
            reset=reset_command,
        )
    )

    loop = asyncio.get_running_loop()

    while True:
        try:
            user_message = await loop.run_in_executor(
                None, input, prompt_template
            )
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat loop.")
            return 0

        if user_message is None:
            continue

        stripped = user_message.strip()
        if not stripped:
            continue

        lowered = stripped.lower()
        if lowered == normalized_exit:
            print("Ending chat loop.")
            return 0

        if lowered == normalized_reset:
            state.clear_session(session_id, persist=True)
            print(f"Session '{session_id}' reset.")
            continue

        human_message = HumanMessage(content=user_message)
        session_history = state.record_message(session_id, human_message)

        try:
            last_ai_message = await stream_agent_response(
                state, session_history
            )
            state.record_message(session_id, last_ai_message)
            print(extract_message_text(last_ai_message))
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            state.pop_last_message(session_id)


async def sessions(state: RuntimeState) -> int:
    """List all active chat sessions."""
    summaries = state.list_sessions()
    if not summaries:
        print("No active sessions.")
        return 0

    print("Active sessions:")
    for info in summaries:
        session_id = info["session_id"]
        count = info.get("message_count", 0)
        updated = info.get("updated_at") or "unknown"
        print(f"- {session_id} ({count} messages, updated {updated})")
    return 0


async def clear_session(state: RuntimeState, session_id: str) -> int:
    """Clear a specific chat session."""
    if session_id in state.chat_sessions:
        state.clear_session(session_id, persist=True)
        print(f"Cleared session '{session_id}'.")
        return 0

    print(f"Session '{session_id}' not found.", file=sys.stderr)
    return 1


async def export_session(
    state: RuntimeState,
    session_id: str,
    output_path: str | None = None,
) -> int:
    """Export a chat session to JSON format."""
    export_payload = state.serialize_session(session_id)
    if export_payload is None:
        print(
            f"Session '{session_id}' not found.",
            file=sys.stderr,
        )
        return 1

    payload_text = json.dumps(export_payload, indent=2, ensure_ascii=False)

    if not output_path:
        print(payload_text)
        return 0

    try:
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload_text + "\n", encoding="utf-8")
    except OSError as exc:
        _eprint(f"Failed to export session: {exc}")
        return 1

    print(f"Session '{session_id}' exported to '{path}'.")
    return 0


async def health(state: RuntimeState) -> int:
    """Show agent health status."""
    status = {
        "agent_initialized": state.agent_executor is not None,
        "tools_available": len(state.tool_summaries),
    }
    if state.agent_executor is None:
        print(
            "Agent not initialized. Run a command that initializes it"
            " (e.g. list-tools)."
        )
    else:
        print("Agent initialized.")
    print(f"Tools available: {status['tools_available']}")
    return 0
