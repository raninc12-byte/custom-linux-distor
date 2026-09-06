"""Tests for model_manager (curated catalog + thin wrappers over ollama_client)."""
from __future__ import annotations

from ai_assistant import model_manager, ollama_client


def test_catalog_entries_have_label_and_tag():
    assert model_manager.CATALOG
    for entry in model_manager.CATALOG:
        assert "label" in entry
        assert "tag" in entry


def test_installed_models_returns_names(monkeypatch):
    monkeypatch.setattr(
        ollama_client,
        "list_models",
        lambda: [{"name": "llama3.2:3b-instruct-q4_K_M"}, {"name": "qwen2.5-coder:7b"}],
    )
    assert model_manager.installed_models() == [
        "llama3.2:3b-instruct-q4_K_M",
        "qwen2.5-coder:7b",
    ]


def test_install_delegates_to_pull_model(monkeypatch):
    monkeypatch.setattr(ollama_client, "pull_model", lambda tag: iter(["downloading", "done"]))
    assert list(model_manager.install("llama3.2:3b-instruct-q4_K_M")) == ["downloading", "done"]


def test_remove_delegates_to_delete_model(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama_client, "delete_model", lambda tag: calls.append(tag))
    model_manager.remove("llama3.2:3b-instruct-q4_K_M")
    assert calls == ["llama3.2:3b-instruct-q4_K_M"]


def test_recommended_tag_for_system_delegates_to_get_default_model(monkeypatch):
    monkeypatch.setattr(ollama_client, "get_default_model", lambda: "llama3.1:8b-instruct-q4_K_M")
    assert model_manager.recommended_tag_for_system() == "llama3.1:8b-instruct-q4_K_M"
