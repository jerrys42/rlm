"""
Anthropic API Pricing Module

Updated: January 2026
Source: https://platform.claude.com/docs/en/about-claude/pricing
"""

from dataclasses import dataclass, field
from typing import Optional


# Pricing per million tokens (MTok)
PRICING = {
    # Claude 4.5 (Latest)
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-opus-4-5-20251101": {"input": 5.00, "output": 25.00},
    "claude-opus-4-5": {"input": 5.00, "output": 25.00},

    # Claude 4 (Legacy but still common)
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "claude-opus-4": {"input": 15.00, "output": 75.00},
    "claude-opus-4-1-20250805": {"input": 15.00, "output": 75.00},
    "claude-opus-4-1": {"input": 15.00, "output": 75.00},

    # Claude 3.x (Legacy)
    "claude-3-7-sonnet-20250219": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},

    # Aliases for backwards compatibility
    "claude-haiku-3-20250813": {"input": 0.25, "output": 1.25},  # Common alias
}

# Default pricing for unknown models
DEFAULT_PRICING = {"input": 3.00, "output": 15.00}


@dataclass
class TokenUsage:
    """Track token usage for a single API call."""
    model: str
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def input_cost(self) -> float:
        """Cost for input tokens in USD."""
        pricing = PRICING.get(self.model, DEFAULT_PRICING)
        return (self.input_tokens / 1_000_000) * pricing["input"]

    @property
    def output_cost(self) -> float:
        """Cost for output tokens in USD."""
        pricing = PRICING.get(self.model, DEFAULT_PRICING)
        return (self.output_tokens / 1_000_000) * pricing["output"]

    @property
    def total_cost(self) -> float:
        """Total cost in USD."""
        return self.input_cost + self.output_cost

    def __str__(self) -> str:
        return (
            f"{self.model}: {self.input_tokens:,} in / {self.output_tokens:,} out "
            f"= ${self.total_cost:.4f}"
        )


@dataclass
class CostTracker:
    """Aggregate cost tracking across multiple API calls."""
    calls: list[TokenUsage] = field(default_factory=list)

    def add(self, model: str, input_tokens: int, output_tokens: int) -> TokenUsage:
        """Add a new API call to tracking."""
        usage = TokenUsage(model=model, input_tokens=input_tokens, output_tokens=output_tokens)
        self.calls.append(usage)
        return usage

    @property
    def total_input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.calls)

    @property
    def total_cost(self) -> float:
        return sum(c.total_cost for c in self.calls)

    def by_model(self) -> dict[str, dict]:
        """Group usage by model."""
        models: dict[str, dict] = {}
        for call in self.calls:
            if call.model not in models:
                models[call.model] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                }
            models[call.model]["calls"] += 1
            models[call.model]["input_tokens"] += call.input_tokens
            models[call.model]["output_tokens"] += call.output_tokens
            models[call.model]["cost"] += call.total_cost
        return models

    def summary(self) -> str:
        """Generate a formatted cost summary."""
        lines = ["=" * 60, "Cost Breakdown", "=" * 60]

        by_model = self.by_model()
        for model, stats in sorted(by_model.items()):
            pricing = PRICING.get(model, DEFAULT_PRICING)
            lines.append(f"\n{model}:")
            lines.append(f"  Pricing: ${pricing['input']:.2f}/MTok in, ${pricing['output']:.2f}/MTok out")
            lines.append(f"  Calls: {stats['calls']}")
            lines.append(f"  Input:  {stats['input_tokens']:>10,} tokens")
            lines.append(f"  Output: {stats['output_tokens']:>10,} tokens")
            lines.append(f"  Cost:   ${stats['cost']:>10.4f}")

        lines.append("\n" + "-" * 60)
        lines.append(f"TOTAL: {len(self.calls)} calls, {self.total_input_tokens:,} in / {self.total_output_tokens:,} out")
        lines.append(f"TOTAL COST: ${self.total_cost:.4f}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def reset(self):
        """Clear all tracked calls."""
        self.calls.clear()


def estimate_tokens(text: str) -> int:
    """
    Rough estimate of token count for text.
    Claude uses ~4 chars per token on average for English.
    """
    return len(text) // 4


def get_model_pricing(model: str) -> dict:
    """Get pricing for a model."""
    return PRICING.get(model, DEFAULT_PRICING)
