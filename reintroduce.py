"""Send a reintroduction message to all configured chat_ids.

Use when subscribers have cleared their chat history with the bot (and
the empty thread has disappeared from their Telegram chat list) or when
recovering after a flood / extended downtime. Sending any message
reinstates the chat entry in the user's chat list — UNLESS the user
blocked the bot. If blocked, Telegram returns HTTP 403 and the only
recovery is for the user to manually unblock and /start the bot.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
import yaml


def load_chat_ids(source: str) -> list[str]:
    if source == "config":
        with open("configs/config_telegram.yaml") as f:
            cfg = yaml.safe_load(f)
        return [str(x) for x in cfg["chat_ids"]]
    if source == "messages":
        path = Path("data/telegram_messages.json")
        if not path.exists():
            return []
        with open(path) as f:
            log = json.load(f)
        seen: list[str] = []
        for entry in log:
            cid = str(entry.get("chat_id"))
            if cid and cid != "None" and cid not in seen:
                seen.append(cid)
        return seen
    raise ValueError(f"unknown source: {source}")


def send_one(token: str, chat_id: str, text: str) -> tuple[str, str]:
    """Returns (outcome, detail) where outcome is 'ok' | 'blocked' | 'error'."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
    except requests.RequestException as e:
        return ("error", f"network: {e}")
    if r.status_code == 200:
        mid = r.json().get("result", {}).get("message_id")
        return ("ok", f"message_id={mid}")
    if r.status_code == 403:
        return ("blocked", r.json().get("description", "Forbidden"))
    return ("error", f"HTTP {r.status_code}: {r.text[:200]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("message", help="Message text (Telegram HTML supported)")
    ap.add_argument(
        "--source",
        choices=["config", "messages"],
        default="config",
        help="Where to read chat_ids from (default: config)",
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds between sends to avoid Telegram rate limits",
    )
    args = ap.parse_args()

    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("BOT_TOKEN env var not set", file=sys.stderr)
        return 2

    chat_ids = load_chat_ids(args.source)
    if not chat_ids:
        print(f"no chat_ids found in source={args.source}", file=sys.stderr)
        return 1

    print(f"Sending reintroduction to {len(chat_ids)} chat(s) from {args.source}...")
    results: dict[str, list[tuple[str, str]]] = {"ok": [], "blocked": [], "error": []}
    for i, cid in enumerate(chat_ids):
        if i:
            time.sleep(args.delay)
        outcome, detail = send_one(token, cid, args.message)
        results[outcome].append((cid, detail))
        sym = {"ok": "✓", "blocked": "🚫", "error": "✗"}[outcome]
        print(f"  {sym} {cid}: {detail}")

    print()
    print(f"  ok:      {len(results['ok'])}")
    print(f"  blocked: {len(results['blocked'])}  (user must manually unblock)")
    print(f"  errors:  {len(results['error'])}")
    if results["blocked"]:
        print("\nBlocked chat_ids (contact out-of-band to unblock):")
        for cid, _ in results["blocked"]:
            print(f"  {cid}")
    return 0 if not results["error"] else 1


if __name__ == "__main__":
    sys.exit(main())
