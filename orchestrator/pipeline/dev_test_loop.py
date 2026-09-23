"""Developer -> Tester loop with Circuit Breaker and Telemetry logging."""

import time
from pathlib import Path
from typing import Optional

from openhands.sdk import Conversation
from orchestrator.agents import create_developer_agent, create_tester_agent
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.telemetry import TelemetryRecorder
from orchestrator.tools import (
    WorkspaceTerminalAction,
    execute_terminal_action,
)
from orchestrator.utils import ConsoleOutput, GitOps


class DevTestLoop:
    """Manages the iteration loop between Developer and Tester agents with cost protection."""

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
    ):
        self.config = config
        self.skill_manager = skill_manager
        self.workspace_path = (workspace_path or config.workspace_path).resolve()
        self.git = GitOps(self.workspace_path)

    def run(self, task_description: str) -> dict:
        """Execute the Dev-Test pipeline with circuit breaker protection."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.git.init_repo()

        recorder = TelemetryRecorder(
            task_description=task_description,
            pipeline_mode="dev-test",
            circuit_breaker_threshold=self.config.circuit_breaker_threshold,
        )

        ConsoleOutput.banner(
            "Starting Developer-Tester Pipeline",
            f"Workspace: {self.workspace_path} | Max Iterations: {self.config.max_iterations}"
        )
        ConsoleOutput.agent_step("System", f"Loaded Skills: {', '.join(self.skill_manager.available_skills)}")

        developer_agent = create_developer_agent(self.config, self.skill_manager, self.workspace_path)
        tester_agent = create_tester_agent(self.config, self.skill_manager, self.workspace_path)

        # Step 1: Initial Implementation by Developer
        t0 = time.perf_counter()
        ConsoleOutput.agent_step("Developer", "Implementing solution based on skills...", task_description)
        dev_conv = Conversation(agent=developer_agent, workspace=str(self.workspace_path))
        dev_conv.send_message(
            f"Implement the following software task:\n\n{task_description}\n\n"
            "Ensure full implementation, type safety, and adhere to clean-python-architecture."
        )
        dev_conv.run()
        duration_dev = time.perf_counter() - t0
        curr_diff = self.git.get_diff() or self.git.get_status()
        recorder.record_step("developer", "initial_implementation", 1, duration_dev, True, curr_diff)
        ConsoleOutput.success("Developer completed implementation phase.")

        # Step 2: Iterative Test & Fix Loop
        iteration = 1
        tests_passed = False

        while iteration <= self.config.max_iterations:
            ConsoleOutput.agent_step("Tester", f"Running test verification (Iteration {iteration}/{self.config.max_iterations})...")
            
            t_test = time.perf_counter()
            tester_conv = Conversation(agent=tester_agent, workspace=str(self.workspace_path))
            tester_conv.send_message(
                f"Task: {task_description}\n\n"
                "Write comprehensive pytest tests in tests/ directory and run pytest. "
                "Ensure edge cases and boundary conditions are covered as per pytest-rigorous-testing."
            )
            tester_conv.run()

            # Run pytest directly in workspace
            test_run = execute_terminal_action(
                WorkspaceTerminalAction(command="pytest -v", timeout_seconds=60),
                base_dir=self.workspace_path,
            )
            dur_test = time.perf_counter() - t_test

            if test_run.exit_code == 0:
                tests_passed = True
                recorder.record_step("tester", "pytest_verification", iteration, dur_test, True)
                ConsoleOutput.success(f"All tests passed in iteration {iteration}!")
                break
            else:
                error_output = f"{test_run.stdout}\n{test_run.stderr}".strip()
                recorder.record_step("tester", "pytest_verification", iteration, dur_test, False, error_summary=error_output[:500])
                recorder.record_incident(f"Iteration_{iteration}_Pytest", "test_failure", error_output[:300])

                # Check Circuit Breaker before proceeding to fix
                curr_diff = self.git.get_diff() or self.git.get_status()
                if recorder.check_circuit_breaker(curr_diff, error_output):
                    ConsoleOutput.error("Circuit Breaker Tripped! Runaway loop detected with identical failure. Halting to save budget.")
                    break

                if iteration == self.config.max_iterations:
                    ConsoleOutput.error("Max iterations reached without achieving all passing tests.")
                    break

                ConsoleOutput.warning(f"Tests failed in iteration {iteration}. Initiating Developer fix.")

                # Step 3: Developer receives test output and fixes
                t_fix = time.perf_counter()
                dev_fix_conv = Conversation(agent=developer_agent, workspace=str(self.workspace_path))
                failure_summary = (
                    f"Pytest execution failed with exit code {test_run.exit_code}.\n"
                    f"STDOUT:\n{test_run.stdout}\n"
                    f"STDERR:\n{test_run.stderr}\n\n"
                    "Please diagnose the failure using the systematic-debugging skill and update the code."
                )
                dev_fix_conv.send_message(failure_summary)
                dev_fix_conv.run()
                dur_fix = time.perf_counter() - t_fix
                new_diff = self.git.get_diff() or self.git.get_status()
                recorder.record_step("developer", "fix_code", iteration, dur_fix, True, new_diff)

            iteration += 1

        # Finalize telemetry report
        diag_report = recorder.finalize(completed_successfully=tests_passed)
        ConsoleOutput.success(f"Telemetry report logged: {diag_report.report_id}")

        # Step 4: Commit on success
        commit_hash = ""
        if tests_passed and self.config.auto_commit:
            commit_msg = f"feat: {task_description[:50]} (verified by multi-agent tests)"
            commit_res = self.git.commit(commit_msg)
            if commit_res:
                commit_hash = commit_res
                ConsoleOutput.success(f"Created Git commit: {commit_hash[:8]}")

        status_str = "SUCCESS" if tests_passed else ("CIRCUIT_BREAKER_ABORT" if recorder.circuit_breaker_triggered else "FAILED")
        ConsoleOutput.summary_table(iteration, status_str, commit_hash)

        return {
            "status": status_str,
            "iterations": iteration,
            "tests_passed": tests_passed,
            "circuit_breaker": recorder.circuit_breaker_triggered,
            "commit_hash": commit_hash,
            "report_id": diag_report.report_id,
            "workspace": str(self.workspace_path)
        }
