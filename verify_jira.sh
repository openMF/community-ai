import os
import requests
from dotenv import load_dotenv

# Load .env file (adjust path if needed)
load_dotenv("./MCP_Enhancement/.env")

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

print("🔍 Verifying Jira Connection...")
print("---------------------------------------")

# 1. Validate environment variables
if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
    print("❌ ERROR: Missing Jira configuration.")
    print("💡 Ensure JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN are set in your .env file.")
    exit(1)

# 2. Test Jira authentication (Jira Cloud uses email + API token)
try:
    response = requests.get(
        f"{JIRA_URL}/rest/api/3/myself",
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        timeout=10
    )

    if response.status_code == 200:
        user = response.json().get("displayName", JIRA_EMAIL)
        print(f"✅ SUCCESS: Jira authenticated as {user}")
        print(f"📊 Status: Connected to {JIRA_URL}")
    elif response.status_code == 401:
        print("❌ FAILED: Authentication error (401)")
        print("💡 Tip: Double-check your email and API token.")
        print("   Note: Use your Atlassian account email, not Slack or GitHub ID.")
    elif response.status_code == 404:
        print("❌ FAILED: Jira URL not found (404)")
        print("💡 Tip: JIRA_URL should look like https://your-domain.atlassian.net")
    else:
        print(f"❌ FAILED: Jira rejected the connection (HTTP {response.status_code})")

except requests.RequestException as e:
    print("❌ ERROR: Could not connect to Jira.")
    print(f"💡 Details: {e}")

print("---------------------------------------")
