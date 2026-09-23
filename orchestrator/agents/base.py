"""Base agent factory establishing standardized lifecycle and tool provisioning."""

from pathlib import Path
from typing import Any, List, Optional

from openhands.sdk import Agent, AgentContext, LLM
from orchestrator.core.config import AgentRoleConfig, OrchestratorConfig
from orchestrator.llm import LLMManager, create_llm_for_role
from orchestrator.skills.manager import SkillManager
from orchestrator.tools import (
    create_workspace_file_tool,
    create_workspace_terminal_tool,
)


class BaseAgentFactory:
    """Base factory encapsulating common agent creation logic across specialized roles."""

    role_name: str = "base"
    system_prompt: str = "You are an autonomous AI agent."

    @classmethod
    def resolve_workspace(
        cls, config: OrchestratorConfig, workspace_path: Optional[Path] = None
    ) -> Path:
        """Resolve target workspace directory."""
        return (workspace_path or config.workspace_path).resolve()

    @classmethod
    def resolve_role_config(
        cls, config: OrchestratorConfig, role_name: Optional[str] = None
    ) -> AgentRoleConfig:
        """Resolve role configuration model from orchestrator config."""
        name = role_name or cls.role_name
        return getattr(config, name, getattr(config, "developer"))

    @classmethod
    def resolve_llm(
        cls, config: OrchestratorConfig, role_name: Optional[str] = None
    ) -> LLM:
        """Obtain pooled or newly instantiated LLM for the role."""
        name = role_name or cls.role_name
        try:
            return LLMManager.get_instance(config).get_llm(name)
        except Exception:
            role_cfg = cls.resolve_role_config(config, name)
            return create_llm_for_role(config, role_cfg)

    @classmethod
    def resolve_context(
        cls,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        skills: Optional[List[str]] = None,
        compact: bool = True,
        task_text: str = "",
    ) -> AgentContext:
        """Construct AgentContext loaded with role skills."""
        skill_names = skills if skills is not None else cls.resolve_role_config(config).skills
        return skill_manager.build_agent_context(
            skill_names, compact=compact, task_text=task_text
        )

    @classmethod
    def resolve_tools(
        cls,
        workspace: Path,
        read_only: bool = False,
        allowed_write_prefixes: Optional[List[str]] = None,
        blocked_write_prefixes: Optional[List[str]] = None,
        include_terminal: bool = True,
    ) -> List[Any]:
        """Construct file and terminal workspace tools."""
        tools: List[Any] = []
        file_tool = create_workspace_file_tool(
            workspace,
            read_only=read_only,
            allowed_write_prefixes=allowed_write_prefixes,
            blocked_write_prefixes=blocked_write_prefixes,
        )
        tools.append(file_tool)

        if include_terminal:
            terminal_tool = create_workspace_terminal_tool(workspace)
            tools.append(terminal_tool)

        return tools

    @classmethod
    def create(
        cls,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
        task_text: str = "",
        **kwargs: Any,
    ) -> Agent:
        """Instantiate and return the configured Agent."""
        workspace = cls.resolve_workspace(config, workspace_path)
        llm = cls.resolve_llm(config)
        context = cls.resolve_context(config, skill_manager, task_text=task_text)
        tools = cls.resolve_tools(workspace, **kwargs)

        return Agent(
            llm=llm,
            tools=tools,
            agent_context=context,
            system_prompt=cls.system_prompt,
        )
