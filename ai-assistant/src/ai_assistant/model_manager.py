"""Wraps the Ollama model list/pull/delete operations for the tray UI."""
from __future__ import annotations

from ai_assistant import ollama_client

# Curated so users never have to know exact Ollama model tags.
CATALOG = [
    {"label": "Small (fits 8GB RAM) - Llama 3.2 3B", "tag": "llama3.2:3b-instruct-q4_K_M"},
    {"label": "Balanced (needs 16GB RAM) - Llama 3.1 8B", "tag": "llama3.1:8b-instruct-q4_K_M"},
    {"label": "Coding-focused - Qwen 2.5 Coder 7B", "tag": "qwen2.5-coder:7b-instruct-q4_K_M"},
]


def installed_models() -> list[str]:
    return [m["name"] for m in ollama_client.list_models()]


def install(tag: str):
    yield from ollama_client.pull_model(tag)


def remove(tag: str) -> None:
    ollama_client.delete_model(tag)


def recommended_tag_for_system() -> str:
    return ollama_client.get_default_model()
