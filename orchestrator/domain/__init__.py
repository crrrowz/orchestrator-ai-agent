"""ORAGAI Pure Domain Core Package.

Classification: Enterprise Architectural Blueprint & Canonical System Standard
Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant: Zero external framework dependencies (stdlib + pydantic only).
"""

from __future__ import annotations

from orchestrator.domain.task_truth import (
    AcceptanceCriterion,
    ImplementationState,
    Requirement,
    RequirementCategory,
    TaskMilestone,
    TaskTruthGraph,
    VerificationState,
)
from orchestrator.domain.evidence import EvidenceReference, EvidenceType
from orchestrator.domain.audit_models import (
    FindingCategory,
    FindingDAG,
    FindingSeverity,
    VerifiedAuditFinding,
)
from orchestrator.domain.recovery_models import (
    MutationStrategy,
    RecoveryDecision,
    VelocityVector,
)
from orchestrator.domain.context_models import (
    ContextTier,
    HandoffEnvelope,
    HandoffType,
)

__all__ = [
    "RequirementCategory",
    "ImplementationState",
    "VerificationState",
    "AcceptanceCriterion",
    "Requirement",
    "TaskMilestone",
    "TaskTruthGraph",
    "EvidenceType",
    "EvidenceReference",
    "FindingCategory",
    "FindingSeverity",
    "VerifiedAuditFinding",
    "FindingDAG",
    "MutationStrategy",
    "VelocityVector",
    "RecoveryDecision",
    "ContextTier",
    "HandoffType",
    "HandoffEnvelope",
]
