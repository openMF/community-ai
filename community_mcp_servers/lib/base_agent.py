import os
from typing import Any, cast

from langchain_core.messages import AIMessage, BaseMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from .state import RuntimeState
from .utils import (
    build_connection_config,
    sanitize_tool_name,
    schema_from_model,
)


__all__ = [
    "BaseAgent",
    "initialize_agent",
    "ensure_agent_initialized",
    "stream_agent_response",
]


def _get_llm_provider():
    from llm_providers import gemini
    from llm_providers import lightning_llm
    from llm_providers import groq_llm

    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "lightning":
        return lightning_llm.get_llm
    elif provider == "groq":
        return groq_llm.get_llm
    elif provider == "gemini":
        return gemini.get_llm
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {provider}. "
            f"Supported values: 'lightning', 'groq', 'gemini'"
        )


class BaseAgent:
    """Base class for MCP agents providing common functionality."""

    def __init__(
        self,
        service_name: str,
        required_env_vars: list[str] | None = None,
        server_url_env: str | None = None,
        default_server_url: str | None = None,
        token_env: str | None = None,
        bearer_token_env: str | None = None,
    ):
        """Initialize base agent with service-specific configuration.
        
        Args:
            service_name: Name of the service (e.g., "github", "jira", "slack")
            required_env_vars: List of required environment variables
            server_url_env: Environment variable name for server URL
            default_server_url: Default server URL if not specified
            token_env: Primary token environment variable name
            bearer_token_env: Optional bearer token environment variable name
        """
        self.service_name = service_name
        self.required_env_vars = required_env_vars or []
        self.server_url_env = server_url_env
        self.default_server_url = default_server_url
        self.token_env = token_env
        self.bearer_token_env = bearer_token_env

    def validate_environment(self) -> None:
        """Validate required environment variables."""
        missing_vars: list[str] = []
        for var in self.required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            missing_str = ", ".join(sorted(set(missing_vars)))
            raise ValueError(
                "Missing required environment variables: " + missing_str
            )

    def get_connection_config(self) -> dict[str, Any]:
        """Get the connection configuration for this service."""
        return build_connection_config(
            service_name=self.service_name,
            server_url_env=self.server_url_env or f"{self.service_name.upper()}_MCP_SERVER_URL",
            default_server_url=self.default_server_url or f"https://api.{self.service_name}.com/mcp/",
            token_env=self.token_env or f"{self.service_name.upper()}_PERSONAL_ACCESS_TOKEN",
            bearer_token_env=self.bearer_token_env,
        )
    
    async def initialize(self, state: RuntimeState) -> None:
        """Initialize the agent with MCP client and tools."""
        self.validate_environment()
        
        connection = self.get_connection_config()
        state.mcp_client = MultiServerMCPClient({self.service_name: connection})
        
        client = state.mcp_client
        if client is None:
            raise RuntimeError("Failed to initialize MCP client.")
        
        # Get tools from MCP client
        tools = await client.get_tools()
        
        state.tool_summaries = []
        state.tool_map = {}
        state.tool_details = {}
        
        for tool in tools:
            original_name = tool.name
            sanitized_name = sanitize_tool_name(original_name)
            
            args_schema = schema_from_model(getattr(tool, "args_schema", None))
            metadata = getattr(tool, "metadata", {}) or {}
            
            state.tool_map[sanitized_name] = tool
            state.tool_details[sanitized_name] = {
                "name": sanitized_name,
                "original_name": original_name,
                "description": getattr(tool, "description", ""),
                "metadata": metadata,
                "args_schema": args_schema,
            }
            state.tool_summaries.append(
                {
                    "name": sanitized_name,
                    "original_name": original_name,
                    "description": getattr(tool, "description", ""),
                }
            )
        
        # Get LLM and create agent with tools
        get_llm = _get_llm_provider()
        llm = get_llm()
        
        # Create React agent with model and tools
        state.agent_executor = create_react_agent(llm, tools)


async def initialize_agent(
    state: RuntimeState,
    agent: BaseAgent,
) -> None:
    """Async Initialize an agent using the base agent class."""
    await agent.initialize(state)


async def ensure_agent_initialized(
    state: RuntimeState,
    agent: BaseAgent,
) -> None:
    """Ensure agent is initialized, initializing if necessary."""
    if state.agent_executor is None or state.mcp_client is None:
        await initialize_agent(state, agent)
    if state.agent_executor is None or state.mcp_client is None:
        raise RuntimeError("Agent failed to initialize")


async def stream_agent_response(
    state: RuntimeState,
    session_history: list[BaseMessage],
) -> AIMessage:
    """Stream agent response for a given session history."""
    if state.agent_executor is None:
        raise RuntimeError("Agent executor is not initialized.")
    
    executor = cast(Any, state.agent_executor)
    
    # Use ainvoke for async execution with the agent
    result = await executor.ainvoke({"messages": session_history})
    
    # Extract the last AI message from the result
    messages = result.get("messages", [])
    last_ai_message: AIMessage | None = None
    
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            last_ai_message = message
            break
    
    if last_ai_message is None:
        raise RuntimeError("The agent did not return a response.")
    return last_ai_message
