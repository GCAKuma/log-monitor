"""
main.py — Entry point for the Log Monitoring & Alert Tool.

Wires together config, watcher, and alert modules:
    1. Loads settings from .env
    2. Tails the configured log file for keyword matches
    3. Sends a webhook alert for every matching line
"""

import sys
from app.config import get_config
from app.watcher import tail_log
from app.alert import send_alert


def main() -> None:
    # ---- Load configuration ----
    try:
        config = get_config()
    except ValueError as err:
        print(f"⚠️  Configuration error: {err}")
        sys.exit(1)

    log_file = config["log_file_path"]
    webhook_url = config["webhook_url"]
    keywords = config["alert_keywords"]
    poll_interval = config["poll_interval"]

    print("=" * 50)
    print("  📋 Log Monitor & Alert Tool")
    print("=" * 50)
    print(f"  Log file     : {log_file}")
    print(f"  Keywords     : {', '.join(keywords)}")
    print(f"  Poll interval: {poll_interval}s")
    print(f"  Webhook URL  : {webhook_url[:40]}…")
    print("=" * 50)
    print("Watching for new log entries… (Ctrl+C to stop)\n")

    # ---- Tail the log and alert on matches ----
    try:
        for matched_line in tail_log(log_file, keywords, poll_interval):
            print(f"🔔 Match found: {matched_line}")
            send_alert(webhook_url, matched_line)
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully. Goodbye!")


if __name__ == "__main__":
    main()
