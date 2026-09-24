"""Autonomous Documentation Pipeline generating enterprise documentation assets."""

import time
from pathlib import Path
from typing import Any, Dict, Optional

from openhands.sdk import Conversation
from orchestrator.agents.documentation import create_documentation_agent
from orchestrator.core.config import OrchestratorConfig
from orchestrator.pipeline.base_pipeline import BasePipeline
from orchestrator.rendering.output import ConsoleOutput
from orchestrator.skills.manager import SkillManager
from orchestrator.telemetry import get_llm_usage


class DocumentationPipeline(BasePipeline):
    """Pipeline orchestrating the DocumentationAgent to generate architecture and user documentation."""

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
        **kwargs: Any,
    ):
        super().__init__(
            config=config,
            skill_manager=skill_manager,
            workspace_path=workspace_path,
            **kwargs,
        )

    def run(self, task_description: str) -> Dict[str, Any]:
        """Execute documentation generation."""
        recorder, memory_store, log_store, visualizer, graft_map = self._setup_run(
            task_description=task_description,
            mode="docs",
            banner_title="Starting Documentation Generation Pipeline",
        )

        doc_agent = create_documentation_agent(
            self.config,
            self.skill_manager,
            self.workspace_path,
            task_text=task_description,
        )

        log_store.set_agent_context(
            "Documentation",
            "Documentation Generation",
            model=doc_agent.llm.model,
            llm=doc_agent.llm,
        )

        ConsoleOutput.pipeline_stage(
            "DOCUMENTATION GENERATION", 1, 1, "Architectural & API reference authoring"
        )

        ConsoleOutput.agent_step(
            "Documentation",
            "Inspecting codebase and authoring documentation...",
            details=f"Task: {task_description}",
            model=doc_agent.llm.model,
        )

        conv = Conversation(
            agent=doc_agent,
            workspace=str(self.workspace_path),
            visualizer=visualizer,
        )

        prompt = (
            f"Generate comprehensive project documentation for this codebase based on: {task_description}.\n\n"
            "Ensure you create or update README.md, CONTRIBUTING.md, and docs/API_REFERENCE.md with full accuracy."
        )

        t0 = time.perf_counter()
        conv.send_message(self.human_channel.inject_into_prompt(prompt))
        self._run_conv(conv, "Documentation")
        dur = time.perf_counter() - t0

        u_doc = get_llm_usage(doc_agent.llm)
        curr_diff = self.git.get_diff() or self.git.get_status()
        recorder.record_step(
            "documentation",
            "generate_docs",
            1,
            dur,
            True,
            curr_diff,
            prompt_tokens=u_doc["prompt_tokens"],
            completion_tokens=u_doc["completion_tokens"],
            total_tokens=u_doc["total_tokens"],
            estimated_cost_usd=u_doc["estimated_cost_usd"],
        )

        return self._finalize_pipeline(
            task_description=task_description,
            success=True,
            iteration=1,
            recorder=recorder,
            memory_store=memory_store,
            log_store=log_store,
            commit_msg_prefix="docs",
        )
