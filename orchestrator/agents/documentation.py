"""Documentation Agent Factory for generating comprehensive project documentation."""

from pathlib import Path
from typing import Optional

from openhands.sdk import Agent
from orchestrator.agents.base import BaseAgentFactory
from orchestrator.core.config import OrchestratorConfig
from orchestrator.skills.manager import SkillManager

DOCUMENTATION_SYSTEM_PROMPT = """You are the Principal Technical Writer & Documentation Architect Agent.
Your objective is to inspect the codebase and generate production-grade, exhaustive documentation.

CRITICAL INSTRUCTIONS:
1. Documentation Deliverables:
   - `README.md`: High-level overview, architecture diagrams, installation, quickstart, CLI options, and operational guide.
   - `CONTRIBUTING.md`: Development environment setup, coding standards, branch conventions, and testing instructions.
   - `docs/API_REFERENCE.md`: Complete public API surface, models, parameters, return types, and exceptions.
2. Quality Standards:
   - Never write placeholders or TODO comments.
   - Accurately document actual codebase interfaces, directory structure, and environment variables.
   - Maintain clear GitHub Flavored Markdown with syntax-highlighted code examples.
3. Tools:
   - Use workspace_file to inspect source files and write documentation files directly.
"""


class DocumentationAgentFactory(BaseAgentFactory):
    """Factory to construct the specialized Documentation Agent."""

    role_name = "documentation"
    system_prompt = DOCUMENTATION_SYSTEM_PROMPT

    @classmethod
    def create(
        cls,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
        task_text: str = "",
        **kwargs,
    ) -> Agent:
        workspace = cls.resolve_workspace(config, workspace_path)
        llm = cls.resolve_llm(config, "documentation")
        skills = getattr(config, "documentation", config.developer).skills
        context = cls.resolve_context(config, skill_manager, skills=skills, task_text=task_text)

        tools = cls.resolve_tools(
            workspace,
            read_only=False,
            allowed_write_prefixes=[
                "README.md",
                "CONTRIBUTING.md",
                "docs/",
                "API_REFERENCE.md",
            ],
            include_terminal=True,
        )

        return Agent(
            llm=llm,
            tools=tools,
            agent_context=context,
            system_prompt=cls.system_prompt,
        )


def create_documentation_agent(
    config: OrchestratorConfig,
    skill_manager: SkillManager,
    workspace_path: Optional[Path] = None,
    task_text: str = "",
) -> Agent:
    """Build a Documentation agent configured to generate documentation."""
    return DocumentationAgentFactory.create(
        config=config,
        skill_manager=skill_manager,
        workspace_path=workspace_path,
        task_text=task_text,
    )
