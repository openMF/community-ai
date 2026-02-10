import logging
import re
import hmac
import hashlib
import json  # Added json import
import asyncio
import uvicorn
from typing import Dict, Any

from fastapi import Request, HTTPException, FastAPI
from starlette.responses import JSONResponse
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from dotenv import load_dotenv

# --- AI & LANGCHAIN IMPORTS ---
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool, StructuredTool
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

# --- IMPORT TOOLS ---
from MCP_Enhancement.tools.mifos_tools import (
    mcp,
    get_issue_context,
    search_knowledge_base,
    check_ci_status,
    get_pr_details,
    post_github_comment,
    get_recent_slack_messages,
    create_issue_logic,
    get_settings,
    process_jira_webhook,
    # Tool Wrappers
    tool_jira_context,
    tool_knowledge_base,
    tool_ci_check,
    tool_pr_details,
    tool_post_pr_comment,
    tool_create_jira,
    tool_get_chat_history,
    tool_search_client,
    tool_loan_details
)

load_dotenv()
settings = get_settings()

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mifos-orchestrator")

# Initialize Slack
slack_app = AsyncApp(
    token=settings.SLACK_BOT_TOKEN,
    signing_secret=settings.SLACK_SIGNING_SECRET
)
app_handler = AsyncSlackRequestHandler(slack_app)

# =========================================================
# 🧠 THE AI AGENT BRAIN
# =========================================================

tools = [
    StructuredTool.from_function(tool_jira_context),
    StructuredTool.from_function(tool_knowledge_base),
    StructuredTool.from_function(tool_ci_check),
    StructuredTool.from_function(tool_pr_details),
    StructuredTool.from_function(tool_post_pr_comment),
    StructuredTool.from_function(tool_create_jira),
    StructuredTool.from_function(tool_get_chat_history),
    StructuredTool.from_function(tool_search_client),
    StructuredTool.from_function(tool_loan_details)
]

llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    api_key=settings.OPENAI_API_KEY,
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are the Mifos AI DevOps Assistant. You help developers by interacting with Jira, GitHub, Slack, Fineract, and Documentation.\n"
     "RULES:\n"
     "1. If a user mentions a Jira Key (e.g., 'WEB-95'), use 'tool_jira_context'.\n"
     "2. If asked about a PR (e.g. 'pr 53'), use 'tool_pr_details' AND 'tool_ci_check' to give a full report.\n"
     "3. SECURITY: If using 'tool_post_pr_comment' or 'tool_create_jira', you MUST pass the user's ID string (provided in context) to the 'ctx' argument.\n"
     "4. If asked about banking data (e.g., 'search for client', 'check loan'), use 'tool_search_client' or 'tool_loan_details'.\n"
     "5. 🧠 KNOWLEDGE BASE: If asked a technical question (e.g., 'how to deploy', 'requirements', 'architecture', 'error 404'), use 'tool_knowledge_base' to find the answer in the docs.\n"
     "6. Always be concise and helpful."),
    ("user", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# =========================================================
# 👂 SLACK LISTENER (CHAT)
# =========================================================

@slack_app.event("app_mention")
async def handle_mentions(event, say):
    user_text = event.get("text", "")
    channel_id = event.get("channel")
    user_id = event.get("user")

    context_data = ""
    if "summarize" in user_text.lower() or "context" in user_text.lower():
        history = get_recent_slack_messages(channel_id, count=10)
        context_data = f"\n\n[RECENT CHAT HISTORY]:\n{history}"

    security_instruction = f"\n[SYSTEM DATA: Requesting User ID is {user_id}. Use this for 'ctx' arguments.]"

    try:
        await say(f"🤖 Processing request for <@{user_id}>...")
        response = await agent_executor.ainvoke({"input": user_text + context_data + security_instruction})
        await say(response["output"])
    except Exception as e:
        await say(f"❌ Error processing request: {e}")


# =========================================================
# 🛡️ GITHUB WEBHOOKS (WATCHDOG) - FIXED & ROBUST
# =========================================================

def verify_signature(payload_body: bytes, secret_token: str, signature_header: str):
    """Verify that the payload was sent from GitHub by validating SHA256."""
    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing!")

    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")


async def process_pr_event(payload: Dict):
    """Background task to process PR logic so we don't block the webhook response."""
    try:
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        pr_title = pr.get("title", "")
        pr_url = pr.get("html_url")
        user = pr.get("user", {}).get("login", "Unknown")

        logger.info(f"🕵️ Watchdog Analyzing PR #{pr_number}: {pr_title}")

        # 1. Regex Extraction
        match = re.search(r'[A-Z]+-\d+', pr_title)
        jira_key = match.group(0) if match else None

        # 2. Fetch Context (Simulated or Real)
        if jira_key:
            jira_info = get_issue_context(jira_key)
        else:
            jira_info = "⚠️ No Jira Ticket Linked in Title."

        # 3. Intelligent Analysis
        # Note: These are blocking calls, running them here in background task is safe
        rag_insight = search_knowledge_base(f"Provide architectural guidance for: {pr_title}")
        ci_status = check_ci_status(pr_number)

        # 4. Construct Slack Message
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": f"🛡️ Watchdog Report: {user}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"<{pr_url}|*PR #{pr_number}: {pr_title}*>"}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Jira Context:*\n{str(jira_info)[:600]}..."}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*CI Status:* {str(ci_status)}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"🤖 *RAG Standards Check:*\n{str(rag_insight)}"}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "Mifos Unified Intelligence | Phase 6"}]}
        ]

        # 5. Send to Slack
        channel_id = settings.SLACK_ALERT_CHANNEL_ID
        if channel_id:
            await slack_app.client.chat_postMessage(channel=channel_id, blocks=blocks, text=f"PR Alert: {pr_title}")
            logger.info(f"✅ Alert sent to Slack channel {channel_id}")
        else:
            logger.warning("⚠️ SLACK_ALERT_CHANNEL_ID is not set in .env")

    except Exception as e:
        logger.error(f"❌ Watchdog Error in Background Task: {e}")


async def github_webhook(request: Request):
    """Main Endpoint for GitHub Webhooks"""
    try:
        # 1. READ BODY ONCE (Fix for stream consumption bug)
        body_bytes = await request.body()

        # 2. VERIFY SIGNATURE
        secret = settings.GITHUB_WEBHOOK_SECRET
        if secret:
            signature_header = request.headers.get("X-Hub-Signature-256")
            verify_signature(body_bytes, secret, signature_header)

        # 3. PARSE JSON
        payload = json.loads(body_bytes)
        event_type = request.headers.get("X-GitHub-Event")

        # 4. FILTER EVENTS
        if event_type == "pull_request":
            action = payload.get("action")
            if action in ["opened", "reopened", "synchronize", "edited"]:
                logger.info(f"📥 Received Valid PR Event: #{payload['pull_request']['number']}")
                # Fire and forget - return 200 immediately to GitHub
                asyncio.create_task(process_pr_event(payload))

        return JSONResponse({"status": "accepted"})

    except Exception as e:
        logger.error(f"❌ Webhook Error: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


# =========================================================
# 🆕 JIRA WEBHOOKS (NOTIFICATIONS)
# =========================================================

async def jira_webhook_endpoint(request: Request):
    try:
        payload = await request.json()
        result = process_jira_webhook(payload)
        logger.info(f"📨 Jira Webhook Processed: {result}")
        return JSONResponse({"status": "ok", "message": result})
    except Exception as e:
        logger.error(f"❌ Jira Webhook Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def slack_endpoint(req: Request):
    return await app_handler.handle(req)


# =========================================================
# 🚀 SERVER SETUP
# =========================================================

target_app = FastAPI(title="Mifos Unified Agent Server")

# Routes
target_app.add_route("/slack/events", slack_endpoint, methods=["POST"])
target_app.add_route("/github/webhook", github_webhook, methods=["POST"])
target_app.add_route("/webhooks/jira", jira_webhook_endpoint, methods=["POST"])

if __name__ == "__main__":
    logger.info("🚀 Starting Mifos Unified Agent on Port 3000...")
    # Using '0.0.0.0' allows external tools (ngrok) to connect
    uvicorn.run(target_app, host="0.0.0.0", port=3000)