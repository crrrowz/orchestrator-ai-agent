"""Context & Evidence Handoff Mesh Package.

File Location: orchestrator/context/handoff/__init__.py
Architecture Reference: docs/plans/P6_CONTEXT_AND_EVIDENCE_HANDOFF_PLAN.md
"""

from orchestrator.context.handoff.compactor import (
    DiagnosticCompactor,
    DiagnosticTraceCompactor,
)
from orchestrator.context.handoff.freshness import FreshnessValidator
from orchestrator.context.handoff.manager import CrossAgentContextManager
from orchestrator.context.handoff.models import (
    ArchitectHandoffPayload,
    CompactedFrame,
    ContextBlock,
    ContextHeadroomExhaustionError,
    ContextTier,
    ContextTierEnum,
    CrossAgentHandoffPayload,
    DeveloperHandoffPayload,
    DiagnosticFailureTrace,
    DiagnosticTraceSummary,
    FileContentDigest,
    FreshnessState,
    FreshnessStateEnum,
    HandoffEnvelope,
    HandoffError,
    HandoffIntegrityError,
    HandoffType,
    HandoffTypeEnum,
    LineAnchoredFix,
    MissingHandoffArtifactError,
    PersonaViewType,
    PersonaViewTypeEnum,
    RequiredSymbolSpec,
    StaleEvidenceError,
    SubjectFingerprint,
    TesterHandoffPayload,
    ReviewerHandoffPayload,
    WorkspaceDigest,
)
from orchestrator.context.handoff.synthesizer import ContextSynthesizer

__all__ = [
    # Enums & Constants
    "ContextTier",
    "ContextTierEnum",
    "HandoffType",
    "HandoffTypeEnum",
    "PersonaViewType",
    "PersonaViewTypeEnum",
    "FreshnessState",
    "FreshnessStateEnum",
    # Exceptions
    "HandoffError",
    "MissingHandoffArtifactError",
    "HandoffIntegrityError",
    "ContextHeadroomExhaustionError",
    "StaleEvidenceError",
    # Data Models
    "RequiredSymbolSpec",
    "LineAnchoredFix",
    "CompactedFrame",
    "DiagnosticFailureTrace",
    "DiagnosticTraceSummary",
    "ContextBlock",
    "SubjectFingerprint",
    "FileContentDigest",
    "WorkspaceDigest",
    # Typed Handoffs & Envelopes
    "ArchitectHandoffPayload",
    "DeveloperHandoffPayload",
    "TesterHandoffPayload",
    "ReviewerHandoffPayload",
    "CrossAgentHandoffPayload",
    "HandoffEnvelope",
    # Engines & Subsystems
    "DiagnosticCompactor",
    "DiagnosticTraceCompactor",
    "FreshnessValidator",
    "ContextSynthesizer",
    "CrossAgentContextManager",
]
