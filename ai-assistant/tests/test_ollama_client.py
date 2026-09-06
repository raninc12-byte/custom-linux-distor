"""Tests for the Ollama HTTP client (all network calls mocked - no real daemon needed)."""
from __future__ import annotations

import pytest
import requests

from ai_assistant import ollama_client


class FakeResponse:
    def __init__(self, json_data=None, status_code=200, lines=None):
        self._json = json_data or {}
        self.status_code = status_code
        self._lines = lines or []

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._json

    def iter_lines(self):
        return iter(self._lines)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_get_default_model_reads_file(tmp_path, monkeypatch):
    model_file = tmp_path / "default-model"
    model_file.write_text("llama3.1:8b-instruct-q4_K_M\n", encoding="utf-8")
    monkeypatch.setattr(ollama_client, "DEFAULT_MODEL_FILE", str(model_file))
    assert ollama_client.get_default_model() == "llama3.1:8b-instruct-q4_K_M"


def test_get_default_model_falls_back_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(ollama_client, "DEFAULT_MODEL_FILE", str(tmp_path / "missing"))
    assert ollama_client.get_default_model() == "llama3.2:3b-instruct-q4_K_M"


def test_is_available_true(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse())
    assert ollama_client.is_available() is True


def test_is_available_false_on_connection_error(monkeypatch):
    def raise_conn_error(*a, **k):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(requests, "get", raise_conn_error)
    assert ollama_client.is_available() is False


def test_list_models_returns_model_list(monkeypatch):
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: FakeResponse({"models": [{"name": "llama3.2:3b"}]})
    )
    assert ollama_client.list_models() == [{"name": "llama3.2:3b"}]


def test_list_models_raises_ollama_error_on_network_failure(monkeypatch):
    def raise_timeout(*a, **k):
        raise requests.Timeout("slow")

    monkeypatch.setattr(requests, "get", raise_timeout)
    with pytest.raises(ollama_client.OllamaError):
        ollama_client.list_models()


def test_pull_model_streams_status_lines(monkeypatch):
    lines = [b'{"status": "downloading"}', b'{"status": "verifying"}', b'']
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse(lines=lines))
    statuses = list(ollama_client.pull_model("llama3.2:3b"))
    assert statuses == ["downloading", "verifying"]


def test_delete_model_raises_ollama_error_on_failure(monkeypatch):
    monkeypatch.setattr(requests, "delete", lambda *a, **k: FakeResponse(status_code=500))
    with pytest.raises(ollama_client.OllamaError):
        ollama_client.delete_model("llama3.2:3b")


def test_chat_returns_message_content(monkeypatch):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **k: FakeResponse({"message": {"content": "hello there"}}),
    )
    assert ollama_client.chat([{"role": "user", "content": "hi"}]) == "hello there"


def test_chat_raises_ollama_error_when_unreachable(monkeypatch):
    def raise_conn_error(*a, **k):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(requests, "post", raise_conn_error)
    with pytest.raises(ollama_client.OllamaError):
        ollama_client.chat([{"role": "user", "content": "hi"}])
