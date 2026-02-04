import os
import logging
import re
import hmac
import hashlib
import asyncio
import uvicorn
from typing import Dict, List, Any

# --- FAST MCP & SERVER ---
from fastmcp import FastMCP
from fastapi import Request, BackgroundTasks, HTTPException

# --- SLACK & CONFIG ---
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from dotenv import load_dotenv

# --- THE TOOLBOX ---
from tools.mifos_tools import (
    get_issue_context,
    smart_search,
    get_pr_details,
    check_ci_status,
    search_knowledge_base,
    get_settings
)

# Load Environment
load_dotenv()
settings = get_settings()

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mifos-orchestrator")

# 1. INITIALIZE FASTMCP
mcp = FastMCP("Mifos Unified Watchdog")

# Initialize Slack Bolt
slack_app = AsyncApp(
    token=settings.SLACK_BOT_TOKEN.get_secret_value(),
    signing_secret=settings.SLACK_SIGNING_SECRET.get_secret_value()
)
app_handler = AsyncSlackRequestHandler(slack_app)


# --- 2. REGISTER TOOLS ---

@mcp.tool
def tool_jira_context(ticket_key: str):
    """Fetches full Jira ticket details and recent comments."""
    return get_issue_context(ticket_key)


@mcp.tool
def tool_knowledge_base(query: str):
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


# --- 3. WATCHDOG LOGIC ---

async def verify_github_signature(request: Request):
    """
    Security Gatekeeper: Ensures the request actually came from GitHub.
    Robustly handles both string and SecretStr types to prevent 500 errors.
    """
    secret = settings.GITHUB_WEBHOOK_SECRET

    if secret is None:
        return  # Dev mode

    # --- ROBUST SECRET EXTRACTION ---
    # This block prevents the 500 Error by checking the type first
    try:
        if hasattr(secret, "get_secret_value"):
            secret_val = secret.get_secret_value()
        else:
            secret_val = str(secret)

        if not secret_val:
            return
    except Exception as e:
        logger.error(f"❌ Config Error: Could not read GITHUB_WEBHOOK_SECRET. {e}")
        raise HTTPException(status_code=500, detail="Server Configuration Error")

    # --- HEADER CHECK ---
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=403, detail="Missing X-Hub-Signature-256 header")

    # --- CRYPTO VERIFICATION ---
    try:
        body = await request.body()
        expected_signature = "sha256=" + hmac.new(
            secret_val.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("⚠️ Security Alert: Invalid GitHub Signature detected.")
            raise HTTPException(status_code=403, detail="Invalid signature")

    except Exception as e:
        logger.error(f"❌ Crypto Error: {e}")
        raise HTTPException(status_code=500, detail="Signature Verification Failed")


async def process_pr_event(payload: Dict):
    """The Integrated Intelligence Loop."""
    try:
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        pr_title = pr.get("title", "")
        pr_url = pr.get("html_url")
        user = pr.get("user", {}).get("login", "Unknown")

        # A. Audit the Context
        match = re.search(r'[A-Z]+-\d+', pr_title)
        jira_key = match.group(0) if match else "UNKNOWN"
        jira_info = tool_jira_context(jira_key) if jira_key != "UNKNOWN" else "⚠️ No Jira Ticket Linked."

        # B. Audit the Quality
        rag_insight = tool_knowledge_base(f"Provide architectural guidance for: {pr_title}")
        ci_status = tool_ci_check(pr_number)

        # C. Build the Unified Slack Block
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": f"🛡️ Watchdog Report: {user}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"<{pr_url}|*PR #{pr_number}: {pr_title}*>"}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Jira Context:*\n{jira_info}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*CI Status:* {ci_status}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"🤖 *RAG Standards Check:*\n{rag_insight}"}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "Mifos Unified Intelligence | Phase 5"}]}
        ]

        # Post to Slack
        channel_id = settings.SLACK_ALERT_CHANNEL_ID
        if channel_id:
            await slack_app.client.chat_postMessage(channel=channel_id, blocks=blocks, text=f"PR Alert: {pr_title}")
            logger.info(f"✅ Alert sent to Slack channel {channel_id}")

    except Exception as e:
        logger.error(f"❌ Processing error in Watchdog Loop: {e}")


# --- 4. EXPOSE WEBHOOKS ---

async def slack_endpoint(req: Request):
    return await app_handler.handle(req)


async def github_webhook(request: Request):
    await verify_github_signature(request)
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    if event == "pull_request":
        action = payload.get("action")
        if action in ["opened", "synchronize"]:
            logger.info(f"📥 Auditing PR #{payload['pull_request']['number']}")
            asyncio.create_task(process_pr_event(payload))

    return {"status": "processing"}


# --- SERVER SETUP & UNWRAPPING ---
target_app = None
try:
    # 1. Get the app object (checking if it's a method or property)
    raw_app = mcp.http_app if not callable(mcp.http_app) else mcp.http_app()

    # 2. Unwrap 'StarletteWithLifespan' if present
    if hasattr(raw_app, "app"):
        target_app = raw_app.app
    else:
        target_app = raw_app

    # 3. Add Routes (Standard Starlette syntax)
    target_app.add_route("/slack/events", slack_endpoint, methods=["POST"])
    target_app.add_route("/github/webhook", github_webhook, methods=["POST"])

    logger.info("✅ Successfully registered Webhook routes.")

except Exception as e:
    logger.error(f"❌ Route registration failed: {e}")
    raise e

# --- 5. RUN SERVER ---
if __name__ == "__main__":
    logger.info("🚀 Starting Mifos Unified Watchdog on Port 3000...")
    uvicorn.run(target_app, host="0.0.0.0", port=3000)