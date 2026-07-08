"""
config.py — Loads configuration from environment variables (.env file).

Environment variables:
    LOG_FILE_PATH   : Path to the log file to monitor.
    WEBHOOK_URL     : Discord/Slack webhook URL for sending alerts.
    ALERT_KEYWORDS  : Comma-separated list of keywords to watch for (default: "ERROR").
    POLL_INTERVAL   : How often (in seconds) to check for new lines (default: 2).
"""

import os
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()


def get_config() -> dict:
    """
    Read and return all configuration values from the environment.
    Raises ValueError if required values are missing.
    """
    log_file_path = os.getenv("LOG_FILE_PATH")
    webhook_url = os.getenv("WEBHOOK_URL")
    alert_keywords_raw = os.getenv("ALERT_KEYWORDS", "ERROR")
    poll_interval = float(os.getenv("POLL_INTERVAL", "2"))

    # --- Validate required settings ---
    if not log_file_path:
        raise ValueError("LOG_FILE_PATH is not set. Add it to your .env file.")
    if not webhook_url:
        raise ValueError("WEBHOOK_URL is not set. Add it to your .env file.")

    # Parse comma-separated keywords into a list and strip whitespace
    alert_keywords = [kw.strip() for kw in alert_keywords_raw.split(",") if kw.strip()]

    return {
        "log_file_path": log_file_path,
        "webhook_url": webhook_url,
        "alert_keywords": alert_keywords,
        "poll_interval": poll_interval,
    }
