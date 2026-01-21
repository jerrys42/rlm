"""
LLM Backend abstractions for RLM.

Supports multiple providers:
- AnthropicBackend: Direct Anthropic API
- OpenAICompatibleBackend: For local models (Ollama, vLLM, LM Studio)
- CallbackBackend: Custom callback for Claude Max / other integrations
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Protocol, runtime_checkable


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0


@runtime_checkable
class LLMBackend(Protocol):
    """Protocol for LLM backends."""

    def complete(self, messages: list[dict], model: str) -> LLMResponse:
        """Synchronous completion."""
        ...

    async def acomplete(self, messages: list[dict], model: str) -> LLMResponse:
        """Asynchronous completion."""
        ...


class AnthropicBackend:
    """
    Backend using the Anthropic API directly.

    Requires: pip install anthropic
    """

    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        'claude-opus-4-20250514': {'input': 15.0, 'output': 75.0},
        'claude-sonnet-4-20250514': {'input': 3.0, 'output': 15.0},
        'claude-haiku-3-20250813': {'input': 0.25, 'output': 1.25},
        # Fallback for unknown models
        'default': {'input': 3.0, 'output': 15.0},
    }

    def __init__(
        self,
        api_key: str | None = None,
        max_tokens: int = 4096,
    ):
        """
        Initialize Anthropic backend.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            max_tokens: Maximum tokens in response
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")

        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set ANTHROPIC_API_KEY or pass api_key parameter.")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.max_tokens = max_tokens

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a request."""
        pricing = self.PRICING.get(model, self.PRICING['default'])
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        return input_cost + output_cost

    def complete(self, messages: list[dict], model: str) -> LLMResponse:
        """Synchronous completion via Anthropic API."""
        # Extract system message if present
        system = None
        filtered_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                system = msg.get('content', '')
            else:
                filtered_messages.append(msg)

        kwargs = {
            'model': model,
            'max_tokens': self.max_tokens,
            'messages': filtered_messages,
        }
        if system:
            kwargs['system'] = system

        response = self.client.messages.create(**kwargs)

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        content = response.content[0].text if response.content else ''

        return LLMResponse(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=self._calculate_cost(model, input_tokens, output_tokens),
        )

    async def acomplete(self, messages: list[dict], model: str) -> LLMResponse:
        """Asynchronous completion via Anthropic API."""
        # Extract system message if present
        system = None
        filtered_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                system = msg.get('content', '')
            else:
                filtered_messages.append(msg)

        kwargs = {
            'model': model,
            'max_tokens': self.max_tokens,
            'messages': filtered_messages,
        }
        if system:
            kwargs['system'] = system

        response = await self.async_client.messages.create(**kwargs)

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        content = response.content[0].text if response.content else ''

        return LLMResponse(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=self._calculate_cost(model, input_tokens, output_tokens),
        )


class OpenAICompatibleBackend:
    """
    Backend for OpenAI-compatible APIs (Ollama, vLLM, LM Studio, etc.).

    Requires: pip install openai
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",  # Ollama doesn't need real key
        max_tokens: int = 4096,
    ):
        """
        Initialize OpenAI-compatible backend.

        Args:
            base_url: API base URL (e.g., http://localhost:11434/v1 for Ollama)
            api_key: API key (use "ollama" for Ollama, or your actual key)
            max_tokens: Maximum tokens in response
        """
        try:
            import openai
        except ImportError:
            raise ImportError("Please install openai: pip install openai")

        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.async_client = openai.AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.max_tokens = max_tokens

    def complete(self, messages: list[dict], model: str) -> LLMResponse:
        """Synchronous completion via OpenAI-compatible API."""
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=self.max_tokens,
        )

        content = response.choices[0].message.content or ''
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return LLMResponse(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=0.0,  # Local models are free
        )

    async def acomplete(self, messages: list[dict], model: str) -> LLMResponse:
        """Asynchronous completion via OpenAI-compatible API."""
        response = await self.async_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=self.max_tokens,
        )

        content = response.choices[0].message.content or ''
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return LLMResponse(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=0.0,
        )


class CallbackBackend:
    """
    Backend using a custom callback function.

    Useful for:
    - Claude Max subscription integration
    - Claude Code / CLI integration
    - Custom LLM wrappers
    """

    def __init__(
        self,
        callback: Callable[[list[dict], str], str],
        async_callback: Callable[[list[dict], str], str] | None = None,
    ):
        """
        Initialize callback backend.

        Args:
            callback: Function that takes (messages, model) and returns response string
            async_callback: Optional async version of callback
        """
        self._callback = callback
        self._async_callback = async_callback

    def complete(self, messages: list[dict], model: str) -> LLMResponse:
        """Synchronous completion via callback."""
        content = self._callback(messages, model)
        return LLMResponse(
            content=content,
            model=model,
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
        )

    async def acomplete(self, messages: list[dict], model: str) -> LLMResponse:
        """Asynchronous completion via callback."""
        if self._async_callback:
            content = await self._async_callback(messages, model)
        else:
            # Fall back to sync callback
            content = self._callback(messages, model)

        return LLMResponse(
            content=content,
            model=model,
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
        )


# Convenience function to create backend from string
def create_backend(
    backend_type: str = "anthropic",
    **kwargs,
) -> LLMBackend:
    """
    Factory function to create a backend.

    Args:
        backend_type: One of "anthropic", "openai", "ollama", "callback"
        **kwargs: Backend-specific arguments

    Returns:
        Configured backend instance
    """
    if backend_type == "anthropic":
        return AnthropicBackend(**kwargs)
    elif backend_type in ("openai", "ollama", "vllm", "lmstudio"):
        return OpenAICompatibleBackend(**kwargs)
    elif backend_type == "callback":
        if 'callback' not in kwargs:
            raise ValueError("callback parameter required for callback backend")
        return CallbackBackend(**kwargs)
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")
