import os
from lib.base_agent import BaseAgent

__all__ = ["get_github_agent"]


def get_github_agent() -> BaseAgent:
    if not (
        os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        or os.getenv("GITHUB_MCP_BEARER_TOKEN")
    ):
        required_vars = [
            "GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_MCP_BEARER_TOKEN"
        ]
    else:
        required_vars = []
    
    return BaseAgent(
        service_name="github",
        required_env_vars=required_vars,
        server_url_env="GITHUB_MCP_SERVER_URL",
        default_server_url="https://api.githubcopilot.com/mcp/",
        token_env="GITHUB_PERSONAL_ACCESS_TOKEN",
        bearer_token_env="GITHUB_MCP_BEARER_TOKEN",
    )
