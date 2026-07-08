"""
test_watcher.py — Unit tests for the watcher module.

Tests:
    • Keyword detection (single keyword, multiple keywords, case-insensitivity)
    • Lines with no keywords are ignored
    • Empty lines are handled gracefully
"""

import os
import tempfile
import threading
import time

import pytest

from app.watcher import contains_keywords, tail_log


# ──────────────────────────────────────────────
#  Tests for contains_keywords()
# ──────────────────────────────────────────────


class TestContainsKeywords:
    """Verify that keyword matching works correctly."""

    def test_single_keyword_match(self):
        assert contains_keywords("2026-07-08 ERROR: disk full", ["ERROR"]) is True

    def test_single_keyword_no_match(self):
        assert contains_keywords("2026-07-08 INFO: all good", ["ERROR"]) is False

    def test_case_insensitive_match(self):
        assert contains_keywords("error: something broke", ["ERROR"]) is True

    def test_multiple_keywords_first_matches(self):
        line = "CRITICAL: out of memory"
        assert contains_keywords(line, ["ERROR", "CRITICAL", "FATAL"]) is True

    def test_multiple_keywords_last_matches(self):
        line = "FATAL: unrecoverable"
        assert contains_keywords(line, ["ERROR", "CRITICAL", "FATAL"]) is True

    def test_multiple_keywords_none_match(self):
        line = "DEBUG: routine check"
        assert contains_keywords(line, ["ERROR", "CRITICAL", "FATAL"]) is False

    def test_empty_line(self):
        assert contains_keywords("", ["ERROR"]) is False

    def test_empty_keywords_list(self):
        assert contains_keywords("ERROR: something", []) is False

    def test_partial_keyword_match(self):
        """Keywords can match as substrings (e.g. 'ERR' in 'ERROR')."""
        assert contains_keywords("2026-07-08 ERROR: oops", ["ERR"]) is True

    def test_keyword_in_middle_of_line(self):
        line = "app[1234]: unexpected ERROR encountered in module X"
        assert contains_keywords(line, ["ERROR"]) is True


# ──────────────────────────────────────────────
#  Tests for tail_log()
# ──────────────────────────────────────────────


class TestTailLog:
    """Integration-style tests for the log tailing generator."""

    def test_new_error_lines_are_yielded(self, tmp_path):
        """
        Append lines to a temp log file *after* tail_log starts;
        verify that matching lines are yielded.
        """
        log_file = tmp_path / "test.log"
        log_file.write_text("")  # create empty file

        results = []

        def writer():
            """Simulate an application writing to the log file."""
            time.sleep(0.5)  # give tailer time to start
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("INFO: startup complete\n")
                f.write("ERROR: disk full\n")
                f.write("WARNING: high memory\n")
                f.write("CRITICAL: service down\n")
                f.flush()

        def reader():
            """Collect matching lines from tail_log (stop after 2 matches)."""
            for line in tail_log(str(log_file), ["ERROR", "CRITICAL"], poll_interval=0.2):
                results.append(line)
                if len(results) >= 2:
                    break

        writer_thread = threading.Thread(target=writer, daemon=True)
        reader_thread = threading.Thread(target=reader, daemon=True)

        reader_thread.start()
        writer_thread.start()

        reader_thread.join(timeout=10)

        assert len(results) == 2
        assert "ERROR: disk full" in results[0]
        assert "CRITICAL: service down" in results[1]

    def test_ignores_existing_content(self, tmp_path):
        """
        Lines that existed *before* the tailer started should be ignored
        (the watcher seeks to end on open).
        """
        log_file = tmp_path / "test.log"
        log_file.write_text("ERROR: old error that should be ignored\n")

        results = []

        def writer():
            time.sleep(0.5)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("ERROR: new error\n")
                f.flush()

        def reader():
            for line in tail_log(str(log_file), ["ERROR"], poll_interval=0.2):
                results.append(line)
                if len(results) >= 1:
                    break

        writer_thread = threading.Thread(target=writer, daemon=True)
        reader_thread = threading.Thread(target=reader, daemon=True)

        reader_thread.start()
        writer_thread.start()

        reader_thread.join(timeout=10)

        assert len(results) == 1
        assert "new error" in results[0]

    def test_waits_for_file_creation(self, tmp_path):
        """
        If the log file doesn't exist yet, tail_log should wait until
        it appears and then start reading.
        """
        log_file = tmp_path / "delayed.log"
        results = []

        def creator():
            # Step 1: Create the empty file so the tailer can find and open it
            time.sleep(1)
            with open(log_file, "w", encoding="utf-8") as f:
                f.flush()
            # Step 2: Wait for the tailer to open & seek to end, then append
            time.sleep(1)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("ERROR: appeared!\n")
                f.flush()

        def reader():
            for line in tail_log(str(log_file), ["ERROR"], poll_interval=0.3):
                results.append(line)
                if len(results) >= 1:
                    break

        creator_thread = threading.Thread(target=creator, daemon=True)
        reader_thread = threading.Thread(target=reader, daemon=True)

        reader_thread.start()
        creator_thread.start()

        reader_thread.join(timeout=15)

        assert len(results) == 1
        assert "appeared!" in results[0]
