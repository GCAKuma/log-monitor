# 📋 Log Monitoring & Alert Tool

A lightweight Python tool that **watches a log file** in real time and **sends alerts** to a Discord or Slack webhook whenever it detects lines containing configurable keywords (e.g. `ERROR`, `CRITICAL`).

---

## ✨ Features

| Feature | Details |
|---|---|
| **Real-time tailing** | Polls the log file for new lines — no external dependencies like `tail -f` |
| **Keyword matching** | Case-insensitive, comma-separated, fully configurable via `.env` |
| **Discord & Slack** | Auto-detects the platform from the webhook URL |
| **Log rotation safe** | Handles file truncation / rotation gracefully |
| **Crash-proof** | Waits patiently if the log file doesn't exist yet |
| **No duplicates** | Only processes lines appended *after* the watcher starts |
| **Dockerized** | Includes a production-ready `Dockerfile` |


---

## 🗂️ Project Structure

```
log-monitor/
├── app/
│   ├── __init__.py
│   ├── watcher.py        # Tails the log file, detects keyword matches
│   ├── alert.py          # Sends webhook alerts (Discord / Slack)
│   └── config.py         # Loads environment variables from .env
├── tests/
│   └── test_watcher.py   # Unit & integration tests
├── logs/
│   └── sample.log        # Sample log file for testing
├── .env.example           # Template for your .env file
├── .gitignore
├── requirements.txt
├── Dockerfile
├── README.md
└── main.py                # Entry point
```

---

## 🚀 Quick Start

### 1. Clone & set up

```bash
cd log-monitor
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` with your real values:

```ini
LOG_FILE_PATH=./logs/sample.log
WEBHOOK_URL=https://discord.com/api/webhooks/123456/abcdef
ALERT_KEYWORDS=ERROR,CRITICAL,FATAL
POLL_INTERVAL=2
```

### 3. Run

```bash
python main.py
```

The tool will start watching the log file. In a **separate terminal**, append a test line:

```bash
echo "2026-07-08 12:05:00 ERROR: test alert" >> logs/sample.log
```

You should see a confirmation in the watcher terminal and receive a webhook notification.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Tests cover:
- Keyword matching (single, multiple, case-insensitive, edge cases)
- Log tailing (new lines detected, old content ignored, file creation wait)

---

## 🐳 Docker

### Build

```bash
docker build -t log-monitor .
```

### Run

Mount your host log file into the container and pass the `.env` file:

```bash
docker run --rm \
  --env-file .env \
  -v /var/log/myapp:/app/logs \
  log-monitor
```

> **Tip:** Set `LOG_FILE_PATH=/app/logs/app.log` in your `.env` to match the mounted path.

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `LOG_FILE_PATH` | ✅ | — | Path to the log file to monitor |
| `WEBHOOK_URL` | ✅ | — | Discord or Slack webhook URL |
| `ALERT_KEYWORDS` | ❌ | `ERROR` | Comma-separated keywords (case-insensitive) |
| `POLL_INTERVAL` | ❌ | `2` | Seconds between poll cycles |

---

## 📝 License

This project is open source and available under the [MIT License](https://opensource.org/licenses/MIT).
