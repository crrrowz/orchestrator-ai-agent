"""Model slug normalization utilities."""


def normalize_model_slug(model: str) -> str:
    """Normalize model slug to include :free suffix for free-tier models and route openrouter/free."""
    resolved = (model or "openrouter/qwen/qwen3.8-27b:free").strip()
    if resolved in ("free", "openrouter/free"):
        return "openrouter/openrouter/free"
    if resolved == "qwen/qwen3.8-27b":
        resolved = "openrouter/qwen/qwen3.8-27b:free"
    elif resolved == "openrouter/qwen/qwen3.8-27b":
        resolved = "openrouter/qwen/qwen3.8-27b:free"
    return resolved
