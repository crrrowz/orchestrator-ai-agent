"""Core configuration models for agents, domains, and the orchestrator engine."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from orchestrator.core.constants import (
    DEFAULT_WORKSPACE_DIR,
)

# Load environment variables from .env if present
load_dotenv()


class AgentRoleConfig(BaseModel):
    """Configuration for a specific agent role."""

    role: str
    model: Optional[str] = None
    temperature: float = 0.2
    skills: List[str] = Field(default_factory=list)
    api_key: Optional[str] = None


class DomainProfile(BaseModel):
    """Execution profile tailored to a programming language or operational domain."""

    name: str
    test_command: Optional[str] = "pytest -v"
    lint_command: Optional[str] = "ruff check ."
    preflight_extensions: List[str] = Field(default_factory=lambda: [".py"])
    skills_override: List[str] = Field(default_factory=list)
    environment_variables: Dict[str, str] = Field(default_factory=dict)


class OrchestratorConfig(BaseModel):
    """Global configuration for orchestrator execution."""

    workspace_path: Path = Field(
        default_factory=lambda: Path(
            os.environ.get("WORKSPACE_PATH", str(DEFAULT_WORKSPACE_DIR))
        ).resolve()
    )
    max_iterations: Union[int, str] = Field(
        default=int(os.environ["MAX_ITERATIONS"])
        if os.environ.get("MAX_ITERATIONS", "").isdigit()
        else os.environ.get("MAX_ITERATIONS", 4)
    )

    @property
    def numeric_max_iterations(self) -> int:
        if isinstance(self.max_iterations, int):
            return self.max_iterations
        try:
            return int(self.max_iterations)
        except (ValueError, TypeError):
            return 4

    auto_commit: bool = Field(
        default=os.environ.get("AUTO_COMMIT", "true").lower() == "true"
    )
    max_budget_usd: float = Field(
        default=float(os.environ.get("MAX_BUDGET_USD", "0.50"))
    )
    max_tokens_budget: int = Field(
        default=int(os.environ.get("MAX_TOKENS_BUDGET", "350000"))
    )
    max_agent_steps: int = Field(default=int(os.environ.get("MAX_AGENT_STEPS", "12")))
    max_tokens_per_call: int = Field(
        default=int(os.environ.get("MAX_TOKENS_PER_CALL", "8192"))
    )
    circuit_breaker_threshold: int = Field(
        default=int(os.environ.get("CIRCUIT_BREAKER_THRESHOLD", "2"))
    )
    conversation_timeout_seconds: int = Field(
        default=int(os.environ.get("CONVERSATION_TIMEOUT_SECONDS", "300"))
    )
    approval_gates: List[str] = Field(
        default_factory=lambda: [
            g.strip()
            for g in os.environ.get("APPROVAL_GATES", "").split(",")
            if g.strip()
        ]
    )
    interactive: bool = Field(
        default_factory=lambda: os.environ.get("INTERACTIVE", "false").lower() == "true"
    )
    verbosity: str = Field(
        default_factory=lambda: os.environ.get("VERBOSITY", "normal")
    )
    enable_memory: bool = Field(
        default=os.environ.get("ENABLE_MEMORY", "true").lower() == "true"
    )
    auto_chain_audit: bool = Field(
        default=os.environ.get("AUTO_CHAIN_AUDIT", "true").lower() == "true"
    )
    max_retained_reports: int = Field(
        default=int(os.environ.get("MAX_RETAINED_REPORTS", "20"))
    )
    max_retained_sessions_per_project: int = Field(
        default=int(os.environ.get("MAX_RETAINED_SESSIONS_PER_PROJECT", "10"))
    )
    log_save_debounce_seconds: int = Field(
        default=int(os.environ.get("LOG_SAVE_DEBOUNCE_SECONDS", "5"))
    )

    # Sentinel Cognitive Supervision & SRE Settings
    enable_cognitive_sentinel: bool = Field(
        default=os.environ.get("ENABLE_COGNITIVE_SENTINEL", "true").lower() == "true"
    )
    self_healing_level: str = Field(
        default=os.environ.get("SELF_HEALING_LEVEL", "full_autonomous")
    )
    cloud_fallback_chain: List[str] = Field(
        default_factory=lambda: [
            m.strip()
            for m in os.environ.get(
                "CLOUD_FALLBACK_CHAIN",
                "openrouter/google/gemini-2.0-flash-exp:free,openrouter/qwen/qwen3.8-27b:free,groq/llama-3.3-70b-versatile",
            ).split(",")
            if m.strip()
        ]
    )
    max_auto_patches_per_file: int = Field(
        default=int(os.environ.get("MAX_AUTO_PATCHES_PER_FILE", "3"))
    )

    # Provider keys
    anthropic_api_key: Optional[str] = Field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY")
    )
    openai_api_key: Optional[str] = Field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY")
    )
    gemini_api_key: Optional[str] = Field(
        default_factory=lambda: (
            os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )
    )
    openrouter_api_key: Optional[str] = Field(
        default_factory=lambda: os.environ.get("OPENROUTER_API_KEY")
    )
    groq_api_key: Optional[str] = Field(
        default_factory=lambda: os.environ.get("GROQ_API_KEY")
    )
    omniroute_api_key: Optional[str] = Field(
        default_factory=lambda: os.environ.get("OMNIROUTE_API_KEY")
    )
    omniroute_base_url: str = Field(
        default_factory=lambda: os.environ.get(
            "OMNIROUTE_BASE_URL", "http://localhost:20128/v1"
        )
    )
    openai_base_url: Optional[str] = Field(
        default_factory=lambda: os.environ.get("OPENAI_BASE_URL")
    )
    provider: str = Field(
        default_factory=lambda: (
            os.environ.get("PROVIDER")
            or os.environ.get("DEFAULT_PROVIDER")
            or "openrouter"
        )
    )

    # Role configs
    developer: AgentRoleConfig = Field(
        default_factory=lambda: AgentRoleConfig(
            role="developer",
            model=os.environ.get("DEVELOPER_MODEL")
            or os.environ.get("MODEL")
            or (
                "openrouter/qwen/qwen3.8-27b:free"
                if os.environ.get("OPENROUTER_API_KEY")
                else "anthropic/claude-sonnet-4-5-20250929"
            ),
            temperature=0.2,
            skills=[
                "clean-python-architecture",
                "systematic-debugging",
                "docker-devops-containerization",
                "graft-architecture-intelligence",
            ],
        )
    )
    tester: AgentRoleConfig = Field(
        default_factory=lambda: AgentRoleConfig(
            role="tester",
            model=os.environ.get("TESTER_MODEL")
            or os.environ.get("MODEL")
            or (
                "openrouter/qwen/qwen3.8-27b:free"
                if os.environ.get("OPENROUTER_API_KEY")
                else "openai/gpt-4o-mini"
            ),
            temperature=0.0,
            skills=["pytest-rigorous-testing"],
        )
    )
    reviewer: AgentRoleConfig = Field(
        default_factory=lambda: AgentRoleConfig(
            role="reviewer",
            model=os.environ.get("REVIEWER_MODEL")
            or os.environ.get("MODEL")
            or (
                "openrouter/google/gemini-2.0-flash-exp:free"
                if os.environ.get("OPENROUTER_API_KEY")
                else "openai/gpt-4o"
            ),
            temperature=0.1,
            skills=["code-review-standards", "security-audit-hardening"],
        )
    )
    architect: AgentRoleConfig = Field(
        default_factory=lambda: AgentRoleConfig(
            role="architect",
            model=os.environ.get("ARCHITECT_MODEL")
            or os.environ.get("MODEL")
            or (
                "openrouter/qwen/qwen3.8-27b:free"
                if os.environ.get("OPENROUTER_API_KEY")
                else "anthropic/claude-sonnet-4-5-20250929"
            ),
            temperature=0.3,
            skills=[
                "architectural-decomposition",
                "api-design-contract",
                "graft-architecture-intelligence",
            ],
        )
    )
    documentation: AgentRoleConfig = Field(
        default_factory=lambda: AgentRoleConfig(
            role="documentation",
            model=os.environ.get("DOCUMENTATION_MODEL")
            or os.environ.get("MODEL")
            or (
                "openrouter/qwen/qwen3.8-27b:free"
                if os.environ.get("OPENROUTER_API_KEY")
                else "openai/gpt-4o-mini"
            ),
            temperature=0.2,
            skills=[
                "architectural-decomposition",
                "api-design-contract",
            ],
        )
    )

    # Domain Profiles
    active_domain: str = Field(
        default_factory=lambda: os.environ.get("ACTIVE_DOMAIN", "python")
    )
    domain_profiles: Dict[str, DomainProfile] = Field(
        default_factory=lambda: {
            "python": DomainProfile(
                name="python",
                test_command="pytest -v",
                lint_command="ruff check .",
                preflight_extensions=[".py"],
                skills_override=[
                    "clean-python-architecture",
                    "pytest-rigorous-testing",
                ],
            ),
            "nodejs": DomainProfile(
                name="nodejs",
                test_command="npm test",
                lint_command="npm run lint",
                preflight_extensions=[".js", ".ts", ".jsx", ".tsx"],
                skills_override=[],
            ),
            "documentation": DomainProfile(
                name="documentation",
                test_command=None,
                lint_command=None,
                preflight_extensions=[".md"],
                skills_override=[],
            ),
            "general": DomainProfile(
                name="general",
                test_command=None,
                lint_command=None,
                preflight_extensions=[],
                skills_override=[],
            ),
        }
    )

    # Safety settings
    terminal_command_allowlist: List[str] = Field(
        default_factory=lambda: [
            "pytest",
            "python",
            "pip",
            "uv",
            "git",
            "ruff",
            "mypy",
            "graft",
            "ls",
            "dir",
            "cat",
            "type",
            "echo",
            "npm",
            "node",
        ]
    )
    blocked_write_prefixes_developer: List[str] = Field(
        default_factory=lambda: ["tests/"]
    )
    allowed_write_prefixes_architect: List[str] = Field(
        default_factory=lambda: ["PLAN.md"]
    )
    allowed_write_prefixes_auditor: List[str] = Field(
        default_factory=lambda: ["AUDIT_REPORT.md", "audit_report.md"]
    )

    # Graft intelligence
    graft_enabled: bool = Field(
        default=os.environ.get("GRAFT_ENABLED", "true").lower() == "true"
    )
    graft_max_age_seconds: float = Field(
        default=float(os.environ.get("GRAFT_MAX_AGE_SECONDS", "300.0"))
    )
    graft_max_map_chars: int = Field(
        default=int(os.environ.get("GRAFT_MAX_MAP_CHARS", "1500"))
    )

    # Rendering settings
    show_diff_preview: bool = Field(
        default=os.environ.get("SHOW_DIFF_PREVIEW", "true").lower() == "true"
    )
    diff_max_lines_per_file: int = Field(
        default=int(os.environ.get("DIFF_MAX_LINES_PER_FILE", "50"))
    )
    diff_max_chars: int = Field(default=int(os.environ.get("DIFF_MAX_CHARS", "4000")))

    # Memory settings
    memory_relevance_min_score: float = Field(
        default=float(os.environ.get("MEMORY_RELEVANCE_MIN_SCORE", "3.0"))
    )
    max_memory_results: int = Field(
        default=int(os.environ.get("MAX_MEMORY_RESULTS", "3"))
    )
    max_memory_chars: int = Field(
        default=int(os.environ.get("MAX_MEMORY_CHARS", "1500"))
    )

    # Metadata tracking
    _loaded_from_path: Optional[Path] = None

    @classmethod
    def from_file(
        cls, path: Union[str, Path], **overrides: Any
    ) -> "OrchestratorConfig":
        """Convenience loader from a JSON configuration file."""
        from orchestrator.config.loader import ConfigLoader

        return ConfigLoader.load(config_path=path, **overrides)

    def get_current_domain_profile(self) -> DomainProfile:
        """Fetch the active domain profile or fallback to python."""
        return self.domain_profiles.get(
            self.active_domain,
            self.domain_profiles.get("python", DomainProfile(name="python")),
        )
