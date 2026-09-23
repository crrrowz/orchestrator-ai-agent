"""Auditor Agent Factory for deep codebase analysis and audit report generation."""

from pathlib import Path
from typing import Optional

from openhands.sdk import Agent
from orchestrator.config import OrchestratorConfig, SkillManager, create_llm_for_role
from orchestrator.tools import (
    create_workspace_file_tool,
    create_workspace_terminal_tool,
)


def create_auditor_agent(
    config: OrchestratorConfig,
    skill_manager: SkillManager,
    workspace_path: Optional[Path] = None,
) -> Agent:
    """Build an Auditor agent driven by architectural skills with docs/ report write permissions."""
    workspace = (workspace_path or config.workspace_path).resolve()

    llm = create_llm_for_role(config, config.reviewer)
    auditor_skills = [
        "code-review-standards",
        "security-audit-hardening",
        "graft-architecture-intelligence",
        "system-unification-audit",
    ]
    context = skill_manager.build_agent_context(auditor_skills)

    file_tool = create_workspace_file_tool(
        workspace,
        read_only=False,
        allowed_write_prefixes=[
            "docs/AUDIT_REPORT.md",
            "docs/audit_report.md",
            "docs/",
            "AUDIT_REPORT.md",
            "audit_report.md",
        ],
    )
    terminal_tool = create_workspace_terminal_tool(workspace)

    return Agent(
        llm=llm,
        tools=[file_tool, terminal_tool],
        agent_context=context,
    )

