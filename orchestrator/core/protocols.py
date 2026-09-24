"""Typing protocols defining clean architectural boundaries without tight coupling."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Protocol, Tuple, runtime_checkable

from openhands.sdk import Agent


@runtime_checkable
class ContextInjectorProtocol(Protocol):
    """Protocol for pluggable context sources in ContextManager."""

    def should_inject(self, role: str, task: str) -> bool:
        """Return True if context should be injected for the given agent role and task."""
        ...

    def get_context(self, task: str, workspace: Path) -> str:
        """Return formatted markdown context string to be appended to prompt."""
        ...


@runtime_checkable
class PipelineProtocol(Protocol):
    """Protocol for end-to-end execution pipelines."""

    def run(self, task_description: str) -> Dict[str, Any]:
        """Execute the pipeline on a software engineering task."""
        ...


@runtime_checkable
class AgentFactoryProtocol(Protocol):
    """Protocol for agent factories constructing specialized agents."""

    @classmethod
    def create(
        cls,
        config: Any,
        skill_manager: Any,
        workspace_path: Optional[Path] = None,
        **kwargs: Any,
    ) -> Agent:
        """Build and configure the specialized Agent instance."""
        ...


@runtime_checkable
class LogStoreProtocol(Protocol):
    """Protocol for recording interactive session steps."""

    def add_step(
        self,
        title: str,
        content: str = "",
        is_error: bool = False,
        observation: str = "",
    ) -> None: ...

    def save_to_file(self) -> Optional[Path]: ...


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class InterventionAction(str, Enum):
    PASS_THROUGH = "PASS_THROUGH"
    AUTO_PATCH_CODE = "AUTO_PATCH_CODE"
    MUTATE_PROMPT = "MUTATE_PROMPT"
    SWITCH_CLOUD_PROVIDER = "SWITCH_CLOUD_PROVIDER"
    THROTTLE_TOKENS = "THROTTLE_TOKENS"
    ROLLBACK_WORKSPACE = "ROLLBACK_WORKSPACE"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"


@dataclass
class CognitiveIncident:
    """Detailed metadata for an intercepted runtime, AST, or cloud anomaly."""

    incident_id: str
    severity: IncidentSeverity
    origin_module: str
    target_role: str
    error_signature: str
    raw_payload: Any
    suggested_action: InterventionAction
    auto_healed: bool = False
    remedy_description: str = ""
    timestamp_epoch: float = 0.0


@runtime_checkable
class ICognitiveSentinel(Protocol):
    """Formal protocol for the internal AI supervisor and cloud auditor."""

    def intercept_ast_mutation(
        self, file_path: Path, new_code: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Audits AST before disk write; returns (is_safe, error_msg, auto_healed_code)."""
        ...

    def intercept_cloud_call(
        self, provider: str, model: str, prompt_tokens: int
    ) -> Tuple[bool, str, Optional[str]]:
        """Pre-evaluates cloud quota and cost ceilings; returns (can_proceed, reason, fallback_model)."""
        ...

    def handle_runtime_error(
        self, exc: Exception, context: Dict[str, Any]
    ) -> CognitiveIncident:
        """Autonomously decodes runtime errors and synthesizes immediate self-healing actions."""
        ...

    def evaluate_investigation_drift(
        self, role: str, steps: int, tokens_burned: int, edits_done: int
    ) -> bool:
        """Detects cognitive loops and triggers proactive prompt redirection."""
        ...


@runtime_checkable
class ISelfHealingEngine(Protocol):
    """Protocol for AST and code auto-patching engines."""

    def heal_syntax(self, code: str, file_path: Optional[Path] = None) -> Tuple[bool, str]: ...

    def heal_missing_imports(self, code: str) -> str: ...


@runtime_checkable
class ICloudResilienceMesh(Protocol):
    """Protocol for multi-tier provider failover and latency monitoring."""

    def get_healthy_provider(self, requested_provider: str) -> str: ...

    def record_provider_result(
        self, provider: str, success: bool, latency_ms: float, error_code: Optional[int] = None
    ) -> None: ...
