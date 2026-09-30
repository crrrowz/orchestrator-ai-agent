"""LLM instance factory with OpenRouter failover and provider routing."""

import os
import re
from typing import TYPE_CHECKING, Optional
from pydantic import SecretStr

from openhands.sdk import LLM
from orchestrator.llm.normalize import normalize_model_slug

if TYPE_CHECKING:
    from orchestrator.config import AgentRoleConfig, OrchestratorConfig


KNOWN_LITELLM_PROVIDERS = {
    "openai",
    "anthropic",
    "gemini",
    "google",
    "openrouter",
    "groq",
    "ollama",
    "vertex_ai",
    "bedrock",
    "azure",
    "mistral",
    "together_ai",
    "deepseek",
    "cohere",
    "voyage",
    "huggingface",
    "cloudflare",
    "replicate",
}


def sanitize_base_url(url: Optional[str]) -> Optional[str]:
    """Sanitize base URL by correcting malformed port syntax (e.g. /:20128) and stripping trailing slashes."""
    if not url:
        return None
    cleaned = url.strip()
    if not cleaned:
        return None
    # Fix malformed port syntax like /:20128 -> :20128
    cleaned = re.sub(r"/+:(\d+)", r":\1", cleaned)
    # Remove trailing slash
    return cleaned.rstrip("/")


def create_llm_for_role(
    config: "OrchestratorConfig", role_config: "AgentRoleConfig"
) -> LLM:
    """Factory to create an OpenHands LLM instance with appropriate credentials and failover."""
    raw_model = normalize_model_slug(role_config.model)
    api_key_val = role_config.api_key
    base_url: Optional[str] = None
    model = raw_model

    # Determine provider prefix
    prefix = raw_model.split("/", 1)[0].lower() if "/" in raw_model else ""
    active_provider = (getattr(config, "provider", None) or os.environ.get("PROVIDER", "")).lower()

    omniroute_base = (
        sanitize_base_url(getattr(config, "omniroute_base_url", None))
        or sanitize_base_url(os.environ.get("OMNIROUTE_BASE_URL"))
        or "http://localhost:20128/v1"
    )
    omniroute_key = (
        getattr(config, "omniroute_api_key", None)
        or os.environ.get("OMNIROUTE_API_KEY")
        or getattr(config, "openai_api_key", None)
        or "sk-omniroute"
    )
    openai_base = sanitize_base_url(
        getattr(config, "openai_base_url", None) or os.environ.get("OPENAI_BASE_URL")
    )
    has_explicit_omniroute_base = bool(
        getattr(config, "omniroute_base_url", None) or os.environ.get("OMNIROUTE_BASE_URL")
    )

    if raw_model.startswith("omniroute/"):
        # Explicit omniroute prefix: route as OpenAI-compatible
        suffix = raw_model[len("omniroute/") :]
        model = f"openai/{suffix}"
        base_url = omniroute_base
        if not api_key_val:
            api_key_val = omniroute_key
    elif prefix in KNOWN_LITELLM_PROVIDERS:
        # Standard LiteLLM built-in provider
        if prefix in ("gemini", "google"):
            if not api_key_val:
                api_key_val = config.gemini_api_key
        elif prefix == "anthropic":
            if not api_key_val:
                api_key_val = config.anthropic_api_key
        elif prefix == "openrouter":
            if not api_key_val:
                api_key_val = config.openrouter_api_key
        elif prefix == "groq":
            if not api_key_val:
                api_key_val = getattr(config, "groq_api_key", None) or os.environ.get("GROQ_API_KEY")
        elif prefix == "openai":
            if openai_base:
                base_url = openai_base
                if not api_key_val:
                    api_key_val = config.openai_api_key
            elif active_provider == "omniroute":
                base_url = omniroute_base
                if not api_key_val:
                    api_key_val = omniroute_key
            else:
                if not api_key_val:
                    api_key_val = config.openai_api_key
    else:
        # Unknown/Custom provider prefix (e.g. antigravity/..., custom/..., or pure model name)
        if active_provider == "omniroute":
            model = f"openai/{raw_model}"
            base_url = omniroute_base
            if not api_key_val:
                api_key_val = omniroute_key
        elif openai_base:
            model = f"openai/{raw_model}"
            base_url = openai_base
            if not api_key_val:
                api_key_val = config.openai_api_key or "sk-custom"
        elif has_explicit_omniroute_base:
            model = f"openai/{raw_model}"
            base_url = omniroute_base
            if not api_key_val:
                api_key_val = omniroute_key
        else:
            model = f"openai/{raw_model}"
            if active_provider == "openai" or config.openai_api_key:
                if not api_key_val:
                    api_key_val = config.openai_api_key
            else:
                base_url = omniroute_base
                if not api_key_val:
                    api_key_val = omniroute_key

    # Export credentials to environment for LiteLLM
    if api_key_val:
        if model.startswith("gemini/") or model.startswith("google/"):
            os.environ["GEMINI_API_KEY"] = api_key_val
        elif model.startswith("groq/"):
            os.environ["GROQ_API_KEY"] = api_key_val
        elif model.startswith("openrouter/"):
            os.environ["OPENROUTER_API_KEY"] = api_key_val
        elif model.startswith("openai/"):
            os.environ["OPENAI_API_KEY"] = api_key_val

    secret = SecretStr(api_key_val) if api_key_val else None

    llm_kwargs = {
        "model": model,
        "api_key": secret,
        "temperature": role_config.temperature,
        "max_output_tokens": config.max_tokens_per_call,
        "usage_id": f"agent-{role_config.role}",
        "num_retries": 2,
        "retry_min_wait": 1,
        "retry_max_wait": 5,
    }

    if base_url:
        llm_kwargs["base_url"] = base_url

    if model.startswith("openrouter/"):
        llm_kwargs["openrouter_site_url"] = "https://github.com/Antigravity-Agent-API"
        llm_kwargs["openrouter_app_name"] = "Antigravity Multi-Agent Orchestrator"

        # OpenRouter Model-Layer Failover Array
        model_slug = model[len("openrouter/") :]
        if model_slug in ("free", "openrouter/free"):
            fallback_models = ["qwen/qwen3.8-27b:free", "openrouter/free"]
            primary_fb_target = "openrouter/qwen/qwen3.8-27b:free"
        elif ":free" in model_slug:
            fallback_models = [model_slug, "qwen/qwen3.8-27b:free", "openrouter/free"]
            primary_fb_target = "openrouter/openrouter/free"
        else:
            fallback_models = [model_slug]
            primary_fb_target = "openrouter/openrouter/free"

        llm_kwargs["litellm_extra_body"] = {"models": fallback_models}

        # Native OpenHands SDK FallbackStrategy for resilient recovery
        from openhands.sdk.llm.fallback_strategy import FallbackStrategy

        fb_kwargs = dict(llm_kwargs)
        fb_kwargs["model"] = primary_fb_target
        fb_kwargs["usage_id"] = f"{role_config.role}-fallback-resilient"
        fb_kwargs["litellm_extra_body"] = {
            "models": ["qwen/qwen3.8-27b:free", "openrouter/free"]
        }
        fb_kwargs.pop("fallback_strategy", None)
        fallback_llm = LLM(**fb_kwargs)
        strat = FallbackStrategy(fallback_llms=["openrouter-resilient-fallback"])
        strat._resolved = [fallback_llm]
        llm_kwargs["fallback_strategy"] = strat

    return LLM(**llm_kwargs)
