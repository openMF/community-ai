import logging
from typing import Optional, List, Dict, Any
from jira import JIRA, JIRAError

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Robust import to handle running from different directories
try:
    from MCP_Enhancement.src.core.config import get_settings
except ImportError:
    from MCP_Enhancement.config import get_settings

logger = logging.getLogger(__name__)

# --- Reusable Prompts ---

JQL_GENERATION_PROMPT = ChatPromptTemplate.from_template(
    """You are an expert in Jira Query Language (JQL). Convert the user's request into a valid JQL query.
Return ONLY the JQL string.

Rules:
1. Quoting: Enclose values with spaces in single quotes (e.g., assignee = 'Aru Sharma').
2. Search: Use ~ for text searches (e.g., summary ~ 'login').
3. Ordering: Always order by created DESC unless specified otherwise.

User Request: "{user_query}"
JQL Query:"""
)

SUMMARIZATION_PROMPT = ChatPromptTemplate.from_template(
    """The user asked: "{user_query}"

I retrieved the following live data from Jira:
{raw_data}

Provide a clear, concise, and helpful summary.
- If it's a list of tickets, mention the Keys, Summaries, and Assignees.
- If it's a specific ticket, summarize the status and the most recent discussion (comments).
"""
)


# --- Helper Logic ---

def get_jira_client() -> JIRA:
    """
    Initializes the JIRA client using credentials from .env
    """
    settings = get_settings()
    return JIRA(
        server=settings.JIRA_URL,
        basic_auth=(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN.get_secret_value())
    )


def get_llm():
    """Initializes the LLM from central config"""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY.get_secret_value(),
        temperature=0
    )


def _format_issues(issues) -> str:
    """Helper to format a list of Jira issues into a readable string."""
    if not issues:
        return "No issues found."

    formatted = []
    for issue in issues:
        assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
        status = issue.fields.status.name
        formatted.append(f"[{issue.key}] {issue.fields.summary} (Status: {status}, Assignee: {assignee})")
    return "\n".join(formatted)


# --- Primary Tools for MCP ---

def smart_search(query: str) -> str:
    """
    Translates natural language to JQL, executes it, and summarizes the result.
    This is the core 'Live' replacement for RAG.
    """
    logger.info(f"Executing smart_search for: {query}")
    jira = get_jira_client()
    llm = get_llm()

    try:
        # 1. Generate JQL
        jql_chain = JQL_GENERATION_PROMPT | llm
        generated_jql = jql_chain.invoke({"user_query": query}).content.strip().strip("'\"")
        logger.info(f"Generated JQL: {generated_jql}")

        # 2. Fetch Live Data
        # maxResults=5 prevents overloading the context window
        issues = jira.search_issues(generated_jql, maxResults=5)

        if not issues:
            return "The search returned no matching issues in Jira."

        formatted_data = _format_issues(issues)

        # 3. Summarize
        summary_chain = SUMMARIZATION_PROMPT | llm
        return summary_chain.invoke({
            "user_query": query,
            "raw_data": formatted_data
        }).content

    except JIRAError as e:
        logger.error(f"Jira API error: {e.text}")
        return f"Jira Error: {e.text}"
    except Exception as e:
        logger.error(f"Smart search failed: {e}")
        return f"An error occurred while searching: {str(e)}"


def get_issue_context(issue_key: str) -> str:
    """
    Fetches the full details of a specific ticket, including the description and
    the 5 most recent comments to understand the context.
    """
    jira = get_jira_client()
    try:
        issue = jira.issue(issue_key)

        # Extract Comments (Crucial for context)
        comments = issue.fields.comment.comments
        recent_comments = []
        for c in comments[-5:]:  # Last 5 comments
            recent_comments.append(f"- {c.author.displayName}: {c.body}")

        comment_text = "\n".join(recent_comments) if recent_comments else "No comments."

        # Construct raw data context
        context_data = (
            f"Ticket: {issue.key}\n"
            f"Summary: {issue.fields.summary}\n"
            f"Status: {issue.fields.status.name}\n"
            f"Assignee: {issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'}\n"
            f"Description: {issue.fields.description}\n"
            f"--- Recent Comments ---\n{comment_text}"
        )

        return context_data

    except JIRAError as e:
        if e.status_code == 404:
            return f"Issue {issue_key} not found."
        return f"Jira API Error: {e.text}"
    except Exception as e:
        return f"Error fetching issue {issue_key}: {str(e)}"


def create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task",
                 priority: str = "Medium") -> str:
    """
    Creates a new issue in Jira.
    """
    jira = get_jira_client()
    try:
        issue_dict = {
            'project': {'key': project_key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': issue_type},
            # Note: Priority implementation varies by Jira instance, removing it for safety
            # unless you are sure of your specific Priority ID/Names.
            # 'priority': {'name': priority}
        }

        new_issue = jira.create_issue(fields=issue_dict)
        return f"Successfully created issue {new_issue.key}: {new_issue.permalink()}"

    except JIRAError as e:
        logger.error(f"Failed to create issue: {e.text}")
        return f"Failed to create issue: {e.text}"
    except Exception as e:
        return f"Error creating issue: {str(e)}"