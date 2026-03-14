import json
import os
import sys
import re
from typing import Any, Callable

from langchain_core.messages import BaseMessage

__all__ = [
    "sanitize_tool_name",
    "truthy",
    "load_json_env",
    "build_connection_config",
    "schema_from_model",
    "extract_message_text",
    "_eprint",
]


def sanitize_tool_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", name.lower()).strip("_")


def truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def load_json_env(
    env_name: str, *, value_validator: Callable[[Any], Any] | None = None
) -> dict[str, str]:
    raw = os.getenv(env_name)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Environment variable {env_name} must contain valid JSON."
        ) from exc
    if not isinstance(parsed, dict):
        raise ValueError(
            (
                f"Environment variable {env_name} must be a JSON object "
                "with string keys."
            )
        )
    if value_validator is None:
        return {str(k): str(v) for k, v in parsed.items()}
    validated: dict[str, str] = {}
    for key, value in parsed.items():
        validated[str(key)] = str(value_validator(value))
    return validated


def build_connection_config(
    service_name: str = "github",
    server_url_env: str = "GITHUB_MCP_SERVER_URL",
    default_server_url: str = "https://api.githubcopilot.com/mcp/",
    token_env: str = "GITHUB_PERSONAL_ACCESS_TOKEN",
    bearer_token_env: str | None = "GITHUB_MCP_BEARER_TOKEN",
) -> dict[str, Any]:
    """
    Build connection configuration for MCP services.
    
    Args:
        service_name: Name of the service (for logging/display)
        server_url_env: Environment variable name for server URL
        default_server_url: Default server URL if not specified
        token_env: Primary token environment variable name
        bearer_token_env: Optional bearer token environment variable name
    """
    server_url = os.getenv(server_url_env, default_server_url).strip()
    if not server_url:
        raise ValueError(f"{server_url_env} cannot be empty.")

    # Check for readonly path configuration
    readonly_path_env = f"{service_name.upper()}_MCP_USE_READONLY_PATH"
    if truthy(os.getenv(readonly_path_env)) and not server_url.endswith("/readonly"):
        server_url = server_url.rstrip("/") + "/readonly"

    transport_env = f"{service_name.upper()}_MCP_TRANSPORT"
    transport = (
        os.getenv(transport_env, "streamable_http").strip().lower()
    )
    if transport not in {"streamable_http", "sse"}:
        raise ValueError(
            f"Unsupported {transport_env}. Use 'streamable_http' or 'sse'."
        )

    headers: dict[str, str] = {}
    auth_token = os.getenv(bearer_token_env) if bearer_token_env else None
    if not auth_token:
        auth_token = os.getenv(token_env)
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    # Check for toolsets configuration
    toolsets_env = f"{service_name.upper()}_MCP_TOOLSETS"
    toolsets = os.getenv(toolsets_env)
    if toolsets:
        headers["X-MCP-Toolsets"] = toolsets.strip()

    # Check for readonly flag
    readonly_env = f"{service_name.upper()}_MCP_READONLY"
    if truthy(os.getenv(readonly_env)):
        headers["X-MCP-Readonly"] = "true"

    # Check for user agent
    user_agent_env = f"{service_name.upper()}_MCP_USER_AGENT"
    user_agent = os.getenv(user_agent_env)
    if user_agent:
        headers["User-Agent"] = user_agent.strip()

    # Check for extra headers
    extra_headers_env = f"{service_name.upper()}_MCP_EXTRA_HEADERS"
    headers.update(load_json_env(extra_headers_env))

    connection: dict[str, Any] = {"url": server_url, "transport": transport}
    if headers:
        connection["headers"] = headers

    timeout_env = f"{service_name.upper()}_MCP_TIMEOUT_SECONDS"
    timeout = os.getenv(timeout_env)
    if timeout:
        try:
            timeout_value = float(timeout)
        except ValueError as exc:
            raise ValueError(
                f"{timeout_env} must be a positive number"
            ) from exc
        if timeout_value <= 0:
            raise ValueError(
                f"{timeout_env} must be greater than zero"
            )
        connection["timeout"] = timeout_value

    return connection


def schema_from_model(model: Any) -> dict[str, Any] | None:
    if model is None:
        return None
    for attr in ("model_json_schema", "schema"):
        schema_fn = getattr(model, attr, None)
        if callable(schema_fn):
            schema = schema_fn()
            if isinstance(schema, dict):
                return schema
    return None


def extract_message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_chunks = [
            c.get("text", "")
            for c in content
            if isinstance(c, dict) and c.get("type") == "text"
        ]
        if text_chunks:
            return "\n".join(text_chunks)
    return str(content)


def _eprint(
    *args: object,
    sep: str | None = None,
    end: str | None = None,
    flush: bool = False,
) -> None:

    print(*args, file=sys.stderr, sep=sep, end=end, flush=flush)
