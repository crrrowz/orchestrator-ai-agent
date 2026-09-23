"""Main Orchestrator coordinator class."""

from pathlib import Path
from typing import Literal, Optional

from orchestrator.config import ORCHESTRATOR_ROOT, OrchestratorConfig, SkillManager
from orchestrator.pipeline import DevTestLoop, FullPipeline
from orchestrator.pipeline.checkpoint import PipelineCheckpoint
from orchestrator.utils import ConsoleOutput, GitOps


class Orchestrator:
    """Coordinates specialized AI agents using OpenHands SDK and architectural skills."""

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.skill_manager = SkillManager(ORCHESTRATOR_ROOT)
        self.workspace = self.config.workspace_path

    def run_task(
        self,
        task: str,
        mode: Literal["dev-test", "full"] = "dev-test",
        workspace_override: Optional[Path] = None,
        checkpoint: Optional[PipelineCheckpoint] = None,
    ) -> dict:
        """Run an autonomous multi-agent task execution."""
        ws = (workspace_override or self.workspace).resolve()

        if mode == "full":
            pipeline = FullPipeline(self.config, self.skill_manager, ws, checkpoint=checkpoint)
        else:
            pipeline = DevTestLoop(self.config, self.skill_manager, ws, checkpoint=checkpoint)

        return pipeline.run(task)
