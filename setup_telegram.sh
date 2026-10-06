#!/usr/bin/env bash
# Stores the Telegram bot token as a GitHub secret and triggers a test run.
# The token stays on your machine. Chat IDs live in the TELEGRAM_CHAT_ID secret
# (comma-separated); everyone listed must press Start in the bot once.
set -euo pipefail
REPO=SwitchmanPlay/hetzner-watch

read -rsp "Paste the bot token from @BotFather: " TOKEN; echo
[ -n "$TOKEN" ] || { echo "No token given."; exit 1; }

curl -fsS "https://api.telegram.org/bot${TOKEN}/getMe" >/dev/null \
  || { echo "Telegram rejected this token. Check it and try again."; exit 1; }

printf '%s' "$TOKEN" | gh secret set TELEGRAM_BOT_TOKEN -R "$REPO"
gh workflow run watch.yml -R "$REPO" -f send_test=true
echo "Done. A test message should arrive in Telegram within a minute."
