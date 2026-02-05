import logging
import re
import hmac
import hashlib
import asyncio
import uvicorn
from typing import Dict

# --- IMPORTS ---
from fastapi import Request, HTTPException
# 🚨 FIX 1: Starlette requires explicit JSONResponse
from starlette.responses import JSONResponse
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from dotenv import load_dotenv

# --- IMPORT TOOLS & MCP ---
# 🚨 FIX 2: Import 'mcp' (the server) and RAW functions (the logic)
# We do NOT import the @mcp.tool wrappers here, or the code will crash.
from MCP_Enhancement.tools.mifos_tools import (
    mcp,  # The FastMCP server instance
    get_issue_context,  # Raw function for Jira
    search_knowledge_base,  # Raw function for RAG
    check_ci_status,  # Raw function for CI
    get_settings
)

# Load Environment
load_dotenv()
settings = get_settings()

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mifos-orchestrator")

# Initialize Slack Bolt
slack_app = AsyncApp(
    token=settings.SLACK_BOT_TOKEN.get_secret_value(),
    signing_secret=settings.SLACK_SIGNING_SECRET.get_secret_value()
)
app_handler = AsyncSlackRequestHandler(slack_app)


# --- 1. WATCHDOG LOGIC (THE BRAIN) ---

async def verify_github_signature(request: Request):
    """
    Security Gatekeeper: Ensures the request actually came from GitHub.
    """
    secret = settings.GITHUB_WEBHOOK_SECRET
    if not secret:
        return

    try:
        secret_val = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)
    except Exception:
        raise HTTPException(status_code=500, detail="Config Error")

    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=403, detail="Missing X-Hub-Signature-256")

    try:
        body = await request.body()
        expected_signature = "sha256=" + hmac.new(
            secret_val.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("⚠️ Security Alert: Invalid GitHub Signature.")
            raise HTTPException(status_code=403, detail="Invalid signature")
    except Exception:
        raise HTTPException(status_code=500, detail="Signature Verification Failed")


async def process_pr_event(payload: Dict):
    """
    The Integrated Intelligence Loop
    """
    try:
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        pr_title = pr.get("title", "")
        pr_url = pr.get("html_url")
        user = pr.get("user", {}).get("login", "Unknown")

        logger.info(f"🕵️ Analyzing PR #{pr_number}: {pr_title}")

        # A. Audit the Context (Jira)
        match = re.search(r'[A-Z]+-\d+', pr_title)
        jira_key = match.group(0) if match else "UNKNOWN"

        # 🚨 FIX 3: Calling the RAW function directly (No "Tool object not callable" error)
        if jira_key != "UNKNOWN":
            jira_info = get_issue_context(jira_key)
        else:
            jira_info = "⚠️ No Jira Ticket Linked in Title."

        # B. Audit the Quality (RAG + CI)
        # 🚨 FIX 3: Calling raw functions
        rag_insight = search_knowledge_base(f"Provide architectural guidance for: {pr_title}")
        ci_status = check_ci_status(pr_number)

        # C. Build the Unified Slack Block
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": f"🛡️ Watchdog Report: {user}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"<{pr_url}|*PR #{pr_number}: {pr_title}*>"}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Jira Context:*\n{str(jira_info)[:600]}..."}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*CI Status:* {str(ci_status)}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"🤖 *RAG Standards Check:*\n{str(rag_insight)}"}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "Mifos Unified Intelligence | Phase 5"}]}
        ]

        # Post to Slack
        channel_id = settings.SLACK_ALERT_CHANNEL_ID
        if channel_id:
            await slack_app.client.chat_postMessage(channel=channel_id, blocks=blocks, text=f"PR Alert: {pr_title}")
            logger.info(f"✅ Alert sent to Slack channel {channel_id}")

    except Exception as e:
        logger.error(f"❌ Processing error in Watchdog Loop: {e}")


# --- 2. EXPOSE WEBHOOKS ---

async def slack_endpoint(req: Request):
    return await app_handler.handle(req)


async def github_webhook(request: Request):
    await verify_github_signature(request)
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    if event == "pull_request":
        action = payload.get("action")
        # Trigger on open, reopen, or synchronize (new commits)
        if action in ["opened", "reopened", "synchronize"]:
            logger.info(f"📥 Auditing PR #{payload['pull_request']['number']}")
            asyncio.create_task(process_pr_event(payload))

    # 🚨 FIX 1: Return JSONResponse explicitly for Starlette/FastAPI compatibility
    return JSONResponse({"status": "processing"})


# --- 3. SERVER SETUP ---
target_app = None
try:
    # We grab the 'http_app' from the imported mcp object
    raw_app = mcp.http_app if not callable(mcp.http_app) else mcp.http_app()

    if hasattr(raw_app, "app"):
        target_app = raw_app.app
    else:
        target_app = raw_app

    # Add Custom Routes
    target_app.add_route("/slack/events", slack_endpoint, methods=["POST"])
    target_app.add_route("/github/webhook", github_webhook, methods=["POST"])

    logger.info("✅ Successfully registered Webhook routes.")

except Exception as e:
    logger.error(f"❌ Route registration failed: {e}")
    raise e

# --- 4. RUN SERVER ---
if __name__ == "__main__":
    logger.info("🚀 Starting Mifos Unified Watchdog on Port 3000...")
    uvicorn.run(target_app, host="0.0.0.0", port=3000)