"""Main Orchestrator coordinator class."""

from pathlib import Path
from typing import Literal, Optional

from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.pipeline import DevTestLoop, FullPipeline
from orchestrator.utils import ConsoleOutput, GitOps


class Orchestrator:
    """Coordinates specialized AI agents using OpenHands SDK and architectural skills."""

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.skill_manager = SkillManager(Path.cwd())
        self.workspace = self.config.workspace_path

    def run_task(
        self,
        task: str,
        mode: Literal["dev-test", "full"] = "dev-test",
        workspace_override: Optional[Path] = None,
    ) -> dict:
        """Run an autonomous multi-agent task execution."""
        ws = (workspace_override or self.workspace).resolve()

        if mode == "full":
            pipeline = FullPipeline(self.config, self.skill_manager, ws)
        else:
            pipeline = DevTestLoop(self.config, self.skill_manager, ws)

        return pipeline.run(task)
