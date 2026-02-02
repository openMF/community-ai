import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

print("🔍 Checking GitHub Token...")
print("---------------------------------------")

if not GITHUB_TOKEN:
    print("❌ Status: FAILED (GITHUB_TOKEN not set)")
    print("💡 Tip: Export GITHUB_TOKEN or add it to your .env file.")
    exit(1)

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# 1. Test authentication
resp = requests.get("https://api.github.com/user", headers=headers)

if resp.status_code != 200:
    print("❌ Status: FAILED (Bad Credentials)")
    print("💡 Tip: Check for extra spaces in your token or regenerate it.")
    exit(1)

user_data = resp.json()
username = user_data.get("login")

print(f"✅ Status: VALID (Logged in as {username})")

# 2. Check scopes
scope_resp = requests.get("https://api.github.com/user", headers=headers)
scopes = scope_resp.headers.get("X-OAuth-Scopes", "Not returned")

print(f"📊 Scopes: {scopes}")

# 3. Check org access
org_resp = requests.get("https://api.github.com/orgs/openMF", headers=headers)

if org_resp.status_code == 200:
    print("✅ Org Access: VALID (Can see openMF)")
else:
    print("⚠️ Org Access: RESTRICTED")
    print("💡 Tip: Go to GitHub Settings → Tokens → Configure SSO and authorize 'openMF'.")

print("---------------------------------------")

