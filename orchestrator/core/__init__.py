"""Core primitives, models, exceptions, constants, and protocols for the Orchestrator."""

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
]
