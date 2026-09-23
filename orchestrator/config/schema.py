"""Schema definitions and validation utilities for Orchestrator configuration."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


CONFIG_JSON_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "OrchestratorConfig",
    "description": "Central configuration schema for Multi-Agent Orchestrator",
    "type": "object",
    "properties": {
        "$schema": {"type": "string"},
        "version": {"type": "string", "default": "1.0.0"},
        "execution": {
            "type": "object",
            "properties": {
                "max_iterations": {"type": ["integer", "string"], "default": 4},
                "max_budget_usd": {"type": "number", "minimum": 0.0, "default": 0.50},
                "max_tokens_budget": {"type": "integer", "minimum": 1000, "default": 350000},
                "max_agent_steps": {"type": "integer", "minimum": 1, "default": 12},
                "max_tokens_per_call": {"type": "integer", "minimum": 512, "default": 8192},
                "circuit_breaker_threshold": {"type": "integer", "minimum": 1, "default": 2},
                "conversation_timeout_seconds": {"type": "integer", "minimum": 10, "default": 300},
                "auto_commit": {"type": "boolean", "default": True},
                "auto_chain_audit": {"type": "boolean", "default": True},
                "workspace_path": {"type": "string", "default": "./workspace"},
            },
        },
        "agents": {
            "type": "object",
            "properties": {
                "architect": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "default": "architect"},
                        "model": {"type": "string"},
                        "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0},
                        "skills": {"type": "array", "items": {"type": "string"}},
                        "api_key": {"type": ["string", "null"]},
                    },
                },
                "developer": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "default": "developer"},
                        "model": {"type": "string"},
                        "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0},
                        "skills": {"type": "array", "items": {"type": "string"}},
                        "api_key": {"type": ["string", "null"]},
                    },
                },
                "tester": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "default": "tester"},
                        "model": {"type": "string"},
                        "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0},
                        "skills": {"type": "array", "items": {"type": "string"}},
                        "api_key": {"type": ["string", "null"]},
                    },
                },
                "reviewer": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "default": "reviewer"},
                        "model": {"type": "string"},
                        "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0},
                        "skills": {"type": "array", "items": {"type": "string"}},
                        "api_key": {"type": ["string", "null"]},
                    },
                },
            },
        },
        "memory": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "relevance_min_score": {"type": "number", "default": 3.0},
                "max_memory_results": {"type": "integer", "default": 3},
                "max_memory_chars": {"type": "integer", "default": 1500},
            },
        },
        "telemetry": {
            "type": "object",
            "properties": {
                "max_retained_reports": {"type": "integer", "default": 20},
                "max_retained_sessions_per_project": {"type": "integer", "default": 10},
                "log_save_debounce_seconds": {"type": "integer", "default": 5},
            },
        },
        "safety": {
            "type": "object",
            "properties": {
                "terminal_command_allowlist": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "blocked_write_prefixes_developer": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "allowed_write_prefixes_architect": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "allowed_write_prefixes_auditor": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
        "graft": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "max_age_seconds": {"type": "number", "default": 300.0},
                "max_map_chars": {"type": "integer", "default": 1500},
            },
        },
        "rendering": {
            "type": "object",
            "properties": {
                "verbosity": {"type": "string", "enum": ["quiet", "normal", "verbose"], "default": "normal"},
                "show_diff_preview": {"type": "boolean", "default": True},
                "diff_max_lines_per_file": {"type": "integer", "default": 50},
                "diff_max_chars": {"type": "integer", "default": 4000},
            },
        },
        "human_in_the_loop": {
            "type": "object",
            "properties": {
                "interactive": {"type": "boolean", "default": False},
                "approval_gates": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
}


class ConfigSchema:
    """Utilities for generating and validating JSON schema definitions."""

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Return the dictionary representation of the config JSON schema."""
        return dict(CONFIG_JSON_SCHEMA)

    @classmethod
    def write_schema_file(cls, output_path: Path) -> Path:
        """Export schema definition as a JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(cls.get_schema(), indent=2), encoding="utf-8")
        return output_path

    @classmethod
    def validate_dict(cls, data: Dict[str, Any]) -> List[str]:
        """Basic schema validation returning a list of validation issues found."""
        errors: List[str] = []
        if not isinstance(data, dict):
            return ["Root configuration must be a JSON object (dict)."]

        # Validate execution block
        if "execution" in data and isinstance(data["execution"], dict):
            exec_sec = data["execution"]
            if "max_budget_usd" in exec_sec:
                try:
                    val = float(exec_sec["max_budget_usd"])
                    if val < 0:
                        errors.append("execution.max_budget_usd cannot be negative.")
                except (ValueError, TypeError):
                    errors.append("execution.max_budget_usd must be a numeric value.")
            if "max_iterations" in exec_sec:
                it = exec_sec["max_iterations"]
                if not (isinstance(it, int) or (isinstance(it, str) and (it.isdigit() or it.lower() == "auto"))):
                    errors.append("execution.max_iterations must be an int or 'auto'.")

        # Validate agents block
        if "agents" in data and isinstance(data["agents"], dict):
            for role_name, role_data in data["agents"].items():
                if not isinstance(role_data, dict):
                    errors.append(f"agents.{role_name} must be an object.")
                    continue
                if "temperature" in role_data:
                    try:
                        t = float(role_data["temperature"])
                        if not (0.0 <= t <= 2.0):
                            errors.append(f"agents.{role_name}.temperature must be between 0.0 and 2.0.")
                    except (ValueError, TypeError):
                        errors.append(f"agents.{role_name}.temperature must be numeric.")
                if "skills" in role_data and not isinstance(role_data["skills"], list):
                    errors.append(f"agents.{role_name}.skills must be a list of skill names.")

        return errors
