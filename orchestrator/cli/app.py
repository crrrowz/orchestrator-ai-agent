"""CLI entry point and command router for Antigravity Multi-Agent Orchestrator."""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

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
if "COLUMNS" not in os.environ:
    os.environ["COLUMNS"] = "160"
if "LINES" not in os.environ:
    os.environ["LINES"] = "40"

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
    handle_ci_diagnose,
    handle_ci_verify,
    handle_diagnostics_clean,
    handle_diagnostics_dashboard,
    handle_diagnostics_search,
    handle_list_skills,
    handle_self_audit,
    handle_sentinel_heal,
    handle_sentinel_status,
    handle_sentinel_test_mesh,
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
        help="Software development task description to execute (or 'gui' to launch the Visual Studio web interface).",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the ORAGAI Visual Studio web interface.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for Visual Studio web interface (default: 8080).",
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
    parser.add_argument(
        "--sentinel-status",
        action="store_true",
        help="Display live Sentinel diagnostics, circuit health, and self-healing statistics.",
    )
    parser.add_argument(
        "--sentinel-heal",
        type=Path,
        nargs="?",
        const=Path("."),
        default=None,
        help="Run standalone zero-token AST audit and auto-healing on a Python file or directory (defaults to current directory if omitted).",
    )
    parser.add_argument(
        "--sentinel-test-mesh",
        action="store_true",
        help="Probe cloud fallback mesh readiness and verify provider circuit breakers.",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Display unified diagnostics intelligence dashboard (telemetry, memory, sentinel, logs).",
    )
    parser.add_argument(
        "--diagnostics-search",
        type=str,
        default=None,
        metavar="QUERY",
        help="Search across all reports, task memories, sentinel incidents, and session logs.",
    )
    parser.add_argument(
        "--diagnostics-clean",
        action="store_true",
        help="Clean up test artifacts, prune old logs/memories, and regenerate the central diagnostics catalog.",
    )
    parser.add_argument(
        "--ci-diagnose",
        nargs="?",
        const="latest",
        default=None,
        metavar="RUN_ID",
        help="Diagnose GitHub Actions CI failure (e.g. --ci-diagnose [RUN_ID]).",
    )
    parser.add_argument(
        "--ci-verify",
        action="store_true",
        help="Run local replication of GitHub Actions CI pipeline verification gates.",
    )
    return parser.parse_args()


def _extract_clean_error_message(raw: str) -> str:
    """Extract human-readable core error string from raw LiteLLM/OpenHands exception payloads."""
    if not raw:
        return "Unknown runtime exception occurred."

    # 1. Check for JSON "message": "..." structure inside the error
    m = re.search(r'"message":\s*"([^"]+)"', raw)
    if m:
        msg = m.group(1).replace("\\n", " ").strip()
        if msg:
            return msg

    # 2. Extract inner exception from litellm/OpenHands wrappers
    if "litellm." in raw:
        parts = raw.split("litellm.")
        inner = parts[-1].strip()
        cleaned = re.sub(r"[\{\}\"]", "", inner).strip()
        if cleaned:
            return cleaned

    # 3. Strip Conversation run failed for id=...
    cleaned = re.sub(r"Conversation run failed for id=[a-f0-9\-]+:\s*", "", raw)
    first_line = cleaned.splitlines()[0] if cleaned else raw
    return first_line.strip()


def _detect_provider_name(err_text: str, config: Optional[Any] = None) -> str:
    """Detect upstream provider from error string or configuration."""
    low = err_text.lower()
    if "gemini" in low or "google" in low:
        return "Google Gemini"
    if "openrouter" in low:
        return "OpenRouter"
    if "groq" in low:
        return "Groq"
    if "anthropic" in low or "claude" in low:
        return "Anthropic"
    if "openai" in low:
        return "OpenAI"
    if config and getattr(config, "provider", None):
        return str(config.provider).capitalize()
    return "LLM Provider"


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

    if getattr(args, "gui", False) or (args.task and str(args.task).strip().lower() in ("gui", "ui", "serve")):
        from orchestrator.ui.server.app import serve
        port = getattr(args, "port", 8080) or 8080
        ConsoleOutput.banner("ORAGAI Visual Studio", f"http://127.0.0.1:{port}")
        serve(port)
        sys.exit(0)

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

    if args.sentinel_status:
        handle_sentinel_status(config)
        sys.exit(0)

    if args.sentinel_heal is not None:
        handle_sentinel_heal(args.sentinel_heal)
        sys.exit(0)

    if args.sentinel_test_mesh:
        handle_sentinel_test_mesh(config)
        sys.exit(0)

    if args.diagnostics:
        handle_diagnostics_dashboard()
        sys.exit(0)

    if args.diagnostics_search:
        handle_diagnostics_search(args.diagnostics_search)
        sys.exit(0)

    if args.diagnostics_clean:
        handle_diagnostics_clean()
        sys.exit(0)

    if args.ci_diagnose is not None:
        target_run = None if args.ci_diagnose == "latest" else args.ci_diagnose
        handle_ci_diagnose(run_id=target_run)
        sys.exit(0)

    if args.ci_verify:
        ws_dir = resolve_workspace_dir(args.workspace, config.workspace_path)
        handle_ci_verify(workspace_path=ws_dir)
        sys.exit(0)

    # Check for --resume, direct audit/docs modes, or interactive wizard
    cp = None
    if args.resume:
        from orchestrator.pipeline.checkpoint import PipelineCheckpointManager
        from orchestrator.pipeline.fsm.checkpoint import FSMCheckpointManager

        target_ws = resolve_workspace_dir(args.workspace, config.workspace_path)
        fsm_cp = FSMCheckpointManager.load_checkpoint(target_ws)
        legacy_cp = PipelineCheckpointManager.load(target_ws)

        if fsm_cp:
            ConsoleOutput.banner(
                "Resuming FSM Pipeline Execution",
                f"State: {fsm_cp.current_state} | Run: {fsm_cp.run_id}",
            )
            task = fsm_cp.task_description
            mode = fsm_cp.profile_name
            workspace = target_ws
            cp = fsm_cp
        elif legacy_cp:
            ConsoleOutput.banner(
                "Resuming Legacy Pipeline Execution",
                f"Phase: {legacy_cp.current_phase} | Run: {legacy_cp.run_id}",
            )
            task = legacy_cp.task
            mode = legacy_cp.mode
            workspace = target_ws
            cp = legacy_cp
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
        ConsoleOutput.execution_error(
            title="Orchestrator Execution Halted",
            message=str(e),
        )
        sys.exit(1)
    except KeyboardInterrupt:
        ConsoleOutput.warning("Execution interrupted by user.")
        sys.exit(130)
    except Exception as e:
        err_text = str(e)
        provider = _detect_provider_name(err_text, config)

        if (
            "429" in err_text
            or "RateLimitError" in err_text
            or "free-models-per-day" in err_text
            or "insufficient_quota" in err_text
        ):
            ConsoleOutput.quota_error(
                ProviderQuotaExceededError(
                    provider=provider,
                    message="Daily free-tier request limit has been exhausted (or rate ceiling reached).",
                    reset_info="Quota resets daily at 00:00 UTC (or upgrade to paid credits).",
                    remedy="Provide GEMINI_API_KEY or GROQ_API_KEY in .env, or add funds to your account.",
                )
            )
            sys.exit(1)

        # Detect 404 Model Not Found / Deprecated
        if (
            "404" in err_text
            or "NotFoundError" in err_text
            or "no longer available" in err_text
            or "NOT_FOUND" in err_text
        ):
            clean_msg = _extract_clean_error_message(err_text)
            ConsoleOutput.provider_error(
                provider=provider,
                error_type="Model Not Found / Deprecated",
                code=404,
                message=clean_msg,
                remedy="Update MODEL in .env (e.g. MODEL=gemini/gemini-3.6-flash or MODEL=openrouter/z-ai/glm-5.2:free).",
            )
            sys.exit(1)

        # Detect 401/403 Authentication Error
        if (
            "401" in err_text
            or "403" in err_text
            or "AuthenticationError" in err_text
            or "PermissionDenied" in err_text
            or "invalid_api_key" in err_text.lower()
        ):
            ConsoleOutput.provider_error(
                provider=provider,
                error_type="Authentication Failed",
                code=401,
                message="The upstream API key is invalid, missing, or unauthorized.",
                remedy=f"Verify your {provider.upper().replace(' ', '_')}_API_KEY in .env.",
            )
            sys.exit(1)

        if os.environ.get("DEBUG") == "true" or os.environ.get("VERBOSITY") == "debug":
            raise

        ConsoleOutput.execution_error(
            title="Pipeline Runtime Error",
            message=_extract_clean_error_message(err_text),
            hint="Run with --verbose or check .env configuration.",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
