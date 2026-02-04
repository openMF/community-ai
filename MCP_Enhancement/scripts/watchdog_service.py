import logging
import hmac
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Correct imports based on your file structure
from MCP_Enhancement.tools.mifos_tools import (
    tool_github_details,
    tool_jira_context,
    tool_ci_check,
    tool_ask_mifos_docs,
    get_settings
)
# Assuming you have a slack agent for posting
from MCP_Enhancement.agents.slack_agent import post_to_slack_channel

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mifos-watchdog")

app = FastAPI(title="Mifos Enhancement Agent - Phase 5")
settings = get_settings()

# --- WEBHOOK SECURITY ---

async def verify_signature(request: Request):
    """
    Verifies that the webhook actually came from GitHub using the secret.
    """
    secret_raw = settings.GITHUB_WEBHOOK_SECRET
    if not secret_raw:
        logger.warning("⚠️ GITHUB_WEBHOOK_SECRET not set. Skipping verification.")
        return

    secret = secret_raw.get_secret_value().encode()
    signature = request.headers.get("X-Hub-Signature-256")
    
    if not signature:
        raise HTTPException(status_code=403, detail="Missing X-Hub-Signature-256")
    
    body = await request.body()
    expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        logger.error("❌ Invalid Webhook Signature!")
        raise HTTPException(status_code=403, detail="Invalid signature")

# --- PROACTIVE LOGIC (THE BRAIN) ---

async def process_pr_event(payload: dict):
    """
    The RAG + Jira + GitHub integration logic.
    """
    action = payload.get("action")
    pr_data = payload.get("pull_request", {})
    pr_number = pr_data.get("number")
    pr_title = pr_data.get("title", "")
    pr_body = pr_data.get("body", "")

    if action not in ["opened", "reopened", "synchronize"]:
        return

    logger.info(f"🕵️ Analyzing PR #{pr_number}: {pr_title}")

    # 1. Gather Context using Tools
    jira_info = "No linked ticket found."
    # Extract Ticket ID if present in title/body (e.g., WEB-95)
    import re
    ticket_match = re.search(r'[A-Z]+-\d+', f"{pr_title} {pr_body}")
    if ticket_match:
        ticket_id = ticket_match.group(0)
        jira_info = tool_jira_context(ticket_id)

    # 2. RAG Check (Retrieving from Pinecone)
    # This is the "Bait" logic for WEB-95/GLIM
    rag_context = tool_ask_mifos_docs(f"{pr_title} {pr_body}")

    # 3. CI/CD Status
    ci_status = tool_ci_check(pr_number)

    # 4. Construct Final Report
    report = f"""
🚀 *Watchdog Alert: New PR #{pr_number}*
*Title:* {pr_title}
*CI Status:* {ci_status}

📖 *Linked Jira Ticket Context:*
{jira_info[:500]}...

🧠 *Intelligence Report (RAG):*
{rag_context}

_Source: Mifos Enhancement Agent | Phase 5_
    """

    # 5. Send to Slack
    post_to_slack_channel(settings.SLACK_ALERT_CHANNEL_ID, report)
    logger.info(f"✅ Analysis for PR #{pr_number} sent to Slack.")

# --- ENDPOINTS ---

@app.post("/github/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    # Verify BEFORE processing
    await verify_signature(request)
    
    payload = await request.json()
    
    # Process in background so GitHub gets an immediate 200 OK
    background_tasks.add_task(process_pr_event, payload)
    
    return {"status": "accepted"}

@app.get("/health")
def health_check():
    return {"status": "online", "env": settings.APP_ENV}

if __name__ == "__main__":
    import uvicorn
    # Use port 3000 to match your ngrok setup
    uvicorn.run(app, host="0.0.0.0", port=3000)