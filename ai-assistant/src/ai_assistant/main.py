"""Entry point: `ai-assistant --tray|--chat|--models|--explain-errors`."""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(prog="ai-assistant")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tray", action="store_true", help="Run as an XFCE panel tray icon (default)")
    group.add_argument("--chat", action="store_true", help="Open the chat window directly")
    group.add_argument("--models", action="store_true", help="Open the model manager window directly")
    group.add_argument("--explain-errors", action="store_true", help="Print an explanation of recent system errors to stdout")
    args = parser.parse_args()

    if args.explain_errors:
        from ai_assistant import system_helper
        print(system_helper.explain_recent_errors())
        return 0

    if args.chat:
        from ai_assistant.chat_window import show_chat_window
        show_chat_window(standalone=True)
        return 0

    if args.models:
        from ai_assistant.model_manager_window import show_model_manager_window
        show_model_manager_window(standalone=True)
        return 0

    from ai_assistant.tray import run_tray
    run_tray()
    return 0


if __name__ == "__main__":
    sys.exit(main())
