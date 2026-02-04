import logging
import os
from typing import Optional, List, Dict, Any

# --- 3rd Party Clients ---
from jira import JIRA, JIRAError
from github import Github, GithubException
from slack_sdk import WebClient  # <--- Added missing import
from slack_sdk.errors import SlackApiError # <--- Added missing import
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

# Setup Logging
logger = logging.getLogger(__name__)

# --- Configuration & Client Initializers ---

def get_settings():
    """Import settings from your central config"""
    try:
        from MCP_Enhancement.src.core.config import get_settings
        return get_settings()
    except ImportError:
        # Fallback for localized testing
        try:
            from config import get_settings
            return get_settings()
        except ImportError:
            from MCP_Enhancement.config import get_settings
            return get_settings()

def _get_jira_client() -> JIRA:
    s = get_settings()
    return JIRA(server=s.JIRA_URL, basic_auth=(s.JIRA_USERNAME, s.JIRA_API_TOKEN.get_secret_value()))

def _get_github_client() -> Github:
    s = get_settings()
    return Github(s.GITHUB_TOKEN.get_secret_value())

def _get_slack_client() -> WebClient:
    s = get_settings()
    return WebClient(token=s.SLACK_BOT_TOKEN.get_secret_value())

def _get_llm():
    s = get_settings()
    return ChatOpenAI(model=s.OPENAI_MODEL, api_key=s.OPENAI_API_KEY.get_secret_value(), temperature=0)


# --- Prompts ---

# 1. GitHub Activity Summary
GITHUB_SUMMARY_PROMPT = ChatPromptTemplate.from_template(
    """You are a senior technical lead. The user is asking about activity in: "{repo_name}".

Live GitHub Data:
{raw_data}

User Question: "{user_query}"

Provide a professional, clear summary. 
- Prioritize "failing" CI statuses or "blocked" PRs.
- Explicitly mention specific authors and PR numbers.
- If everything looks good, state that the repository health is stable.
"""
)

# 2. Natural Language to JQL (Strict Output)
JQL_GENERATION_PROMPT = ChatPromptTemplate.from_template(
    """You are an expert in Jira Query Language (JQL). Convert the user's request into a valid JQL query.
Return ONLY the JQL string. Do not include markdown code blocks or explanations.

Rules:
1. Quoting: Enclose values with spaces in single quotes (e.g., assignee = 'Aru Sharma').
2. Search: Use ~ for text searches (e.g., summary ~ 'login').
3. Ordering: Always order by created DESC unless specified otherwise.

User Request: "{user_query}"
JQL Query:"""
)

# 3. Jira Data Summarization
SUMMARIZATION_PROMPT = ChatPromptTemplate.from_template(
    """You are a project management assistant. 
The user asked: "{user_query}"

Live Data from Jira:
{raw_data}

Provide a clear, concise, and helpful summary:
- For lists: Mention Keys, Summaries, and Assignees.
- For specific tickets: Summarize the current status and the sentiment/content of recent comments.
- If no data is found, suggest what keywords the user might try instead.
"""
)

# SLACK
SLACK_SUMMARY_PROMPT = PromptTemplate.from_template(
    """The user is asking for information based on Slack conversations.
    Raw message data: {raw_data}
    User Question: "{user_query}"
    Provide a concise summary. Mention usernames so the user knows the source of truth."""
)

# KNOWLEDGE SYNTHESIS (The Librarian)
MIFOS_DOC_PROMPT = PromptTemplate.from_template(
    """You are the Mifos Technical Librarian. Your task is to produce professional documentation 
    based on combined data from GitHub, Jira, and Slack.

    Source Context: {context_data}
    Target Project: Mifos (Non-Apache Fineract context)

    Create a 'Technical Release Note' that summarizes:
    1. The core functional change.
    2. The consensus reached in the discussion/comments.
    3. The expected impact on the Mifos Web-App/Mobile UI.

    Format as a clean markdown summary."""
)


# --- 1. JIRA TOOLS ---

def smart_search(query: str) -> str:
    """Translates natural language to JQL, searches Jira, and summarizes results."""
    jira = _get_jira_client()
    llm = _get_llm()
    try:
        jql = (JQL_GENERATION_PROMPT | llm).invoke({"user_query": query}).content.strip().strip("'\"")
        issues = jira.search_issues(jql, maxResults=5)
        if not issues: return "No issues found."

        formatted = "\n".join([f"[{i.key}] {i.fields.summary} ({i.fields.status.name})" for i in issues])
        return (SUMMARIZATION_PROMPT | llm).invoke({"user_query": query, "raw_data": formatted}).content
    except Exception as e:
        return f"Jira Search Error: {str(e)}"

def create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
    """Creates a new Jira issue."""
    jira = _get_jira_client()
    try:
        issue = jira.create_issue(
            fields={'project': {'key': project_key}, 'summary': summary, 'description': description,
                    'issuetype': {'name': issue_type}})
        return f"Created {issue.key}: {issue.permalink()}"
    except Exception as e:
        return f"Failed to create issue: {str(e)}"

def get_issue_context(issue_key: str) -> str:
    """
    Fetches the full details of a specific ticket, including the description and
    the 5 most recent comments to understand the context.
    """
    jira = _get_jira_client()
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


# --- 2. GITHUB TOOLS ---

def get_repo_overview(query: str) -> str:
    """Summarizes recent open PRs and Issues in the repository."""
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        prs = repo.get_pulls(state='open')[:5]
        issues = repo.get_issues(state='open')[:5]

        raw_data = f"PRs: {[p.title for p in prs]}\nIssues: {[i.title for i in issues]}"
        return (_get_llm() | GITHUB_SUMMARY_PROMPT).invoke(
            {"repo_name": repo.full_name, "raw_data": raw_data, "user_query": query}).content
    except Exception as e:
        return f"GitHub Error: {str(e)}"

def get_pr_details(pr_number: int) -> str:
    """Fetches deep context for a specific PR and files changed."""
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        pr = repo.get_pull(pr_number)
        files = [f.filename for f in pr.get_files()][:10]
        return f"PR #{pr.number}: {pr.title}\nBody: {pr.body}\nFiles: {', '.join(files)}"
    except Exception as e:
        return f"PR #{pr_number} not found: {str(e)}"

def check_ci_status(pr_number: Optional[int] = None) -> str:
    """Checks the CI/Build status for a PR or the main branch."""
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        sha = repo.get_pull(pr_number).head.sha if pr_number else repo.get_branch(repo.default_branch).commit.sha
        status = repo.get_commit(sha).get_combined_status()
        return f"CI Status: {status.state.upper()} (SHA: {sha[:7]})"
    except Exception as e:
        return f"CI Check Error: {str(e)}"

def create_pull_request(title: str, body: str, head_branch: str, base_branch: str = "develop") -> str:
    """Creates a new GitHub Pull Request."""
    gh = _get_github_client()
    s = get_settings()
    try:
        pr = gh.get_repo(s.GITHUB_REPOSITORY).create_pull(title=title, body=body, head=head_branch, base=base_branch)
        return f"PR Created: {pr.html_url}"
    except Exception as e:
        return f"PR Creation Failed: {str(e)}"


# --- 3. SLACK TOOLS ---

def _format_messages(messages: List[Dict[str, Any]]) -> str:
    """Formats raw Slack JSON into readable text for the LLM."""
    formatted = []
    for msg in messages:
        if "subtype" in msg or not msg.get("text"):
            continue
        user = msg.get("user", "Unknown User")
        text = msg.get("text", "").replace("\n", " ")
        formatted.append(f"User {user}: {text}")
    return "\n".join(formatted) if formatted else "No relevant content found."


def _build_rich_blocks(title: str, content: str, is_draft: bool = True) -> List[Dict]:
    """Creates a professional Block Kit layout for documentation summaries."""
    header_prefix = "🧪 [SHADOW MODE DRAFT]" if is_draft else "📄 MIFOS UPDATE"
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{header_prefix}: {title}"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": content}
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "*Source: Mifos Enhancement Agent | Combined GitHub & Jira Context*"}]
        }
    ]


def search_messages(query: str) -> str:
    """Searches Slack across channels to find specific discussions (e.g., 'database migration')."""
    # Fixed: call the internal helper with the underscore
    client = _get_slack_client() 
    try:
        result = client.search_messages(query=query, count=10)
        matches = result.get("messages", {}).get("matches", [])
        if not matches:
            return f"No Slack messages found for '{query}'."

        raw_text = "\n".join([f"User: {m.get('username')} | Text: {m.get('text')}" for m in matches])

        llm = _get_llm()
        summary_chain = SLACK_SUMMARY_PROMPT | llm
        return summary_chain.invoke({"raw_data": raw_text, "user_query": query}).content
    except SlackApiError as e:
        return f"Error: {e.response['error']}"


def get_thread_replies(channel_id: str, thread_ts: str) -> str:
    """
    Fetches all replies in a Slack thread to understand developer consensus.
    """
    # Fixed: call the internal helper with the underscore
    client = _get_slack_client()
    try:
        # conversations_replies gets the full depth of a thread
        result = client.conversations_replies(channel=channel_id, ts=thread_ts)
        messages = result.get("messages", [])
        formatted = _format_messages(messages)

        llm = _get_llm()
        return llm.predict(f"Summarize the key decisions made in this developer thread: {formatted}")
    except SlackApiError as e:
        return f"Error fetching thread: {e.response['error']}"


def produce_mifos_summary(channel_id: str, title: str, raw_context: str, is_draft: bool = True) -> str:
    """
    The 'Librarian' Tool: Takes combined Jira/GitHub data and posts a rich summary to Slack.
    """
    # Fixed: call the internal helper with the underscore
    client = _get_slack_client()
    llm = _get_llm()

    try:
        # Generate the professional documentation text
        formatted_summary = llm.predict(MIFOS_DOC_PROMPT.format(
            context_data=raw_context,
            user_query=title
        ))

        # Build and send the rich UI blocks
        blocks = _build_rich_blocks(title, formatted_summary, is_draft)
        client.chat_postMessage(channel=channel_id, blocks=blocks, text=title)

        return f"Success: Summary sent to {channel_id}."
    except SlackApiError as e:
        return f"Error: {e.response['error']}"


def get_channel_history(channel_id: str) -> str:
    """Fetches recent history to understand the 'vibe' or current status of a project."""
    # Fixed: call the internal helper with the underscore
    client = _get_slack_client()
    try:
        result = client.conversations_history(channel=channel_id, limit=15)
        return f"Recent history for {channel_id}:\n{_format_messages(result.get('messages', []))}"
    except SlackApiError as e:
        return f"Error: {e.response['error']}"


# --- 4. KNOWLEDGE BASE & RAG TOOLS ---

import logging
import os
from typing import Optional, List, Dict, Any

# --- 3rd Party Clients ---
from jira import JIRA, JIRAError
from github import Github, GithubException
from slack_sdk import WebClient  # <--- Added missing import
from slack_sdk.errors import SlackApiError # <--- Added missing import
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

# Setup Logging
logger = logging.getLogger(__name__)

# --- Configuration & Client Initializers ---

def get_settings():
    """Import settings from your central config"""
    try:
        from MCP_Enhancement.src.core.config import get_settings
        return get_settings()
    except ImportError:
        # Fallback for localized testing
        try:
            from config import get_settings
            return get_settings()
        except ImportError:
            from MCP_Enhancement.config import get_settings
            return get_settings()

def _get_jira_client() -> JIRA:
    s = get_settings()
    return JIRA(server=s.JIRA_URL, basic_auth=(s.JIRA_USERNAME, s.JIRA_API_TOKEN.get_secret_value()))

def _get_github_client() -> Github:
    s = get_settings()
    return Github(s.GITHUB_TOKEN.get_secret_value())

def _get_slack_client() -> WebClient:
    s = get_settings()
    return WebClient(token=s.SLACK_BOT_TOKEN.get_secret_value())

def _get_llm():
    s = get_settings()
    return ChatOpenAI(model=s.OPENAI_MODEL, api_key=s.OPENAI_API_KEY.get_secret_value(), temperature=0)


# --- Prompts ---

# 1. GitHub Activity Summary
GITHUB_SUMMARY_PROMPT = ChatPromptTemplate.from_template(
    """You are a senior technical lead. The user is asking about activity in: "{repo_name}".

Live GitHub Data:
{raw_data}

User Question: "{user_query}"

Provide a professional, clear summary. 
- Prioritize "failing" CI statuses or "blocked" PRs.
- Explicitly mention specific authors and PR numbers.
- If everything looks good, state that the repository health is stable.
"""
)

# 2. Natural Language to JQL (Strict Output)
JQL_GENERATION_PROMPT = ChatPromptTemplate.from_template(
    """You are an expert in Jira Query Language (JQL). Convert the user's request into a valid JQL query.
Return ONLY the JQL string. Do not include markdown code blocks or explanations.

Rules:
1. Quoting: Enclose values with spaces in single quotes (e.g., assignee = 'Aru Sharma').
2. Search: Use ~ for text searches (e.g., summary ~ 'login').
3. Ordering: Always order by created DESC unless specified otherwise.

User Request: "{user_query}"
JQL Query:"""
)

# 3. Jira Data Summarization
SUMMARIZATION_PROMPT = ChatPromptTemplate.from_template(
    """You are a project management assistant. 
The user asked: "{user_query}"

Live Data from Jira:
{raw_data}

Provide a clear, concise, and helpful summary:
- For lists: Mention Keys, Summaries, and Assignees.
- For specific tickets: Summarize the current status and the sentiment/content of recent comments.
- If no data is found, suggest what keywords the user might try instead.
"""
)

# SLACK
SLACK_SUMMARY_PROMPT = PromptTemplate.from_template(
    """The user is asking for information based on Slack conversations.
    Raw message data: {raw_data}
    User Question: "{user_query}"
    Provide a concise summary. Mention usernames so the user knows the source of truth."""
)

# KNOWLEDGE SYNTHESIS (The Librarian)
MIFOS_DOC_PROMPT = PromptTemplate.from_template(
    """You are the Mifos Technical Librarian. Your task is to produce professional documentation 
    based on combined data from GitHub, Jira, and Slack.

    Source Context: {context_data}
    Target Project: Mifos (Non-Apache Fineract context)

    Create a 'Technical Release Note' that summarizes:
    1. The core functional change.
    2. The consensus reached in the discussion/comments.
    3. The expected impact on the Mifos Web-App/Mobile UI.

    Format as a clean markdown summary."""
)


# --- 1. JIRA TOOLS ---

def smart_search(query: str) -> str:
    """Translates natural language to JQL, searches Jira, and summarizes results."""
    jira = _get_jira_client()
    llm = _get_llm()
    try:
        jql = (JQL_GENERATION_PROMPT | llm).invoke({"user_query": query}).content.strip().strip("'\"")
        issues = jira.search_issues(jql, maxResults=5)
        if not issues: return "No issues found."

        formatted = "\n".join([f"[{i.key}] {i.fields.summary} ({i.fields.status.name})" for i in issues])
        return (SUMMARIZATION_PROMPT | llm).invoke({"user_query": query, "raw_data": formatted}).content
    except Exception as e:
        return f"Jira Search Error: {str(e)}"

def create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
    """Creates a new Jira issue."""
    jira = _get_jira_client()
    try:
        issue = jira.create_issue(
            fields={'project': {'key': project_key}, 'summary': summary, 'description': description,
                    'issuetype': {'name': issue_type}})
        return f"Created {issue.key}: {issue.permalink()}"
    except Exception as e:
        return f"Failed to create issue: {str(e)}"

def get_issue_context(issue_key: str) -> str:
    """
    Fetches the full details of a specific ticket, including the description and
    the 5 most recent comments to understand the context.
    """
    jira = _get_jira_client()
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


# --- 2. GITHUB TOOLS ---

def get_repo_overview(query: str) -> str:
    """Summarizes recent open PRs and Issues in the repository."""
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        prs = repo.get_pulls(state='open')[:5]
        issues = repo.get_issues(state='open')[:5]

        raw_data = f"PRs: {[p.title for p in prs]}\nIssues: {[i.title for i in issues]}"
        return (_get_llm() | GITHUB_SUMMARY_PROMPT).invoke(
            {"repo_name": repo.full_name, "raw_data": raw_data, "user_query": query}).content
    except Exception as e:
        return f"GitHub Error: {str(e)}"

def get_pr_details(pr_number: int) -> str:
    """Fetches deep context for a specific PR and files changed."""
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        pr = repo.get_pull(pr_number)
        files = [f.filename for f in pr.get_files()][:10]
        return f"PR #{pr.number}: {pr.title}\nBody: {pr.body}\nFiles: {', '.join(files)}"
    except Exception as e:
        return f"PR #{pr_number} not found: {str(e)}"

def check_ci_status(pr_number: Optional[int] = None) -> str:
    """Checks the CI/Build status for a PR or the main branch."""
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        sha = repo.get_pull(pr_number).head.sha if pr_number else repo.get_branch(repo.default_branch).commit.sha
        status = repo.get_commit(sha).get_combined_status()
        return f"CI Status: {status.state.upper()} (SHA: {sha[:7]})"
    except Exception as e:
        return f"CI Check Error: {str(e)}"

def create_pull_request(title: str, body: str, head_branch: str, base_branch: str = "develop") -> str:
    """Creates a new GitHub Pull Request."""
    gh = _get_github_client()
    s = get_settings()
    try:
        pr = gh.get_repo(s.GITHUB_REPOSITORY).create_pull(title=title, body=body, head=head_branch, base=base_branch)
        return f"PR Created: {pr.html_url}"
    except Exception as e:
        return f"PR Creation Failed: {str(e)}"


# --- 3. SLACK TOOLS ---

def _format_messages(messages: List[Dict[str, Any]]) -> str:
    """Formats raw Slack JSON into readable text for the LLM."""
    formatted = []
    for msg in messages:
        if "subtype" in msg or not msg.get("text"):
            continue
        user = msg.get("user", "Unknown User")
        text = msg.get("text", "").replace("\n", " ")
        formatted.append(f"User {user}: {text}")
    return "\n".join(formatted) if formatted else "No relevant content found."


def _build_rich_blocks(title: str, content: str, is_draft: bool = True) -> List[Dict]:
    """Creates a professional Block Kit layout for documentation summaries."""
    header_prefix = "🧪 [SHADOW MODE DRAFT]" if is_draft else "📄 MIFOS UPDATE"
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{header_prefix}: {title}"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": content}
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "*Source: Mifos Enhancement Agent | Combined GitHub & Jira Context*"}]
        }
    ]


def search_messages(query: str) -> str:
    """Searches Slack across channels to find specific discussions (e.g., 'database migration')."""
    # Fixed: call the internal helper with the underscore
    client = _get_slack_client() 
    try:
        result = client.search_messages(query=query, count=10)
        matches = result.get("messages", {}).get("matches", [])
        if not matches:
            return f"No Slack messages found for '{query}'."

        raw_text = "\n".join([f"User: {m.get('username')} | Text: {m.get('text')}" for m in matches])

        llm = _get_llm()
        summary_chain = SLACK_SUMMARY_PROMPT | llm
        return summary_chain.invoke({"raw_data": raw_text, "user_query": query}).content
    except SlackApiError as e:
        return f"Error: {e.response['error']}"


def get_thread_replies(channel_id: str, thread_ts: str) -> str:
    """
    Fetches all replies in a Slack thread to understand developer consensus.
    """
    # Fixed: call the internal helper with the underscore
    client = _get_slack_client()
    try:
        # conversations_replies gets the full depth of a thread
        result = client.conversations_replies(channel=channel_id, ts=thread_ts)
        messages = result.get("messages", [])
        formatted = _format_messages(messages)

        llm = _get_llm()
        return llm.predict(f"Summarize the key decisions made in this developer thread: {formatted}")
    except SlackApiError as e:
        return f"Error fetching thread: {e.response['error']}"


def produce_mifos_summary(channel_id: str, title: str, raw_context: str, is_draft: bool = True) -> str:
    """
    The 'Librarian' Tool: Takes combined Jira/GitHub data and posts a rich summary to Slack.
    """
    # Fixed: call the internal helper with the underscore
    client = _get_slack_client()
    llm = _get_llm()

    try:
        # Generate the professional documentation text
        formatted_summary = llm.predict(MIFOS_DOC_PROMPT.format(
            context_data=raw_context,
            user_query=title
        ))

        # Build and send the rich UI blocks
        blocks = _build_rich_blocks(title, formatted_summary, is_draft)
        client.chat_postMessage(channel=channel_id, blocks=blocks, text=title)

        return f"Success: Summary sent to {channel_id}."
    except SlackApiError as e:
        return f"Error: {e.response['error']}"


def get_channel_history(channel_id: str) -> str:
    """Fetches recent history to understand the 'vibe' or current status of a project."""
    # Fixed: call the internal helper with the underscore
    client = _get_slack_client()
    try:
        result = client.conversations_history(channel=channel_id, limit=15)
        return f"Recent history for {channel_id}:\n{_format_messages(result.get('messages', []))}"
    except SlackApiError as e:
        return f"Error: {e.response['error']}"


# --- 4. KNOWLEDGE BASE & RAG TOOLS ---

def search_knowledge_base(query: str) -> str:
    """
    The 'Librarian's Brain': Queries Pinecone for Mifos/Fineract documentation
    and returns a synthesized technical answer.
    """
    try:
        # We import here to avoid circular dependencies if rag_agent imports tools
        from agents.rag_agent import query_docs

        logger.info(f"🔍 Querying Vector DB for: {query}")
        answer = query_docs(query)

        # Validation to ensure we don't return empty strings to the Orchestrator
        if not answer or "I don't have enough information" in answer:
            return f"The knowledge base contains no specific guidance regarding: '{query}'."

        return answer

    except ImportError:
        logger.error("rag_agent.py not found in agents directory.")
        return "Knowledge Base Error: RAG module is missing."
    except Exception as e:
        logger.error(f"RAG Query failed: {str(e)}")
        return "Knowledge Base is currently offline or re-indexing."


def add_to_knowledge_base(documents: List[str], metadata: List[Dict] = None):
    """
    Utility to inject new PR summaries or Slack decisions back into Pinecone.
    """
    try:
        from agents.rag_agent import get_vectorstore
        from langchain_core.documents import Document

        vectorstore = get_vectorstore()
        docs = [Document(page_content=text, metadata=metadata[i] if metadata else {})
                for i, text in enumerate(documents)]

        vectorstore.add_documents(docs)
        return f"Successfully indexed {len(docs)} items to the knowledge base."
    except Exception as e:
        return f"Failed to update knowledge base: {str(e)}"