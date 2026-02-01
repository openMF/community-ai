import logging
from typing import Optional, List, Dict, Any

# Direct SDK for precise control over Block Kit and Threads
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# Robust import for config
try:
    from MCP_Enhancement.src.core.config import get_settings
except ImportError:
    from MCP_Enhancement.config import get_settings

logger = logging.getLogger(__name__)

# --- Reusable Prompts for Knowledge Synthesis ---

# Standard summary for searches
SLACK_SUMMARY_PROMPT = PromptTemplate.from_template(
    """The user is asking for information based on Slack conversations.
    Raw message data: {raw_data}
    User Question: "{user_query}"
    Provide a concise summary. Mention usernames so the user knows the source of truth."""
)

# New: Document Production Prompt (The 'Librarian' Logic)
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


# --- Helper Logic ---

def get_slack_client() -> WebClient:
    settings = get_settings()
    return WebClient(token=settings.SLACK_BOT_TOKEN.get_secret_value())


def get_llm():
    settings = get_settings()
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY.get_secret_value(),
        temperature=0
    )


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


# --- Primary Tools for MCP ---

def search_messages(query: str) -> str:
    """Searches Slack across channels to find specific discussions (e.g., 'database migration')."""
    client = get_slack_client()
    try:
        result = client.search_messages(query=query, count=10)
        matches = result.get("messages", {}).get("matches", [])
        if not matches:
            return f"No Slack messages found for '{query}'."

        raw_text = "\n".join([f"User: {m.get('username')} | Text: {m.get('text')}" for m in matches])

        llm = get_llm()
        summary_chain = SLACK_SUMMARY_PROMPT | llm
        return summary_chain.invoke({"raw_data": raw_text, "user_query": query}).content
    except SlackApiError as e:
        return f"Error: {e.response['error']}"


def get_thread_replies(channel_id: str, thread_ts: str) -> str:
    """
    David's Request: 'Query for comments on tickets.'
    Fetches all replies in a Slack thread to understand developer consensus.
    """
    client = get_slack_client()
    try:
        # conversations_replies gets the full depth of a thread
        result = client.conversations_replies(channel=channel_id, ts=thread_ts)
        messages = result.get("messages", [])
        formatted = _format_messages(messages)

        llm = get_llm()
        return llm.predict(f"Summarize the key decisions made in this developer thread: {formatted}")
    except SlackApiError as e:
        return f"Error fetching thread: {e.response['error']}"


def produce_mifos_summary(channel_id: str, title: str, raw_context: str, is_draft: bool = True) -> str:
    """
    The 'Librarian' Tool: Takes combined Jira/GitHub data and posts a rich summary to Slack.
    Use this for the Phase 3 'Slack-First' approval.
    """
    client = get_slack_client()
    llm = get_llm()

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
    client = get_slack_client()
    try:
        result = client.conversations_history(channel=channel_id, limit=15)
        return f"Recent history for {channel_id}:\n{_format_messages(result.get('messages', []))}"
    except SlackApiError as e:
        return f"Error: {e.response['error']}"