import os
import re
import requests
from typing import Optional, Dict, Any, List
from github import Github
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from atlassian import Jira
from mcp.server.fastmcp import FastMCP
from pydantic_settings import BaseSettings

# ✅ IMPORT REAL RAG LOGIC
try:
    from MCP_Enhancement.agents.rag_agent import query_docs
except ImportError:
    def query_docs(query):
        return "⚠️ RAG Module not found. Please check MCP_Enhancement/agents/rag_agent.py"


# =========================================================
# 1. CONFIGURATION
# =========================================================

class Settings(BaseSettings):
    # --- JIRA ---
    JIRA_URL: str
    JIRA_EMAIL: str
    JIRA_API_TOKEN: str
    JIRA_PROJECT_KEY: str = "WEB"

    # --- GITHUB ---
    GITHUB_TOKEN: str
    GITHUB_REPOSITORY: str
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    # --- FINERACT (BANKING) ---
    FINERACT_BASE_URL: str = "https://demo.mifos.io/fineract-provider/api/v1"
    FINERACT_TENANT_ID: str = "default"
    FINERACT_USERNAME: str = "mifos"
    FINERACT_PASSWORD: str = "password"

    # --- AI & DATA ---
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str = "mifos-knowledge"

    # --- SLACK ---
    SLACK_BOT_TOKEN: str
    SLACK_SIGNING_SECRET: str
    SLACK_ALERT_CHANNEL_ID: Optional[str] = None  # Channel for notifications

    # --- SECURITY ---
    AUTHORIZED_USERS: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


def get_settings():
    return Settings()


mcp = FastMCP("mifos-agent-tools")


# =========================================================
# 2. CLIENT HELPERS
# =========================================================

def _get_jira_client():
    s = get_settings()
    return Jira(url=s.JIRA_URL, username=s.JIRA_EMAIL, password=s.JIRA_API_TOKEN)


def _get_github_client():
    s = get_settings()
    return Github(s.GITHUB_TOKEN)


def _get_slack_client():
    s = get_settings()
    return WebClient(token=s.SLACK_BOT_TOKEN)


def _check_authorization(ctx_string: str) -> bool:
    s = get_settings()
    match = re.search(r'U[A-Z0-9]+', ctx_string)
    user_id = match.group(0) if match else None
    allowed_list = [u.strip() for u in s.AUTHORIZED_USERS.split(",") if u.strip()]
    if not user_id or not allowed_list:
        return False
    return user_id in allowed_list


# =========================================================
# 3. CORE LOGIC FUNCTIONS
# =========================================================

# --- BANKING LOGIC (Fineract) ---
def search_fineract_clients(display_name: str) -> str:
    s = get_settings()
    endpoint = f"{s.FINERACT_BASE_URL}/clients"
    params = {"displayName": display_name}
    headers = {
        "Fineract-Platform-TenantId": s.FINERACT_TENANT_ID,
        "Content-Type": "application/json"
    }
    auth = (s.FINERACT_USERNAME, s.FINERACT_PASSWORD)

    try:
        response = requests.get(endpoint, params=params, auth=auth, headers=headers, timeout=30)
        if response.status_code == 200:
            clients = response.json().get("pageItems", [])
            if not clients: return f"ℹ️ No live clients found matching '{display_name}'."
            summary = [f"✅ Found {len(clients)} matches:"]
            for c in clients[:3]:
                summary.append(f"- ID: {c.get('id')} | Name: {c.get('displayName')} | Office: {c.get('officeName')}")
            return "\n".join(summary)
        return f"❌ Fineract API Error: {response.status_code}"
    except Exception as e:
        return f"⚠️ Connection Failed: {str(e)}"


def get_loan_details(client_id: int) -> str:
    s = get_settings()
    endpoint = f"{s.FINERACT_BASE_URL}/clients/{client_id}/accounts"
    headers = {
        "Fineract-Platform-TenantId": s.FINERACT_TENANT_ID,
        "Content-Type": "application/json"
    }
    auth = (s.FINERACT_USERNAME, s.FINERACT_PASSWORD)

    try:
        response = requests.get(endpoint, auth=auth, headers=headers, timeout=10)
        if response.status_code == 200:
            loans = response.json().get("loanAccounts", [])
            if not loans: return f"ℹ️ Client {client_id} has no live loans."
            summary = [f"🏦 Live Loans for Client {client_id}:"]
            for l in loans:
                summary.append(
                    f"- Acct: {l.get('accountNo')} | Bal: {l.get('loanBalance', 0)} | Status: {l.get('status', {}).get('value')}")
            return "\n".join(summary)
        return f"❌ Fineract API Error: {response.status_code}"
    except Exception as e:
        return f"⚠️ Connection Failed: {str(e)}"


# --- DEVOPS LOGIC ---
def get_issue_context(ticket_key: str) -> str:
    try:
        jira = _get_jira_client()
        issue = jira.issue(ticket_key)
        fields = issue.get("fields", {})
        return (
            f"🎫 **{ticket_key}**: {fields.get('summary')}\n"
            f"📂 Status: {fields.get('status', {}).get('name')}\n"
            f"👤 Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned')}\n"
            f"📝 Description: {fields.get('description', '')[:500]}..."
        )
    except Exception as e:
        return f"⚠️ Could not find Jira ticket {ticket_key}. Error: {e}"


def search_knowledge_base(query: str) -> str:
    try:
        return query_docs(query)
    except Exception as e:
        return f"⚠️ RAG Error: {e}"


def check_ci_status(pr_number: int) -> str:
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        pr = repo.get_pull(pr_number)
        sha = pr.head.sha
        commit = repo.get_commit(sha=sha)
        statuses = commit.get_statuses()

        if statuses.totalCount > 0:
            latest = statuses[0]
            return f"⚙️ CI Status: **{latest.state.upper()}** ({latest.description})"

        checks = repo.get_commit(sha).get_check_runs()
        if checks.totalCount > 0:
            latest = checks[0]
            return f"⚙️ CI Status: **{latest.status.upper()}** ({latest.conclusion})"

        return "⚠️ No CI/CD pipelines found for this PR."
    except Exception as e:
        return f"❌ Error checking CI: {e}"


def get_pr_details(pr_number: int) -> str:
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        pr = repo.get_pull(pr_number)
        description = pr.body if pr.body else "No description provided."
        return (
            f"🔗 **PR #{pr_number}**: {pr.title}\n"
            f"👤 Author: {pr.user.login}\n"
            f"📂 State: {pr.state.upper()}\n"
            f"--------------------------------------\n"
            f"{description}"
        )
    except Exception as e:
        return f"❌ Error fetching PR details: {e}"


def post_github_comment(pr_number: int, comment_body: str) -> str:
    gh = _get_github_client()
    s = get_settings()
    try:
        repo = gh.get_repo(s.GITHUB_REPOSITORY)
        issue = repo.get_issue(number=pr_number)
        issue.create_comment(comment_body)
        return f"✅ Successfully posted comment on PR #{pr_number}"
    except Exception as e:
        return f"❌ Failed to comment: {e}"


def get_recent_slack_messages(channel_id: str, count: int = 10) -> str:
    client = _get_slack_client()
    try:
        response = client.conversations_history(channel=channel_id, limit=count)
        messages = response.get("messages", [])
        user_map = {}
        formatted_messages = []

        for m in reversed(messages):
            user_id = m.get("user")
            text = m.get("text", "")
            display_name = "User"
            if user_id:
                if user_id in user_map:
                    display_name = user_map[user_id]
                else:
                    try:
                        user_info = client.users_info(user=user_id)
                        user = user_info.get("user", {})
                        display_name = user.get("real_name") or user.get("name") or "User"
                        user_map[user_id] = display_name
                    except Exception:
                        user_map[user_id] = "User"
            formatted_messages.append(f"- **{display_name}**: {text}")
        return "\n".join(formatted_messages)
    except Exception as e:
        return f"❌ Could not fetch chat history: {e}"


def create_issue_logic(project_key: str, summary: str, description: str, priority: str = "Medium") -> str:
    """Creates a ticket with a specific priority."""
    jira = _get_jira_client()
    try:
        # standardizing priority to title case (e.g. "high" -> "High")
        clean_priority = priority.capitalize()

        issue_dict = {
            'project': {'key': project_key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': 'Task'},
            'priority': {'name': clean_priority}  # <--- NEW LINE ADDS PRIORITY
        }
        new_issue = jira.issue_create(fields=issue_dict)
        return f"✅ Created Ticket: **{new_issue['key']}** (Priority: {clean_priority})"
    except Exception as e:
        return f"❌ Failed to create ticket: {e}"


# --- WEBHOOK HANDLERS (NEW!) ---
def process_jira_webhook(payload: Dict[str, Any], target_channel: str = None) -> str:
    """
    Parses Jira Webhook JSON and sends a formatted notification to Slack.
    """
    client = _get_slack_client()
    s = get_settings()

    if not target_channel:
        target_channel = s.SLACK_ALERT_CHANNEL_ID
    if not target_channel:
        return "❌ No target channel configured."

    event = payload.get('webhookEvent')
    if not event: return "⚠️ Ignored."

    try:
        issue = payload.get('issue', {})
        key = issue.get('key', 'UNKNOWN')
        fields = issue.get('fields', {})
        summary = fields.get('summary', 'No Summary')
        message_text = ""

        # A. Issue Created
        if event == 'jira:issue_created':
            reporter = fields.get('creator', {}).get('displayName', 'Unknown')
            priority = fields.get('priority', {}).get('name', 'Normal')
            message_text = (
                f"🚨 *New Issue Created: {key}*\n"
                f"*Summary:* {summary}\n"
                f"*Reporter:* {reporter} | *Priority:* {priority}\n"
                f"<{s.JIRA_URL}/browse/{key}|View in Jira>"
            )

        # B. Issue Updated (Status OR Assignee)
        elif event == 'jira:issue_updated':
            changelog = payload.get('changelog', {}).get('items', [])
            for item in changelog:
                field = item.get('field')

                # 1. Status Change (To Do -> Done)
                if field == 'status':
                    from_status = item.get('fromString')
                    to_status = item.get('toString')
                    message_text = (
                        f"✅ *Task Completed: {key}*\n" if to_status == 'Done' else f"🔄 *Status Update: {key}*\n"
                    )
                    message_text += (
                        f"*Summary:* {summary}\n"
                        f"Moved from *{from_status}* → *{to_status}*\n"
                        f"<{s.JIRA_URL}/browse/{key}|View in Jira>"
                    )
                    break

                    # 2. Assignee Change
                elif field == 'assignee':
                    to_user = item.get('toString') or "Unassigned"
                    message_text = (
                        f"👤 *Assignee Update: {key}*\n"
                        f"*Summary:* {summary}\n"
                        f"Assigned to: *{to_user}*\n"
                        f"<{s.JIRA_URL}/browse/{key}|View in Jira>"
                    )
                    break

        if message_text:
            client.chat_postMessage(channel=target_channel, text=message_text)
            return f"✅ Notification sent for {key}"

        return "ℹ️ Ignored: No relevant field changed."

    except Exception as e:
        print(f"Webhook Error: {e}")
        return f"❌ Error: {str(e)}"


# =========================================================
# 4. MCP TOOL WRAPPERS
# =========================================================

@mcp.tool()
def tool_jira_context(ticket_key: str):
    """Get details of a Jira ticket (Read Only)."""
    return get_issue_context(ticket_key)


@mcp.tool()
def tool_knowledge_base(query: str):
    """Search documentation via RAG (Read Only)."""
    return search_knowledge_base(query)


@mcp.tool()
def tool_ci_check(pr_number: int):
    """Check CI status of a PR (Read Only)."""
    return check_ci_status(pr_number)


@mcp.tool()
def tool_pr_details(pr_number: int):
    """Get title and author of a PR (Read Only)."""
    return get_pr_details(pr_number)


@mcp.tool()
def tool_get_chat_history(channel_id: str, count: int = 10):
    """Reads recent Slack messages. default count is 10."""
    return get_recent_slack_messages(channel_id, count=count)


@mcp.tool()
def tool_search_client(name: str):
    """Search for a bank client by name in Fineract/Mifos."""
    return search_fineract_clients(name)


@mcp.tool()
def tool_loan_details(client_id: int):
    """Get active loan details for a client ID."""
    return get_loan_details(client_id)


@mcp.tool()
def tool_post_pr_comment(ctx: str, pr_number: int, comment: str):
    """Posts a comment to a GitHub PR (Requires Auth)."""
    if not _check_authorization(ctx):
        return "⛔ SECURITY ALERT: You are not authorized to post comments."
    return post_github_comment(pr_number, comment)


@mcp.tool()
def tool_create_jira(ctx: str, project_key: str, summary: str, description: str, priority: str = "Medium"):
    """Creates a new Jira ticket. Priority options: High, Medium, Low."""
    if not _check_authorization(ctx):
        return "⛔ SECURITY ALERT: You are not authorized to create tickets."
    return create_issue_logic(project_key, summary, description, priority)