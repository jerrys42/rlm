"""
RLM - Recursive Language Model

A Python implementation of the Recursive Language Model paradigm from MIT CSAIL.
Enables LLMs to process arbitrarily long contexts by treating them as external
variables in a sandboxed Python REPL environment.

Usage:
    from rlm import RLM
    from rlm.backends import AnthropicBackend

    backend = AnthropicBackend()
    rlm = RLM(backend, model="claude-sonnet-4-20250514", verbose=True)

    result = rlm.completion(
        context=large_document,
        query="What are the main themes in this document?"
    )
    print(result.answer)
    print(rlm.cost_summary())
"""

from .rlm import RLM, RLMResult, RLMStats
from .repl import REPLEnv, REPLResult, SecurityError
from .backends import (
    LLMBackend,
    LLMResponse,
    AnthropicBackend,
    OpenAICompatibleBackend,
    CallbackBackend,
    create_backend,
)

__version__ = "0.1.0"
__author__ = "Based on MIT CSAIL research by Alex L. Zhang, Tim Kraska, and Omar Khattab"

__all__ = [
    # Core
    "RLM",
    "RLMResult",
    "RLMStats",
    # REPL
    "REPLEnv",
    "REPLResult",
    "SecurityError",
    # Backends
    "LLMBackend",
    "LLMResponse",
    "AnthropicBackend",
    "OpenAICompatibleBackend",
    "CallbackBackend",
    "create_backend",
]
