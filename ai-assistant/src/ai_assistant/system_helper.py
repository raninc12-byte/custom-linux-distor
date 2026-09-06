"""Explains recent system errors using the local model.

Security note: this module only ever *displays* a suggested shell command as
text for the user to read and run themselves. It must never eval/exec model
output - the log content sent to the model is untrusted input from the
user's own system, and the model's reply is untrusted output, so both ends
of this pipe are treated as display-only data.
"""
from __future__ import annotations

import subprocess

from ai_assistant import ollama_client

MAX_LOG_CHARS = 6000

SYSTEM_PROMPT = (
    "You are a Linux system troubleshooting assistant running locally on the "
    "user's machine. You will be given recent error logs. Explain in plain "
    "language what likely went wrong, then suggest ONE shell command that "
    "might fix it, clearly labeled 'Suggested command:'. You are not able to "
    "run commands yourself - only suggest them for the user to review and "
    "run manually."
)


def _run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=False
        )
        return result.stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def collect_recent_errors() -> str:
    journal_errors = _run(["journalctl", "-p", "err", "-b", "-n", "100", "--no-pager"])
    failed_units = _run(["systemctl", "--failed", "--no-pager"])
    combined = f"=== journalctl (errors, this boot) ===\n{journal_errors}\n\n" \
               f"=== systemctl --failed ===\n{failed_units}"
    return combined[-MAX_LOG_CHARS:]


def explain_recent_errors() -> str:
    logs = collect_recent_errors()
    if not logs.strip():
        return "No recent errors found in the system journal or failed units."
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Recent system logs:\n\n{logs}"},
    ]
    return ollama_client.chat(messages)
