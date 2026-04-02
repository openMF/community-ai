import os
from typing import Any
from lib.base_agent import BaseAgent
from lib.base_transport import StdioTransportMixin, HttpTransportMixin

__all__ = ["get_jira_agent"]

# Environment variables for Jira MCP (mcp-atlassian package)
# See: https://github.com/sooperset/mcp-atlassian
# Configured for Jira-only usage (no Confluence)
JIRA_ENV_VARS = [
    # Connection settings
    "JIRA_URL",  # Jira instance URL
    # Cloud authentication (API Token)
    "JIRA_USERNAME",  # Email for Cloud
    "JIRA_API_TOKEN",  # API token from id.atlassian.com
    # Server/Data Center authentication (PAT)
    "JIRA_PERSONAL_TOKEN",  # Personal Access Token
    # SSL and proxy settings
    "JIRA_SSL_VERIFY",  # SSL verification (true/false)
    "HTTP_PROXY",  # HTTP proxy URL
    "HTTPS_PROXY",  # HTTPS proxy URL
    "JIRA_HTTPS_PROXY",  # Jira-specific HTTPS proxy
    "NO_PROXY",  # Hosts to bypass proxy
    "SOCKS_PROXY",  # SOCKS proxy URL
    # Custom headers (for corporate environments)
    "JIRA_CUSTOM_HEADERS",  # Format: key=value,key2=value2
    # Filtering and access control
    "JIRA_PROJECTS_FILTER",  # Limit to specific projects
    "ENABLED_TOOLS",  # Enable specific tools only
    "READ_ONLY_MODE",  # Disable write operations
    # Server options
    "TRANSPORT",  # Transport type for the server
    "PORT",  # Port for HTTP transports (default: 8000)
    "HOST",  # Host for HTTP transports (default: 0.0.0.0)
    "STATELESS",  # Enable stateless mode
    # Logging
    "MCP_VERBOSE",  # Enable verbose logging
    "MCP_VERY_VERBOSE",  # Enable debug logging
    "MCP_LOGGING_STDOUT",  # Log to stdout instead of stderr
]


def get_jira_agent() -> BaseAgent:
    """Create and return a Jira MCP agent.
    
    Uses mcp-atlassian package via uvx (Python).
    Configured for Jira-only access (no Confluence).
    
    Supports two authentication methods:
    1. API Token (Cloud): JIRA_USERNAME + JIRA_API_TOKEN
    2. Personal Access Token (Server/DC): JIRA_PERSONAL_TOKEN
    
    Transport options:
    - stdio (default): Direct subprocess communication
    - sse: Server-Sent Events over HTTP
    - streamable_http: HTTP transport
    """
    has_url = bool(os.getenv("JIRA_URL"))
    has_api_token = bool(
        os.getenv("JIRA_USERNAME") and os.getenv("JIRA_API_TOKEN")
    )
    has_pat = bool(os.getenv("JIRA_PERSONAL_TOKEN"))
    
    # Build list of missing required variables
    required_vars = []
    if not has_url:
        required_vars.append("JIRA_URL")
    if not has_api_token and not has_pat:
        required_vars.append(
            "(JIRA_USERNAME and JIRA_API_TOKEN) or JIRA_PERSONAL_TOKEN"
        )
    
    transport = os.getenv("JIRA_MCP_TRANSPORT", "stdio").lower()
    
    if transport == "stdio":
        return _create_stdio_agent(required_vars)
    elif transport in ("sse", "streamable_http"):
        return _create_http_agent(required_vars, transport)
    else:
        raise ValueError(
            f"Unsupported JIRA_MCP_TRANSPORT: {transport}. "
            f"Use 'stdio', 'sse', or 'streamable_http'"
        )


def _create_stdio_agent(required_vars: list[str]) -> BaseAgent:
    """Create a Jira agent using stdio transport (uvx subprocess)."""
    
    class JiraStdioAgent(BaseAgent, StdioTransportMixin):
        def get_connection_config(self) -> dict[str, Any]:
            use_docker = os.getenv("JIRA_MCP_USE_DOCKER", "").lower()
            if use_docker in ("true", "1", "yes"):
                return self._get_docker_config()
            return self._get_uvx_config()
        
        def _get_docker_config(self) -> dict[str, Any]:
            """Build Docker configuration for mcp-atlassian."""
            docker_args = ["run", "-i", "--rm"]
            
            # Forward all configured Jira environment variables
            for var in JIRA_ENV_VARS:
                if os.getenv(var):
                    docker_args.extend(["-e", var])
            
            image = os.getenv(
                "JIRA_MCP_DOCKER_IMAGE",
                "ghcr.io/sooperset/mcp-atlassian:latest",
            )
            docker_args.append(image)
            
            # Build env dict for subprocess
            env = {var: os.getenv(var, "") for var in JIRA_ENV_VARS}
            env["PATH"] = os.environ.get("PATH", "")
            
            return self.build_stdio_config("docker", docker_args, env)
        
        def _get_uvx_config(self) -> dict[str, Any]:
            """Build uvx configuration for mcp-atlassian.
            
            Uses uvx (Python package runner) instead of npx.
            Official usage: uvx mcp-atlassian
            """
            # Build environment with all Jira variables
            env: dict[str, str] = {
                "PATH": os.environ.get("PATH", ""),
            }
            
            # Forward all configured Jira environment variables
            for var in JIRA_ENV_VARS:
                value = os.getenv(var)
                if value:
                    env[var] = value
            
            # Use uvx to run mcp-atlassian
            # Note: Use --python=3.12 if Python 3.14+ causes issues
            return self.build_stdio_config(
                "uvx",
                ["mcp-atlassian"],
                env
            )
    
    return JiraStdioAgent(
        service_name="jira", required_env_vars=required_vars
    )


def _create_http_agent(required_vars: list[str], transport: str) -> BaseAgent:
    """Create a Jira agent using SSE or HTTP transport.
    
    Requires a running mcp-atlassian server.
    Default: http://127.0.0.1:8000
    """
    
    class JiraHttpAgent(BaseAgent, HttpTransportMixin):
        def __init__(self, transport_type: str, **kwargs):
            super().__init__(**kwargs)
            self.transport_type = transport_type
        
        def get_connection_config(self) -> dict[str, Any]:
            # Get server URL from environment or use default
            host = os.getenv("HOST", "127.0.0.1")
            port = os.getenv("PORT", "8000")
            default_url = f"http://{host}:{port}/sse"
            
            return self.build_http_config(
                "jira", default_url, self.transport_type
            )
    
    return JiraHttpAgent(
        transport_type=transport,
        service_name="jira",
        required_env_vars=required_vars,
    )
