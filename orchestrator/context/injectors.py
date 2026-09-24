"""Modular Context Injectors for Prompt Assembly."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class ContextInjector(ABC):
    """Abstract base class for all context injection sources."""

    @abstractmethod
    def should_inject(self, role: str, task: str) -> bool:
        """Predicate checking whether this context block is relevant for the role and task."""
        pass

    @abstractmethod
    def get_context(self, task: str, workspace: Path) -> Optional[str]:
        """Produce the formatted context text to be included in the agent prompt."""
        pass


class GraftInjector(ContextInjector):
    """Injects cached or generated codebase architecture graphs from Graft."""

    def __init__(self, max_chars: int = 1500, enabled: bool = True):
        self.max_chars = max_chars
        self.enabled = enabled

    def should_inject(self, role: str, task: str) -> bool:
        if not self.enabled:
            return False
        # Inject for architect and developer roles
        return role in ("architect", "developer", "auditor")

    def get_context(self, task: str, workspace: Path) -> Optional[str]:
        try:
            from orchestrator.analysis.graft_context import GraftContextProvider

            graft_map = GraftContextProvider.get_condensed_map(
                workspace, max_chars=self.max_chars
            )
            if graft_map and graft_map.strip():
                return f"[Codebase Architecture Map (Graft)]:\n{graft_map.strip()}"
        except Exception:
            pass
        return None


class MemoryInjector(ContextInjector):
    """Injects historical conversation lessons and session outcomes."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def should_inject(self, role: str, task: str) -> bool:
        if not self.enabled:
            return False
        return role in ("architect", "developer", "tester", "reviewer")

    def get_context(self, task: str, workspace: Path) -> Optional[str]:
        try:
            from orchestrator.memory.conversation_store import SessionMemoryStore

            store = SessionMemoryStore(workspace_path=workspace)
            mem_text = store.format_memory_context(task)
            if mem_text and mem_text.strip():
                return mem_text.strip()
        except Exception:
            pass
        return None


class PlanInjector(ContextInjector):
    """Injects PLAN.md contents or structured milestones into prompt."""

    def should_inject(self, role: str, task: str) -> bool:
        # Relevant for developer and tester roles
        return role in ("developer", "tester", "reviewer")

    def get_context(self, task: str, workspace: Path) -> Optional[str]:
        plan_file = workspace / "PLAN.md"
        if plan_file.is_file():
            try:
                content = plan_file.read_text(
                    encoding="utf-8", errors="replace"
                ).strip()
                if content:
                    return f"[System Blueprint (PLAN.md)]:\n{content}"
            except Exception:
                pass
        return None
