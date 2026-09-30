"""Central Context Manager for prompt assembly and token budget management."""

from pathlib import Path
from typing import List, Optional, Tuple

from orchestrator.core.config import OrchestratorConfig
from orchestrator.context.file_resolver import FilePathResolver
from orchestrator.context.injectors import (
    CIFailureReportInjector,
    ContextInjector,
    GraftInjector,
    MemoryInjector,
    PlanInjector,
)


class ContextManager:
    """Central assembly engine for multi-agent prompt construction and token governance."""

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        # (priority, injector)
        self._injectors: List[Tuple[int, ContextInjector]] = []

    def register(self, injector: ContextInjector, priority: int = 50) -> None:
        """Register a context source with priority (lower number = higher priority)."""
        self._injectors.append((priority, injector))
        self._injectors.sort(key=lambda x: x[0])

    @classmethod
    def create_default(
        cls, config: Optional[OrchestratorConfig] = None
    ) -> "ContextManager":
        """Instantiate a ContextManager populated with standard enterprise injectors."""
        cfg = config or OrchestratorConfig()
        mgr = cls(cfg)
        mgr.register(
            GraftInjector(
                max_chars=getattr(cfg, "graft_max_map_chars", 1500),
                enabled=getattr(cfg, "graft_enabled", True),
            ),
            priority=30,
        )
        mgr.register(MemoryInjector(enabled=cfg.enable_memory), priority=40)
        mgr.register(PlanInjector(), priority=50)
        mgr.register(CIFailureReportInjector(enabled=True), priority=60)
        return mgr

    def build_prompt(
        self,
        task: str,
        role: str,
        workspace: Path,
        max_tokens: int = 6000,
        extra_instructions: str = "",
    ) -> str:
        """Assemble a complete prompt with all relevant context blocks within token budget."""
        # 1. Resolve embedded file paths in task text
        resolved_task, _ = FilePathResolver.extract_and_resolve(task, workspace)

        blocks: List[str] = []
        if extra_instructions.strip():
            blocks.append(extra_instructions.strip())

        task_str = resolved_task.strip()
        max_chars = max_tokens * 4
        if len(task_str) > max_chars - 500 and max_chars > 1000:
            task_str = (
                task_str[: max_chars - 600]
                + "\n... [Task specification truncated to token ceiling]"
            )

        blocks.append(f"Task Specification:\n{task_str}")

        # Approximate token count (1 token ~= 4 chars)
        current_chars = sum(len(b) for b in blocks)

        for _priority, injector in self._injectors:
            if not injector.should_inject(role=role, task=resolved_task):
                continue

            block = injector.get_context(task=resolved_task, workspace=workspace)
            if not block or not block.strip():
                continue

            block_clean = block.strip()
            block_len = len(block_clean)

            if current_chars + block_len > max_chars:
                remaining_chars = max_chars - current_chars
                if remaining_chars > 200:
                    truncated = (
                        block_clean[:remaining_chars]
                        + "\n... [Context Truncated to fit token budget]"
                    )
                    blocks.append(truncated)
                break

            blocks.append(block_clean)
            current_chars += block_len

        return "\n\n".join(blocks)
