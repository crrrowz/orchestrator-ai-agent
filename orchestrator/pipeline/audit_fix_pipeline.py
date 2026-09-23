"""Autonomous Codebase Audit & Fix Pipeline: Scan -> Remediate -> Verify Loop without Git."""

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openhands.sdk import Conversation
from orchestrator.config import (
    OrchestratorConfig,
    SkillManager,
)
from orchestrator.agents import (
    create_auditor_agent,
    create_developer_agent,
    create_tester_agent,
)
from orchestrator.control import (
    BudgetGuard,
    HumanInterventionChannel,
    PipelineController,
)
from orchestrator.control.human_channel import set_active_channel
from orchestrator.guards import PreFlightGuard
from orchestrator.telemetry import TelemetryRecorder, get_llm_usage
from orchestrator.tools import WorkspaceTerminalAction, execute_terminal_action
from orchestrator.utils import (
    ConsoleOutput,
    GraftContextProvider,
    OrchestratorLiveVisualizer,
    PytestOutputParser,
    SessionLogStore,
)


class AuditFixPipeline:
    """Autonomous self-healing loop: audits defects/optimizations, applies fixes via Developer,
    and validates with Tester and static checks in a continuous loop without any Git operations.
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
        human_channel: Optional[HumanInterventionChannel] = None,
        controller: Optional[PipelineController] = None,
    ):
        self.config = config
        self.skill_manager = skill_manager
        self.workspace_path = (workspace_path or config.workspace_path).resolve()
        self.human_channel = human_channel or HumanInterventionChannel(
            enabled=config.interactive or bool(config.approval_gates)
        )
        self.controller = controller or PipelineController()
        self.budget_guard = BudgetGuard(max_budget_usd=config.max_budget_usd)

    def _run_conv(
        self,
        conv: Conversation,
        role: str,
        max_retries: int = 2,
        timeout_seconds: int = 300,
    ) -> None:
        """Execute conversation with retry on transient API/model failures and wall-clock timeout."""
        import threading

        for attempt in range(max_retries + 1):
            timer = None
            if timeout_seconds > 0:

                def on_timeout():
                    ConsoleOutput.warning(
                        f"Agent {role} exceeded {timeout_seconds}s timeout cap."
                    )
                    if hasattr(conv, "cancel"):
                        conv.cancel()
                    elif hasattr(conv, "stop"):
                        conv.stop()

                timer = threading.Timer(timeout_seconds, on_timeout)
                timer.daemon = True
                timer.start()

            try:
                conv.run()
                return
            except Exception as e:
                if attempt < max_retries:
                    delay = 2**attempt
                    ConsoleOutput.warning(
                        f"Agent {role} execution failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    raise
            finally:
                if timer:
                    timer.cancel()

    def collect_codebase_metrics(self) -> dict:
        """Scan workspace to calculate file counts and lines of code."""
        excluded_dirs = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            "site-packages",
            ".pytest_cache",
            ".agents",
        }
        total_py_files = 0
        total_loc = 0
        files_by_size: list[tuple[str, int]] = []

        for p in self.workspace_path.rglob("*.py"):
            if any(part in excluded_dirs for part in p.parts):
                continue
            try:
                lines = len(
                    p.read_text(encoding="utf-8", errors="replace").splitlines()
                )
                total_py_files += 1
                total_loc += lines
                files_by_size.append(
                    (p.relative_to(self.workspace_path).as_posix(), lines)
                )
            except Exception:
                continue

        files_by_size.sort(key=lambda x: x[1], reverse=True)
        return {
            "total_files": total_py_files,
            "total_loc": total_loc,
            "avg_loc": (total_loc // total_py_files) if total_py_files > 0 else 0,
            "top_files": files_by_size[:10],
        }

    def run_static_checks(self) -> Tuple[bool, List[str]]:
        """Execute zero-token AST syntax validation and Ruff static analysis."""
        issues: List[str] = []

        # 1. AST Syntax validation
        syntax_ok, syntax_err = PreFlightGuard.check_syntax(self.workspace_path)
        if not syntax_ok and syntax_err:
            issues.append(f"[Syntax Error]\n{syntax_err}")

        # 2. Ruff analysis if installed
        if shutil.which("ruff"):
            try:
                res = subprocess.run(
                    ["ruff", "check", ".", "--output-format=concise"],
                    cwd=str(self.workspace_path),
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if res.returncode != 0 and res.stdout.strip():
                    lines = [
                        line.strip() for line in res.stdout.splitlines() if line.strip()
                    ]
                    issues.append(
                        f"[Ruff Lint Issues ({len(lines)})]\n" + "\n".join(lines[:15])
                    )
            except Exception:
                pass

        return (len(issues) == 0, issues)

    def run_test_suite(self, timeout_seconds: int = 60) -> Tuple[bool, str]:
        """Execute pytest suite if tests directory or test files exist."""
        has_tests = (
            (self.workspace_path / "tests").exists()
            or list(self.workspace_path.glob("test_*.py"))
            or list(self.workspace_path.glob("*_test.py"))
            or (self.workspace_path / "pyproject.toml").exists()
        )
        if not has_tests:
            return (True, "No test suite detected in workspace.")

        pytest_cmd = (
            "uv run pytest -v"
            if (shutil.which("uv") and (self.workspace_path / "uv.lock").exists())
            else "python -m pytest -v"
        )
        test_run = execute_terminal_action(
            WorkspaceTerminalAction(
                command=pytest_cmd, timeout_seconds=timeout_seconds
            ),
            base_dir=self.workspace_path,
        )

        if test_run.exit_code == 0:
            return (True, "All pytest unit tests passed successfully.")

        compact = PytestOutputParser.extract_compact_failures(
            test_run.stdout, test_run.stderr
        )
        return (False, f"[Pytest Failures (Exit Code {test_run.exit_code})]\n{compact}")

    def run_zero_token_autofix(self) -> Tuple[bool, str]:
        """Execute local deterministic code fixes (Ruff check --fix and format) in ~50ms with 0 tokens.

        Fixes unused imports, basic syntax deprecations, formatting, and PEP 8 issues without LLM invocation.
        """
        if not shutil.which("ruff"):
            return (False, "ruff not available")

        try:
            # 1. Automatic safe lint fixes (unused imports, syntax deprecations, etc.)
            subprocess.run(
                [
                    "ruff",
                    "check",
                    "--fix",
                    "--unsafe-fixes",
                    "--output-format=concise",
                    ".",
                ],
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=15,
            )
            # 2. Deterministic code formatting
            subprocess.run(
                ["ruff", "format", "."],
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=15,
            )
            return (True, "Zero-token auto-fixes applied")
        except Exception as e:
            return (False, str(e))

    def run(self, task_description: str = "") -> dict:
        """Run the continuous autonomous audit-and-fix loop without Git operations."""
        set_active_channel(self.human_channel)
        if not self.controller.check_should_continue():
            return {"status": "AUDIT_FIX_ABORTED", "reason": "Controller abort signal"}

        ConsoleOutput.banner(
            "Autonomous Audit & Auto-Fix Loop (Git-Free)",
            f"Workspace: {self.workspace_path} | Max Iterations: {self.config.max_iterations}",
        )

        # Step 0: Zero-Token Pre-Fix Strategy (Deterministic Local Linter & Formatter)
        ConsoleOutput.agent_step(
            "PRE-FIX", "Running zero-token automated lint & format fixer (Ruff)..."
        )
        autofix_ok, _ = self.run_zero_token_autofix()
        if autofix_ok:
            ConsoleOutput.info(
                "Zero-token local auto-fix executed successfully (0 tokens consumed)."
            )

        log_store = SessionLogStore(workspace_path=self.workspace_path)
        visualizer = OrchestratorLiveVisualizer(
            log_store, verbosity=self.config.verbosity
        )
        telemetry = TelemetryRecorder(
            task_description=task_description or "Autonomous Codebase Audit & Fix Loop",
            pipeline_mode="audit-fix",
            max_budget_usd=self.config.max_budget_usd,
        )

        metrics = self.collect_codebase_metrics()
        graft_map = GraftContextProvider.get_compact_map(self.workspace_path)
        graft_part = (
            f"\n\n[Codebase Architecture Map (Graft)]:\n{graft_map}"
            if graft_map
            else ""
        )

        # Check for existing AUDIT_REPORT.md or explicit file in task
        existing_report_content = ""
        audit_file = self.workspace_path / "AUDIT_REPORT.md"
        if audit_file.exists():
            try:
                existing_report_content = audit_file.read_text(
                    encoding="utf-8", errors="replace"
                ).strip()
                ConsoleOutput.info(
                    f"Loaded existing audit report from {audit_file.name} ({len(existing_report_content)} chars)."
                )
            except Exception:
                pass

        developer_agent = create_developer_agent(
            self.config,
            self.skill_manager,
            self.workspace_path,
            allow_test_writes=True,
        )
        tester_agent = create_tester_agent(
            self.config,
            self.skill_manager,
            self.workspace_path,
        )

        dev_conv = Conversation(
            agent=developer_agent,
            workspace=str(self.workspace_path),
            visualizer=visualizer,
        )
        dev_conv.human_channel = self.human_channel

        tester_conv = Conversation(
            agent=tester_agent,
            workspace=str(self.workspace_path),
            visualizer=visualizer,
        )
        tester_conv.human_channel = self.human_channel

        fixes_applied_log: List[Dict[str, Any]] = []
        final_status = "IN_PROGRESS"
        last_issues: List[str] = []

        for iteration in range(1, self.config.max_iterations + 1):
            if not self.controller.check_should_continue():
                ConsoleOutput.warning(
                    f"Audit-fix loop stopped by controller at iteration {iteration}."
                )
                final_status = "STOPPED_BY_CONTROLLER"
                break

            # Run zero-token auto-fix before each inspection pass
            self.run_zero_token_autofix()

            ConsoleOutput.agent_step(
                "AUDIT",
                f"Iteration {iteration}/{self.config.max_iterations}: Scanning workspace...",
            )

            # 1. Run static checks
            static_clean, static_issues = self.run_static_checks()

            # 2. Run test suite
            tests_clean, test_feedback = self.run_test_suite()

            all_issues: List[str] = []
            if not static_clean:
                all_issues.extend(static_issues)
            if not tests_clean:
                all_issues.append(test_feedback)

            # 3. On iteration 1: If static and tests are clean but an existing audit report exists, include it.
            # If nothing was found and no audit report, run Auditor agent once to find subtle logic / architectural flaws.
            auditor_findings = ""
            if iteration == 1 and not all_issues:
                if existing_report_content:
                    auditor_findings = f"[Existing Audit Report Recommendations]\n{existing_report_content[:3000]}"
                    all_issues.append(auditor_findings)
                else:
                    auditor_agent = create_auditor_agent(
                        self.config, self.skill_manager, self.workspace_path
                    )
                    ConsoleOutput.agent_step(
                        "Auditor",
                        "Running deep semantic inspection...",
                        model=auditor_agent.llm.model,
                    )
                    t_audit = time.perf_counter()
                    aud_conv = Conversation(
                        agent=auditor_agent,
                        workspace=str(self.workspace_path),
                        visualizer=visualizer,
                    )
                    aud_conv.human_channel = self.human_channel
                    aud_prompt = (
                        "Perform an immediate semantic inspection of the codebase in the workspace. "
                        "Identify any logic bugs, unhandled exceptions, missing type annotations, or performance bottlenecks. "
                        "List specific, actionable defects that need fixing."
                    )
                    aud_conv.send_message(
                        self.human_channel.inject_into_prompt(aud_prompt)
                    )
                    self._run_conv(aud_conv, "Auditor")
                    dur_audit = time.perf_counter() - t_audit
                    u_aud = get_llm_usage(auditor_agent.llm)
                    telemetry.record_step(
                        "auditor",
                        "semantic_scan",
                        iteration,
                        dur_audit,
                        True,
                        prompt_tokens=u_aud["prompt_tokens"],
                        completion_tokens=u_aud["completion_tokens"],
                        total_tokens=u_aud["total_tokens"],
                        estimated_cost_usd=u_aud["estimated_cost_usd"],
                    )
                    # Check if auditor produced AUDIT_REPORT.md
                    if audit_file.exists():
                        try:
                            fresh_report = audit_file.read_text(
                                encoding="utf-8", errors="replace"
                            ).strip()
                            if (
                                "## Key Recommendations" in fresh_report
                                or "###" in fresh_report
                            ):
                                auditor_findings = fresh_report[:3000]
                                all_issues.append(
                                    f"[Auditor Findings]\n{auditor_findings}"
                                )
                        except Exception:
                            pass

            last_issues = all_issues

            # 4. Check Convergence
            if not all_issues:
                ConsoleOutput.success(
                    f"Audit-Fix Loop Converged in iteration {iteration}! Zero defects detected."
                )
                final_status = "CONVERGED_CLEAN"
                break

            # 5. Remediation by Developer Agent
            ConsoleOutput.warning(
                f"Iteration {iteration}: {len(all_issues)} issue group(s) detected. Developer applying fixes..."
            )
            log_store.set_agent_context(
                "Developer",
                f"Fix Iteration {iteration}",
                model=developer_agent.llm.model,
                llm=developer_agent.llm,
            )

            issues_text = "\n\n".join(all_issues)
            user_directive = (
                task_description.strip()
                if task_description
                else "Audit and auto-fix all codebase defects and optimizations."
            )

            dev_prompt = (
                f"Task: {user_directive}\n\n"
                f"Iteration {iteration} of {self.config.max_iterations} - Auto-Fix Remediation Directive:\n"
                "The automated audit detected the following issues that must be solved:\n\n"
                f"{issues_text}\n"
                f"{graft_part}\n\n"
                "INSTRUCTIONS:\n"
                "1. Inspect ONLY the specific affected files where errors/failures were reported.\n"
                "2. Do NOT read unmentioned files or list unrelated directories to conserve token context.\n"
                "3. Apply robust, production-grade fixes directly to the files adhering to clean-python-architecture.\n"
                "4. Ensure all syntax, type errors, lint issues, and test failures are completely resolved.\n"
                "5. Do NOT use git commands (all changes must be made directly to the workspace files)."
            )

            t_dev = time.perf_counter()
            dev_conv.send_message(self.human_channel.inject_into_prompt(dev_prompt))
            self._run_conv(dev_conv, "Developer")
            dur_dev = time.perf_counter() - t_dev
            u_dev = get_llm_usage(developer_agent.llm)

            telemetry.record_step(
                "developer",
                "auto_fix",
                iteration,
                dur_dev,
                True,
                prompt_tokens=u_dev["prompt_tokens"],
                completion_tokens=u_dev["completion_tokens"],
                total_tokens=u_dev["total_tokens"],
                estimated_cost_usd=u_dev["estimated_cost_usd"],
            )

            fixes_applied_log.append(
                {
                    "iteration": iteration,
                    "issues_count": len(all_issues),
                    "duration_seconds": round(dur_dev, 2),
                    "tokens": u_dev["total_tokens"],
                    "cost_usd": u_dev["estimated_cost_usd"],
                }
            )

            # Check total cost against budget guard
            total_cost_usd = u_dev["estimated_cost_usd"]
            if self.budget_guard.update_cost(total_cost_usd):
                ConsoleOutput.error(
                    "Budget ceiling reached during auto-fix loop. Halting."
                )
                final_status = "BUDGET_EXHAUSTED"
                break

            # 6. Verification: Immediate check post-remediation
            post_static_ok, post_static_issues = self.run_static_checks()
            post_tests_ok, post_test_feedback = self.run_test_suite()

            from orchestrator.pipeline.checkpoint import PipelineCheckpointManager

            PipelineCheckpointManager.save(
                workspace=self.workspace_path,
                run_id=telemetry.report_id,
                task=task_description or "Autonomous Codebase Audit & Fix Loop",
                mode="audit-fix",
                current_phase=f"iteration_{iteration}",
                iteration=iteration,
                tests_passed=(post_static_ok and post_tests_ok),
            )

            if post_static_ok and post_tests_ok:
                ConsoleOutput.success(
                    f"Verification successful in iteration {iteration}! All tests and static checks pass."
                )
                final_status = "CONVERGED_CLEAN"
                break
            else:
                ConsoleOutput.warning(
                    f"Iteration {iteration} verification: Issues remain "
                    f"(Static Clean: {post_static_ok}, Tests Clean: {post_tests_ok}). Proceeding to next iteration."
                )

        if final_status == "IN_PROGRESS":
            final_status = "MAX_ITERATIONS_REACHED"

        # Generate AUDIT_FIX_REPORT.md
        report_file = self.workspace_path / "AUDIT_FIX_REPORT.md"
        report_content = self._generate_report_content(
            task_description=task_description,
            final_status=final_status,
            metrics=metrics,
            fixes_log=fixes_applied_log,
            last_issues=last_issues,
        )
        report_file.write_text(report_content, encoding="utf-8")

        telemetry.finalize(completed_successfully=(final_status == "CONVERGED_CLEAN"))
        log_store.save_to_file()

        u_total = get_llm_usage(developer_agent.llm)
        ConsoleOutput.banner(
            "Audit & Auto-Fix Run Finished",
            f"Status: {final_status} | Report: {report_file.name} | Total Tokens: {u_total['total_tokens']:,}",
        )

        return {
            "status": final_status,
            "report_path": str(report_file),
            "iterations": len(fixes_applied_log) or 1,
            "tokens": u_total.get("total_tokens", 0),
            "cost_usd": u_total.get("estimated_cost_usd", 0.0),
        }

    def _generate_report_content(
        self,
        task_description: str,
        final_status: str,
        metrics: dict,
        fixes_log: List[dict],
        last_issues: List[str],
    ) -> str:
        """Construct the markdown summary of the audit-fix session."""
        ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        lines = [
            "# Autonomous Codebase Audit & Auto-Fix Report",
            "",
            f"- **Execution Timestamp**: {ts}",
            f"- **Final Outcome**: `{final_status}`",
            f"- **Target Workspace**: `{self.workspace_path}`",
            f"- **Task Directive**: {task_description or 'Comprehensive Audit & Fix'}",
            f"- **Total Python Files**: {metrics.get('total_files', 0)}",
            f"- **Total Lines of Code**: {metrics.get('total_loc', 0)}",
            "",
            "## Iteration History",
            "",
        ]

        if not fixes_log:
            lines.append(
                "No remediation iterations were needed; workspace was clean on initial scan."
            )
        else:
            lines.append(
                "| Iteration | Issues Addressed | Duration (s) | Tokens Used | Est. Cost ($) |"
            )
            lines.append("|---|---|---|---|---|")
            for entry in fixes_log:
                lines.append(
                    f"| {entry['iteration']} | {entry['issues_count']} | "
                    f"{entry['duration_seconds']}s | {entry['tokens']:,} | ${entry['cost_usd']:.4f} |"
                )

        lines.append("")
        lines.append("## Final Verification State")
        lines.append("")
        if final_status == "CONVERGED_CLEAN":
            lines.append("- [x] AST Syntax Validation: **PASS**")
            lines.append("- [x] Ruff Static Linting: **CLEAN**")
            lines.append("- [x] Automated Pytest Suite: **PASS**")
            lines.append(
                "- [x] Zero Git Footprint: Edits made directly in workspace working tree."
            )
        else:
            lines.append(
                f"Status: `{final_status}`. Some remaining issues require further review:"
            )
            for issue in last_issues[:5]:
                lines.append(f"```text\n{issue[:500]}\n```")

        return "\n".join(lines)
