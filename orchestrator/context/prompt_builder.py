"""Prompt composition builder for multi-agent roles."""

from pathlib import Path
from typing import List, Optional

from orchestrator.core.config import OrchestratorConfig
from orchestrator.context.manager import ContextManager


class PromptBuilder:
    """Fluent builder for constructing structured agent prompts."""

    def __init__(self, role: str, config: Optional[OrchestratorConfig] = None):
        self.role = role
        self.config = config or OrchestratorConfig()
        self._sections: List[str] = []
        self._directives: List[str] = []

    def add_directive(self, directive: str) -> "PromptBuilder":
        """Add a high-priority system directive or requirement."""
        if directive.strip():
            self._directives.append(directive.strip())
        return self

    def add_section(self, title: str, content: str) -> "PromptBuilder":
        """Add a named markdown section to the prompt."""
        if content.strip():
            self._sections.append(f"### {title}\n{content.strip()}")
        return self

    def build(self, task: str, workspace: Path, max_tokens: int = 6000) -> str:
        """Compose the final prompt using ContextManager."""
        ctx_mgr = ContextManager.create_default(self.config)
        extra = "\n\n".join(self._directives + self._sections)
        return ctx_mgr.build_prompt(
            task=task,
            role=self.role,
            workspace=workspace,
            max_tokens=max_tokens,
            extra_instructions=extra,
        )
