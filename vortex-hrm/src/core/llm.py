"""
VORTEX LLM backends — zero-dependency mock, local Ollama, and cloud OpenAI.
Two design rules:
  1. Every backend has `chat_completion(**kwargs) -> dict`.
  2. Default is MockBackend — no network, no keys, no downloads.
"""

import json
from typing import Optional, Protocol


class LLMBackend(Protocol):
    def chat_completion(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> dict:
        ...


class MockBackend:
    """
    Offline deterministic backend — no network, no API keys.
    Returns canned XML responses for planner/executor to validate the architecture.
    """

    def __init__(self, responses: Optional[list[str]] = None):
        self.responses = responses or []
        self.call_count = 0

    def chat_completion(self, **kwargs) -> dict:
        idx = min(self.call_count, len(self.responses) - 1) if self.responses else 0
        content = self.responses[idx] if self.responses else "<think>mock</think><final_answer>mock answer</final_answer>"
        self.call_count += 1
        return {"choices": [{"message": {"content": content}}]}


class OllamaBackend:
    """
    Local LLM via Ollama's OpenAI-compatible API.
    Requires Ollama running on the machine:  https://ollama.com
    Default endpoint:  http://localhost:11434/v1

    Two transport options:
      - stdlib (requests) — zero pip installs beyond what's already present.
      - openai package    — richer error handling, streaming support.
    """

    def __init__(
        self,
        model: str = "qwen2.5:0.5b",
        base_url: str = "http://localhost:11434/v1",
        temperature: float = 0.0,
        max_tokens: int = 2048,
        timeout: int = 300,
        use_openai_package: bool = False,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._use_openai = use_openai_package

    def chat_completion(self, **kwargs) -> dict:
        model = kwargs.get("model", self.model)
        messages = kwargs.get("messages", [])
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        if self._use_openai:
            return self._via_openai_package(model, messages, temperature, max_tokens)
        return self._via_requests(model, messages, temperature, max_tokens)

    def _via_requests(self, model: str, messages: list, temperature: float, max_tokens: int) -> dict:
        import requests

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    def _via_openai_package(self, model: str, messages: list, temperature: float, max_tokens: int) -> dict:
        from openai import OpenAI

        client = OpenAI(base_url=self.base_url, api_key="ollama")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {
            "choices": [
                {
                    "message": {
                        "content": response.choices[0].message.content,
                    }
                }
            ]
        }


class OpenAIBackend:
    """
    Cloud LLM via OpenAI API.
    Requires `pip install openai` and a valid API key.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str = "",
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ):
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat_completion(self, **kwargs) -> dict:
        from openai import OpenAI

        model = kwargs.get("model", self.model)
        messages = kwargs.get("messages", [])
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {
            "choices": [
                {
                    "message": {
                        "content": response.choices[0].message.content,
                    }
                }
            ]
        }


def backend_from_config(cfg) -> LLMBackend:
    """
    Factory: create an LLMBackend from VORTEXConfig.LLMConfig or a dict.
    """
    if hasattr(cfg, "mode"):
        mode = cfg.mode
    elif isinstance(cfg, dict):
        mode = cfg.get("mode", "mock")
    else:
        mode = "mock"

    if mode == "mock":
        return MockBackend()
    elif mode == "ollama":
        return OllamaBackend(
            model=getattr(cfg, "model", "qwen2.5:0.5b") if hasattr(cfg, "model") else cfg.get("model", "qwen2.5:0.5b"),
            base_url=getattr(cfg, "base_url", "http://localhost:11434/v1") if hasattr(cfg, "base_url") else cfg.get("base_url", "http://localhost:11434/v1"),
            temperature=getattr(cfg, "temperature", 0.0) if hasattr(cfg, "temperature") else cfg.get("temperature", 0.0),
            max_tokens=getattr(cfg, "max_tokens", 2048) if hasattr(cfg, "max_tokens") else cfg.get("max_tokens", 2048),
            timeout=getattr(cfg, "timeout", 300) if hasattr(cfg, "timeout") else cfg.get("timeout", 300),
        )
    elif mode == "openai":
        return OpenAIBackend(
            model=getattr(cfg, "model", "gpt-4o-mini") if hasattr(cfg, "model") else cfg.get("model", "gpt-4o-mini"),
            api_key=getattr(cfg, "api_key", "") if hasattr(cfg, "api_key") else cfg.get("api_key", ""),
            temperature=getattr(cfg, "temperature", 0.0) if hasattr(cfg, "temperature") else cfg.get("temperature", 0.0),
            max_tokens=getattr(cfg, "max_tokens", 2048) if hasattr(cfg, "max_tokens") else cfg.get("max_tokens", 2048),
        )
    else:
        raise ValueError(f"Unknown LLM mode: {mode}. Expected: mock, ollama, openai")
