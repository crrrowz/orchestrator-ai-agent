"""Model pricing rates and calculations in USD."""

from typing import Tuple


def get_pricing_rates(model: str) -> Tuple[float, float]:
    """Return (input_rate_per_1M, output_rate_per_1M) in USD for a given model slug."""
    m = (model or "").lower()
    if ":free" in m or "openrouter/free" in m:
        return 0.0, 0.0
    if (
        "claude-sonnet-4-5" in m
        or "claude-3-5-sonnet" in m
        or "claude-3.5-sonnet" in m
    ):
        return 3.0, 15.0
    if "gpt-4o-mini" in m:
        return 0.15, 0.60
    if "gpt-4o" in m:
        return 2.50, 10.00
    if "gemini-2.0-flash" in m or "gemini-1.5-flash" in m:
        return 0.10, 0.40
    if "gemini-1.5-pro" in m:
        return 1.25, 5.00
    # Generic fallback
    return 1.00, 3.00
