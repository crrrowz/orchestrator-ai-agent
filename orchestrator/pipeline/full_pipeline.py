"""Full Multi-Agent Pipeline: Architect -> Developer -> Tester -> Reviewer with Telemetry."""

import time
from pathlib import Path
from typing import Optional

from openhands.sdk import Conversation
from orchestrator.agents import (
    create_architect_agent,
    create_developer_agent,
    create_reviewer_agent,
    create_tester_agent,
)
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.telemetry import TelemetryRecorder
from orchestrator.tools import (
    WorkspaceTerminalAction,
    execute_terminal_action,
)
from orchestrator.utils import ConsoleOutput, GitOps


class FullPipeline:
    """End-to-end 4-role multi-agent pipeline with circuit breaker and independent review."""

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
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.git.init_repo()

        recorder = TelemetryRecorder(
            task_description=task_description,
            pipeline_mode="full",
            circuit_breaker_threshold=self.config.circuit_breaker_threshold,
        )

        ConsoleOutput.banner(
            "Starting Full 4-Agent Pipeline",
            f"Workspace: {self.workspace_path} | Max Iterations: {self.config.max_iterations}"
        )
        ConsoleOutput.agent_step("System", f"Loaded Skills: {', '.join(self.skill_manager.available_skills)}")

        # Agents
        architect_agent = create_architect_agent(self.config, self.skill_manager, self.workspace_path)
        developer_agent = create_developer_agent(self.config, self.skill_manager, self.workspace_path)
        tester_agent = create_tester_agent(self.config, self.skill_manager, self.workspace_path)
        reviewer_agent = create_reviewer_agent(self.config, self.skill_manager, self.workspace_path)

        # -------------------------------------------------------------------
        # Phase 1: Architectural Decomposition
        # -------------------------------------------------------------------
        t0 = time.perf_counter()
        ConsoleOutput.agent_step("Architect", "Designing modular blueprint and PLAN.md...")
        arch_conv = Conversation(agent=architect_agent, workspace=str(self.workspace_path))
        arch_conv.send_message(
            f"User Task:\n{task_description}\n\n"
            "Decompose this task according to architectural-decomposition skill. "
            "Write the complete specification into PLAN.md in the workspace root."
        )
        arch_conv.run()
        dur_arch = time.perf_counter() - t0
        recorder.record_step("architect", "plan_generation", 1, dur_arch, True)
        ConsoleOutput.success("Architect generated PLAN.md.")

        # -------------------------------------------------------------------
        # Phase 2: Implementation & Rigorous Testing Loop
        # -------------------------------------------------------------------
        t_dev = time.perf_counter()
        ConsoleOutput.agent_step("Developer", "Implementing specification from PLAN.md...")
        dev_conv = Conversation(agent=developer_agent, workspace=str(self.workspace_path))
        dev_conv.send_message(
            f"Task: {task_description}\n\n"
            "Read PLAN.md and implement the complete solution adhering to clean-python-architecture."
        )
        dev_conv.run()
        dur_dev = time.perf_counter() - t_dev
        curr_diff = self.git.get_diff() or self.git.get_status()
        recorder.record_step("developer", "initial_implementation", 1, dur_dev, True, curr_diff)
        ConsoleOutput.success("Developer completed initial code.")

        iteration = 1
        tests_passed = False

        while iteration <= self.config.max_iterations:
            ConsoleOutput.agent_step("Tester", f"Verifying test suite (Iteration {iteration}/{self.config.max_iterations})...")
            t_test = time.perf_counter()
            tester_conv = Conversation(agent=tester_agent, workspace=str(self.workspace_path))
            tester_conv.send_message(
                f"Task: {task_description}\n\n"
                "Read PLAN.md and source files. Write and execute complete pytest tests as per pytest-rigorous-testing."
            )
            tester_conv.run()

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

                curr_diff = self.git.get_diff() or self.git.get_status()
                if recorder.check_circuit_breaker(curr_diff, error_output):
                    ConsoleOutput.error("Circuit Breaker Tripped! Runaway loop detected with identical failure. Halting.")
                    break

                if iteration == self.config.max_iterations:
                    ConsoleOutput.error("Max test iterations reached.")
                    break

                ConsoleOutput.warning(f"Tests failed in iteration {iteration}. Requesting fix.")
                t_fix = time.perf_counter()
                dev_fix = Conversation(agent=developer_agent, workspace=str(self.workspace_path))
                dev_fix.send_message(
                    f"Pytest output:\n{test_run.stdout}\n{test_run.stderr}\n"
                    "Fix issues following systematic-debugging protocol."
                )
                dev_fix.run()
                dur_fix = time.perf_counter() - t_fix
                new_diff = self.git.get_diff() or self.git.get_status()
                recorder.record_step("developer", "fix_code", iteration, dur_fix, True, new_diff)

            iteration += 1

        if not tests_passed:
            diag_report = recorder.finalize(completed_successfully=False)
            ConsoleOutput.error("Pipeline aborted: Tests failed.")
            return {"status": "FAILED_TESTS", "iterations": iteration, "report_id": diag_report.report_id}

        # -------------------------------------------------------------------
        # Phase 3: Independent Review
        # -------------------------------------------------------------------
        t_rev = time.perf_counter()
        ConsoleOutput.agent_step("Reviewer", f"Auditing code with independent model '{self.config.reviewer.model}'...")
        git_diff = self.git.get_diff() or self.git.get_status()
        reviewer_conv = Conversation(agent=reviewer_agent, workspace=str(self.workspace_path))
        reviewer_conv.send_message(
            f"Task: {task_description}\n\n"
            f"Git Changes:\n{git_diff}\n\n"
            "Perform an independent review according to code-review-standards and security-audit-hardening. "
            "Inspect workspace files and conclude with VERDICT: APPROVED or VERDICT: REJECTED."
        )
        reviewer_conv.run()
        dur_rev = time.perf_counter() - t_rev

        review_approved = True
        if reviewer_conv.state and reviewer_conv.state.events:
            for ev in reversed(reviewer_conv.state.events):
                text = str(getattr(ev, "content", "") or getattr(ev, "text", ""))
                if "VERDICT: REJECTED" in text:
                    review_approved = False
                    recorder.record_step("reviewer", "code_audit", iteration, dur_rev, False, error_summary="Reviewer rejected code")
                    ConsoleOutput.warning("Reviewer rejected current code.")
                    break
                elif "VERDICT: APPROVED" in text:
                    review_approved = True
                    recorder.record_step("reviewer", "code_audit", iteration, dur_rev, True)
                    ConsoleOutput.success("Reviewer approved code.")
                    break

        diag_report = recorder.finalize(completed_successfully=review_approved)
        ConsoleOutput.success(f"Telemetry report logged: {diag_report.report_id}")

        # -------------------------------------------------------------------
        # Phase 4: Commit on Success
        # -------------------------------------------------------------------
        commit_hash = ""
        if review_approved and self.config.auto_commit:
            commit_msg = f"feat: {task_description[:50]} (Architect -> Dev -> Test -> Review)"
            commit_res = self.git.commit(commit_msg)
            if commit_res:
                commit_hash = commit_res
                ConsoleOutput.success(f"Created Git commit: {commit_hash[:8]}")

        status_str = "SUCCESS" if review_approved else "REVIEW_REJECTED"
        ConsoleOutput.summary_table(iteration, status_str, commit_hash)

        return {
            "status": status_str,
            "iterations": iteration,
            "tests_passed": tests_passed,
            "review_approved": review_approved,
            "commit_hash": commit_hash,
            "report_id": diag_report.report_id,
            "workspace": str(self.workspace_path)
        }
