"""Simple GTK chat window talking to the local model."""
from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from ai_assistant import ollama_client  # noqa: E402


class ChatWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="AI Assistant")
        self.set_default_size(480, 560)
        self._messages: list[dict] = []

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(box)

        self._history_buffer = Gtk.TextBuffer()
        history_view = Gtk.TextView(buffer=self._history_buffer)
        history_view.set_editable(False)
        history_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        scroller.add(history_view)
        box.pack_start(scroller, True, True, 6)

        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._entry = Gtk.Entry()
        self._entry.set_placeholder_text("Ask the local AI assistant...")
        self._entry.connect("activate", self._on_send)
        entry_box.pack_start(self._entry, True, True, 6)

        send_btn = Gtk.Button(label="Send")
        send_btn.connect("clicked", self._on_send)
        entry_box.pack_start(send_btn, False, False, 6)
        box.pack_start(entry_box, False, False, 6)

    def _append(self, speaker: str, text: str) -> None:
        end_iter = self._history_buffer.get_end_iter()
        self._history_buffer.insert(end_iter, f"{speaker}: {text}\n\n")

    def _on_send(self, _widget) -> None:
        text = self._entry.get_text().strip()
        if not text:
            return
        self._entry.set_text("")
        self._append("You", text)
        self._messages.append({"role": "user", "content": text})
        threading.Thread(target=self._get_reply, daemon=True).start()

    def _get_reply(self) -> None:
        try:
            reply = ollama_client.chat(self._messages)
        except ollama_client.OllamaError as exc:
            reply = str(exc)
        self._messages.append({"role": "assistant", "content": reply})
        GLib.idle_add(self._append, "Assistant", reply)


def show_chat_window(standalone: bool = False) -> None:
    """Shows the chat window. Set standalone=True only when there is no
    existing Gtk.main() loop already running (e.g. launched directly, not
    from the tray icon)."""
    win = ChatWindow()
    if standalone:
        win.connect("destroy", Gtk.main_quit)
    win.show_all()
    if standalone:
        Gtk.main()
