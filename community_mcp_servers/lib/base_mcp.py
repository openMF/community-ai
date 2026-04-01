import asyncio
import typer
from typing import Callable

from .base_agent import BaseAgent
from .state import RuntimeState
from . import base_commands


__all__ = ["create_mcp_cli"]


def create_mcp_cli(
    service_name: str,
    agent_factory: Callable[[], BaseAgent],
    description: str | None = None,
) -> typer.Typer:
    if description is None:
        description = f"{service_name.title()} MCP Agent CLI"
    
    state = RuntimeState(service_name=service_name)
    agent = agent_factory()
    
    app = typer.Typer(help=description)
    
    @app.command("list-tools")
    def list_tools() -> int:
        return asyncio.run(base_commands.list_tools(state, agent))
    
    @app.command("chat")
    def chat(
        message: str = typer.Argument(..., help="Message to send to the agent."),
        session_id: str = typer.Option("default", help="Chat session identifier."),
    ) -> int:
        return asyncio.run(base_commands.chat(state, agent, message, session_id))
    
    @app.command("chat-loop")
    def chat_loop(
        session_id: str = typer.Option("default", help="Chat session identifier."),
        exit_command: str = typer.Option("/exit", help="Command to end the loop."),
        reset_command: str = typer.Option("/reset", help="Command to reset session."),
        prompt_prefix: str | None = typer.Option(None, help="Custom prompt prefix."),
    ) -> int:
        return asyncio.run(
            base_commands.chat_loop(
                state, agent, session_id, exit_command, reset_command, prompt_prefix
            )
        )
    
    @app.command("tool-info")
    def tool_info(
        tool_identifier: str = typer.Argument(..., help="Tool CLI or original name.")
    ) -> int:
        return asyncio.run(base_commands.tool_info(state, agent, tool_identifier))
    
    @app.command("invoke-tool")
    def invoke_tool(
        tool_identifier: str = typer.Argument(..., help="Tool to invoke."),
        args_json: str = typer.Option("{}", help="JSON arguments for the tool."),
    ) -> int:
        return asyncio.run(
            base_commands.invoke_tool(state, agent, tool_identifier, args_json)
        )
    
    @app.command("sessions")
    def sessions() -> int:
        return asyncio.run(base_commands.sessions(state))
    
    @app.command("clear-session")
    def clear_session(
        session_id: str = typer.Argument(..., help="Session id to clear."),
    ) -> int:
        return asyncio.run(base_commands.clear_session(state, session_id))
    
    @app.command("export-session")
    def export_session(
        session_id: str = typer.Argument(..., help="Session id to export."),
        output_path: str | None = typer.Option(None, "--output", "-o", help="Output path."),
    ) -> int:
        return asyncio.run(
            base_commands.export_session(state, session_id, output_path)
        )
    
    @app.command("health")
    def health() -> int:
        return asyncio.run(base_commands.health(state))
    
    return app
