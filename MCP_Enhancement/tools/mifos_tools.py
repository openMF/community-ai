import logging
from typing import Optional, List, Dict, Any

# --- 3rd Party Clients ---
from jira import JIRA, JIRAError
from github import Github
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from fastmcp import FastMCP  # ✅ KEY ADDITION

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

logger = logging.getLogger(__name__)

# =========================================================
# 1. INITIALIZE FASTMCP SERVER
# =========================================================
# This object is imported by agent_start.py to run the server
mcp = FastMCP("Mifos Unified Tools")


# =========================================================
# 2. CONFIGURATION & CLIENT INITIALIZERS
# =========================================================

def get_settings():
    """Import settings from central config (robust path resolution)."""
    try:
        from MCP_Enhancement.src.core.config import get_settings
        return get_settings()
    except ImportError:
        try:
            from MCP_Enhancement.config import get_settings
            return get_settings()
        except ImportError:
            # Fallback for when running from root as module
            from MCP_Enhancement.config import get_settings
            return get_settings()


def _get_jira_client() -> JIRA:
    s = get_settings()
    return JIRA(
        server=s.JIRA_URL,
        basic_auth=(s.JIRA_EMAIL, s.JIRA_API_TOKEN.get_secret_value())
    )


def _get_github_client() -> Github:
    s = get_settings()
    return Github(s.GITHUB_TOKEN.get_secret_value())


def _get_slack_client() -> WebClient:
    s = get_settings()
    return WebClient(token=s.SLACK_BOT_TOKEN.get_secret_value())


def _get_llm() -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=s.OPENAI_MODEL,
        api_key=s.OPENAI_API_KEY.get_secret_value(),
        temperature=0
    )


# =========================================================
# 3. PROMPTS
# =========================================================

GITHUB_SUMMARY_PROMPT = ChatPromptTemplate.from_template(
    """You are a senior technical lead reviewing repository activity.

Repository: {repo_name}

GitHub Data:
{raw_data}

User Question:
{user_query}

Instructions:
- Highlight failing CI or blocked PRs.
- Mention authors and PR numbers.
- If all is healthy, say so clearly.
"""
)

JQL_GENERATION_PROMPT = ChatPromptTemplate.from_template(
    """Convert the request into valid JQL.

Rules:
- Use ~ for text search
- Quote values with spaces
- Always ORDER BY created DESC

User Request:
{user_query}

JQL:
"""
)

SUMMARIZATION_PROMPT = ChatPromptTemplate.from_template(
    """Summarize the Jira results.

User Request:
{user_query}

Raw Data:
{raw_data}

Instructions:
- List key, summary, assignee
- Summarize recent discussion
- Suggest alternatives if empty
"""
)

SLACK_SUMMARY_PROMPT = PromptTemplate.from_template(
    """Summarize Slack discussions.

Raw Messages:
{raw_data}

User Question:
{user_query}

Mention usernames explicitly.
"""
)


# =========================================================
# 4. RAW LOGIC FUNCTIONS (Internal Use)
# =========================================================
# These are normal Python functions. Your Watchdog script calls THESE.

def smart_search(query: str) -> str:
    """Searches Jira using natural language converted to JQL."""
    jira = _get_jira_client()
    llm = _get_llm()
    try:
        jql = (JQL_GENERATION_PROMPT | llm).invoke(
            {"user_query": query}
        ).content.strip().strip("'\"")

        issues = jira.search_issues(jql, maxResults=5)
        if not issues:
            return "No issues found."

        formatted = "\n".join(
            f"[{i.key}] {i.fields.summary} ({i.fields.status.name})"
            for i in issues
        )
        return (SUMMARIZATION_PROMPT | llm).invoke(
            {"user_query": query, "raw_data": formatted}
        ).content

    except Exception as e:
        return f"Jira Search Error: {e}"


def create_issue_logic(project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
    """Creates a Jira ticket."""
    jira = _get_jira_client()
    try:
        issue = jira.create_issue(fields={
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        })
        return f"Created {issue.key}: {issue.permalink()}"
    except Exception as e:
        return f"Failed to create issue: {e}"


def get_issue_context(issue_key: str) -> str:
    """Fetches details for a specific Jira ticket."""
    jira = _get_jira_client()
    try:
        issue = jira.issue(issue_key)
        comments = issue.fields.comment.comments[-5:]
        comment_text = "\n".join(
            f"- {c.author.displayName}: {c.body}" for c in comments
        ) or "No comments."

        return (
            f"Ticket: {issue.key}\n"
            f"Summary: {issue.fields.summary}\n"
            f"Status: {issue.fields.status.name}\n"
            f"Assignee: {issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'}\n"
            f"Description: {issue.fields.description}\n"
            f"--- Recent Comments ---\n{comment_text}"
        )

    except JIRAError as e:
        return f"Jira API Error: {e.text}"
    except Exception as e:
        return f"Error fetching issue {issue_key}: {e}"


def get_pr_details(pr_number: int) -> str:
    """Fetches GitHub PR metadata."""
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        pr = repo.get_pull(pr_number)
        files = [f.filename for f in pr.get_files()][:10]
        return f"PR #{pr.number}: {pr.title}\nFiles: {', '.join(files)}"
    except Exception as e:
        return f"PR #{pr_number} not found: {e}"


def check_ci_status(pr_number: Optional[int] = None) -> str:
    """Checks GitHub CI status."""
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        if pr_number:
            sha = repo.get_pull(pr_number).head.sha
        else:
            sha = repo.get_branch(repo.default_branch).commit.sha

        status = repo.get_commit(sha).get_combined_status()
        return f"CI Status: {status.state.upper()} ({sha[:7]})"
    except Exception as e:
        return f"CI Check Error: {e}"


def search_knowledge_base(query: str) -> str:
    """Queries the Pinecone RAG system."""
    try:
        # Import inside function to avoid circular imports
        from MCP_Enhancement.agents.rag_agent import query_docs
        answer = query_docs(query)
        if not answer:
            return f"No documentation found for '{query}'."
        return answer
    except Exception as e:
        logger.error(f"RAG Error: {e}")
        return "Knowledge base unavailable."


# =========================================================
# 5. MCP TOOL WRAPPERS (External Use)
# =========================================================
# These are wrapped in @mcp.tool. The AI uses THESE.

@mcp.tool
def tool_jira_context(ticket_key: str):
    """Fetches full Jira ticket details and recent comments."""
    return get_issue_context(ticket_key)


@mcp.tool
def tool_ask_mifos_docs(query: str):
    """Queries the Mifos/Fineract Phase 4 RAG for documentation standards."""
    return search_knowledge_base(query)


@mcp.tool
def tool_github_details(pr_number: int):
    """Fetches PR metadata and changed files for audit."""
    return get_pr_details(pr_number)


@mcp.tool
def tool_ci_check(pr_number: int):
    """Checks if the build/tests are passing for a specific PR."""
    return check_ci_status(pr_number)


@mcp.tool
def tool_smart_search_jira(query: str):
    """Smart search for Jira tickets using natural language."""
    return smart_search(query)
