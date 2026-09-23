"""Reviewer Agent Factory with independent LLM model and review rubric skill."""

from pathlib import Path
from typing import Optional

from openhands.sdk import Agent
from orchestrator.config import OrchestratorConfig, SkillManager, create_llm_for_role
from orchestrator.tools import create_workspace_file_tool

REVIEWER_SYSTEM_PROMPT = """You are the Senior Technical Lead & Security Auditor Agent.
Your objective is to provide an uncompromising, independent review of the proposed changes.

CRITICAL INSTRUCTIONS:
1. Independence:
   - You evaluate the code objectively against loaded skills: `code-review-standards`.
   - Never rubber-stamp code without reviewing diffs, implementation, and test cases.
2. Tools:
   - Inspect files via read-only workspace operations.
3. Verdict Format:
   Your review must conclude with a structured JSON block:
   ```json
   {
     "verdict": "APPROVED",
     "reasoning": [
       "Adheres to clean architecture",
       "Tests cover edge cases"
     ],
     "required_fixes": []
   }
   ```
   Or if rejected:
   ```json
   {
     "verdict": "REJECTED",
     "reasoning": [
       "Critical security or architectural flaw identified"
     ],
     "required_fixes": [
       "Detail specific actionable code changes needed"
     ]
   }
   ```
"""


def create_reviewer_agent(
    config: OrchestratorConfig,
    skill_manager: SkillManager,
    workspace_path: Optional[Path] = None
) -> Agent:
    """Build a Reviewer agent with an independent LLM model and review skill."""
    workspace = workspace_path or config.workspace_path
    
    # Enforce independent model check
    if config.reviewer.model == config.developer.model:
        import warnings
        warnings.warn(
            f"Reviewer model ({config.reviewer.model}) is identical to Developer model. "
            "For true independent review, configure different models across providers."
        )

    llm = create_llm_for_role(config, config.reviewer)
    context = skill_manager.build_agent_context(config.reviewer.skills)
    file_tool = create_workspace_file_tool(workspace, read_only=True)

    return Agent(
        llm=llm,
        tools=[file_tool],
        agent_context=context,
        system_prompt=REVIEWER_SYSTEM_PROMPT,
    )
