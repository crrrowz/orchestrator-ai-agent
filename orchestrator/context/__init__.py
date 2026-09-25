"""Context management and prompt construction package."""

from orchestrator.context.file_resolver import FilePathResolver
from orchestrator.context.injectors import (
    ContextInjector,
    GraftInjector,
    MemoryInjector,
    PlanInjector,
)
from orchestrator.context.manager import ContextManager
from orchestrator.context.prompt_builder import PromptBuilder
from orchestrator.context.handoff import (
    ContextTier,
    ContextTierEnum,
    HandoffType,
    HandoffTypeEnum,
    PersonaViewType,
    FreshnessState,
    CrossAgentHandoffPayload,
    HandoffEnvelope,
    RequiredSymbolSpec,
    LineAnchoredFix,
    DiagnosticTraceCompactor,
    DiagnosticCompactor,
    FreshnessValidator,
    ContextSynthesizer,
    CrossAgentContextManager,
)

__all__ = [
    "ContextManager",
    "ContextInjector",
    "GraftInjector",
    "MemoryInjector",
    "PlanInjector",
    "FilePathResolver",
    "PromptBuilder",
    # P6 Handoff Mesh Exports
    "ContextTier",
    "ContextTierEnum",
    "HandoffType",
    "HandoffTypeEnum",
    "PersonaViewType",
    "FreshnessState",
    "CrossAgentHandoffPayload",
    "HandoffEnvelope",
    "RequiredSymbolSpec",
    "LineAnchoredFix",
    "DiagnosticTraceCompactor",
    "DiagnosticCompactor",
    "FreshnessValidator",
    "ContextSynthesizer",
    "CrossAgentContextManager",
]
