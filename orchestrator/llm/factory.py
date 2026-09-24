"""LLM instance factory with OpenRouter failover and provider routing."""

import os
from typing import TYPE_CHECKING
from pydantic import SecretStr

from openhands.sdk import LLM
from orchestrator.llm.normalize import normalize_model_slug

if TYPE_CHECKING:
    from orchestrator.config import AgentRoleConfig, OrchestratorConfig


def create_llm_for_role(
    config: "OrchestratorConfig", role_config: "AgentRoleConfig"
) -> LLM:
    """Factory to create an OpenHands LLM instance with appropriate credentials and failover."""
    model = normalize_model_slug(role_config.model)
    api_key_val = role_config.api_key

    # Resolve API Key by provider prefix if not explicitly set
    if not api_key_val:
        if model.startswith("anthropic/"):
            api_key_val = config.anthropic_api_key
        elif model.startswith("omniroute/"):
            api_key_val = (
                config.omniroute_api_key
                or os.environ.get("OMNIROUTE_API_KEY")
                or config.openai_api_key
                or "sk-omniroute"
            )
        elif model.startswith("openai/"):
            api_key_val = config.openai_api_key or config.omniroute_api_key
        elif model.startswith("gemini/") or model.startswith("google/"):
            api_key_val = config.gemini_api_key
        elif model.startswith("openrouter/"):
            api_key_val = config.openrouter_api_key
        elif model.startswith("groq/"):
            api_key_val = getattr(config, "groq_api_key", None) or os.environ.get(
                "GROQ_API_KEY"
            )

    base_url = None
    if model.startswith("omniroute/"):
        base_url = getattr(config, "omniroute_base_url", None) or os.environ.get(
            "OMNIROUTE_BASE_URL", "http://localhost:20128/v1"
        )
        # Translate to OpenAI-compatible provider slug for LiteLLM engine
        model = f"openai/{model[len('omniroute/') :]}"
    elif model.startswith("openai/"):
        if getattr(config, "openai_base_url", None) or os.environ.get(
            "OPENAI_BASE_URL"
        ):
            base_url = config.openai_base_url or os.environ.get("OPENAI_BASE_URL")
        elif getattr(config, "provider", "") == "omniroute":
            base_url = getattr(config, "omniroute_base_url", None) or os.environ.get(
                "OMNIROUTE_BASE_URL", "http://localhost:20128/v1"
            )

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
