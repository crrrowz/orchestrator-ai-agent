"""Developer Agent Factory powered by OpenHands SDK and architectural skills."""

from pathlib import Path
from typing import Optional

from openhands.sdk import Agent
from orchestrator.config import OrchestratorConfig, SkillManager, create_llm_for_role
from orchestrator.tools import create_workspace_file_tool, create_workspace_terminal_tool

DEVELOPER_SYSTEM_PROMPT = """You are the Senior Staff Developer Agent.
Your objective is to produce production-grade, bug-free, fully implemented software.

CRITICAL INSTRUCTIONS:
1. Skills Enforcement: You MUST adhere to all loaded skills:
   - clean-python-architecture: Complete code, strict types, modern Python 3.12+ idioms, zero stubs or placeholders.
   - systematic-debugging: When fixing bugs or test failures, diagnose root causes methodically.
2. Tools:
   - Use the workspace file editor to inspect existing files and write complete code files.
   - Use the workspace terminal to verify syntax or run local commands if needed.
3. Quality:
   - Never output `# TODO` or incomplete code.
   - Always ensure module imports, classes, and function signatures match architectural requirements.
4. Deliverables:
   - For all newly implemented services or libraries, create a concise `README.md` (quickstart + usage commands) and a standalone runnable `demo.py` verifying functionality interactively.
"""


def create_developer_agent(
    config: OrchestratorConfig,
    skill_manager: SkillManager,
    workspace_path: Optional[Path] = None
) -> Agent:
    """Build a Developer agent configured with developer skills and tools."""
    workspace = workspace_path or config.workspace_path
    llm = create_llm_for_role(config, config.developer)
    context = skill_manager.build_agent_context(config.developer.skills)

    file_tool = create_workspace_file_tool(workspace, blocked_write_prefixes=["tests/"])
    terminal_tool = create_workspace_terminal_tool(workspace)

    return Agent(
        llm=llm,
        tools=[file_tool, terminal_tool],
        agent_context=context,
        system_prompt=DEVELOPER_SYSTEM_PROMPT,
    )
