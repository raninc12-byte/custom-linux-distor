"""Simple GTK window to install/remove local models without a terminal."""
from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from ai_assistant import model_manager, ollama_client  # noqa: E402


class ModelManagerWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="AI Model Manager")
        self.set_default_size(420, 360)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(10)
        self.add(box)

        box.pack_start(Gtk.Label(label="Available models:", xalign=0), False, False, 0)
        for entry in model_manager.CATALOG:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.pack_start(Gtk.Label(label=entry["label"], xalign=0), True, True, 0)
            install_btn = Gtk.Button(label="Install")
            install_btn.connect("clicked", self._on_install, entry["tag"])
            row.pack_start(install_btn, False, False, 0)
            box.pack_start(row, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 6)
        box.pack_start(Gtk.Label(label="Installed models:", xalign=0), False, False, 0)

        self._installed_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.pack_start(self._installed_box, True, True, 0)

        self._status_label = Gtk.Label(label="", xalign=0)
        box.pack_start(self._status_label, False, False, 0)

        self._refresh_installed()

    def _refresh_installed(self) -> None:
        for child in self._installed_box.get_children():
            self._installed_box.remove(child)
        try:
            names = model_manager.installed_models()
        except ollama_client.OllamaError as exc:
            self._status_label.set_text(str(exc))
            return
        if not names:
            self._installed_box.add(Gtk.Label(label="(none yet)", xalign=0))
        for name in names:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.pack_start(Gtk.Label(label=name, xalign=0), True, True, 0)
            remove_btn = Gtk.Button(label="Remove")
            remove_btn.connect("clicked", self._on_remove, name)
            row.pack_start(remove_btn, False, False, 0)
            self._installed_box.add(row)
        self._installed_box.show_all()

    def _on_install(self, _btn, tag: str) -> None:
        self._status_label.set_text(f"Installing {tag}...")

        def worker():
            try:
                for status in model_manager.install(tag):
                    GLib.idle_add(self._status_label.set_text, status)
            except ollama_client.OllamaError as exc:
                GLib.idle_add(self._status_label.set_text, str(exc))
            GLib.idle_add(self._refresh_installed)

        threading.Thread(target=worker, daemon=True).start()

    def _on_remove(self, _btn, name: str) -> None:
        try:
            model_manager.remove(name)
        except ollama_client.OllamaError as exc:
            self._status_label.set_text(str(exc))
        self._refresh_installed()


def show_model_manager_window(standalone: bool = False) -> None:
    """Shows the model manager window. Set standalone=True only when there is
    no existing Gtk.main() loop already running (e.g. launched directly, not
    from the tray icon)."""
    win = ModelManagerWindow()
    if standalone:
        win.connect("destroy", Gtk.main_quit)
    win.show_all()
    if standalone:
        Gtk.main()
