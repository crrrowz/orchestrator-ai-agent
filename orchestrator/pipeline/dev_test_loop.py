"""Developer -> Tester loop with Circuit Breaker and Telemetry logging."""

import time
from pathlib import Path
from typing import Optional

from openhands.sdk import Conversation
from orchestrator.agents import create_developer_agent, create_tester_agent
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.telemetry import TelemetryRecorder, get_llm_usage
from orchestrator.tools import (
    WorkspaceTerminalAction,
    execute_terminal_action,
)
from orchestrator.guards import PreFlightGuard
from orchestrator.utils import (
    ConsoleOutput,
    GitOps,
    GraftContextProvider,
    InteractiveLogExplorer,
    OrchestratorLiveVisualizer,
    PytestOutputParser,
    SessionLogStore,
)
from orchestrator.control import HumanInterventionChannel
from orchestrator.memory import ConversationStore
from orchestrator.pipeline.checkpoint import PipelineCheckpointManager


class DevTestLoop:
    """Manages the iteration loop between Developer and Tester agents with cost protection."""

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
        human_channel: Optional[HumanInterventionChannel] = None,
    ):
        self.config = config
        self.skill_manager = skill_manager
        self.workspace_path = (workspace_path or config.workspace_path).resolve()
        self.git = GitOps(self.workspace_path)
        self.human_channel = human_channel or HumanInterventionChannel(
            enabled=config.interactive or bool(config.approval_gates)
        )

    def run(self, task_description: str) -> dict:
        """Execute the Dev-Test pipeline with circuit breaker protection."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.git.init_repo()
        task_branch = self.git.create_task_branch(task_description)
        if task_branch:
            ConsoleOutput.agent_step("Git", f"Isolated task branch created: [bold cyan]{task_branch}[/bold cyan]")

        recorder = TelemetryRecorder(
            task_description=task_description,
            pipeline_mode="dev-test",
            circuit_breaker_threshold=self.config.circuit_breaker_threshold,
            max_budget_usd=self.config.max_budget_usd,
        )

        log_store = SessionLogStore(self.workspace_path)
        visualizer = OrchestratorLiveVisualizer(log_store, verbosity=self.config.verbosity)

        ConsoleOutput.banner(
            "Starting Developer-Tester Pipeline",
            f"Workspace: {self.workspace_path} | Max Iterations: {self.config.max_iterations} | Budget: ${self.config.max_budget_usd:.2f}"
        )
        ConsoleOutput.agent_step("System", f"Loaded Skills: {', '.join(self.skill_manager.available_skills)}")

        developer_agent = create_developer_agent(self.config, self.skill_manager, self.workspace_path)
        tester_agent = create_tester_agent(self.config, self.skill_manager, self.workspace_path)

        def _get_total_cost() -> float:
            return get_llm_usage(developer_agent.llm)["estimated_cost_usd"] + get_llm_usage(tester_agent.llm)["estimated_cost_usd"]

        try:
            # Step 1: Initial Implementation by Developer
            t0 = time.perf_counter()
            log_store.set_agent_context("Developer", "Initial Implementation", model=developer_agent.llm.model, llm=developer_agent.llm)
            ConsoleOutput.agent_step("Developer", "Implementing solution based on skills...", details=f"Task: {task_description}", model=developer_agent.llm.model)
            # Graft zero-token codebase context injection
            graft_map = GraftContextProvider.get_compact_map(self.workspace_path)
            graft_part = f"\n\n[Codebase Architecture Map (Graft)]:\n{graft_map}" if graft_map else ""

            # Memory cross-run intelligence injection
            memory_store = ConversationStore()
            memory_ctx = memory_store.format_memory_context(task_description)
            memory_part = f"\n\n{memory_ctx}" if memory_ctx else ""

            dev_conv = Conversation(agent=developer_agent, workspace=str(self.workspace_path), visualizer=visualizer)
            dev_prompt = (
                f"Implement the following software task:\n\n{task_description}\n\n"
                "Ensure full implementation, type safety, and adhere to clean-python-architecture."
                f"{graft_part}"
                f"{memory_part}"
            )
            dev_conv.send_message(self.human_channel.inject_into_prompt(dev_prompt))
            dev_conv.run()
            duration_dev = time.perf_counter() - t0
            curr_diff = self.git.get_diff() or self.git.get_status()
            u_dev = get_llm_usage(developer_agent.llm)
            recorder.record_step(
                "developer", "initial_implementation", 1, duration_dev, True, curr_diff,
                prompt_tokens=u_dev["prompt_tokens"],
                completion_tokens=u_dev["completion_tokens"],
                total_tokens=u_dev["total_tokens"],
                estimated_cost_usd=u_dev["estimated_cost_usd"],
            )
            ConsoleOutput.success(f"Developer completed implementation phase (Tokens: {u_dev['total_tokens']:,}, Cost: ${u_dev['estimated_cost_usd']:.4f}).")

            if recorder.check_budget(_get_total_cost()):
                ConsoleOutput.error("Budget ceiling reached after initial implementation. Halting.")
                diag_report = recorder.finalize(completed_successfully=False)
                log_store.save_to_file()
                return {"status": "BUDGET_EXHAUSTED", "iterations": 1, "report_id": diag_report.report_id}

            # Persist checkpoint after developer implementation
            PipelineCheckpointManager.save(
                workspace=self.workspace_path,
                run_id=recorder.report_id,
                task=task_description,
                mode="dev-test",
                current_phase="after_developer",
                completed_phases=["developer"],
            )

            # Approval Gate: after_developer
            if "after_developer" in self.config.approval_gates:
                diff_preview = self.git.get_diff() or self.git.get_status()
                gate_decision = self.human_channel.prompt_gate("after_developer", context_preview=diff_preview[:1500])
                if gate_decision == "rejected":
                    ConsoleOutput.error("Execution halted: human operator rejected changes at 'after_developer' gate.")
                    log_store.add_step("Changes rejected at after_developer approval gate.", is_error=True)
                    diag_report = recorder.finalize(completed_successfully=False)
                    log_store.save_to_file()
                    return {"status": "HUMAN_REJECTED", "phase": "developer", "report_id": diag_report.report_id}

            # Step 2: Iterative Test & Fix Loop
            iteration = 1
            tests_passed = False
            tester_conv = Conversation(agent=tester_agent, workspace=str(self.workspace_path), visualizer=visualizer)

            while iteration <= self.config.max_iterations:
                # Step 2a: Zero-Token Pre-flight Syntax Check (<50ms)
                syntax_ok, syntax_err = PreFlightGuard.check_syntax(self.workspace_path)
                if not syntax_ok:
                    ConsoleOutput.warning(f"Pre-flight syntax check failed in iteration {iteration}! Prompting Developer immediately without wasting test tokens.")
                    log_store.add_step(f"Pre-flight syntax error detected in iteration {iteration}", is_error=True, observation=syntax_err)
                    recorder.record_incident(f"Iteration_{iteration}_Syntax", "syntax_error", syntax_err[:300])
                    t_syntax_fix = time.perf_counter()
                    dev_conv.send_message(
                        f"Pre-flight syntax validation detected syntax errors:\n\n{syntax_err}\n\n"
                        "Please correct syntax immediately so tests can run."
                    )
                    dev_conv.run()
                    dur_syntax = time.perf_counter() - t_syntax_fix
                    u_dev_syntax = get_llm_usage(developer_agent.llm)
                    recorder.record_step(
                        "developer", "fix_syntax", iteration, dur_syntax, True,
                        prompt_tokens=u_dev_syntax["prompt_tokens"],
                        completion_tokens=u_dev_syntax["completion_tokens"],
                        total_tokens=u_dev_syntax["total_tokens"],
                        estimated_cost_usd=u_dev_syntax["estimated_cost_usd"],
                    )

                t_test = time.perf_counter()
                if iteration == 1:
                    # Iteration 1: Tester creates test suite
                    tester_conv.send_message(
                        f"Task: {task_description}\n\n"
                        "Write comprehensive pytest tests in tests/ directory and run pytest. "
                        "Ensure edge cases and boundary conditions are covered as per pytest-rigorous-testing."
                    )
                    tester_conv.run()
                else:
                    # Iteration 2+: Reuse tester conversation to verify fixes
                    tester_conv.send_message(
                        f"Iteration {iteration}: Developer updated the code to address previous failures. "
                        "Run pytest -v to re-verify the test suite. If needed, update tests."
                    )
                    tester_conv.run()

                # Run pytest directly in workspace
                test_run = execute_terminal_action(
                    WorkspaceTerminalAction(command="pytest -v", timeout_seconds=60),
                    base_dir=self.workspace_path,
                )
                dur_test = time.perf_counter() - t_test
                u_test = get_llm_usage(tester_agent.llm)

                if test_run.exit_code == 0:
                    tests_passed = True
                    recorder.record_step(
                        "tester", "pytest_verification", iteration, dur_test, True,
                        prompt_tokens=u_test["prompt_tokens"],
                        completion_tokens=u_test["completion_tokens"],
                        total_tokens=u_test["total_tokens"],
                        estimated_cost_usd=u_test["estimated_cost_usd"],
                    )
                    log_store.add_step(f"All pytest tests passed in iteration {iteration}.", is_error=False, observation=test_run.stdout)
                    ConsoleOutput.success(f"All tests passed in iteration {iteration}!")
                    break
                else:
                    error_output = f"{test_run.stdout}\n{test_run.stderr}".strip()
                    recorder.record_step(
                        "tester", "pytest_verification", iteration, dur_test, False,
                        error_summary=error_output[:500],
                        prompt_tokens=u_test["prompt_tokens"],
                        completion_tokens=u_test["completion_tokens"],
                        total_tokens=u_test["total_tokens"],
                        estimated_cost_usd=u_test["estimated_cost_usd"],
                    )
                    recorder.record_incident(f"Iteration_{iteration}_Pytest", "test_failure", error_output[:300])
                    log_store.add_step(f"Tests failed in iteration {iteration} (Exit code {test_run.exit_code})", is_error=True, observation=error_output[:600])

                    # Check Circuit Breaker before proceeding to fix
                    curr_diff = self.git.get_diff() or self.git.get_status()
                    if recorder.check_circuit_breaker(curr_diff, error_output):
                        ConsoleOutput.error("Circuit Breaker Tripped! Runaway loop detected with identical failure. Halting to save budget.")
                        break

                    if recorder.check_budget(_get_total_cost()):
                        ConsoleOutput.error("Budget ceiling reached during test iterations. Halting.")
                        break

                    if iteration == self.config.max_iterations:
                        ConsoleOutput.error("Max iterations reached without achieving all passing tests.")
                        break

                    ConsoleOutput.warning(f"Tests failed in iteration {iteration}. Initiating Developer fix (reusing conversation context).")

                    # Step 3: Developer receives test output and fixes (REUSING dev_conv to preserve context)
                    t_fix = time.perf_counter()
                    log_store.set_agent_context("Developer", f"Fix Iteration {iteration}", model=developer_agent.llm.model, llm=developer_agent.llm)
                    ConsoleOutput.agent_step("Developer", f"Fixing failures (Iteration {iteration})...", model=developer_agent.llm.model)
                    compact_failure = PytestOutputParser.extract_compact_failures(test_run.stdout, test_run.stderr)
                    failure_summary = (
                        f"Pytest execution failed with exit code {test_run.exit_code}.\n\n"
                        f"{compact_failure}\n\n"
                        "Please diagnose the failure using the systematic-debugging skill and update the code."
                    )
                    dev_conv.send_message(self.human_channel.inject_into_prompt(failure_summary))
                    dev_conv.run()
                    dur_fix = time.perf_counter() - t_fix
                    new_diff = self.git.get_diff() or self.git.get_status()
                    u_dev_fix = get_llm_usage(developer_agent.llm)
                    recorder.record_step(
                        "developer", "fix_code", iteration, dur_fix, True, new_diff,
                        prompt_tokens=u_dev_fix["prompt_tokens"],
                        completion_tokens=u_dev_fix["completion_tokens"],
                        total_tokens=u_dev_fix["total_tokens"],
                        estimated_cost_usd=u_dev_fix["estimated_cost_usd"],
                    )

                    if recorder.check_budget(_get_total_cost()):
                        ConsoleOutput.error("Budget ceiling reached after developer fix. Halting.")
                        break

                iteration += 1


            # Finalize telemetry report
            diag_report = recorder.finalize(completed_successfully=tests_passed)
            ConsoleOutput.success(f"Telemetry report logged: {diag_report.report_id}")

            # Step 4: Commit on success
            commit_hash = ""
            if tests_passed and self.config.auto_commit:
                can_commit = True
                if "before_commit" in self.config.approval_gates:
                    gate_decision = self.human_channel.prompt_gate("before_commit", context_preview="All tests passed. Confirm Git commit.")
                    if gate_decision == "rejected":
                        ConsoleOutput.warning("Git commit cancelled by human operator.")
                        can_commit = False

                if can_commit:
                    commit_msg = f"feat: {task_description[:50]} (verified by multi-agent tests)"
                    commit_res = self.git.commit(commit_msg)
                    if commit_res:
                        commit_hash = commit_res
                        ConsoleOutput.success(f"Created Git commit: {commit_hash[:8]}")

            status_str = "SUCCESS" if tests_passed else ("CIRCUIT_BREAKER_ABORT" if recorder.circuit_breaker_triggered else "FAILED")
            ConsoleOutput.summary_table(iteration, status_str, commit_hash)

            # Persist execution memory for cross-run learning
            try:
                memory_store.save_run_memory(
                    task=task_description,
                    summary=f"Dev-Test loop concluded with {status_str} in {iteration} iteration(s).",
                    tests_passed=tests_passed,
                    lessons=recorder.recommendations[0] if recorder.recommendations else None,
                )
            except Exception:
                pass

            if tests_passed:
                PipelineCheckpointManager.clear(self.workspace_path)

            InteractiveLogExplorer(log_store).run()

            return {
                "status": status_str,
                "iterations": iteration,
                "tests_passed": tests_passed,
                "circuit_breaker": recorder.circuit_breaker_triggered,
                "commit_hash": commit_hash,
                "report_id": diag_report.report_id,
                "workspace": str(self.workspace_path)
            }
        except KeyboardInterrupt:
            ConsoleOutput.warning("Pipeline execution interrupted by user.")
            log_store.add_step("Session interrupted by user (KeyboardInterrupt).", is_error=True)
            recorder.record_incident("Pipeline", "user_interruption", "Session interrupted by user (KeyboardInterrupt).")
            diag_report = recorder.finalize(completed_successfully=False)
            ConsoleOutput.warning(f"Partial telemetry saved: {diag_report.report_id}")
            raise
        except Exception as e:
            ConsoleOutput.error(f"Pipeline crashed: {e}")
            recorder.record_incident("Pipeline", "unhandled_exception", str(e))
            recorder.finalize(completed_successfully=False)
            raise
        finally:
            log_store.save_to_file()

