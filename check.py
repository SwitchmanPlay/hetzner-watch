#!/usr/bin/env python3
"""Watch Hetzner dedicated-server configurators and ping Telegram when one becomes orderable.

Mirrors the logic of hetzner.com's configurator.js:
  - <server>/configurator/getServerConfig/ lists the variations and their datacenters
  - /_resources/app/data/app/live_data_upfront.json lists in-stock product IDs -> datacenters
A variation is orderable if at least one of its datacenters is enabled.
"""
import json
import os
import sys
import time
import urllib.request

SERVERS = [s.strip().lower() for s in os.environ.get("SERVERS", "ex44").split(",") if s.strip()]
STATE_FILE = os.environ.get("STATE_FILE", "state.json")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")

BASE = "https://www.hetzner.com"
LIVE_URL = f"{BASE}/_resources/app/data/app/live_data_upfront.json"
REGION_IDS = {"NBG1": 1, "FSN1": 2, "HEL1": 5}
REGION_NAMES = {v: k for k, v in REGION_IDS.items()}


def fetch_json(url):
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (hetzner-watch)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # network blips, 5xx, bad JSON
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


def stock_regions(product_id, live):
    """configurator.js Y(): region IDs where any live key contains the numeric product ID."""
    if not product_id:
        return set()
    pid = str(product_id).replace("ROBOT_", "")
    regions = set()
    for key, dcs in live.items():
        if pid in key:
            regions.update(REGION_IDS[dc] for dc in dcs if dc in REGION_IDS)
    return regions


def orderable_variants(server, live):
    """Return [(variant name, [datacenters])] that are orderable right now."""
    cfg = fetch_json(f"{BASE}/dedicated-rootserver/{server}/configurator/getServerConfig/")
    result = []
    for item in cfg["Variations"]["Items"]:
        item_regions = [loc["RegionID"] for loc in item["Locations"]]
        limited = item.get("Limited") or {}
        exclusive = limited.get("LimitedMode") == "Exclusive"
        candidates = []
        if limited.get("Enabled") and limited.get("ProductID"):
            candidates.append(stock_regions(limited["ProductID"], live))
        if not exclusive:
            if item.get("CheckAvailability"):
                candidates.append(stock_regions(item["ProductID"], live))
            else:
                candidates.append(set(item_regions))
        enabled = sorted({r for c in candidates for r in c if r in item_regions})
        if enabled:
            result.append((item.get("Name", item["ProductID"]), [REGION_NAMES.get(r, str(r)) for r in enabled]))
    return result


def send_telegram(text):
    if not (TG_TOKEN and TG_CHAT):
        print("[telegram not configured]", text)
        return
    data = json.dumps({"chat_id": TG_CHAT, "text": text, "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


def main():
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {}

    if os.environ.get("SEND_TEST") == "true":
        send_telegram("✅ Hetzner watcher підключено. Стежу за: " + ", ".join(s.upper() for s in SERVERS))

    live = fetch_json(LIVE_URL)
    for server in SERVERS:
        variants = orderable_variants(server, live)
        available = bool(variants)
        url = f"{BASE}/dedicated-rootserver/{server}/configurator/"
        print(f"{server}: {'AVAILABLE ' + str(variants) if available else 'not available'}")

        was = state.get(server)
        if available and was is not True:
            lines = "\n".join(f"• {name}: {', '.join(dcs)}" for name, dcs in variants)
            send_telegram(f"🟢 {server.upper()} можна замовити!\n{lines}\n\n{url}")
        elif not available and was is True:
            send_telegram(f"🔴 {server.upper()} знову недоступний.\n{url}")
        state[server] = available

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
