"""Centralized LLM Lifecycle Manager: creation, pooling, tracking, and runtime routing."""

from typing import TYPE_CHECKING, Any, Dict, Optional

from openhands.sdk import LLM
from orchestrator.llm.factory import create_llm_for_role

if TYPE_CHECKING:
    from orchestrator.config import OrchestratorConfig


def get_llm_usage(llm: Any) -> Dict[str, Any]:
    """Helper to extract token metrics and cost from an LLM instance."""
    metrics = getattr(llm, "metrics", None)
    if not metrics:
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
    tu = getattr(metrics, "accumulated_token_usage", None)
    prompt = getattr(tu, "prompt_tokens", 0) if tu else 0
    completion = getattr(tu, "completion_tokens", 0) if tu else 0
    cost = getattr(metrics, "accumulated_cost", 0.0)
    try:
        cost = float(cost)
    except (TypeError, ValueError):
        cost = 0.0

    try:
        prompt = int(prompt)
    except (TypeError, ValueError):
        prompt = 0

    try:
        completion = int(completion)
    except (TypeError, ValueError):
        completion = 0

    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "estimated_cost_usd": cost,
    }


class LLMManager:
    """Singleton LLM lifecycle manager: creation, pooling, tracking, and runtime model swapping."""

    _instance: Optional["LLMManager"] = None

    def __init__(self, config: Optional["OrchestratorConfig"] = None):
        from orchestrator.config import OrchestratorConfig

        self._config: OrchestratorConfig = config or OrchestratorConfig()
        self._pool: Dict[str, LLM] = {}

    @classmethod
    def get_instance(
        cls, config: Optional["OrchestratorConfig"] = None
    ) -> "LLMManager":
        """Access the singleton LLMManager instance."""
        if cls._instance is None:
            cls._instance = cls(config)
        elif config is not None:
            cls._instance._config = config
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful in test isolation)."""
        cls._instance = None

    def get_llm(self, role: str) -> LLM:
        """Fetch or create a cached LLM instance for a specific agent role."""
        if role not in self._pool:
            role_config = getattr(self._config, role, None)
            if not role_config:
                from orchestrator.config import AgentRoleConfig

                default_model = (
                    os.environ.get(f"{role.upper()}_MODEL")
                    or os.environ.get("MODEL")
                    or getattr(self._config, "model", None)
                    or "openrouter/qwen/qwen3.8-27b:free"
                )
                role_config = AgentRoleConfig(
                    role=role, model=default_model
                )
            self._pool[role] = create_llm_for_role(self._config, role_config)
        return self._pool[role]

    def get_role_usage(self, role: str) -> Dict[str, Any]:
        """Fetch usage stats for a specific agent role."""
        if role in self._pool:
            return get_llm_usage(self._pool[role])
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    def get_total_cost(self) -> float:
        """Aggregate total estimated cost (USD) across all active LLM pool instances."""
        return sum(
            get_llm_usage(llm)["estimated_cost_usd"] for llm in self._pool.values()
        )

    def get_total_tokens(self) -> int:
        """Aggregate total token consumption across all active LLM pool instances."""
        return sum(get_llm_usage(llm)["total_tokens"] for llm in self._pool.values())

    def swap_model(self, role: str, new_model: str) -> LLM:
        """Hot-swap model for a role dynamically at runtime."""
        if role in self._pool:
            del self._pool[role]
        role_config = getattr(self._config, role, None)
        if role_config:
            role_config.model = new_model
        return self.get_llm(role)

    def failover_model(self, role: str) -> Optional[str]:
        """Automatically swap the role to the next healthy model in the cloud fallback chain."""
        role_config = getattr(self._config, role, None)
        current_model = getattr(role_config, "model", "") if role_config else ""
        chain = getattr(self._config, "cloud_fallback_chain", [])
        next_model = None
        for candidate in chain:
            if candidate != current_model:
                next_model = candidate
                break
        if next_model:
            self.swap_model(role, next_model)
            return next_model
        return None

    def reset_pool(self) -> None:
        """Clear all pooled LLM instances."""
        self._pool.clear()


class CloudResilienceMesh:
    """Multi-tier provider failover and latency monitoring mesh."""

    def __init__(self, config: Optional["OrchestratorConfig"] = None) -> None:
        from orchestrator.config import OrchestratorConfig

        self._config = config or OrchestratorConfig()
        self._degraded_providers: set[str] = set()

    def get_healthy_provider(self, requested_provider: str) -> str:
        """Return healthy provider or fallback if requested is degraded."""
        if requested_provider.lower() not in self._degraded_providers:
            return requested_provider
        for candidate in getattr(self._config, "cloud_fallback_chain", []):
            prov = candidate.split("/")[0] if "/" in candidate else candidate
            if prov.lower() not in self._degraded_providers:
                return prov
        return requested_provider

    def record_provider_result(
        self,
        provider: str,
        success: bool,
        latency_ms: float,
        error_code: Optional[int] = None,
    ) -> None:
        """Update degraded status based on call result."""
        if not success and error_code in (429, 500, 502, 503):
            self._degraded_providers.add(provider.lower())
        elif success and provider.lower() in self._degraded_providers:
            self._degraded_providers.discard(provider.lower())

    def test_mesh(self) -> list[dict[str, Any]]:
        """Probe cloud fallback mesh readiness and return health diagnostics per tier."""
        import os

        results: list[dict[str, Any]] = []
        chain = getattr(self._config, "cloud_fallback_chain", [])
        if not chain:
            chain = [
                "openrouter/google/gemini-2.0-flash-001",
                "gemini/gemini-2.0-flash",
                "openrouter/anthropic/claude-3.5-sonnet",
            ]

        key_map = {
            "openrouter": ["OPENROUTER_API_KEY"],
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "google": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "groq": ["GROQ_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
        }

        for tier, model in enumerate(chain, start=1):
            prov = model.split("/")[0].lower() if "/" in model else "unknown"
            req_keys = key_map.get(prov, [f"{prov.upper()}_API_KEY"])
            has_key = any(bool(os.environ.get(k)) for k in req_keys)

            if prov in self._degraded_providers:
                circuit_state = "DEGRADED (TRIPPED)"
            elif has_key:
                circuit_state = "ONLINE (ARMED)"
            else:
                circuit_state = "STANDBY (KEY UNSET)"

            results.append(
                {
                    "tier": tier,
                    "model": model,
                    "provider": prov,
                    "circuit_state": circuit_state,
                    "has_key": has_key,
                    "keys_checked": req_keys,
                }
            )
        return results
