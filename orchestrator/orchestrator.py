"""Main Orchestrator coordinator class."""

from pathlib import Path
from typing import Literal, Optional

from orchestrator.config import ORCHESTRATOR_ROOT, OrchestratorConfig, SkillManager
from orchestrator.pipeline import (
    DevTestLoop,
    FullPipeline,
    AuditPipeline,
    AuditFixPipeline,
)
from orchestrator.pipeline.checkpoint import PipelineCheckpoint
from orchestrator.utils import ConsoleOutput


class Orchestrator:
    """Coordinates specialized AI agents using OpenHands SDK and architectural skills."""

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.skill_manager = SkillManager(ORCHESTRATOR_ROOT)
        self.workspace = self.config.workspace_path

    def run_task(
        self,
        task: str,
        mode: Literal["dev-test", "full", "audit", "audit-fix"] = "dev-test",
        workspace_override: Optional[Path] = None,
        checkpoint: Optional[PipelineCheckpoint] = None,
    ) -> dict:
        """Run an autonomous multi-agent task execution."""
        raw_ws = (workspace_override or self.workspace).resolve()
        # Guard against file path accidentally passed as workspace directory
        if raw_ws.is_file():
            ConsoleOutput.warning(
                f"Target workspace '{raw_ws}' is a file. Resolving to parent directory: '{raw_ws.parent}'."
            )
            ws = raw_ws.parent
        else:
            ws = raw_ws

        if mode == "audit":
            pipeline = AuditPipeline(self.config, self.skill_manager, ws)
        elif mode == "audit-fix":
            pipeline = AuditFixPipeline(self.config, self.skill_manager, ws)
        elif mode == "full":
            pipeline = FullPipeline(
                self.config, self.skill_manager, ws, checkpoint=checkpoint
            )
        else:
            pipeline = DevTestLoop(
                self.config, self.skill_manager, ws, checkpoint=checkpoint
            )

        return pipeline.run(task)
