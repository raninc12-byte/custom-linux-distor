"""Thin client for the local Ollama HTTP API (localhost only, no cloud calls)."""
from __future__ import annotations

import json
from collections.abc import Iterator

import requests

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL_FILE = "/etc/aibase/default-model"
REQUEST_TIMEOUT = 30


class OllamaError(RuntimeError):
    """Raised when the local Ollama daemon is unreachable or returns an error."""


def get_default_model() -> str:
    try:
        with open(DEFAULT_MODEL_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "llama3.2:3b-instruct-q4_K_M"


def is_available() -> bool:
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return True
    except requests.RequestException:
        return False


def list_models() -> list[dict]:
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("models", [])
    except requests.RequestException as exc:
        raise OllamaError(f"Could not reach local Ollama service: {exc}") from exc


def pull_model(name: str) -> Iterator[str]:
    """Streams progress status strings while a model is downloaded."""
    try:
        with requests.post(
            f"{OLLAMA_BASE_URL}/api/pull",
            json={"name": name, "stream": True},
            stream=True,
            timeout=REQUEST_TIMEOUT,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                yield data.get("status", "")
    except requests.RequestException as exc:
        raise OllamaError(f"Model pull failed: {exc}") from exc


def delete_model(name: str) -> None:
    try:
        resp = requests.delete(
            f"{OLLAMA_BASE_URL}/api/delete", json={"name": name}, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise OllamaError(f"Model delete failed: {exc}") from exc


def chat(messages: list[dict], model: str | None = None) -> str:
    """Single-shot (non-streaming) chat completion."""
    model = model or get_default_model()
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "")
    except requests.RequestException as exc:
        raise OllamaError(
            "Could not reach local Ollama service. Is the model downloaded? "
            "Open the Model Manager to check."
        ) from exc
