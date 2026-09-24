"""Cloud LLM mesh governor, quota monitoring, and circuit breaker."""

import time
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.core.constants import SENTINEL_CIRCUIT_BREAKER_THRESHOLD


class CloudMeshGovernor:
    """Manages cloud provider health, latency metrics, and auto-failover chains."""

    def __init__(
        self,
        fallback_chain: Optional[List[str]] = None,
        max_prompt_ceiling: int = 150_000,
        circuit_threshold: int = SENTINEL_CIRCUIT_BREAKER_THRESHOLD,
    ) -> None:
        self.fallback_chain: List[str] = fallback_chain or [
            "openrouter/google/gemini-2.0-flash-exp:free",
            "openrouter/qwen/qwen3.8-27b:free",
            "groq/llama-3.3-70b-versatile",
        ]
        self.max_prompt_ceiling = max_prompt_ceiling
        self.circuit_threshold = circuit_threshold
        # State tracking: {provider_or_model: {...}}
        self._provider_stats: Dict[str, Dict[str, Any]] = {}

    def _get_stats(self, key: str) -> Dict[str, Any]:
        if key not in self._provider_stats:
            self._provider_stats[key] = {
                "failures": 0,
                "consecutive_429": 0,
                "is_tripped": False,
                "tripped_at": 0.0,
                "total_calls": 0,
                "latencies": [],
            }
        return self._provider_stats[key]

    def intercept_cloud_call(
        self, provider: str, model: str, prompt_tokens: int
    ) -> Tuple[bool, str, Optional[str]]:
        """Pre-evaluates cloud quota and cost ceilings.

        Returns:
            Tuple[bool, str, Optional[str]]: (can_proceed, reason, fallback_model)
        """
        key = f"{provider}/{model}" if provider and model else (model or provider)
        stats = self._get_stats(key)

        # 1. Check prompt ceiling
        if prompt_tokens > self.max_prompt_ceiling:
            fallback = self._get_next_fallback(model)
            return (
                False,
                f"Prompt tokens ({prompt_tokens}) exceed safety ceiling ({self.max_prompt_ceiling})",
                fallback,
            )

        # 2. Check if circuit is currently open
        if stats["is_tripped"]:
            # Auto-reset circuit after 60 seconds (cool-down period)
            if time.time() - stats["tripped_at"] > 60.0:
                stats["is_tripped"] = False
                stats["failures"] = 0
                stats["consecutive_429"] = 0
            else:
                fallback = self._get_next_fallback(model)
                return (
                    False,
                    f"Provider/model '{key}' circuit breaker is TRIPPED ({stats['failures']} consecutive failures)",
                    fallback,
                )

        return True, "Provider verified healthy", None

    def record_call_result(
        self,
        provider: str,
        model: str,
        success: bool,
        latency_ms: float,
        status_code: Optional[int] = None,
        error_message: str = "",
    ) -> Optional[str]:
        """Records call outcome and updates circuit breaker state.

        Returns:
            Optional[str]: Recommended fallback model if circuit tripped, else None.
        """
        key = f"{provider}/{model}" if provider and model else (model or provider)
        stats = self._get_stats(key)
        stats["total_calls"] += 1
        stats["latencies"].append(latency_ms)
        if len(stats["latencies"]) > 20:
            stats["latencies"].pop(0)

        if success:
            stats["failures"] = 0
            stats["consecutive_429"] = 0
            return None

        # Failure handling
        stats["failures"] += 1
        if (
            status_code == 429
            or "rate limit" in error_message.lower()
            or "quota" in error_message.lower()
        ):
            stats["consecutive_429"] += 1

        if stats["failures"] >= self.circuit_threshold or stats["consecutive_429"] >= 2:
            stats["is_tripped"] = True
            stats["tripped_at"] = time.time()
            return self._get_next_fallback(model)

        return None

    def _get_next_fallback(self, current_model: str) -> Optional[str]:
        """Find the next available healthy model in fallback chain."""
        for candidate in self.fallback_chain:
            if candidate != current_model:
                cand_stats = self._get_stats(candidate)
                if not cand_stats["is_tripped"]:
                    return candidate
        return self.fallback_chain[0] if self.fallback_chain else None

    def get_health_status(self) -> Dict[str, Any]:
        """Summary of provider latency and circuit health."""
        summary: Dict[str, Any] = {}
        for key, stats in self._provider_stats.items():
            avg_lat = (
                sum(stats["latencies"]) / len(stats["latencies"])
                if stats["latencies"]
                else 0.0
            )
            summary[key] = {
                "tripped": stats["is_tripped"],
                "failures": stats["failures"],
                "avg_latency_ms": round(avg_lat, 2),
                "total_calls": stats["total_calls"],
            }
        return summary
