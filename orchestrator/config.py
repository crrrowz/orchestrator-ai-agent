"""Configuration and Skill Management for Multi-Agent Orchestrator."""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic import SecretStr

from openhands.sdk import LLM, AgentContext
from openhands.sdk.skills import Skill, load_project_skills


# Load environment variables from .env if present
load_dotenv()


class AgentRoleConfig(BaseModel):
    """Configuration for a specific agent role."""
    role: str
    model: str
    temperature: float = 0.2
    skills: List[str] = Field(default_factory=list)
    api_key: Optional[str] = None


class OrchestratorConfig(BaseModel):
    """Global configuration for orchestrator execution."""
    workspace_path: Path = Field(default_factory=lambda: Path(os.environ.get("WORKSPACE_PATH", "./workspace")).resolve())
    max_iterations: int = Field(default=int(os.environ.get("MAX_ITERATIONS", "4")))
    auto_commit: bool = Field(default=os.environ.get("AUTO_COMMIT", "true").lower() == "true")
    max_budget_usd: float = Field(default=float(os.environ.get("MAX_BUDGET_USD", "0.50")))
    max_tokens_per_call: int = Field(default=int(os.environ.get("MAX_TOKENS_PER_CALL", "4096")))
    circuit_breaker_threshold: int = Field(default=int(os.environ.get("CIRCUIT_BREAKER_THRESHOLD", "2")))
    
    # Provider keys
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY"))
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get("OPENAI_API_KEY"))
    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    openrouter_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get("OPENROUTER_API_KEY"))

    # Role configs
    developer: AgentRoleConfig = Field(default_factory=lambda: AgentRoleConfig(
        role="developer",
        model=os.environ.get("DEVELOPER_MODEL", "openrouter/qwen/qwen3.8-27b:free" if os.environ.get("OPENROUTER_API_KEY") else "anthropic/claude-sonnet-4-5-20250929"),
        temperature=0.2,
        skills=["clean-python-architecture", "systematic-debugging", "docker-devops-containerization"],
    ))
    tester: AgentRoleConfig = Field(default_factory=lambda: AgentRoleConfig(
        role="tester",
        model=os.environ.get("TESTER_MODEL", "openrouter/qwen/qwen3.8-27b:free" if os.environ.get("OPENROUTER_API_KEY") else "openai/gpt-4o-mini"),
        temperature=0.0,
        skills=["pytest-rigorous-testing"],
    ))
    reviewer: AgentRoleConfig = Field(default_factory=lambda: AgentRoleConfig(
        role="reviewer",
        model=os.environ.get("REVIEWER_MODEL", "openrouter/google/gemini-2.0-flash-exp:free" if os.environ.get("OPENROUTER_API_KEY") else "openai/gpt-4o"),
        temperature=0.1,
        skills=["code-review-standards", "security-audit-hardening"],
    ))
    architect: AgentRoleConfig = Field(default_factory=lambda: AgentRoleConfig(
        role="architect",
        model=os.environ.get("ARCHITECT_MODEL", "openrouter/qwen/qwen3.8-27b:free" if os.environ.get("OPENROUTER_API_KEY") else "anthropic/claude-sonnet-4-5-20250929"),
        temperature=0.3,
        skills=["architectural-decomposition", "api-design-contract"],
    ))


class SkillManager:
    """Discovers, validates, and provisions skills to agents."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = (project_root or Path.cwd()).resolve()
        self._skills_cache: Dict[str, Skill] = {}
        self.refresh()

    def refresh(self) -> None:
        """Scan project directory and cache all discoverable skills."""
        discovered = load_project_skills(self.project_root)
        self._skills_cache = {s.name: s for s in discovered}

    @property
    def available_skills(self) -> List[str]:
        return list(self._skills_cache.keys())

    def get_skill(self, name: str) -> Optional[Skill]:
        return self._skills_cache.get(name)

    def get_skills_for_role(self, role_names: List[str]) -> List[Skill]:
        """Fetch matching skill objects for designated role skill names."""
        selected: List[Skill] = []
        for name in role_names:
            skill = self.get_skill(name)
            if skill:
                selected.append(skill)
        return selected

    def build_agent_context(self, skill_names: List[str]) -> AgentContext:
        """Construct an AgentContext loaded with the specified skills."""
        role_skills = self.get_skills_for_role(skill_names)
        return AgentContext(
            skills=role_skills,
            load_project_skills=True,
            load_user_skills=True,
            load_memory=True
        )


def create_llm_for_role(config: OrchestratorConfig, role_config: AgentRoleConfig) -> LLM:
    """Factory to create an OpenHands LLM instance with appropriate credentials."""
    model = role_config.model
    api_key_val = role_config.api_key

    # Resolve API Key by provider prefix if not explicitly set
    if not api_key_val:
        if model.startswith("anthropic/"):
            api_key_val = config.anthropic_api_key
        elif model.startswith("openai/"):
            api_key_val = config.openai_api_key
        elif model.startswith("gemini/") or model.startswith("google/"):
            api_key_val = config.gemini_api_key
        elif model.startswith("openrouter/"):
            api_key_val = config.openrouter_api_key

    secret = SecretStr(api_key_val) if api_key_val else None

    llm_kwargs = {
        "model": model,
        "api_key": secret,
        "temperature": role_config.temperature,
        "max_output_tokens": config.max_tokens_per_call,
        "usage_id": f"agent-{role_config.role}",
    }

    if model.startswith("openrouter/"):
        llm_kwargs["openrouter_site_url"] = "https://github.com/Antigravity-Agent-API"
        llm_kwargs["openrouter_app_name"] = "Antigravity Multi-Agent Orchestrator"

    return LLM(**llm_kwargs)
