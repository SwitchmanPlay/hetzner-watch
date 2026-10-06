# hetzner-watch

Checks Hetzner dedicated-server configurators every 5 minutes (GitHub Actions) and sends a Telegram message when a server becomes orderable ("Order now"), and again when it disappears.

How it works: the configurator page is a JS app, so `curl | grep` sees nothing. The page itself reads two JSON files:

- `https://www.hetzner.com/dedicated-rootserver/<server>/configurator/getServerConfig/` — variants, product IDs, datacenters
- `https://www.hetzner.com/_resources/app/data/app/live_data_upfront.json` — product IDs currently in stock → datacenters

`check.py` applies the same rules as the site's `configurator.js`. No browser needed.

## Setup

1. In Telegram, talk to **@BotFather** → `/newbot` → copy the token.
2. Open your new bot and press **Start**.
3. Set chat IDs: `gh secret set TELEGRAM_CHAT_ID --body "id1,id2"` (each person presses Start in the bot).
4. Run `./setup_telegram.sh` and paste the token.

## Watch other servers

Set a repo variable `SERVERS` (comma-separated), e.g. `ex44,ex131`:

```
gh variable set SERVERS --body "ex44,ex131"
```

## Run locally

```
SERVERS=ex44,ex131 python3 check.py
```
