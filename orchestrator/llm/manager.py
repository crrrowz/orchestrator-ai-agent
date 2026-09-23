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
    def get_instance(cls, config: Optional["OrchestratorConfig"] = None) -> "LLMManager":
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
                role_config = AgentRoleConfig(role=role, model="openrouter/qwen/qwen3.8-27b:free")
            self._pool[role] = create_llm_for_role(self._config, role_config)
        return self._pool[role]

    def get_role_usage(self, role: str) -> Dict[str, Any]:
        """Fetch usage stats for a specific agent role."""
        if role in self._pool:
            return get_llm_usage(self._pool[role])
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "estimated_cost_usd": 0.0}

    def get_total_cost(self) -> float:
        """Aggregate total estimated cost (USD) across all active LLM pool instances."""
        return sum(get_llm_usage(llm)["estimated_cost_usd"] for llm in self._pool.values())

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

    def reset_pool(self) -> None:
        """Clear all pooled LLM instances."""
        self._pool.clear()
