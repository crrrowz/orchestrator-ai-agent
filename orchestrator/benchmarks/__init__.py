"""ORAGAI Autonomous Benchmark & Verification Engine (Phase 11).

Provides empirical evaluation harnesses, canonical BM-01 through BM-08 benchmarks,
zero-token mock ReAct simulator, false completion detection (FCR == 0.000),
and publication report generation.
"""

from __future__ import annotations

from orchestrator.benchmarks.catalog import BenchmarkCatalog
from orchestrator.benchmarks.evaluator import EmpiricalEvaluator
from orchestrator.benchmarks.models import (
    AgentExitReason,
    BenchmarkDomain,
    BenchmarkEvaluationResult,
    BenchmarkMetricType,
    BenchmarkRequirementCriterion,
    BenchmarkStatus,
    BenchmarkSuiteSummary,
    BenchmarkSuiteType,
    BenchmarkTaskSpec,
    BenchmarkTaskTier,
    InvariantAssertionSpec,
    MockConversationScript,
    MockTurnStep,
)
from orchestrator.benchmarks.runner import BenchmarkRunner

__all__ = [
    # Catalog
    "BenchmarkCatalog",
    # Runner
    "BenchmarkRunner",
    # Evaluator
    "EmpiricalEvaluator",
    # Models & Enums
    "BenchmarkSuiteType",
    "BenchmarkTaskTier",
    "BenchmarkMetricType",
    "BenchmarkStatus",
    "BenchmarkDomain",
    "InvariantAssertionSpec",
    "BenchmarkRequirementCriterion",
    "BenchmarkTaskSpec",
    "MockTurnStep",
    "MockConversationScript",
    "BenchmarkEvaluationResult",
    "BenchmarkSuiteSummary",
    "AgentExitReason",
]
