"""Configuration Loader with hierarchical cascading priority.

Priority Chain:
1. Runtime Overrides (explicit kwargs / CLI flags)
2. orchestrator.config.json (central configuration file)
3. .env file & Environment Variables
4. Default Fallbacks
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()


class ConfigLoader:
    """Manages discovery, hierarchical loading, validation, and serialization of Orchestrator configs."""

    @classmethod
    def get_orchestrator_root(cls) -> Path:
        """Resolve repository root directory."""
        # loader.py is in orchestrator/config/loader.py -> root is 3 levels up
        return Path(__file__).resolve().parent.parent.parent

    @classmethod
    def find_config_file(
        cls,
        custom_path: Optional[Union[str, Path]] = None,
        start_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """Locate the active orchestrator.config.json according to resolution rules."""
        if custom_path:
            p = Path(custom_path).resolve()
            if p.is_file():
                return p
            return None

        # Check explicit environment variable
        env_path = os.environ.get("ORCHESTRATOR_CONFIG_PATH")
        if env_path:
            p = Path(env_path).resolve()
            if p.is_file():
                return p

        # Check current / start directory
        if start_dir:
            p = (start_dir / "orchestrator.config.json").resolve()
            if p.is_file():
                return p

        # Check ORCHESTRATOR_ROOT
        root = cls.get_orchestrator_root()
        root_config = root / "orchestrator.config.json"
        if root_config.is_file():
            return root_config

        # Check internal package config
        pkg_config = root / "orchestrator" / "config" / "orchestrator.config.json"
        if pkg_config.is_file():
            return pkg_config

        return None

    @classmethod
    def load_raw_json(cls, path: Path) -> Dict[str, Any]:
        """Safely parse a JSON configuration file."""
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError(f"Configuration file at {path} must contain a JSON object.")
        return data

    @classmethod
    def parse_json_to_config_kwargs(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested sections of orchestrator.config.json into OrchestratorConfig keyword arguments."""
        kwargs: Dict[str, Any] = {}

        # 1. Execution section
        exec_sec = data.get("execution", {})
        if isinstance(exec_sec, dict):
            if "max_iterations" in exec_sec:
                kwargs["max_iterations"] = exec_sec["max_iterations"]
            if "max_budget_usd" in exec_sec:
                kwargs["max_budget_usd"] = float(exec_sec["max_budget_usd"])
            if "max_tokens_budget" in exec_sec:
                kwargs["max_tokens_budget"] = int(exec_sec["max_tokens_budget"])
            if "max_agent_steps" in exec_sec:
                kwargs["max_agent_steps"] = int(exec_sec["max_agent_steps"])
            if "max_tokens_per_call" in exec_sec:
                kwargs["max_tokens_per_call"] = int(exec_sec["max_tokens_per_call"])
            if "circuit_breaker_threshold" in exec_sec:
                kwargs["circuit_breaker_threshold"] = int(exec_sec["circuit_breaker_threshold"])
            if "conversation_timeout_seconds" in exec_sec:
                kwargs["conversation_timeout_seconds"] = int(exec_sec["conversation_timeout_seconds"])
            if "auto_commit" in exec_sec:
                kwargs["auto_commit"] = bool(exec_sec["auto_commit"])
            if "auto_chain_audit" in exec_sec:
                kwargs["auto_chain_audit"] = bool(exec_sec["auto_chain_audit"])
            if "workspace_path" in exec_sec:
                ws = Path(exec_sec["workspace_path"])
                if not ws.is_absolute():
                    ws = (cls.get_orchestrator_root() / ws).resolve()
                kwargs["workspace_path"] = ws

        # 2. Agents section
        from orchestrator.config import AgentRoleConfig

        agents_sec = data.get("agents", {})
        if isinstance(agents_sec, dict):
            for role_name in ("developer", "tester", "reviewer", "architect"):
                role_dict = agents_sec.get(role_name)
                if isinstance(role_dict, dict):
                    role_kwargs: Dict[str, Any] = {"role": role_name}
                    if "model" in role_dict:
                        role_kwargs["model"] = role_dict["model"]
                    if "temperature" in role_dict:
                        role_kwargs["temperature"] = float(role_dict["temperature"])
                    if "skills" in role_dict and isinstance(role_dict["skills"], list):
                        role_kwargs["skills"] = list(role_dict["skills"])
                    if "api_key" in role_dict:
                        role_kwargs["api_key"] = role_dict["api_key"]
                    kwargs[role_name] = AgentRoleConfig(**role_kwargs)

        # 3. Memory section
        mem_sec = data.get("memory", {})
        if isinstance(mem_sec, dict):
            if "enabled" in mem_sec:
                kwargs["enable_memory"] = bool(mem_sec["enabled"])
            if "relevance_min_score" in mem_sec:
                kwargs["memory_relevance_min_score"] = float(mem_sec["relevance_min_score"])
            if "max_memory_results" in mem_sec:
                kwargs["max_memory_results"] = int(mem_sec["max_memory_results"])
            if "max_memory_chars" in mem_sec:
                kwargs["max_memory_chars"] = int(mem_sec["max_memory_chars"])

        # 4. Telemetry section
        telem_sec = data.get("telemetry", {})
        if isinstance(telem_sec, dict):
            if "max_retained_reports" in telem_sec:
                kwargs["max_retained_reports"] = int(telem_sec["max_retained_reports"])
            if "max_retained_sessions_per_project" in telem_sec:
                kwargs["max_retained_sessions_per_project"] = int(telem_sec["max_retained_sessions_per_project"])
            if "log_save_debounce_seconds" in telem_sec:
                kwargs["log_save_debounce_seconds"] = int(telem_sec["log_save_debounce_seconds"])

        # 5. Safety section
        safety_sec = data.get("safety", {})
        if isinstance(safety_sec, dict):
            if "terminal_command_allowlist" in safety_sec:
                kwargs["terminal_command_allowlist"] = list(safety_sec["terminal_command_allowlist"])
            if "blocked_write_prefixes_developer" in safety_sec:
                kwargs["blocked_write_prefixes_developer"] = list(safety_sec["blocked_write_prefixes_developer"])
            if "allowed_write_prefixes_architect" in safety_sec:
                kwargs["allowed_write_prefixes_architect"] = list(safety_sec["allowed_write_prefixes_architect"])
            if "allowed_write_prefixes_auditor" in safety_sec:
                kwargs["allowed_write_prefixes_auditor"] = list(safety_sec["allowed_write_prefixes_auditor"])

        # 6. Graft section
        graft_sec = data.get("graft", {})
        if isinstance(graft_sec, dict):
            if "enabled" in graft_sec:
                kwargs["graft_enabled"] = bool(graft_sec["enabled"])
            if "max_age_seconds" in graft_sec:
                kwargs["graft_max_age_seconds"] = float(graft_sec["max_age_seconds"])
            if "max_map_chars" in graft_sec:
                kwargs["graft_max_map_chars"] = int(graft_sec["max_map_chars"])

        # 7. Rendering section
        rend_sec = data.get("rendering", {})
        if isinstance(rend_sec, dict):
            if "verbosity" in rend_sec:
                kwargs["verbosity"] = str(rend_sec["verbosity"])
            if "show_diff_preview" in rend_sec:
                kwargs["show_diff_preview"] = bool(rend_sec["show_diff_preview"])
            if "diff_max_lines_per_file" in rend_sec:
                kwargs["diff_max_lines_per_file"] = int(rend_sec["diff_max_lines_per_file"])
            if "diff_max_chars" in rend_sec:
                kwargs["diff_max_chars"] = int(rend_sec["diff_max_chars"])

        # 8. Human-in-the-loop section
        hitl_sec = data.get("human_in_the_loop", {})
        if isinstance(hitl_sec, dict):
            if "interactive" in hitl_sec:
                kwargs["interactive"] = bool(hitl_sec["interactive"])
            if "approval_gates" in hitl_sec:
                kwargs["approval_gates"] = list(hitl_sec["approval_gates"])

        # 9. Direct flat keys (if user provided top-level keys in JSON)
        for direct_key in (
            "max_iterations",
            "max_budget_usd",
            "max_tokens_budget",
            "max_agent_steps",
            "max_tokens_per_call",
            "circuit_breaker_threshold",
            "conversation_timeout_seconds",
            "auto_commit",
            "auto_chain_audit",
            "enable_memory",
            "verbosity",
            "interactive",
            "approval_gates",
        ):
            if direct_key in data:
                kwargs[direct_key] = data[direct_key]

        return kwargs

    @classmethod
    def load(
        cls,
        config_path: Optional[Union[str, Path]] = None,
        start_dir: Optional[Path] = None,
        **overrides: Any,
    ) -> Any:
        """Load OrchestratorConfig following the 4-layer priority cascade.

        Cascade:
        1. Explicit overrides (**overrides)
        2. orchestrator.config.json (if discovered or specified)
        3. .env and system environment variables
        4. Hardcoded defaults
        """
        from orchestrator.config import OrchestratorConfig

        resolved_file = cls.find_config_file(custom_path=config_path, start_dir=start_dir)
        json_kwargs: Dict[str, Any] = {}

        if resolved_file:
            try:
                raw_data = cls.load_raw_json(resolved_file)
                json_kwargs = cls.parse_json_to_config_kwargs(raw_data)
            except Exception as e:
                import logging
                logging.getLogger("orchestrator.config").warning(
                    f"Failed to load config from {resolved_file}: {e}. Falling back to env/defaults."
                )

        # Merge JSON kwargs into overrides, where overrides take precedence
        merged_kwargs = dict(json_kwargs)
        for k, v in overrides.items():
            if v is not None:
                merged_kwargs[k] = v

        config = OrchestratorConfig(**merged_kwargs)
        if resolved_file:
            config._loaded_from_path = resolved_file
        return config

    @classmethod
    def save(cls, config: Any, target_path: Union[str, Path]) -> Path:
        """Serialize an OrchestratorConfig instance to an orchestrator.config.json structure."""
        out = Path(target_path).resolve()
        data: Dict[str, Any] = {
            "$schema": "./orchestrator/config/config_schema.json",
            "version": "1.0.0",
            "execution": {
                "max_iterations": config.max_iterations,
                "max_budget_usd": config.max_budget_usd,
                "max_tokens_budget": config.max_tokens_budget,
                "max_agent_steps": config.max_agent_steps,
                "max_tokens_per_call": config.max_tokens_per_call,
                "circuit_breaker_threshold": config.circuit_breaker_threshold,
                "conversation_timeout_seconds": getattr(config, "conversation_timeout_seconds", 300),
                "auto_commit": config.auto_commit,
                "auto_chain_audit": config.auto_chain_audit,
                "workspace_path": str(config.workspace_path),
            },
            "agents": {
                "architect": {
                    "role": config.architect.role,
                    "model": config.architect.model,
                    "temperature": config.architect.temperature,
                    "skills": config.architect.skills,
                },
                "developer": {
                    "role": config.developer.role,
                    "model": config.developer.model,
                    "temperature": config.developer.temperature,
                    "skills": config.developer.skills,
                },
                "tester": {
                    "role": config.tester.role,
                    "model": config.tester.model,
                    "temperature": config.tester.temperature,
                    "skills": config.tester.skills,
                },
                "reviewer": {
                    "role": config.reviewer.role,
                    "model": config.reviewer.model,
                    "temperature": config.reviewer.temperature,
                    "skills": config.reviewer.skills,
                },
            },
            "memory": {
                "enabled": config.enable_memory,
                "relevance_min_score": getattr(config, "memory_relevance_min_score", 3.0),
                "max_memory_results": getattr(config, "max_memory_results", 3),
                "max_memory_chars": getattr(config, "max_memory_chars", 1500),
            },
            "telemetry": {
                "max_retained_reports": config.max_retained_reports,
                "max_retained_sessions_per_project": getattr(config, "max_retained_sessions_per_project", 10),
                "log_save_debounce_seconds": getattr(config, "log_save_debounce_seconds", 5),
            },
            "safety": {
                "terminal_command_allowlist": getattr(
                    config,
                    "terminal_command_allowlist",
                    ["pytest", "python", "pip", "uv", "git", "ruff", "mypy", "graft", "ls", "dir", "cat", "type", "echo"],
                ),
                "blocked_write_prefixes_developer": getattr(config, "blocked_write_prefixes_developer", ["tests/"]),
                "allowed_write_prefixes_architect": getattr(config, "allowed_write_prefixes_architect", ["PLAN.md"]),
                "allowed_write_prefixes_auditor": getattr(
                    config, "allowed_write_prefixes_auditor", ["AUDIT_REPORT.md", "audit_report.md"]
                ),
            },
            "graft": {
                "enabled": getattr(config, "graft_enabled", True),
                "max_age_seconds": getattr(config, "graft_max_age_seconds", 300.0),
                "max_map_chars": getattr(config, "graft_max_map_chars", 1500),
            },
            "rendering": {
                "verbosity": config.verbosity,
                "show_diff_preview": getattr(config, "show_diff_preview", True),
                "diff_max_lines_per_file": getattr(config, "diff_max_lines_per_file", 50),
                "diff_max_chars": getattr(config, "diff_max_chars", 4000),
            },
            "human_in_the_loop": {
                "interactive": config.interactive,
                "approval_gates": config.approval_gates,
            },
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return out
