import os
import logging
import requests
import re
from typing import Optional, List, Dict

# Environment & Server
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Slack Bolt App
slack_app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
app_handler = AsyncSlackRequestHandler(slack_app)

# Initialize FastAPI
api = FastAPI()


# --- HELPER FUNCTIONS ---

def get_jira_auth():
    """Returns the tuple for Basic Auth (Email, Token)."""
    return (os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))


def parse_adf_text(adf_node):
    """Helper to recursively extract all plain text from Jira's ADF format."""
    if not adf_node: return ""
    texts = []
    if isinstance(adf_node, dict):
        if adf_node.get("type") == "text":
            texts.append(adf_node.get("text", ""))
        for value in adf_node.values():
            if isinstance(value, (dict, list)):
                texts.append(parse_adf_text(value))
    elif isinstance(adf_node, list):
        for item in adf_node:
            texts.append(parse_adf_text(item))
    return " ".join(filter(None, texts))


def extract_jira_keys(text: str) -> List[str]:
    """Finds unique Jira keys (e.g., MIFOS-123, WEB-45) in a string."""
    if not text:
        return []
    # Pattern: Uppercase letters, hyphen, numbers
    return list(set(re.findall(r"([A-Z]+-\d+)", text)))


def _create_block_kit_summary(title: str, content: str) -> List[Dict]:
    """Helper to build a professional Slack UI message."""
    return [
        {"type": "header", "text": {"type": "plain_text", "text": f"📄 {title}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": content}},
        {"type": "divider"},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": "*Source: Mifos Watchdog Agent*"}]}
    ]


# --- JIRA TOOLS (Phase 1 & 2) ---

async def get_jira_ticket_details(ticket_key: str):
    """Fetches Jira ticket summary, description, AND recent comments."""
    jira_url = os.getenv("JIRA_URL")
    if not jira_url: return "❌ Error: JIRA_URL not set."

    try:
        url = f"{jira_url}/rest/api/3/issue/{ticket_key}"
        resp = requests.get(url, auth=get_jira_auth())

        if resp.status_code != 200:
            return f"❌ Error fetching ticket {ticket_key}: {resp.status_code}"

        data = resp.json()
        fields = data.get("fields", {})
        summary = fields.get("summary", "No Summary")
        description = parse_adf_text(fields.get("description")) or "No Description"

        # Comments Logic
        comments_data = fields.get("comment", {}).get("comments", [])
        comments_text = []
        seen = set()
        for c in comments_data:
            body = parse_adf_text(c.get("body")).strip()
            if body and body not in seen:
                comments_text.append(f"- {body[:100]}...")  # Truncate for brevity
                seen.add(body)

        discussion = "\n".join(comments_text[-3:]) if comments_text else "No recent comments."

        return (
            f"*Summary:* {summary}\n"
            f"*Description:* {description[:300]}...\n"  # Truncate for Slack
            f"*Recent Discussion:*\n{discussion}"
        )
    except Exception as e:
        return f"❌ Exception reading Jira: {str(e)}"


async def check_jira_for_ui_assets(ticket_key: str):
    """Checks for UI screenshots in Jira."""
    jira_url = os.getenv("JIRA_URL")
    url = f"{jira_url}/rest/api/3/issue/{ticket_key}?fields=attachment"
    try:
        resp = requests.get(url, auth=get_jira_auth())
        data = resp.json()
        attachments = data.get("fields", {}).get("attachment", [])
        images = [f"• <{a['content']}|{a['filename']}>" for a in attachments if a['mimeType'].startswith('image/')]
        return "\n".join(images) if images else "No UI screenshots found."
    except Exception:
        return "Error checking assets."


# --- PHASE 3: GITHUB WATCHDOG LOGIC ---

async def process_github_pr(payload: Dict):
    """
    1. Extracts PR details.
    2. Finds Jira Key.
    3. Fetches Jira Data.
    4. Posts Alert to Slack.
    """
    pr = payload.get("pull_request", {})
    pr_number = pr.get("number")
    pr_title = pr.get("title", "")
    pr_body = pr.get("body", "") or ""
    pr_url = pr.get("html_url")
    author = pr.get("user", {}).get("login", "Unknown")

    # 1. Identify Jira Ticket
    full_text = f"{pr_title} {pr_body}"
    jira_keys = extract_jira_keys(full_text)

    channel_id = os.getenv("SLACK_ALERT_CHANNEL_ID")
    if not channel_id:
        logger.warning("SLACK_ALERT_CHANNEL_ID not set. Skipping notification.")
        return

    # 2. Logic: If Jira Key found, fetch details. If not, Warn.
    if jira_keys:
        ticket_key = jira_keys[0]  # Take the first one found
        jira_info = await get_jira_ticket_details(ticket_key)

        msg_text = (
            f"👀 *Watchdog Alert:* New PR #{pr_number} by {author}\n"
            f"🔗 <{pr_url}|{pr_title}>\n\n"
            f"✅ *Linked Jira Ticket:* `{ticket_key}`\n"
            f"{jira_info}"
        )
    else:
        msg_text = (
            f"⚠️ *Watchdog Warning:* New PR #{pr_number} by {author}\n"
            f"🔗 <{pr_url}|{pr_title}>\n\n"
            f"❌ *No Jira Ticket Detected!*\n"
            f"Please ensure the PR description includes a valid ticket key (e.g., MIFOS-123)."
        )

    # 3. Post to Slack
    await slack_app.client.chat_postMessage(
        channel=channel_id,
        text=f"Watchdog Update: PR #{pr_number}",
        blocks=_create_block_kit_summary(f"GitHub PR #{pr_number} Analysis", msg_text)
    )


# --- API ENDPOINTS ---

@api.post("/slack/events")
async def slack_endpoint(req: Request):
    """Handles Slack Events (Mentions)."""
    return await app_handler.handle(req)


@api.post("/github/webhook")
async def github_endpoint(request: Request, background_tasks: BackgroundTasks):
    """
    Handles GitHub Webhooks.
    Triggers the Watchdog agent in the background to avoid timeouts.
    """
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    # Only react to Pull Requests that are opened or edited
    if event_type == "pull_request":
        action = payload.get("action")
        if action in ["opened", "edited", "synchronize"]:
            logger.info(f"Received GitHub PR Event: {action}")
            # Run processing in background so GitHub gets a 200 OK immediately
            background_tasks.add_task(process_github_pr, payload)

    return {"status": "received"}


# --- SLACK HANDLERS (Manual Trigger) ---

@slack_app.event("app_mention")
async def handle_mentions(body, say):
    text = body["event"]["text"]
    match = re.search(r"([A-Z]+-\d+)", text)
    if match:
        ticket_key = match.group(1)
        await say(f"🔍 Checking Jira for *{ticket_key}*...")
        details = await get_jira_ticket_details(ticket_key)
        assets = await check_jira_for_ui_assets(ticket_key)
        blocks = _create_block_kit_summary(f"Librarian Report: {ticket_key}", f"{details}\n\n*UI Assets:*\n{assets}")
        await say(blocks=blocks, text=f"Report for {ticket_key}")
    else:
        await say(
            "👋 I am the Watchdog. I listen for PRs automatically, but you can mention me with a Ticket ID to look it up manually.")


@slack_app.event("message")
async def handle_message_events(body, logger):
    logger.info(body)


if __name__ == "__main__":
    import uvicorn

    print("⚡️ Mifos Phase 3 Watchdog is listening on port 3000...")
    uvicorn.run(api, host="0.0.0.0", port=3000)