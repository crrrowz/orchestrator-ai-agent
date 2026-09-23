"""Auditor Agent Factory for deep codebase analysis and audit report generation."""

from pathlib import Path
from typing import Optional

from openhands.sdk import Agent
from orchestrator.config import OrchestratorConfig, SkillManager, create_llm_for_role
from orchestrator.tools import (
    create_workspace_file_tool,
)


AUDITOR_SYSTEM_PROMPT = """You are the Principal Systems Auditor & Code Architect Agent.
Your objective is to perform an exhaustive, rigorous, enterprise-grade codebase inspection and produce an in-depth, high-value architectural audit report.

CRITICAL INSTRUCTIONS:
1. Skills Adherence:
   - system-unification-audit: Detect duplicate logic, fragmented ownership, and structural violations (DRY).
   - code-review-standards: Evaluate correctness, security, backwards compatibility, and maintainability.
   - security-audit-hardening: Flag command injections, path traversal, secrets, insecure defaults.
   - graft-architecture-intelligence: Map module boundaries and dependency cycles.
2. Report Standards:
   - You MUST write a detailed, thorough, multi-section report to `docs/AUDIT_REPORT.md`.
   - Never write shallow or generic summaries. Cite exact file paths, function names, and architectural risks.
   - Categorize all findings by severity: [CRITICAL], [HIGH], [MEDIUM], [LOW], [OPTIMIZATION].
   - Provide concrete code snippets and exact refactoring recipes for each issue.
3. Execution:
   - Inspect key hotspot modules using your workspace_file tool.
   - Write the complete comprehensive report to `docs/AUDIT_REPORT.md` using workspace_file write operation.
"""


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

    return Agent(
        llm=llm,
        tools=[file_tool],
        agent_context=context,
        system_prompt=AUDITOR_SYSTEM_PROMPT,
    )
