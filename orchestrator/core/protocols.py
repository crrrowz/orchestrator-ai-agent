"""Typing protocols defining clean architectural boundaries without tight coupling."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from openhands.sdk import Agent, LLM


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
    ) -> None:
        ...

    def save_to_file(self) -> Optional[Path]:
        ...
