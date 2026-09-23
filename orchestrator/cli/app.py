"""CLI entry point and command router for Antigravity Multi-Agent Orchestrator."""

import argparse
import logging
import os
import sys
from pathlib import Path

# Force UTF-8 encoding for standard streams on Windows to prevent UnicodeEncodeError
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Suppress OpenHands banner box & debug spam immediately before any SDK import
os.environ["OPENHANDS_SUPPRESS_BANNER"] = "1"
os.environ["LITELLM_LOG"] = "CRITICAL"

for _logger_name in [
    "openhands",
    "litellm",
    "LiteLLM",
    "httpx",
    "httpcore",
    "urllib3",
    "asyncio",
]:
    logging.getLogger(_logger_name).setLevel(logging.CRITICAL)

try:
    import litellm

    litellm.suppress_debug_info = True
    litellm.set_verbose = False
except ImportError:
    pass

from orchestrator.cli.handlers import (  # noqa: E402
    handle_check_config,
    handle_list_skills,
    handle_self_audit,
    handle_view_logs,
    resolve_task_input,
    resolve_workspace_dir,
)
from orchestrator.cli.wizard import interactive_wizard  # noqa: E402
from orchestrator.config import ConfigLoader  # noqa: E402
from orchestrator.core.constants import ORCHESTRATOR_ROOT  # noqa: E402
from orchestrator.core.exceptions import (  # noqa: E402
    OrchestratorException,
    ProviderQuotaExceededError,
)
from orchestrator.orchestrator import Orchestrator  # noqa: E402
from orchestrator.rendering.diff_renderer import DiffRenderer  # noqa: E402
from orchestrator.rendering.output import ConsoleOutput  # noqa: E402
from orchestrator.skills.manager import SkillManager  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Software Development Orchestrator powered by OpenHands SDK & Skills."
    )
    parser.add_argument(
        "task",
        nargs="?",
        default=None,
        help="Software development task description to execute.",
    )
    parser.add_argument(
        "--mode",
        choices=["dev-test", "full", "audit", "audit-fix", "docs"],
        default="dev-test",
        help="Pipeline mode: 'dev-test' (MVP), 'full' (4-Agent Pipeline), 'audit' (Codebase Analysis), 'audit-fix' (Auto-Remediation Loop), or 'docs' (Generate Documentation).",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Target workspace directory for code generation and testing.",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default=None,
        help="Domain execution profile (e.g. 'python', 'nodejs', 'documentation', 'general').",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Display syntax-highlighted git diff of the workspace using DiffRenderer.",
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="List all skills discovered in .agents/skills/ and exit.",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Check configured models, API keys, and settings.",
    )
    parser.add_argument(
        "--self-audit",
        action="store_true",
        help="Run offline self-evolution analysis on historical execution reports.",
    )
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Open the interactive collapsible log explorer (arrow keys / dropdowns) for the latest session.",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Enable Human-in-the-Loop (HITL) interactive guidance and approval checkpoints.",
    )
    parser.add_argument(
        "--approval-gates",
        type=str,
        default=None,
        help="Comma-separated approval checkpoints (e.g. 'after_architect,after_developer,before_commit').",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose stream showing full agent thoughts and detailed action parameters.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode showing only milestone transitions and errors.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume pipeline execution from previous checkpoint in .orchestrator_state.json.",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable cross-run historical memory injection to save tokens.",
    )
    parser.add_argument(
        "--estimate",
        action="store_true",
        help="Pre-execution token & cost projection without invoking LLMs.",
    )
    parser.add_argument(
        "--max-iterations",
        type=str,
        default=None,
        help="Maximum loop iterations: integer (e.g. 8) or 'auto' to scale dynamically with the audit backlog.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to custom orchestrator.config.json file.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override LLM model across all agents (e.g. 'openrouter/z-ai/glm-5.2:free', 'gemini/gemini-2.0-flash').",
    )
    return parser.parse_args()


def main() -> None:
    """CLI application entry point."""
    args = parse_args()
    config = ConfigLoader.load(config_path=args.config)
    if args.workspace:
        config.workspace_path = args.workspace.resolve()
    if args.domain:
        config.active_domain = args.domain.strip().lower()
    if args.interactive:
        config.interactive = True
    if args.approval_gates:
        config.approval_gates = [
            g.strip() for g in args.approval_gates.split(",") if g.strip()
        ]
    if args.verbose:
        config.verbosity = "verbose"
    elif args.quiet:
        config.verbosity = "quiet"
    if args.max_iterations is not None:
        clean_it = args.max_iterations.strip().lower()
        if clean_it == "auto":
            config.max_iterations = "auto"
        elif clean_it.isdigit():
            config.max_iterations = int(clean_it)

    if args.model:
        clean_model = args.model.strip()
        for role_attr in (
            "developer",
            "tester",
            "reviewer",
            "architect",
            "documentation",
        ):
            role_cfg = getattr(config, role_attr, None)
            if role_cfg and hasattr(role_cfg, "model"):
                role_cfg.model = clean_model

    skill_manager = SkillManager(ORCHESTRATOR_ROOT)

    if args.no_memory:
        config.enable_memory = False

    if args.diff:
        ws_dir = resolve_workspace_dir(args.workspace, config.workspace_path)
        ConsoleOutput.banner("Workspace Rich Diff Preview", str(ws_dir))
        DiffRenderer.render_git_diff_rich(ws_dir)
        sys.exit(0)

    if args.estimate:
        from orchestrator.control import CostEstimator

        task_desc = resolve_task_input(args.task) or "Sample development task"
        result = CostEstimator.estimate(task_desc, args.mode, config)
        CostEstimator.render(result, config)
        sys.exit(0)

    if args.list_skills:
        handle_list_skills(skill_manager)
        sys.exit(0)

    if args.check_config:
        handle_check_config(config)
        sys.exit(0)

    if args.self_audit:
        handle_self_audit()
        sys.exit(0)

    if args.logs:
        handle_view_logs(args.workspace)
        sys.exit(0)

    # Check for --resume, direct audit/docs modes, or interactive wizard
    cp = None
    if args.resume:
        from orchestrator.pipeline.checkpoint import PipelineCheckpointManager

        target_ws = resolve_workspace_dir(args.workspace, config.workspace_path)
        cp = PipelineCheckpointManager.load(target_ws)
        if cp:
            ConsoleOutput.banner(
                "Resuming Pipeline Execution",
                f"Phase: {cp.current_phase} | Run: {cp.run_id}",
            )
            task = cp.task
            mode = cp.mode
            workspace = target_ws
        else:
            ConsoleOutput.warning(
                f"No checkpoint file found at {target_ws}. Starting fresh."
            )
            if args.mode in ("audit", "audit-fix", "docs"):
                default_task = (
                    "Generate comprehensive project architecture and API documentation."
                    if args.mode == "docs"
                    else (
                        "Autonomous codebase defect and optimization fix loop."
                        if args.mode == "audit-fix"
                        else "Comprehensive codebase architecture, security, and bug audit."
                    )
                )
                task = resolve_task_input(args.task) if args.task else default_task
                mode = args.mode
                workspace = target_ws
            elif not args.task:
                task, mode, workspace = interactive_wizard(
                    config, skill_manager, default_mode=args.mode
                )
            else:
                task = resolve_task_input(args.task)
                mode = args.mode or "dev-test"
                workspace = target_ws
    elif args.mode in ("audit", "audit-fix", "docs"):
        default_task = (
            "Generate comprehensive project architecture and API documentation."
            if args.mode == "docs"
            else (
                "Autonomous codebase defect and optimization fix loop."
                if args.mode == "audit-fix"
                else "Comprehensive codebase architecture, security, and bug audit."
            )
        )
        task = resolve_task_input(args.task) if args.task else default_task
        mode = args.mode
        default_ws = (
            Path.cwd().resolve() if not args.workspace else config.workspace_path
        )
        workspace = resolve_workspace_dir(args.workspace, default_ws)
    elif not args.task:
        task, mode, workspace = interactive_wizard(
            config, skill_manager, default_mode=args.mode
        )
    else:
        task = resolve_task_input(args.task)
        mode = args.mode or "dev-test"
        workspace = resolve_workspace_dir(args.workspace, config.workspace_path)

    orchestrator = Orchestrator(config)
    try:
        orchestrator.run_task(
            task=task,
            mode=mode,
            workspace_override=workspace,
            checkpoint=cp,
        )
    except ProviderQuotaExceededError as e:
        ConsoleOutput.quota_error(e)
        sys.exit(1)
    except OrchestratorException as e:
        ConsoleOutput.error(f"Execution halted: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        ConsoleOutput.warning("Execution interrupted by user.")
        sys.exit(130)
    except Exception as e:
        err_text = str(e)
        if (
            "429" in err_text
            or "RateLimitError" in err_text
            or "free-models-per-day" in err_text
        ):
            ConsoleOutput.quota_error(
                ProviderQuotaExceededError(
                    provider="OpenRouter"
                    if "openrouter" in err_text.lower()
                    else "LLM Provider",
                    message="Daily free-tier request limit has been exhausted (1,000 requests/day).",
                    reset_info="Quota resets daily at 00:00 UTC (or upgrade to paid credits).",
                    remedy="Provide GEMINI_API_KEY or GROQ_API_KEY in .env, or add funds to OpenRouter.",
                )
            )
            sys.exit(1)
        if os.environ.get("DEBUG") == "true" or os.environ.get("VERBOSITY") == "debug":
            raise
        ConsoleOutput.error(f"Execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
