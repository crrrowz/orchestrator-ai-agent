"""Outbound Driven Ports for ORAGAI Hexagonal Architecture.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from orchestrator.ports.driven.runtime_port import AgentExecutionOutcome, AgentRuntimePort
from orchestrator.ports.driven.tool_port import ToolExecutionPort
from orchestrator.ports.driven.storage_port import TelemetryStoragePort
from orchestrator.ports.driven.vcs_port import RollbackControllerPort, VCSPort
from orchestrator.ports.driven.language_port import (
    CodebaseMetrics,
    CompactedFailureFrame,
    DynamicEcosystemProfile,
    ILanguageDriver,
    LanguageType,
    StaticAnalysisResult,
    StubSeverity,
    StubViolation,
    SymbolEntity,
    SymbolKind,
    SymbolOutline,
    SyntaxCheckResult,
    TestExecutionOutcome,
    TestStatus,
)

__all__ = [
    "AgentExecutionOutcome",
    "AgentRuntimePort",
    "ToolExecutionPort",
    "TelemetryStoragePort",
    "VCSPort",
    "RollbackControllerPort",
    "ILanguageDriver",
    "LanguageType",
    "TestStatus",
    "StubSeverity",
    "SymbolKind",
    "SyntaxCheckResult",
    "CompactedFailureFrame",
    "TestExecutionOutcome",
    "StubViolation",
    "SymbolEntity",
    "SymbolOutline",
    "StaticAnalysisResult",
    "CodebaseMetrics",
    "DynamicEcosystemProfile",
]
