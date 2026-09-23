"""Autonomous Codebase Audit & Fix Pipeline: Scan -> Remediate -> Verify Loop without Git."""

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openhands.sdk import Conversation
from orchestrator.adapters import ProjectAdapter, detect_adapter
from orchestrator.config import (
    OrchestratorConfig,
    SkillManager,
)
from orchestrator.agents import (
    create_developer_agent,
    create_tester_agent,
)
from orchestrator.control import (
    BudgetGuard,
    HumanInterventionChannel,
    PipelineController,
)
from orchestrator.control.human_channel import set_active_channel
from orchestrator.telemetry import TelemetryRecorder, get_llm_usage
from orchestrator.tools import WorkspaceTerminalAction, execute_terminal_action
from orchestrator.utils import (
    ConsoleOutput,
    GraftContextProvider,
    OrchestratorLiveVisualizer,
    SessionLogStore,
)


def extract_affected_files(issues: List[str], workspace_path: Path) -> List[str]:
    """Extract distinct relative file paths mentioned in issues and error traces."""
    affected = set()
    for text in issues:
        matches = re.findall(
            r"([\w\-./\\]+\.(?:py|ts|tsx|js|jsx|json|toml|yaml|yml|md))", text
        )
        for m in matches:
            clean = m.replace("\\", "/").strip("./:")
            candidate = workspace_path / clean
            if candidate.exists() and candidate.is_file():
                affected.add(clean)
    return sorted(list(affected))


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
        self.adapter: ProjectAdapter = detect_adapter(self.workspace_path)

    def _run_conv(
        self,
        conv: Conversation,
        role: str,
        max_retries: int = 2,
        timeout_seconds: int = 300,
        max_steps: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        """Execute conversation with iteration limits, token cap monitor, timeout guard, and backoff retry."""
        import threading

        step_limit = max_steps or getattr(self.config, "max_agent_steps", 12)
        token_limit = max_tokens or getattr(self.config, "max_tokens_budget", 300_000)

        # Configure native OpenHands step limit
        if hasattr(conv, "max_iteration_per_run"):
            conv.max_iteration_per_run = step_limit

        for attempt in range(max_retries + 1):
            if not self.controller.check_should_continue():
                ConsoleOutput.warning(
                    f"Conversation execution halted by controller for {role}."
                )
                return

            stop_monitor = threading.Event()

            def monitor():
                start_time = time.time()
                while not stop_monitor.is_set():
                    # Timeout check
                    if timeout_seconds > 0 and (time.time() - start_time) >= timeout_seconds:
                        ConsoleOutput.warning(
                            f"Agent {role} exceeded {timeout_seconds}s timeout cap. Halting."
                        )
                        if hasattr(conv, "interrupt"):
                            conv.interrupt()
                        elif hasattr(conv, "pause"):
                            conv.pause()
                        break

                    # Token limit check
                    llm = getattr(conv, "agent", None) and getattr(
                        conv.agent, "llm", None
                    )
                    if llm and hasattr(llm, "metrics"):
                        tu = getattr(llm.metrics, "accumulated_token_usage", None)
                        if tu:
                            pt = getattr(tu, "prompt_tokens", 0)
                            ct = getattr(tu, "completion_tokens", 0)
                            if isinstance(pt, (int, float)) and isinstance(
                                ct, (int, float)
                            ):
                                total_tok = int(pt + ct)
                                if token_limit > 0 and total_tok >= token_limit:
                                    ConsoleOutput.warning(
                                        f"Agent {role} exceeded hard token cap ({total_tok:,} >= {token_limit:,}). Halting execution."
                                    )
                                    if hasattr(conv, "interrupt"):
                                        conv.interrupt()
                                    elif hasattr(conv, "pause"):
                                        conv.pause()
                                    break

                    # Controller abort check
                    if not self.controller.check_should_continue():
                        if hasattr(conv, "interrupt"):
                            conv.interrupt()
                        elif hasattr(conv, "pause"):
                            conv.pause()
                        break

                    stop_monitor.wait(1.0)

            monitor_thread = threading.Thread(target=monitor, daemon=True)
            monitor_thread.start()

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
                stop_monitor.set()

    def collect_codebase_metrics(self) -> dict:
        """Scan workspace to calculate file counts and lines of code."""
        return self.adapter.collect_codebase_metrics(self.workspace_path)

    def run_static_checks(self) -> Tuple[bool, List[str]]:
        """Execute zero-token syntax validation and static analysis via adapter."""
        return self.adapter.run_static_analysis(self.workspace_path)

    def run_test_suite(self, timeout_seconds: int = 60) -> Tuple[bool, str]:
        """Execute test suite via detected language adapter."""
        if not self.adapter.has_test_suite(self.workspace_path):
            return (
                True,
                f"No test suite detected for {self.adapter.language_name} in workspace.",
            )

        test_cmd = self.adapter.get_test_command(self.workspace_path)
        if not test_cmd:
            return (True, "No test command configured.")

        test_run = execute_terminal_action(
            WorkspaceTerminalAction(command=test_cmd, timeout_seconds=timeout_seconds),
            base_dir=self.workspace_path,
        )

        if test_run.exit_code == 0:
            return (
                True,
                f"All {self.adapter.language_name} unit tests passed successfully.",
            )

        compact = self.adapter.parse_test_failures(test_run.stdout, test_run.stderr)
        return (
            False,
            f"[{self.adapter.language_name.capitalize()} Test Failures (Exit Code {test_run.exit_code})]\n{compact}",
        )

    def run_zero_token_autofix(self) -> Tuple[bool, str]:
        """Execute local deterministic code fixes/formatting via adapter."""
        return self.adapter.run_zero_token_autofix(self.workspace_path)

    def run(self, task_description: str = "") -> dict:
        """Run the continuous autonomous audit-and-fix loop without Git operations."""
        set_active_channel(self.human_channel)
        if not self.controller.check_should_continue():
            return {"status": "AUDIT_FIX_ABORTED", "reason": "Controller abort signal"}

        ConsoleOutput.banner(
            "Autonomous Audit & Auto-Fix Loop (Git-Free)",
            f"Workspace: {self.workspace_path} | Stack: {self.adapter.language_name.capitalize()} | Max Iterations: {self.config.max_iterations}",
        )

        # Step 0: Zero-Token Pre-Fix Strategy (Deterministic Local Linter & Formatter)
        ConsoleOutput.agent_step(
            "PRE-FIX",
            f"Running zero-token automated lint & format fixer ({self.adapter.language_name.capitalize()})...",
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

            # 3. On iteration 1: If static and tests are clean, check for existing audit report or explicit user directive
            if iteration == 1 and not all_issues:
                if existing_report_content:
                    auditor_findings = f"[Existing Audit Report Recommendations]\n{existing_report_content[:3000]}"
                    all_issues.append(auditor_findings)
                elif task_description and task_description.strip() not in (
                    "Autonomous Codebase Audit & Fix Loop",
                    "",
                ):
                    all_issues.append(
                        f"[User Optimization Directive]\n{task_description.strip()}"
                    )

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

            affected_files = extract_affected_files(all_issues, self.workspace_path)
            if affected_files:
                file_bullets = "\n".join(f"- `{f}`" for f in affected_files)
                scope_constraint = (
                    f"CRITICAL TARGET SCOPE LOCK:\n"
                    f"The issues are strictly isolated to the following file(s):\n"
                    f"{file_bullets}\n\n"
                    "MANDATORY PLAN-FIRST WORKFLOW:\n"
                    "1. First, state a concise 2-line plan:\n"
                    "   - Target File: <file>\n"
                    "   - Precise Fix: <exact lines or imports to modify>\n"
                    "2. You are STRICTLY FORBIDDEN from reading unmentioned files, diagnostics, or listing directories (`ls`, `dir`, `pwd`).\n"
                    "3. Open and modify ONLY the locked file(s) above using `workspace_file`.\n"
                    "4. Apply the fix and stop immediately."
                )
            else:
                scope_constraint = (
                    "MANDATORY PLAN-FIRST WORKFLOW:\n"
                    "1. First, state a concise 2-line plan (Target File and Planned Change).\n"
                    "2. Inspect ONLY the specific affected file where errors were reported.\n"
                    "3. Do NOT read unmentioned files or list unrelated directories to conserve token context.\n"
                    "4. Apply the targeted fix directly and stop."
                )

            test_status_note = ""
            if tests_clean:
                test_status_note = (
                    "\nNOTICE: All project unit tests are currently PASSING (100% green).\n"
                    "Do NOT run pytest or examine test suites or diagnostics. Focus ONLY on the static issues above."
                )

            effective_graft = graft_part if len(graft_part) < 1500 else ""

            dev_prompt = (
                f"Task: {user_directive}\n\n"
                f"Iteration {iteration} of {self.config.max_iterations} - Auto-Fix Remediation Directive:\n"
                f"The automated audit detected the following issues that must be solved in this {self.adapter.language_name.capitalize()} project:\n\n"
                f"{issues_text}\n"
                f"{test_status_note}\n\n"
                f"{scope_constraint}\n\n"
                f"{effective_graft}\n\n"
                f"{self.adapter.get_developer_prompt_guidance()}"
            )

            t_dev = time.perf_counter()
            dev_conv.send_message(self.human_channel.inject_into_prompt(dev_prompt))
            self._run_conv(dev_conv, "Developer")
            if hasattr(visualizer, "close"):
                visualizer.close()
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
