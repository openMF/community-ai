import os
from typing import Any
from lib.base_agent import BaseAgent
from lib.base_transport import StdioTransportMixin, HttpTransportMixin

__all__ = ["get_slack_agent"]

# All environment variables supported by slack-mcp-server
# See: https://github.com/korotovsky/slack-mcp-server
SLACK_ENV_VARS = [
    # Authentication tokens (one required)
    "SLACK_MCP_XOXP_TOKEN",  # User OAuth token (xoxp-...)
    "SLACK_MCP_XOXB_TOKEN",  # Bot token (xoxb-...) - limited
    "SLACK_MCP_XOXC_TOKEN",  # Browser token (xoxc-...)
    "SLACK_MCP_XOXD_TOKEN",  # Browser cookie d (xoxd-...)
    # Server configuration
    "SLACK_MCP_PORT",  # Port for SSE/HTTP (default: 13080)
    "SLACK_MCP_HOST",  # Host for SSE/HTTP (default: 127.0.0.1)
    "SLACK_MCP_API_KEY",  # Bearer token for SSE/HTTP transports
    # Proxy and network settings
    "SLACK_MCP_PROXY",  # Proxy URL for outgoing requests
    "SLACK_MCP_USER_AGENT",  # Custom User-Agent (Enterprise)
    "SLACK_MCP_CUSTOM_TLS",  # Custom TLS (Enterprise Slack)
    # TLS/SSL settings
    "SLACK_MCP_SERVER_CA",  # Path to CA certificate
    "SLACK_MCP_SERVER_CA_TOOLKIT",  # HTTPToolkit CA
    "SLACK_MCP_SERVER_CA_INSECURE",  # Trust insecure (NOT RECOMMENDED)
    # Message posting settings
    "SLACK_MCP_ADD_MESSAGE_TOOL",  # Enable posting
    "SLACK_MCP_ADD_MESSAGE_MARK",  # Auto-mark as read
    "SLACK_MCP_ADD_MESSAGE_UNFURLING",  # Enable link unfurling
    # Cache configuration
    "SLACK_MCP_USERS_CACHE",  # Path to users cache file
    "SLACK_MCP_CHANNELS_CACHE",  # Path to channels cache
    # Logging
    "SLACK_MCP_LOG_LEVEL",  # debug, info, warn, error
]


def get_slack_agent() -> BaseAgent:
    """Create and return a Slack MCP agent.
    
    Supports three authentication methods:
    1. XOXP token (User OAuth token)
    2. XOXB token (Bot token - limited access, no search)
    3. XOXC + XOXD tokens (Browser tokens - stealth mode)
    
    Transport options:
    - stdio (default): Direct subprocess communication
    - sse: Server-Sent Events over HTTP
    - streamable_http: HTTP transport
    """
    has_xoxp = bool(os.getenv("SLACK_MCP_XOXP_TOKEN"))
    has_xoxb = bool(os.getenv("SLACK_MCP_XOXB_TOKEN"))
    has_xoxc = bool(os.getenv("SLACK_MCP_XOXC_TOKEN"))
    has_xoxd = bool(os.getenv("SLACK_MCP_XOXD_TOKEN"))
    
    # Validate authentication: need xoxp OR xoxb OR (xoxc AND xoxd)
    if not has_xoxp and not has_xoxb and not (has_xoxc and has_xoxd):
        required_vars = [
            "SLACK_MCP_XOXP_TOKEN or SLACK_MCP_XOXB_TOKEN or "
            "(SLACK_MCP_XOXC_TOKEN and SLACK_MCP_XOXD_TOKEN)"
        ]
    else:
        required_vars = []
    
    transport = os.getenv("SLACK_MCP_TRANSPORT", "stdio").lower()
    
    if transport == "stdio":
        return _create_stdio_agent(required_vars)
    elif transport in ("sse", "streamable_http"):
        return _create_http_agent(required_vars, transport)
    else:
        raise ValueError(
            f"Unsupported SLACK_MCP_TRANSPORT: {transport}. "
            f"Use 'stdio', 'sse', or 'streamable_http'"
        )


def _create_stdio_agent(required_vars: list[str]) -> BaseAgent:
    """Create a Slack agent using stdio transport (npx subprocess)."""
    
    class SlackStdioAgent(BaseAgent, StdioTransportMixin):
        def get_connection_config(self) -> dict[str, Any]:
            # Build environment with all supported Slack MCP variables
            env: dict[str, str] = {
                "PATH": os.environ.get("PATH", ""),
            }
            
            # Forward all configured Slack environment variables
            for var in SLACK_ENV_VARS:
                value = os.getenv(var)
                if value:
                    env[var] = value
            
            # Use npx with -y flag to auto-confirm install
            return self.build_stdio_config(
                "npx",
                ["-y", "slack-mcp-server@latest", "--transport", "stdio"],
                env
            )
    
    return SlackStdioAgent(
        service_name="slack", required_env_vars=required_vars
    )


def _create_http_agent(required_vars: list[str], transport: str) -> BaseAgent:
    """Create a Slack agent using SSE or HTTP transport.
    
    Requires SLACK_MCP_SERVER_URL to be set, pointing to a running
    slack-mcp-server instance (e.g., http://127.0.0.1:13080/sse).
    
    Optionally use SLACK_MCP_API_KEY for authentication.
    """
    
    class SlackHttpAgent(BaseAgent, HttpTransportMixin):
        def __init__(self, transport_type: str, **kwargs):
            super().__init__(**kwargs)
            self.transport_type = transport_type
        
        def get_connection_config(self) -> dict[str, Any]:
            # Get server URL from environment or use default
            host = os.getenv("SLACK_MCP_HOST", "127.0.0.1")
            port = os.getenv("SLACK_MCP_PORT", "13080")
            default_url = f"http://{host}:{port}/sse"
            
            return self.build_http_config(
                "slack", default_url, self.transport_type
            )
    
    return SlackHttpAgent(
        transport_type=transport,
        service_name="slack",
        required_env_vars=required_vars,
    )
