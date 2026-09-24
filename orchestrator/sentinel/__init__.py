"""Autonomous Cognitive Sentinel and Self-Healing SRE Mesh."""

from orchestrator.core.protocols import (
    CognitiveIncident,
    ICloudResilienceMesh,
    ICognitiveSentinel,
    IncidentSeverity,
    InterventionAction,
    ISelfHealingEngine,
)
from orchestrator.sentinel.ast_guard import ASTGuard
from orchestrator.sentinel.cloud_governor import CloudMeshGovernor
from orchestrator.sentinel.cloud_mesh import CloudResilienceMesh
from orchestrator.sentinel.command_interceptor import TerminalCommandTranslator
from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB
from orchestrator.sentinel.heuristics import HeuristicsDriftDetector
from orchestrator.sentinel.schemas import (
    CloudProviderHealth,
    ProviderHealthStatus,
    SentinelDashboardState,
    SentinelMode,
)
from orchestrator.sentinel.self_healing import SelfHealingEngine
from orchestrator.sentinel.supervisor import CognitiveSentinelSupervisor


def get_sentinel_supervisor() -> CognitiveSentinelSupervisor:
    """Convenience helper to access the central Sentinel Supervisor."""
    return CognitiveSentinelSupervisor.get_instance()


__all__ = [
    "CognitiveSentinelSupervisor",
    "get_sentinel_supervisor",
    "ASTGuard",
    "CloudMeshGovernor",
    "CloudResilienceMesh",
    "TerminalCommandTranslator",
    "HeuristicsDriftDetector",
    "SentinelDiagnosticsDB",
    "SelfHealingEngine",
    "ICognitiveSentinel",
    "CognitiveIncident",
    "IncidentSeverity",
    "InterventionAction",
    "ISelfHealingEngine",
    "ICloudResilienceMesh",
    "SentinelMode",
    "ProviderHealthStatus",
    "CloudProviderHealth",
    "SentinelDashboardState",
]
