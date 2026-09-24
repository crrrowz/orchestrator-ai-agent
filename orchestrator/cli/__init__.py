"""Command line interface layer for the Antigravity Multi-Agent Orchestrator."""

from orchestrator.cli.app import main, parse_args
from orchestrator.cli.handlers import (
    handle_check_config,
    handle_list_skills,
    handle_self_audit,
    handle_view_logs,
    resolve_task_input,
    resolve_workspace_dir,
)
from orchestrator.cli.wizard import interactive_wizard

__all__ = [
    "main",
    "parse_args",
    "resolve_task_input",
    "resolve_workspace_dir",
    "handle_list_skills",
    "handle_check_config",
    "handle_self_audit",
    "handle_view_logs",
    "interactive_wizard",
]
