import logging
from fastmcp import FastMCP

# --- 1. Imports from Your Refactored Agents ---
# Ensure these match the function names in your agent files exactly
from MCP_Enhancement.agents.jira_agent import smart_search, get_issue_context, create_issue
from MCP_Enhancement.agents.github_agent import get_repo_overview, get_pr_details, check_ci_status
from MCP_Enhancement.agents.slack_agent import search_messages, get_channel_history, send_slack_message

# --- 2. Import from the New Banking Agent ---
# We will create this file next to satisfy the mentor's request
from MCP_Enhancement.agents.fineract_agent import search_clients, get_loan_details

# Configure unified logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mifos-mcp-server")

# --- 3. Initialize Server ---
mcp = FastMCP(
    "mifos-community-ai",
    description="""
    Mifos Community AI Unified Server.
    - DevOps: Live Jira tickets, GitHub PRs/CI, and Slack context.
    - Banking: Live Fineract Backoffice data (Clients, Loans, Accounts).
    """
)

# --- 4. JIRA TOOLS ---

@mcp.tool(name="jira_search")
def tool_jira_search(query: str) -> str:
    """Find Jira tickets using natural language (e.g. 'high priority bugs')."""
    return smart_search(query)

@mcp.tool(name="jira_context")
def tool_jira_context(issue_key: str) -> str:
    """Get status, description, and recent comments for a Jira ticket."""
    return get_issue_context(issue_key)

# --- 5. GITHUB TOOLS ---

@mcp.tool(name="github_overview")
def tool_github_overview(query: str) -> str:
    """Get a summary of recent PRs and Issues in the repository."""
    return get_repo_overview(query)

@mcp.tool(name="github_ci_status")
def tool_github_ci(pr_number: int = None) -> str:
    """Check if the build/CI is passing for a specific PR or the main branch."""
    return check_ci_status(pr_number)

# --- 6. SLACK TOOLS ---

@mcp.tool(name="slack_search")
def tool_slack_search(query: str) -> str:
    """Search Slack history for specific discussions or mentions."""
    return search_messages(query)

# --- 7. FINERACT / BANKING TOOLS (The Mentor's Request) ---

@mcp.tool(name="fineract_search_clients")
def tool_fineract_search(display_name: str) -> str:
    """Search for banking clients in the Mifos/Fineract sandbox by name."""
    return search_clients(display_name)

@mcp.tool(name="fineract_loan_details")
def tool_fineract_loan(client_id: int) -> str:
    """Fetch loan summary and status for a specific client ID from the sandbox."""
    return get_loan_details(client_id)

if __name__ == "__main__":
    logger.info("🚀 Starting Unified Mifos MCP Server...")
    mcp.run()