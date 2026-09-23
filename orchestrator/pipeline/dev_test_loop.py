"""Developer -> Tester loop with automatic failure feedback and Git integration."""

from pathlib import Path
from typing import Optional

from openhands.sdk import Conversation
from orchestrator.agents import create_developer_agent, create_tester_agent
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.tools import (
    WorkspaceTerminalAction,
    execute_terminal_action,
)
from orchestrator.utils import ConsoleOutput, GitOps


class DevTestLoop:
    """Manages the iteration loop between Developer and Tester agents."""

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
        """Execute the Dev-Test pipeline for the provided task."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.git.init_repo()

        ConsoleOutput.banner(
            "Starting Developer-Tester Pipeline",
            f"Workspace: {self.workspace_path}"
        )
        ConsoleOutput.agent_step("System", f"Loaded Skills: {', '.join(self.skill_manager.available_skills)}")

        developer_agent = create_developer_agent(self.config, self.skill_manager, self.workspace_path)
        tester_agent = create_tester_agent(self.config, self.skill_manager, self.workspace_path)

        # Step 1: Initial Implementation by Developer
        ConsoleOutput.agent_step("Developer", "Implementing solution based on skills...", task_description)
        dev_conv = Conversation(agent=developer_agent, workspace=str(self.workspace_path))
        dev_conv.send_message(
            f"Implement the following software task:\n\n{task_description}\n\n"
            "Ensure full implementation, type safety, and adhere to clean-python-architecture."
        )
        dev_conv.run()
        ConsoleOutput.success("Developer completed implementation phase.")

        # Step 2: Iterative Test & Fix Loop
        iteration = 1
        tests_passed = False

        while iteration <= self.config.max_iterations:
            ConsoleOutput.agent_step("Tester", f"Running test verification (Iteration {iteration}/{self.config.max_iterations})...")
            
            # Tester creates/updates tests
            tester_conv = Conversation(agent=tester_agent, workspace=str(self.workspace_path))
            tester_conv.send_message(
                f"Task: {task_description}\n\n"
                "Write comprehensive pytest tests in tests/ directory and run pytest. "
                "Ensure edge cases and boundary conditions are covered as per pytest-rigorous-testing."
            )
            tester_conv.run()

            # Execute pytest directly in workspace to verify result
            test_run = execute_terminal_action(
                WorkspaceTerminalAction(command="pytest -v", timeout_seconds=60),
                base_dir=self.workspace_path,
            )

            if test_run.exit_code == 0:
                tests_passed = True
                ConsoleOutput.success(f"All tests passed in iteration {iteration}!")
                break
            else:
                ConsoleOutput.warning(f"Tests failed in iteration {iteration}. Initiating Developer fix.")
                if iteration == self.config.max_iterations:
                    ConsoleOutput.error("Max iterations reached without achieving all passing tests.")
                    break

                # Step 3: Developer receives test output and fixes
                dev_fix_conv = Conversation(agent=developer_agent, workspace=str(self.workspace_path))
                failure_summary = (
                    f"Pytest execution failed with exit code {test_run.exit_code}.\n"
                    f"STDOUT:\n{test_run.stdout}\n"
                    f"STDERR:\n{test_run.stderr}\n\n"
                    "Please diagnose the failure using the systematic-debugging skill and update the code."
                )
                dev_fix_conv.send_message(failure_summary)
                dev_fix_conv.run()

            iteration += 1

        # Step 4: Commit on success
        commit_hash = ""
        if tests_passed and self.config.auto_commit:
            commit_msg = f"feat: {task_description[:50]} (verified by multi-agent tests)"
            commit_res = self.git.commit(commit_msg)
            if commit_res:
                commit_hash = commit_res
                ConsoleOutput.success(f"Created Git commit: {commit_hash[:8]}")

        status_str = "SUCCESS" if tests_passed else "FAILED"
        ConsoleOutput.summary_table(iteration, status_str, commit_hash)

        return {
            "status": status_str,
            "iterations": iteration,
            "tests_passed": tests_passed,
            "commit_hash": commit_hash,
            "workspace": str(self.workspace_path)
        }
