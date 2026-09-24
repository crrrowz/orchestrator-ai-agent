"""Cloud Resilience Mesh for multi-tier provider failover, latency radar, and quota protection."""

import time
from typing import Dict, List, Optional, Tuple

from orchestrator.sentinel.protocols import ICloudResilienceMesh
from orchestrator.sentinel.schemas import CloudProviderHealth, ProviderHealthStatus


class CloudResilienceMesh(ICloudResilienceMesh):
    """Manages cloud provider health, latency probing, quota circuit-breakers, and automated failover."""

    DEFAULT_FALLBACK_CHAIN: List[str] = [
        "google/gemini-3.7-flash",
        "openrouter/google/gemini-2.5-flash",
        "openrouter/qwen/qwen-2.5-72b-instruct",
        "groq/llama-3.3-70b-versatile",
        "openrouter/anthropic/claude-3-5-sonnet",
    ]

    def __init__(self, fallback_chain: Optional[List[str]] = None):
        self.fallback_chain = fallback_chain or list(self.DEFAULT_FALLBACK_CHAIN)
        self.providers: Dict[str, CloudProviderHealth] = {}
        self.circuit_breaker_threshold: int = 3
        self._init_providers()

    def _init_providers(self) -> None:
        for model in self.fallback_chain:
            provider_id = model.split("/")[0] if "/" in model else "custom"
            self.providers[model] = CloudProviderHealth(
                provider_id=provider_id,
                model_name=model,
                status=ProviderHealthStatus.ONLINE,
                latency_ms=0.0,
                consecutive_failures=0,
                total_calls=0,
                quota_exhausted=False,
                last_checked_epoch=time.time(),
            )

    def record_call_success(self, provider_model: str, latency_ms: float = 0.0) -> None:
        """Records a successful cloud LLM invocation."""
        if provider_model not in self.providers:
            self._init_single(provider_model)
        health = self.providers[provider_model]
        health.total_calls += 1
        health.consecutive_failures = 0
        health.latency_ms = latency_ms
        health.status = ProviderHealthStatus.ONLINE
        health.quota_exhausted = False
        health.last_checked_epoch = time.time()

    def record_call_failure(
        self, provider_model: str, error_text: str
    ) -> Tuple[bool, Optional[str]]:
        """Records an invocation failure and calculates whether failover is required."""
        if provider_model not in self.providers:
            self._init_single(provider_model)

        health = self.providers[provider_model]
        health.total_calls += 1
        health.consecutive_failures += 1
        health.last_checked_epoch = time.time()

        err_lower = error_text.lower()
        is_429 = "429" in error_text or "ratelimit" in err_lower or "quota" in err_lower
        is_server_err = (
            "500" in error_text
            or "502" in error_text
            or "503" in error_text
            or "504" in error_text
        )

        if is_429 or "insufficient_quota" in err_lower:
            health.status = ProviderHealthStatus.QUOTA_EXHAUSTED
            health.quota_exhausted = True
        elif (
            health.consecutive_failures >= self.circuit_breaker_threshold
            or is_server_err
        ):
            health.status = ProviderHealthStatus.DEGRADED

        should_failover = health.quota_exhausted or health.status in (
            ProviderHealthStatus.QUOTA_EXHAUSTED,
            ProviderHealthStatus.DEGRADED,
        )

        if should_failover:
            next_candidate = self.get_healthy_provider(exclude_model=provider_model)
            return True, next_candidate

        return False, None

    def get_healthy_provider(
        self, requested_model: Optional[str] = None, exclude_model: Optional[str] = None
    ) -> str:
        """Finds the healthiest model candidate in the fallback mesh."""
        if requested_model and requested_model in self.providers:
            p = self.providers[requested_model]
            if (
                not p.quota_exhausted
                and p.status == ProviderHealthStatus.ONLINE
                and requested_model != exclude_model
            ):
                return requested_model

        for candidate in self.fallback_chain:
            if candidate == exclude_model:
                continue
            if candidate in self.providers:
                p = self.providers[candidate]
                if not p.quota_exhausted and p.status != ProviderHealthStatus.OFFLINE:
                    return candidate
            else:
                return candidate

        for candidate in self.fallback_chain:
            if candidate != exclude_model:
                return candidate

        return requested_model or self.fallback_chain[0]

    def _init_single(self, model: str) -> None:
        provider_id = model.split("/")[0] if "/" in model else "custom"
        self.providers[model] = CloudProviderHealth(
            provider_id=provider_id,
            model_name=model,
            status=ProviderHealthStatus.ONLINE,
            latency_ms=0.0,
            consecutive_failures=0,
            total_calls=0,
            quota_exhausted=False,
            last_checked_epoch=time.time(),
        )

    @staticmethod
    def calculate_backoff_delay(
        attempt: int, base_delay: float = 1.0, max_delay: float = 30.0
    ) -> float:
        """Calculate exponential backoff with full jitter to avoid thundering herd."""
        import random

        backoff = min(max_delay, base_delay * (2**attempt))
        jitter = random.uniform(0.0, 0.5) * backoff
        return backoff + jitter

    @staticmethod
    def extract_retry_after(error_text: str) -> Optional[float]:
        """Extract retry-after duration in seconds if present in error message."""
        import re

        m = re.search(
            r"(?:retry[-_ ]after|resets in|wait)[:\s]+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?",
            error_text,
            re.IGNORECASE,
        )
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
        return None

    def get_dashboard_summary(self) -> Dict[str, Dict]:
        """Returns snapshot for TUI rendering."""
        return {
            m: {
                "status": h.status.value,
                "latency_ms": round(h.latency_ms, 1),
                "calls": h.total_calls,
                "quota_exhausted": h.quota_exhausted,
            }
            for m, h in self.providers.items()
        }
