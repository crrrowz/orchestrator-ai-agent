"""Configuration and Skill Management for Multi-Agent Orchestrator."""

from orchestrator.core.config import AgentRoleConfig, DomainProfile, OrchestratorConfig
from orchestrator.core.constants import (
    DEFAULT_CONFIG_FILENAME,
    DEFAULT_DIAGNOSTICS_DIR,
    DEFAULT_WORKSPACE_DIR,
    ORCHESTRATOR_ROOT,
)
from orchestrator.core.exceptions import (
    BudgetExhaustedError,
    CircuitBreakerTrippedError,
    HumanRejectedError,
    OrchestratorException,
    PipelineAbortedError,
    PreflightCheckError,
)
from orchestrator.core.protocols import (
    AgentFactoryProtocol,
    ContextInjectorProtocol,
    LogStoreProtocol,
    PipelineProtocol,
)
from orchestrator.config.loader import ConfigLoader
from orchestrator.config.schema import ConfigSchema
from orchestrator.context import ContextManager, FilePathResolver, PromptBuilder
from orchestrator.llm import (
    LLMManager,
    create_llm_for_role,
    get_pricing_rates,
    normalize_model_slug,
)
from orchestrator.skills import (
    CompactSkillInjector,
    SkillManager,
    SkillMetadata,
    SkillRegistry,
    SkillResolver,
)

__all__ = [
    "ORCHESTRATOR_ROOT",
    "DEFAULT_DIAGNOSTICS_DIR",
    "DEFAULT_WORKSPACE_DIR",
    "DEFAULT_CONFIG_FILENAME",
    "AgentRoleConfig",
    "DomainProfile",
    "OrchestratorConfig",
    "OrchestratorException",
    "BudgetExhaustedError",
    "CircuitBreakerTrippedError",
    "PipelineAbortedError",
    "PreflightCheckError",
    "HumanRejectedError",
    "AgentFactoryProtocol",
    "ContextInjectorProtocol",
    "PipelineProtocol",
    "LogStoreProtocol",
    "SkillManager",
    "SkillMetadata",
    "SkillRegistry",
    "SkillResolver",
    "CompactSkillInjector",
    "normalize_model_slug",
    "create_llm_for_role",
    "ConfigLoader",
    "ConfigSchema",
    "ContextManager",
    "PromptBuilder",
    "FilePathResolver",
    "LLMManager",
    "get_pricing_rates",
]
