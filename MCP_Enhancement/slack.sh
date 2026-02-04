#!/bin/bash

# Load variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🔍 Starting Slack Configuration Check..."
echo "---------------------------------------"

# 1. Check Bot Token (xoxb)
if [ -z "$SLACK_BOT_TOKEN" ]; then
    echo "❌ Error: SLACK_BOT_TOKEN is missing in .env"
else
    echo "🤖 Testing Bot Token..."
    BOT_TEST=$(curl -s -X POST -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
         -H "Content-type: application/json" \
         https://slack.com/api/auth.test)

    if [[ $BOT_TEST == *"\"ok\":true"* ]]; then
        BOT_NAME=$(echo $BOT_TEST | grep -o '"user":"[^"]*' | cut -d'"' -f4)
        TEAM_NAME=$(echo $BOT_TEST | grep -o '"team":"[^"]*' | cut -d'"' -f4)
        echo "✅ Bot Token is VALID!"
        echo "   -> Identity: $BOT_NAME"
        echo "   -> Workspace: $TEAM_NAME"
    else
        ERROR_MSG=$(echo $BOT_TEST | grep -o '"error":"[^"]*' | cut -d'"' -f4)
        echo "❌ Bot Token FAILED: $ERROR_MSG"
    fi
fi

echo "---------------------------------------"

# 2. Check App Token (xapp)
if [ -z "$SLACK_APP_TOKEN" ]; then
    echo "❌ Error: SLACK_APP_TOKEN is missing in .env"
else
    echo "⚡ Testing App Token (Socket Mode)..."
    # Apps.connections.open is the standard way to test if an xapp token can start a websocket
    APP_TEST=$(curl -s -X POST -H "Authorization: Bearer $SLACK_APP_TOKEN" \
         -H "Content-type: application/json" \
         https://slack.com/api/apps.connections.open)

    if [[ $APP_TEST == *"\"ok\":true"* ]]; then
        echo "✅ App Token is VALID!"
        echo "   -> Connection: Ready for Socket Mode."
    else
        ERROR_MSG=$(echo $APP_TEST | grep -o '"error":"[^"]*' | cut -d'"' -f4)
        echo "❌ App Token FAILED: $ERROR_MSG"
        echo "   (Make sure you added 'connections:write' scope to the App Token)"
    fi
fi

echo "---------------------------------------"
echo "Done."