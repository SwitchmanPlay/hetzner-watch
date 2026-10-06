#!/usr/bin/env bash
# Connects the watcher to your Telegram bot: finds your chat ID, stores both as
# GitHub secrets, and triggers a test run. The token stays on your machine.
set -euo pipefail
cd "$(dirname "$0")"

read -rsp "Paste the bot token from @BotFather: " TOKEN; echo
[ -n "$TOKEN" ] || { echo "No token given."; exit 1; }

echo "Looking for your chat with the bot (send it any message first, e.g. /start)..."
CHAT_ID=$(curl -fsS "https://api.telegram.org/bot${TOKEN}/getUpdates" \
  | python3 -c 'import json,sys; u=json.load(sys.stdin).get("result",[]); ids=[(x.get("message") or x.get("my_chat_member") or {}).get("chat",{}).get("id") for x in u]; ids=[i for i in ids if i]; print(ids[-1] if ids else "")')
if [ -z "$CHAT_ID" ]; then
  echo "Couldn't find a chat. Open your bot in Telegram, press Start / send any message, then rerun this script."
  exit 1
fi
echo "Found chat ID: $CHAT_ID"

printf '%s' "$TOKEN"   | gh secret set TELEGRAM_BOT_TOKEN
printf '%s' "$CHAT_ID" | gh secret set TELEGRAM_CHAT_ID
gh workflow run watch.yml -f send_test=true
echo "Done. A test message should arrive in Telegram within a minute."
