"""Auditor Agent Factory for deep codebase analysis and audit report generation."""

from pathlib import Path
from typing import Optional

from openhands.sdk import Agent
from orchestrator.config import OrchestratorConfig, SkillManager, create_llm_for_role
from orchestrator.tools import (
    create_workspace_file_tool,
    create_workspace_terminal_tool,
)


AUDITOR_SYSTEM_PROMPT = """You are the Senior Code Auditor & Software Architect Agent.
Your objective is to perform an internal audit of an existing codebase and write a comprehensive audit report.

CRITICAL OPERATIONAL CONSTRAINTS:
1. You are strictly READ-ONLY on source files. You may ONLY create `AUDIT_REPORT.md` in the workspace root.
2. Read at most 3 to 5 critical hotspot files. NEVER attempt to read every file or run directory scans.
3. Write `AUDIT_REPORT.md` in a SINGLE comprehensive `write` operation. Do NOT read `AUDIT_REPORT.md` back or append incrementally.
4. Immediately call FinishAction once `AUDIT_REPORT.md` is written.

ANALYSIS DIMENSIONS:
- BUGS & CODE INTEGRITY:
  Identify unhandled exceptions, race conditions, type mismatches, dead code, and unreachable paths.
- ARCHITECTURE & COUPLING:
  Evaluate modularity, Single Responsibility Principle (SRP), circular dependencies, and abstractions.
- SECURITY & VULNERABILITIES:
  Flag unsafe subprocess calls (shell=True), path traversal, credential exposure, and injection vectors.
- PERFORMANCE & EFFICIENCY:
  Spot unnecessary I/O, quadratic or nested loops, memory leaks, and redundant token consumption.
- PRIORITIZED RECOMMENDATIONS:
  Provide clear, actionable fixes with file and line references, categorized by severity (CRITICAL, HIGH, MEDIUM, LOW).

OUTPUT SPECIFICATION:
Generate `AUDIT_REPORT.md` containing:
# Codebase Architecture & Security Audit Report
## 1. Executive Summary & Code Metrics
## 2. Critical Bugs & Logic Errors
## 3. Architecture & Structural Hotspots
## 4. Security & Hardening Findings
## 5. Performance & Efficiency Bottlenecks
## 6. Actionable Roadmap & Priority Matrix
"""


def create_auditor_agent(
    config: OrchestratorConfig,
    skill_manager: SkillManager,
    workspace_path: Optional[Path] = None,
) -> Agent:
    """Build an Auditor agent with read-only source access and AUDIT_REPORT.md write permission."""
    workspace = (workspace_path or config.workspace_path).resolve()

    llm = create_llm_for_role(config, config.reviewer)
    auditor_skills = [
        "code-review-standards",
        "security-audit-hardening",
        "graft-architecture-intelligence",
    ]
    context = skill_manager.build_agent_context(auditor_skills)

    file_tool = create_workspace_file_tool(
        workspace,
        read_only=False,
        allowed_write_prefixes=["AUDIT_REPORT.md", "audit_report.md"],
    )
    terminal_tool = create_workspace_terminal_tool(workspace)

    return Agent(
        llm=llm,
        tools=[file_tool, terminal_tool],
        agent_context=context,
        system_prompt=AUDITOR_SYSTEM_PROMPT,
    )
