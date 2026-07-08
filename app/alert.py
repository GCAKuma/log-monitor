"""
alert.py — Sends alert messages to a Discord or Slack webhook.

Supports both platforms automatically:
    • Discord expects  {"content": "..."}
    • Slack  expects   {"text": "..."}

The function detects the platform from the URL and formats accordingly.
"""

import requests
from datetime import datetime, timezone


def _build_payload(webhook_url: str, message: str) -> dict:
    """
    Build the JSON payload based on whether the webhook is Discord or Slack.
    Falls back to Discord format if the platform can't be determined.
    """
    if "slack" in webhook_url.lower():
        return {"text": message}
    # Default: Discord-style payload
    return {"content": message}


def send_alert(webhook_url: str, matched_line: str) -> bool:
    """
    POST an alert message to the given webhook URL.

    Args:
        webhook_url:  Full webhook URL (Discord or Slack).
        matched_line: The log line that triggered the alert.

    Returns:
        True if the request succeeded (2xx), False otherwise.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    message = (
        f"🚨 **Log Alert**\n"
        f"**Time:** {timestamp}\n"
        f"**Matched Line:**\n```\n{matched_line}\n```"
    )

    payload = _build_payload(webhook_url, message)

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.ok:
            print(f"✅ Alert sent successfully (HTTP {response.status_code})")
            return True
        else:
            print(
                f"❌ Webhook returned HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )
            return False
    except requests.RequestException as exc:
        print(f"❌ Failed to send alert: {exc}")
        return False
