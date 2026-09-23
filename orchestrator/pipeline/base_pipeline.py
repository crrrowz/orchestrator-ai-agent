"""Base Pipeline defining common lifecycle, telemetry, git ops, and execution loops."""

from abc import ABC, abstractmethod
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from openhands.sdk import Conversation

from orchestrator.adapters import ProjectAdapter, detect_adapter
from orchestrator.config import (
    DEFAULT_DIAGNOSTICS_DIR,
    OrchestratorConfig,
    SkillManager,
)
from orchestrator.control import BudgetGuard, HumanChannel, PipelineController
from orchestrator.guards.preflight import PreFlightGuard
from orchestrator.memory import ConversationMemoryStore
from orchestrator.pipeline.checkpoint import PipelineCheckpoint
from orchestrator.pipeline.state_machine import PipelinePhase, PipelineStateMachine
from orchestrator.telemetry import TelemetryRecorder, get_llm_usage
from orchestrator.tools import (
    WorkspaceTerminalAction,
    WorkspaceTerminalObservation,
    execute_terminal_action,
)
from orchestrator.utils import (
    ConsoleOutput,
    GitOps,
    GraftContextProvider,
    InteractiveLogExplorer,
    OrchestratorLiveVisualizer,
    SessionLogStore,
)


class BasePipeline(ABC):
    """Abstract base class consolidating git isolation, telemetry, preflight, and lifecycle controls."""

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
        checkpoint: Optional[PipelineCheckpoint] = None,
        controller: Optional[PipelineController] = None,
        human_channel: Optional[Any] = None,
    ):
        self.config = config
        self.skill_manager = skill_manager
        self.workspace_path = (workspace_path or config.workspace_path).resolve()
        self.checkpoint = checkpoint
        self.controller = controller or PipelineController()
        self.budget_guard = BudgetGuard(max_budget_usd=config.max_budget_usd)
        self.state_machine = PipelineStateMachine()
        self.git = GitOps(self.workspace_path)
        self.human_channel = human_channel or HumanChannel(
            enabled=config.interactive or bool(config.approval_gates),
        )
        self.adapter: ProjectAdapter = detect_adapter(self.workspace_path)

    def _setup_run(
        self,
        task_description: str,
        mode: str,
        banner_title: str,
    ) -> Tuple[
        TelemetryRecorder,
        ConversationMemoryStore,
        SessionLogStore,
        OrchestratorLiveVisualizer,
        str,
    ]:
        """Initialize git isolation branch, telemetry recorder, memory store, and logger."""
        # 0. State Machine Initialization
        if (
            self.state_machine.current_phase != PipelinePhase.INIT
            and self.state_machine.can_transition(PipelinePhase.INIT)
        ):
            self.state_machine.transition_to(PipelinePhase.INIT)

        # 1. Git task branch isolation
        self.git.init_if_needed()
        if self.git.is_dirty():
            ConsoleOutput.warning(
                "Workspace has uncommitted changes. Stashing or proceeding on working tree."
            )
        task_slug = (
            re.sub(r"[^a-zA-Z0-9_\-]+", "-", task_description.lower())[:30].strip("-")
            or "task"
        )
        branch_name = f"agent/{task_slug}-{int(time.time())}"
        if self.git.create_and_checkout_branch(branch_name):
            ConsoleOutput.agent_step(
                "GIT", f"Isolated task branch created: [bold]{branch_name}[/bold]"
            )

        # 2. Output and Telemetry
        ConsoleOutput.banner(
            banner_title,
            f"Workspace: {self.workspace_path} | Max Iterations: {self.config.max_iterations} | Budget: ${self.config.max_budget_usd:.2f}",
        )
        ConsoleOutput.agent_step(
            "SYSTEM",
            f"Loaded Skills: {', '.join(sorted(self.skill_manager.available_skills))}",
        )

        recorder = TelemetryRecorder(
            task_description=task_description,
            pipeline_mode=mode,
            reports_dir=DEFAULT_DIAGNOSTICS_DIR / "reports",
            max_budget_usd=self.config.max_budget_usd,
            max_retained_reports=getattr(self.config, "max_retained_reports", 20),
        )
        memory_store = ConversationMemoryStore(DEFAULT_DIAGNOSTICS_DIR)
        log_store = SessionLogStore(self.workspace_path)
        visualizer = OrchestratorLiveVisualizer(
            log_store=log_store, verbosity=self.config.verbosity
        )

        # 3. Graft Architecture Context
        graft_map = GraftContextProvider.get_compact_map(self.workspace_path)
        if graft_map:
            ConsoleOutput.agent_step(
                "GRAFT", "Injected zero-token codebase architecture map."
            )

        return recorder, memory_store, log_store, visualizer, graft_map

    def _run_conv(
        self,
        conv: Conversation,
        role_name: str,
        max_retries: int = 2,
        max_steps: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        """Run agent conversation with iteration limits, token cap monitor, timeout guard, and backoff retry."""
        timeout_seconds = 300.0
        step_limit = max_steps or getattr(self.config, "max_agent_steps", 12)
        token_limit = max_tokens or getattr(self.config, "max_tokens_budget", 350_000)

        # Configure native OpenHands step limit
        if hasattr(conv, "max_iteration_per_run"):
            conv.max_iteration_per_run = step_limit

        for attempt in range(max_retries + 1):
            if not self.controller.check_should_continue():
                ConsoleOutput.warning(
                    f"Conversation execution halted by controller for {role_name}."
                )
                return

            stop_monitor = threading.Event()

            def monitor():
                start_time = time.time()
                while not stop_monitor.is_set():
                    # Timeout check
                    if timeout_seconds > 0 and (time.time() - start_time) >= timeout_seconds:
                        ConsoleOutput.warning(
                            f"Agent {role_name} exceeded {timeout_seconds}s timeout cap. Halting."
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
                                        f"Agent {role_name} exceeded hard token cap ({total_tok:,} >= {token_limit:,}). Halting execution."
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
                    backoff = 2**attempt
                    ConsoleOutput.warning(
                        f"{role_name} conversation failed (attempt {attempt + 1}): {e}. Retrying in {backoff}s..."
                    )
                    time.sleep(backoff)
                else:
                    ConsoleOutput.error(
                        f"{role_name} conversation failed after {max_retries + 1} attempts: {e}"
                    )
                    raise
            finally:
                stop_monitor.set()

    def _run_preflight(
        self,
        iteration: int,
        dev_conv: Conversation,
        developer_agent: Any,
        recorder: TelemetryRecorder,
        log_store: SessionLogStore,
    ) -> bool:
        """Execute zero-token syntax and importability checks. If errors found, invoke Developer to fix."""
        if self.state_machine.can_transition(PipelinePhase.PREFLIGHT):
            self.state_machine.transition_to(PipelinePhase.PREFLIGHT)

        syntax_ok, syntax_err = PreFlightGuard.check_syntax(self.workspace_path)
        import_ok, import_err = PreFlightGuard.check_importability(self.workspace_path)

        if not syntax_ok or not import_ok:
            combined_err = f"{syntax_err}\n\n{import_err}".strip()
            ConsoleOutput.warning(
                f"Pre-flight validation failed in iteration {iteration}! Routing errors to Developer."
            )
            log_store.add_step(
                f"Pre-flight code error in iteration {iteration}",
                is_error=True,
                observation=combined_err,
            )
            recorder.record_incident(
                f"Iteration_{iteration}_Preflight",
                "preflight_error",
                combined_err[:300],
            )

            t_syntax_fix = time.perf_counter()
            dev_conv.send_message(
                f"Pre-flight code validation detected compilation/import errors in workspace:\n\n{combined_err}\n\n"
                "Please fix these syntax and import errors immediately."
            )
            self._run_conv(dev_conv, "Developer (Preflight Fix)")
            dur_syntax = time.perf_counter() - t_syntax_fix
            u_dev_syntax = get_llm_usage(developer_agent.llm)
            recorder.record_step(
                "developer",
                "fix_syntax",
                iteration,
                dur_syntax,
                True,
                prompt_tokens=u_dev_syntax["prompt_tokens"],
                completion_tokens=u_dev_syntax["completion_tokens"],
                total_tokens=u_dev_syntax["total_tokens"],
                estimated_cost_usd=u_dev_syntax["estimated_cost_usd"],
            )
            return False
        return True

    def _execute_tests(self, timeout_seconds: int = 60) -> WorkspaceTerminalObservation:
        """Execute project test suite using detected language adapter."""
        test_cmd = self.adapter.get_test_command(self.workspace_path)
        if not test_cmd:
            if (self.workspace_path / "pyproject.toml").exists():
                test_cmd = "pytest -v"
            elif (self.workspace_path / "tests").exists():
                test_cmd = "pytest tests/ -v"
            else:
                test_cmd = "pytest -v"

        return execute_terminal_action(
            WorkspaceTerminalAction(command=test_cmd, timeout_seconds=timeout_seconds),
            base_dir=self.workspace_path,
        )

    def _execute_pytest(
        self, timeout_seconds: int = 60
    ) -> WorkspaceTerminalObservation:
        """Execute pytest against the workspace directory (backward-compatible alias)."""
        return self._execute_tests(timeout_seconds=timeout_seconds)

    def _finalize_pipeline(
        self,
        task_description: str,
        success: bool,
        iteration: int,
        recorder: TelemetryRecorder,
        memory_store: ConversationMemoryStore,
        log_store: SessionLogStore,
        commit_msg_prefix: str,
        status_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Finalize telemetry report, git commit, summary table, memory persistence, and log explorer."""
        diag_report = recorder.finalize(completed_successfully=success)
        ConsoleOutput.success(f"Telemetry report logged: {diag_report.report_id}")

        commit_hash = ""
        if success and self.config.auto_commit:
            if self.state_machine.can_transition(PipelinePhase.COMMIT):
                self.state_machine.transition_to(PipelinePhase.COMMIT)

            can_commit = True
            if "before_commit" in self.config.approval_gates:
                gate_decision = self.human_channel.prompt_gate(
                    "before_commit",
                    context_preview="All tests and checks passed. Confirm Git commit.",
                )
                if gate_decision == "rejected":
                    ConsoleOutput.warning("Git commit cancelled by human operator.")
                    can_commit = False

            if can_commit:
                commit_msg = f"{commit_msg_prefix}: {task_description[:50]} (verified by multi-agent pipeline)"
                commit_res = self.git.commit(commit_msg)
                if commit_res:
                    commit_hash = commit_res
                    ConsoleOutput.success(f"Created Git commit: {commit_hash[:8]}")

        if success:
            if self.state_machine.can_transition(PipelinePhase.COMPLETED):
                self.state_machine.transition_to(PipelinePhase.COMPLETED)
        else:
            if self.state_machine.can_transition(PipelinePhase.FAILED):
                self.state_machine.transition_to(PipelinePhase.FAILED)

        status_str = status_override or ("SUCCESS" if success else "FAILED")
        ConsoleOutput.summary_table(
            iterations=iteration,
            status=status_str,
            commit_hash=commit_hash,
            total_tokens=diag_report.total_tokens,
            total_cost_usd=diag_report.total_cost_usd,
        )

        try:
            memory_store.save_run_memory(
                task=task_description,
                summary=f"Pipeline concluded with {status_str} in {iteration} iteration(s).",
                tests_passed=success,
                lessons=recorder.recommendations[0]
                if recorder.recommendations
                else None,
            )
        except Exception:
            pass

        log_store.save_to_file()
        if sys.stdin.isatty() and self.config.interactive:
            try:
                InteractiveLogExplorer(log_store).run()
            except Exception:
                pass

        return {
            "status": status_str,
            "iterations": iteration,
            "commit_hash": commit_hash,
            "report_id": diag_report.report_id,
        }

    @abstractmethod
    def run(self, task_description: str) -> Dict[str, Any]:
        """Execute the pipeline run."""
        pass
