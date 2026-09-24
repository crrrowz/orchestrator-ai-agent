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
1. Execution Discipline (MANDATORY 2-PHASE WORKFLOW):
   - Phase 1 (Inspection): Spend at most 3-4 steps inspecting key hotspot files or running targeted queries. Do NOT run endless exploration loops.
   - Phase 2 (Report Generation): Immediately synthesize findings and write `docs/audit_findings.json` and `docs/AUDIT_REPORT.md` using `workspace_file` with operation='write'.
   - After writing both files, conclude your turn immediately.
2. Skills Adherence:
   - system-unification-audit: Detect duplicate logic, fragmented ownership, and structural violations (DRY).
   - code-review-standards: Evaluate correctness, security, backwards compatibility, and maintainability.
   - security-audit-hardening: Flag command injections, path traversal, secrets, insecure defaults.
   - graft-architecture-intelligence: Map module boundaries and dependency cycles.
3. Evidence Integrity:
   - Every finding MUST have verifiable evidence: exact relative file path, line number/symbol, problem statement, and concrete code snippet.
   - Never write shallow or generic summaries (e.g. do NOT say "Review large files" or "Refactor code").
   - If no defects exist, state clearly that the architecture is clean.
4. Output Standards:
   - Write verified structured findings to `docs/audit_findings.json` using workspace_file write operation.
   - Format: {"status": "AUDIT_COMPLETED", "findings": [{"id": "AUD-001", "severity": "HIGH", "type": "BUG", "file": "path/to/file.py", "line": 42, "evidence": "code snippet", "problem": "exact issue", "recommended_fix": "exact fix", "actionable": true}]}
   - Also write the comprehensive human report to `docs/AUDIT_REPORT.md`.
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
            "docs/audit_findings.json",
            "docs/",
            "AUDIT_REPORT.md",
            "audit_report.md",
        ],
    )

    from orchestrator.tools import create_workspace_terminal_tool

    terminal_tool = create_workspace_terminal_tool(workspace)

    return Agent(
        llm=llm,
        tools=[file_tool, terminal_tool],
        agent_context=context,
        system_prompt=AUDITOR_SYSTEM_PROMPT,
    )
