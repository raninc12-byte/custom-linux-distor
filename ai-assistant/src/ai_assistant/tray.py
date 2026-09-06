"""XFCE panel tray icon: chat, system helper, model manager, quit."""
from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3
    HAVE_APPINDICATOR = True
except (ImportError, ValueError):
    HAVE_APPINDICATOR = False

from gi.repository import GLib, Gtk  # noqa: E402

from ai_assistant import system_helper  # noqa: E402
from ai_assistant.chat_window import show_chat_window  # noqa: E402


def _show_text_dialog(title: str, text: str) -> None:
    dialog = Gtk.MessageDialog(
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(text)
    dialog.run()
    dialog.destroy()


def _run_system_helper(_item) -> None:
    def worker():
        try:
            explanation = system_helper.explain_recent_errors()
        except Exception as exc:  # noqa: BLE001 - surface any error to the user
            explanation = f"System helper failed: {exc}"
        GLib.idle_add(_show_text_dialog, "System Helper", explanation)

    threading.Thread(target=worker, daemon=True).start()


def _open_chat(_item) -> None:
    # Runs on the GTK main thread already (menu activate callback), and the
    # tray owns the single Gtk.main() loop, so just show the window here.
    show_chat_window()


def _open_model_manager(_item) -> None:
    from ai_assistant.model_manager_window import show_model_manager_window
    show_model_manager_window()


def build_menu() -> Gtk.Menu:
    menu = Gtk.Menu()

    chat_item = Gtk.MenuItem(label="Open Chat")
    chat_item.connect("activate", _open_chat)
    menu.append(chat_item)

    helper_item = Gtk.MenuItem(label="Explain Recent Errors")
    helper_item.connect("activate", _run_system_helper)
    menu.append(helper_item)

    models_item = Gtk.MenuItem(label="Model Manager")
    models_item.connect("activate", _open_model_manager)
    menu.append(models_item)

    menu.append(Gtk.SeparatorMenuItem())

    quit_item = Gtk.MenuItem(label="Quit")
    quit_item.connect("activate", lambda _i: Gtk.main_quit())
    menu.append(quit_item)

    menu.show_all()
    return menu


def run_tray() -> None:
    menu = build_menu()
    if HAVE_APPINDICATOR:
        indicator = AppIndicator3.Indicator.new(
            "ai-assistant", "aibase-assistant",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        indicator.set_menu(menu)
    else:
        # Fallback: no tray protocol support, just open the chat window.
        _open_chat(None)
    Gtk.main()
