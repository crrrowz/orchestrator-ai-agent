"""Tester Agent Factory powered by OpenHands SDK and testing skills."""

from pathlib import Path
from typing import Optional

from openhands.sdk import Agent
from orchestrator.config import OrchestratorConfig, SkillManager, create_llm_for_role
from orchestrator.tools import create_workspace_file_tool, create_workspace_terminal_tool

TESTER_SYSTEM_PROMPT = """You are the Senior Staff QA & Test Engineer Agent.
Your objective is to guarantee code correctness, edge-case resilience, and regression prevention.

CRITICAL INSTRUCTIONS:
1. Skills Enforcement: You MUST adhere to all loaded skills:
   - pytest-rigorous-testing: Isolated tests, AAA structure, boundary conditions, edge cases, deterministic execution.
2. Tools:
   - Write comprehensive pytest suites in `tests/test_*.py`.
   - Run tests via terminal tool using `pytest -v` or `python -m pytest`.
3. Strict Constraints:
   - NEVER modify production code files (outside `tests/`).
   - If tests fail, provide a structured failure report with exact tracebacks and suggested root cause analysis.
   - If all tests pass, report clear test metrics (tests passed, coverage).
"""


def create_tester_agent(
    config: OrchestratorConfig,
    skill_manager: SkillManager,
    workspace_path: Optional[Path] = None
) -> Agent:
    """Build a Tester agent configured with testing skills and execution tools."""
    workspace = workspace_path or config.workspace_path
    llm = create_llm_for_role(config, config.tester)
    context = skill_manager.build_agent_context(config.tester.skills)

    file_tool = create_workspace_file_tool(workspace, allowed_write_prefixes=["tests/"])
    terminal_tool = create_workspace_terminal_tool(workspace)

    return Agent(
        llm=llm,
        tools=[file_tool, terminal_tool],
        agent_context=context,
        system_prompt=TESTER_SYSTEM_PROMPT,
    )
