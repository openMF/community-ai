#!/bin/bash

echo "🔍 Slack Connectivity Test"
echo "---------------------------------------"

# Bot Token Test
if [ -n "$SLACK_BOT_TOKEN" ]; then
  curl -s -X POST \
    -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
    -H "Content-type: application/json" \
    https://slack.com/api/auth.test \
    | grep -q '"ok":true' && echo "✅ Bot Token: VALID" || echo "❌ Bot Token: FAILED"
else
  echo "⚠️  Bot Token not set (SLACK_BOT_TOKEN)"
fi

# App Token Test
if [ -n "$SLACK_APP_TOKEN" ]; then
  curl -s -X POST \
    -H "Authorization: Bearer $SLACK_APP_TOKEN" \
    -H "Content-type: application/json" \
    https://slack.com/api/apps.connections.open \
    | grep -q '"ok":true' && echo "✅ App Token: VALID" || echo "❌ App Token: FAILED"
else
  echo "⚠️  App Token not set (SLACK_APP_TOKEN)"
fi

echo "---------------------------------------"
