import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

# Import your Central Orchestrator
# This assumes you have an 'agent_start.py' or similar that handles the LLM logic
from agents.agent_start import handle_user_query

try:
    from MCP_Enhancement.src.core.config import get_settings
except ImportError:
    from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize the Bolt App
# This handles the Slack Events API (mentions, messages)
app = App(
    token=settings.SLACK_BOT_TOKEN.get_secret_value(),
    signing_secret=settings.SLACK_SIGNING_SECRET.get_secret_value()
)
handler = SlackRequestHandler(app)

@app.event("app_mention")
def handle_app_mentions(event, say):
    """
    The Entry Point: Catches a mention in Slack, passes the text 
    to the Orchestrator, and speaks the answer back.
    """
    user_query = event.get("text")
    channel_id = event.get("channel")
    thread_ts = event.get("ts")

    logger.info(f"📥 Slack Mention from {event.get('user')}: {user_query}")

    try:
        # 1. Send the raw message to the Central Orchestrator
        # The Orchestrator decides which tool from mifos_tools.py to use.
        response_text = handle_user_query(user_query)

        # 2. Post the response back to Slack in the same thread
        say(text=response_text, thread_ts=thread_ts)

    except Exception as e:
        logger.error(f"Error processing Slack mention: {e}")
        say(text="Sorry, I encountered an error while processing that request.", thread_ts=thread_ts)

@app.message(".*")
def handle_all_messages(message, say):
    """
    Optional: Catch all messages in a specific 'watch' channel 
    or DMs if needed.
    """
    pass

# Helper function to post messages from other parts of the system (like the Watchdog)
def post_to_slack(channel_id: str, text: str, blocks: list = None):
    """Directly post to a channel (used by Watchdog for reports)."""
    client = WebClient(token=settings.SLACK_BOT_TOKEN.get_secret_value())
    try:
        client.chat_postMessage(channel=channel_id, text=text, blocks=blocks)
    except SlackApiError as e:
        logger.error(f"Error posting to Slack: {e.response['error']}")