import os
import logging
import re
import requests
from dotenv import load_dotenv

# Importing your logic from the main agent
from agent_start import (
    get_jira_ticket_details,
    check_jira_for_ui_assets,
    post_mifos_summary
)

load_dotenv()
# Set logging to INFO to see the request flow
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_phase_1_test(repo_owner: str, repo_name: str, pr_number: int):
    print(f"\n🚀 Starting Phase 1 Shadow Test: {repo_name} PR #{pr_number}")
    print("-" * 50)

    # 1. Fetch GitHub PR Info
    github_token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {github_token}"}
    pr_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"

    try:
        pr_resp = requests.get(pr_url, headers=headers)
        pr_resp.raise_for_status()
        pr_data = pr_resp.json()
    except Exception as e:
        print(f"❌ GitHub API Error: {e}")
        return

    pr_title = pr_data.get("title", "")
    pr_body = pr_data.get("body", "") or ""
    print(f"✅ Found PR: {pr_title}")

    # 2. Extract Jira ID (Search Title THEN Body)
    # UPDATED: Added [a-zA-Z] and re.IGNORECASE to catch lowercase like 'web-100'
    jira_pattern = r'([a-zA-Z]+-\d+)'
    jira_match = re.search(jira_pattern, pr_title, re.IGNORECASE) or \
                 re.search(jira_pattern, pr_body, re.IGNORECASE)

    if not jira_match:
        print("❌ No Jira ID found in PR title or description.")
        print("💡 Tip: Manually check the PR to see if a ticket is linked.")
        return

    # UPDATED: Convert to UPPERCASE for Jira API compatibility
    jira_id = jira_match.group(1).upper()
    print(f"🔍 Linking to Jira Ticket: {jira_id}")

    # 3. Use your MCP Tools to fetch Jira context
    print("🛰️ Querying Jira for Consensus and UI Assets...")
    consensus = get_jira_ticket_details(jira_id)
    ui_assets = check_jira_for_ui_assets(jira_id)

    # 4. Synthesize the Librarian Report
    final_report = (
        f"*Project:* Mifos Web-App Integration\n"
        f"*GitHub Source:* PR #{pr_number} - _{pr_title}_\n"
        f"*Jira Reference:* `{jira_id}`\n\n"
        f"--- \n"
        f"*💬 Developer Consensus (Comments):*\n{consensus}\n\n"
        f"*🖼️ Visual Asset Check (Jira Attachments):*\n{ui_assets}\n\n"
        f"--- \n"
        f"*Analysis:* This summary bridges code changes in GitHub with visual proof found in Jira."
    )

    # 5. Send to your Private Slack (Shadow Mode - Private Review)
    print("📤 Sending Draft to your Slack for private review...")

    target_channel = os.getenv("MY_SLACK_ID")

    if not target_channel:
        print("❌ Error: MY_SLACK_ID not found in .env. Cannot send Slack DM.")
        print("\n--- Terminal Preview of Report ---\n")
        print(final_report)
        return

    result = post_mifos_summary(
        title=f"Librarian Synthesis: {jira_id}",
        summary_content=final_report,
        is_draft=True
    )

    print(f"\n🏁 Test Complete: {result}")
    print("-" * 50)


if __name__ == "__main__":
    TARGET_PR_NUMBER = 2717
    run_phase_1_test("openMF", "web-app", TARGET_PR_NUMBER)