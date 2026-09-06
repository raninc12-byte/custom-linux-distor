"""Tests for system_helper (log collection + explanation, all execution mocked)."""
from __future__ import annotations

import subprocess

from ai_assistant import ollama_client, system_helper


class FakeCompletedProcess:
    def __init__(self, stdout):
        self.stdout = stdout


def test_collect_recent_errors_combines_journal_and_failed_units(monkeypatch):
    def fake_run(cmd, **kwargs):
        if cmd[0] == "journalctl":
            return FakeCompletedProcess("some journal error line\n")
        if cmd[0] == "systemctl":
            return FakeCompletedProcess("nginx.service failed\n")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    combined = system_helper.collect_recent_errors()
    assert "some journal error line" in combined
    assert "nginx.service failed" in combined


def test_collect_recent_errors_survives_missing_binaries(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise FileNotFoundError(cmd[0])

    monkeypatch.setattr(subprocess, "run", fake_run)
    combined = system_helper.collect_recent_errors()
    # Should not raise, just return the (mostly empty) template.
    assert "journalctl" in combined


def test_explain_recent_errors_short_circuits_when_no_logs(monkeypatch):
    monkeypatch.setattr(system_helper, "collect_recent_errors", lambda: "   \n\n  ")
    result = system_helper.explain_recent_errors()
    assert "No recent errors" in result


def test_explain_recent_errors_calls_chat_with_system_prompt(monkeypatch):
    monkeypatch.setattr(system_helper, "collect_recent_errors", lambda: "boom: disk full")
    captured = {}

    def fake_chat(messages, model=None):
        captured["messages"] = messages
        return "Disk is full. Suggested command: sudo journalctl --vacuum-size=200M"

    monkeypatch.setattr(ollama_client, "chat", fake_chat)
    result = system_helper.explain_recent_errors()

    assert "Suggested command:" in result
    assert captured["messages"][0]["role"] == "system"
    assert "boom: disk full" in captured["messages"][1]["content"]
