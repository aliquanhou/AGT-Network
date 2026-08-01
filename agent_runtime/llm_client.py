"""
AGT Agent Runtime — Unified LLM Client

Supports multiple LLM providers through a single interface:
- DeepSeek (deepseek-chat)
- OpenAI (gpt-4o, gpt-4o-mini)
- Claude (claude-sonnet-5, claude-opus-5)
- Ollama (local models)

Usage:
    client = create_llm_client("deepseek", api_key="sk-...")
    result = await client.chat("Hello", system="You are helpful.")
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class Provider(str, Enum):
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"


@dataclass
class LLMResponse:
    """Unified LLM response"""
    content: str
    model: str = ""
    usage: dict = field(default_factory=dict)
    finish_reason: str = "stop"
    raw: dict = field(default_factory=dict)


# ============================================================
# Abstract Base
# ============================================================

class LLMClient(ABC):
    """Abstract LLM client"""

    def __init__(self):
        self.total_tokens: int = 0      # v0.36.4: cumulative token tracking
        self.total_cost: float = 0.0    # v0.36.4: estimated cost in USD

    def _track_usage(self, usage: dict, model: str = ""):
        """Accumulate token usage and estimate cost (v0.36.4)"""
        tokens = usage.get("total_tokens", 0)
        self.total_tokens += tokens
        cost = self._estimate_cost(usage, model)
        self.total_cost += cost
        return {"tokens": tokens, "cost": cost, "model": model}

    def _estimate_cost(self, usage: dict, model: str = "") -> float:
        """Estimate cost in USD. Override per provider."""
        return 0.0

    @abstractmethod
    async def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        ...


# ============================================================
# DeepSeek Client
# ============================================================

class DeepSeekClient(LLMClient):
    """DeepSeek API client (OpenAI-compatible)"""

    BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"
    # DeepSeek pricing per 1M tokens (input / output)
    PRICE_INPUT_PER_1M = 0.14
    PRICE_OUTPUT_PER_1M = 0.28

    def __init__(self, api_key: str, model: str = None):
        super().__init__()
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    async def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = await self._client.post("/chat/completions", json={
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        })
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})
        self._track_usage(usage, self.model)
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            usage=usage,
            finish_reason=choice.get("finish_reason", "stop"),
            raw=data,
        )

    def _estimate_cost(self, usage: dict, model: str = "") -> float:
        """DeepSeek pricing: $0.14/1M input, $0.28/1M output"""
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        return (prompt_tokens * self.PRICE_INPUT_PER_1M / 1_000_000 +
                completion_tokens * self.PRICE_OUTPUT_PER_1M / 1_000_000)


# ============================================================
# OpenAI Client
# ============================================================

class OpenAIClient(LLMClient):
    """OpenAI API client"""

    BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, api_key: str, model: str = None, base_url: str = None):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        self._client = httpx.AsyncClient(
            base_url=base_url or self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    async def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = await self._client.post("/chat/completions", json={
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        })
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
            raw=data,
        )


# ============================================================
# Claude (Anthropic) Client
# ============================================================

class ClaudeClient(LLMClient):
    """Anthropic Claude API client"""

    BASE_URL = "https://api.anthropic.com/v1"
    DEFAULT_MODEL = "claude-sonnet-5-20251001"

    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            timeout=120.0,
        )

    async def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs,
        }
        if system:
            body["system"] = system

        resp = await self._client.post("/messages", json=body)
        resp.raise_for_status()
        data = resp.json()

        content = ""
        for block in data.get("content", []):
            if block["type"] == "text":
                content += block["text"]

        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            usage=data.get("usage", {}),
            finish_reason=data.get("stop_reason", "end_turn"),
            raw=data,
        )


# ============================================================
# Ollama Client
# ============================================================

class OllamaClient(LLMClient):
    """Ollama local LLM client"""

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2"

    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        self._client = httpx.AsyncClient(
            base_url=f"{self.base_url}/api",
            timeout=300.0,
        )

    async def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        body = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            body["system"] = system

        resp = await self._client.post("/generate", json=body)
        resp.raise_for_status()
        data = resp.json()

        return LLMResponse(
            content=data.get("response", ""),
            model=data.get("model", self.model),
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
            finish_reason=data.get("done_reason", "stop"),
            raw=data,
        )


# ============================================================
# Factory
# ============================================================

def create_llm_client(
    provider: str,
    api_key: str = None,
    model: str = None,
    base_url: str = None,
) -> LLMClient:
    """
    Create an LLM client for the given provider.

    Args:
        provider: "deepseek" | "openai" | "claude" | "ollama"
        api_key: API key (not needed for ollama)
        model: Model name override
        base_url: API base URL override (ollama only)
    """
    provider = provider.lower()

    if provider == Provider.DEEPSEEK:
        key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if not key:
            raise ValueError("DEEPSEEK_API_KEY is required")
        return DeepSeekClient(key, model=model)

    elif provider == Provider.OPENAI:
        key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise ValueError("OPENAI_API_KEY is required")
        return OpenAIClient(key, model=model, base_url=base_url)

    elif provider == Provider.CLAUDE:
        key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        return ClaudeClient(key, model=model)

    elif provider == Provider.OLLAMA:
        url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaClient(base_url=url, model=model)

    else:
        raise ValueError(f"Unsupported provider: {provider}. "
                         f"Choose from: deepseek, openai, claude, ollama")
