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
    """
    wait_for_file(filepath, poll_interval)

    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        # Jump to end — we only care about NEW lines
        fh.seek(0, os.SEEK_END)

        while True:
            line = fh.readline()

            if not line:
                # No new data — check for log rotation (file got smaller)
                try:
                    current_size = os.path.getsize(filepath)
                except OSError:
                    # File was deleted — wait for it to come back
                    print("⚠️  Log file removed. Waiting for it to reappear…")
                    fh.close()
                    wait_for_file(filepath, poll_interval)
                    # Re-open from the generator (recursive-ish via new call)
                    yield from tail_log(filepath, keywords, poll_interval)
                    return

                if current_size < fh.tell():
                    # File was truncated / rotated — start from the beginning
                    print("🔄 Log file rotated. Re-reading from start.")
                    fh.seek(0)
                    continue

                time.sleep(poll_interval)
                continue

            line = line.rstrip("\n\r")
            if line and contains_keywords(line, keywords):
                yield line
