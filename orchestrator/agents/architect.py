"""Architect Agent Factory for decomposing requirements into formal specifications."""

from pathlib import Path
from typing import Optional

from openhands.sdk import Agent
from orchestrator.config import OrchestratorConfig, SkillManager, create_llm_for_role
from orchestrator.tools import create_workspace_file_tool, create_workspace_terminal_tool

ARCHITECT_SYSTEM_PROMPT = """You are the Principal System Architect Agent.
Your objective is to decompose high-level user tasks into precise, modular technical designs.

CRITICAL INSTRUCTIONS:
1. Skills Enforcement: Adhere to `architectural-decomposition` and `graft-architecture-intelligence` skills:
   - Identify modules, classes, and public interfaces.
   - Detail data flow, dependency graph, and invariants.
2. Codebase Intelligence (Graft):
   - When inspecting existing projects, run `graft map` via terminal to view directory clusters, hubs, and hotspots without token waste.
   - Run `graft skeleton <file>` to inspect APIs and signatures before proposing changes.
   - Run `graft callers <symbol>` to trace call graphs and coupling.
3. Tools:
   - Inspect existing project structure using workspace file and terminal tools.
   - Write the technical blueprint into `PLAN.md` in the workspace.
4. Delivery:
   - Clear module boundaries and interface contracts.
   - Step-by-step implementation order for the Developer agent.
   - Comprehensive test strategy for the Tester agent.
"""


def create_architect_agent(
    config: OrchestratorConfig,
    skill_manager: SkillManager,
    workspace_path: Optional[Path] = None
) -> Agent:
    """Build an Architect agent configured with architectural decomposition skills and graft intelligence."""
    workspace = workspace_path or config.workspace_path
    llm = create_llm_for_role(config, config.architect)
    context = skill_manager.build_agent_context(config.architect.skills)
    file_tool = create_workspace_file_tool(workspace)
    terminal_tool = create_workspace_terminal_tool(workspace)

    return Agent(
        llm=llm,
        tools=[file_tool, terminal_tool],
        agent_context=context,
        system_prompt=ARCHITECT_SYSTEM_PROMPT,
    )
