import sys
from pathlib import Path

import typer
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from lib.base_mcp import create_mcp_cli
from agents import get_github_agent, get_jira_agent, get_slack_agent


app = typer.Typer(
    help="Community AI MCP Agent - Unified access to GitHub, Slack, and more"
)

app.add_typer(
    create_mcp_cli("github", get_github_agent, "GitHub MCP Agent CLI"),
    name="github",
    help="GitHub MCP Agent - Interact with GitHub repositories",
)

app.add_typer(
    create_mcp_cli("jira", get_jira_agent, "Jira MCP Agent CLI"),
    name="jira",
    help="Jira MCP Agent - Interact with Jira projects",
)

app.add_typer(
    create_mcp_cli("slack", get_slack_agent, "Slack MCP Agent CLI"),
    name="slack",
    help="Slack MCP Agent - Interact with Slack workspaces",
)

if __name__ == "__main__":
    app()
