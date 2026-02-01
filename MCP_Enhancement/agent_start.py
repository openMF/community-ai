import os
import logging
import requests
import re
from typing import Optional, List, Dict

# Environment & Server
from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn

# Slack & Bolt
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

# Mifos Phase 4 Imports
from MCP_Enhancement.config import get_settings
from MCP_Enhancement.agents.rag_agent import query_docs
from MCP_Enhancement.agents.mifos_document_agent import FineractAgent

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mifos-watchdog")

settings = get_settings()
fineract = FineractAgent()

# Initialize Slack Bolt App
slack_app = AsyncApp(
    token=settings.SLACK_BOT_TOKEN.get_secret_value(),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")  # Still usually a raw env var
)
app_handler = AsyncSlackRequestHandler(slack_app)
api = FastAPI()


# --- HELPER FUNCTIONS ---

def extract_jira_keys(text: str) -> List[str]:
    """Finds unique Jira keys (e.g., MIFOS-123) in a string."""
    if not text: return []
    return list(set(re.findall(r"([A-Z]+-\d+)", text)))


def _build_phase4_blocks(title: str, jira_info: str, rag_context: str, fineract_status: str = None) -> List[Dict]:
    """Builds a high-density Slack UI for Phase 4 Knowledge Aggregation."""
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"🚀 {title}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*1. Jira Context:*\n{jira_info}"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*2. Knowledge Base Insight (RAG):*\n{rag_context}"}}
    ]

    if fineract_status:
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*3. Live System Status:*\n{fineract_status}"}})

    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": "🛡️ *Mifos AI Guardian v4.0*"}]})
    return blocks


# --- CORE LOGIC ---

async def process_github_pr(payload: Dict):
    """The Phase 4 Intelligence Loop."""
    pr = payload.get("pull_request", {})
    pr_title = pr.get("title", "")
    pr_body = pr.get("body", "") or ""
    pr_url = pr.get("html_url")

    # 1. RAG Analysis: What does our documentation say about this change?
    # We query Pinecone using the PR title to find related technical debt or specs.
    knowledge_insight = query_docs(f"Context for PR: {pr_title}. {pr_body[:200]}")

    # 2. Jira Linking
    jira_keys = extract_jira_keys(f"{pr_title} {pr_body}")
    jira_info = "⚠️ No Jira Ticket Linked."
    if jira_keys:
        # We assume you still have your get_jira_ticket_details function logic
        jira_info = f"✅ Linked to `{jira_keys[0]}`. (Summary: {pr_title})"

        # 3. Fineract Live Check (Optional: Only if PR title mentions 'balance' or 'loan')
    fineract_context = None
    if any(keyword in pr_title.lower() for keyword in ["loan", "precision", "decimal"]):
        fineract_context = fineract.search_clients("Test")  # Example probe

    # 4. Final Alert
    channel_id = os.getenv("SLACK_ALERT_CHANNEL_ID")
    await slack_app.client.chat_postMessage(
        channel=channel_id,
        text=f"PR Analysis: {pr_title}",
        blocks=_build_phase4_blocks(f"PR #{pr.get('number')} Intelligence", jira_info, knowledge_insight,
                                    fineract_context)
    )


# --- API ENDPOINTS ---

@api.post("/slack/events")
async def slack_endpoint(req: Request):
    return await app_handler.handle(req)


@api.post("/github/webhook")
async def github_endpoint(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")
    if event_type == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
        background_tasks.add_task(process_github_pr, payload)
    return {"status": "received"}


# --- SLACK HANDLERS ---

@slack_app.event("app_mention")
async def handle_mentions(body, say):
    text = body["event"]["text"]

    # If user asks "search docs: [query]"
    if "search docs" in text.lower():
        query = text.split("search docs")[-1].strip()
        await say(f"🔎 Querying Pinecone for: _{query}_...")
        answer = query_docs(query)
        await say(f"📚 *Knowledge Base Response:*\n{answer}")

    # If user provides a Jira Key
    elif re.search(r"([A-Z]+-\d+)", text):
        ticket = re.search(r"([A-Z]+-\d+)", text).group(1)
        # Combine Jira and RAG for the manual lookup
        knowledge = query_docs(f"Historical info for {ticket}")
        await say(f"🎫 *Report for {ticket}*:\n{knowledge}")

    else:
        await say("I am the Mifos Guardian. Try '@bot search docs: <topic>' or mention a Jira ID.")


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=3000)