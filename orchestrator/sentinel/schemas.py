"""Data schemas and contracts for Cognitive Sentinel, SRE monitoring, and Self-Healing."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class IncidentSeverity(str, Enum):
    """Classification of severity for intercepted anomalies."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class InterventionAction(str, Enum):
    """Action taken by the Sentinel to resolve or mitigate an incident."""

    PASS_THROUGH = "PASS_THROUGH"
    AUTO_PATCH_CODE = "AUTO_PATCH_CODE"
    INJECT_MISSING_IMPORT = "INJECT_MISSING_IMPORT"
    REWRITE_TERMINAL_CMD = "REWRITE_TERMINAL_CMD"
    MUTATE_PROMPT = "MUTATE_PROMPT"
    SWITCH_CLOUD_PROVIDER = "SWITCH_CLOUD_PROVIDER"
    THROTTLE_TOKENS = "THROTTLE_TOKENS"
    ROLLBACK_WORKSPACE = "ROLLBACK_WORKSPACE"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"


class SentinelMode(str, Enum):
    """Operational mode of the Sentinel."""

    PASSIVE = "passive"
    ENFORCING = "enforcing"
    AUTONOMOUS_SRE = "autonomous_sre"


class ProviderHealthStatus(str, Enum):
    """Health status of a cloud LLM provider."""

    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    OFFLINE = "OFFLINE"


@dataclass
class CognitiveIncident:
    """Detailed record of an intercepted system or runtime anomaly."""

    incident_id: str
    severity: IncidentSeverity
    origin_module: str
    target_role: str
    error_signature: str
    raw_payload: Any = None
    suggested_action: InterventionAction = InterventionAction.PASS_THROUGH
    auto_healed: bool = False
    remedy_description: str = ""
    timestamp_epoch: float = 0.0


@dataclass
class CloudProviderHealth:
    """Realtime health metrics for an upstream cloud provider."""

    provider_id: str
    model_name: str
    status: ProviderHealthStatus = ProviderHealthStatus.ONLINE
    latency_ms: float = 0.0
    consecutive_failures: int = 0
    total_calls: int = 0
    quota_exhausted: bool = False
    last_checked_epoch: float = 0.0


@dataclass
class SentinelDashboardState:
    """Aggregate state payload for Live Terminal UI rendering."""

    sentinel_mode: SentinelMode = SentinelMode.ENFORCING
    is_healthy: bool = True
    total_interceptions: int = 0
    total_auto_heals: int = 0
    active_cloud_provider: str = "default"
    active_cloud_model: str = "default"
    provider_health: Dict[str, CloudProviderHealth] = field(default_factory=dict)
    recent_incidents: List[CognitiveIncident] = field(default_factory=list)
    ast_guard_clean: bool = True
    circuit_breakers_tripped: int = 0
