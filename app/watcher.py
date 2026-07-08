"""
watcher.py — Tails a log file and detects lines containing alert keywords.

Key behaviour:
    • If the log file doesn't exist yet, the watcher waits and retries.
    • Only *new* lines (appended after the watcher starts) are processed.
    • Each matching line is yielded exactly once (no duplicate alerts).
"""

import os
import time
from typing import Generator, List


def contains_keywords(line: str, keywords: List[str]) -> bool:
    """
    Return True if the line contains ANY of the given keywords (case-insensitive).
    """
    line_upper = line.upper()
    return any(kw.upper() in line_upper for kw in keywords)


def wait_for_file(filepath: str, poll_interval: float = 2.0) -> None:
    """
    Block until *filepath* exists on disk.  Prints a message every cycle
    so the operator knows the watcher is alive.
    """
    while not os.path.exists(filepath):
        print(f"⏳ Waiting for log file to appear: {filepath}")
        time.sleep(poll_interval)
    print(f"✅ Log file found: {filepath}")


def tail_log(
    filepath: str,
    keywords: List[str],
    poll_interval: float = 2.0,
) -> Generator[str, None, None]:
    """
    Tail *filepath* indefinitely, yielding each new line that contains
    one of the *keywords*.

    The generator:
      1. Waits for the file to exist.
      2. Seeks to the end (ignores historical content).
      3. Polls for new content every *poll_interval* seconds.
      4. Handles log rotation (file shrinks / is replaced).

    NOTE: The file is opened and closed on each poll cycle so that
    other processes (or manual edits) can write to it on Windows.
    """
    wait_for_file(filepath, poll_interval)

    # Get initial file size — we only care about NEW lines added after this point
    position = os.path.getsize(filepath)

    while True:
        try:
            current_size = os.path.getsize(filepath)
        except OSError:
            # File was deleted — wait for it to come back
            print("⚠️  Log file removed. Waiting for it to reappear…")
            wait_for_file(filepath, poll_interval)
            position = 0
            continue

        if current_size < position:
            # File was truncated / rotated — start from the beginning
            print("🔄 Log file rotated. Re-reading from start.")
            position = 0

        if current_size > position:
            # New data available — open briefly, read, then close
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                fh.seek(position)
                for line in fh:
                    line = line.rstrip("\n\r")
                    if line and contains_keywords(line, keywords):
                        yield line
                position = fh.tell()
        else:
            time.sleep(poll_interval)
