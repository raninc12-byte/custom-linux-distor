# AI Assistant Architecture

## Overview

`ai-assistant` is a small Python/GTK app (`ai-assistant/`) that talks only to
a local [Ollama](https://ollama.com/) daemon (`http://127.0.0.1:11434`) —
no cloud API calls. It runs three ways from the same entry point
(`ai_assistant.main`):

- `ai-assistant --tray` — XFCE panel tray icon (autostarted for every user,
  see `airootfs-profile/airootfs/etc/skel/.config/autostart/ai-assistant.desktop`)
- `ai-assistant --chat` — chat window standalone
- `ai-assistant --models` — model manager window standalone
- `ai-assistant --explain-errors` — CLI one-shot system helper output

## Modules

| File | Responsibility |
|---|---|
| `ollama_client.py` | HTTP client for the local Ollama API: chat, list/pull/delete models |
| `system_helper.py` | Gathers `journalctl -p err` + `systemctl --failed`, asks the local model to explain, **never executes** anything |
| `model_manager.py` | Curated model catalog + install/remove wrapper |
| `chat_window.py`, `model_manager_window.py`, `tray.py` | GTK UI |

## Tests

`ollama_client.py`, `model_manager.py`, and `system_helper.py` have no GTK
dependency, so they're covered by real unit tests in `ai-assistant/tests/`
(all network/subprocess calls mocked - no live Ollama or Linux system
needed). Run them from `ai-assistant/`:

```bash
pip install -e .[test]
pytest -q
```

The GTK-facing modules (`chat_window.py`, `model_manager_window.py`,
`tray.py`) are not unit tested - they need a real X11/Wayland display and
PyGObject/AppIndicator3, so they're only verified by manual testing on the
built ISO.

## Security boundary: the system helper never runs commands

`system_helper.explain_recent_errors()` sends local log text to the local
model and returns its reply as **plain text only**. The tray/chat UI only
ever displays this text in a dialog — nothing in this codebase passes model
output to `subprocess`/`os.system`/`eval`. This matters because both ends of
that pipe are technically untrusted: log content could contain attacker
crafted lines, and the model's own reply must never be auto-executed on the
strength of an LLM's suggestion.

## RAM-tiered default model

`aibase-first-boot-setup` (systemd oneshot, see BUILDING.md) reads
`/proc/meminfo` and pulls:
- `llama3.2:3b-instruct-q4_K_M` on systems with < 15GB RAM
- `llama3.1:8b-instruct-q4_K_M` on systems with >= 15GB RAM

into Ollama, then records the choice in `/etc/aibase/default-model`, which
`ollama_client.get_default_model()` reads at runtime. Users can install
additional/different models any time via the Model Manager window without
touching a terminal.

## GPU acceleration

No GPU-specific code lives in `ai-assistant` — Ollama automatically uses the
NVIDIA GPU via CUDA if the `nvidia-open` driver is active (decided by
`aibase-gpu-detect` at first boot, see BUILDING.md), and falls back to CPU
inference otherwise.
