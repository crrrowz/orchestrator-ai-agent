"""Full Multi-Agent Pipeline: Architect -> Developer -> Tester -> Reviewer."""

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
from orchestrator.tools import (
    WorkspaceTerminalAction,
    execute_terminal_action,
)
from orchestrator.utils import ConsoleOutput, GitOps


class FullPipeline:
    """End-to-end 4-role multi-agent pipeline with independent review."""

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

        ConsoleOutput.banner(
            "Starting Full 4-Agent Pipeline",
            f"Workspace: {self.workspace_path}"
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
        ConsoleOutput.agent_step("Architect", "Designing modular blueprint and PLAN.md...")
        arch_conv = Conversation(agent=architect_agent, workspace=str(self.workspace_path))
        arch_conv.send_message(
            f"User Task:\n{task_description}\n\n"
            "Decompose this task according to architectural-decomposition skill. "
            "Write the complete specification into PLAN.md in the workspace root."
        )
        arch_conv.run()
        ConsoleOutput.success("Architect generated PLAN.md.")

        # -------------------------------------------------------------------
        # Phase 2: Implementation & Rigorous Testing Loop
        # -------------------------------------------------------------------
        ConsoleOutput.agent_step("Developer", "Implementing specification from PLAN.md...")
        dev_conv = Conversation(agent=developer_agent, workspace=str(self.workspace_path))
        dev_conv.send_message(
            f"Task: {task_description}\n\n"
            "Read PLAN.md and implement the complete solution adhering to clean-python-architecture."
        )
        dev_conv.run()
        ConsoleOutput.success("Developer completed initial code.")

        iteration = 1
        tests_passed = False

        while iteration <= self.config.max_iterations:
            ConsoleOutput.agent_step("Tester", f"Verifying test suite (Iteration {iteration}/{self.config.max_iterations})...")
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

            if test_run.exit_code == 0:
                tests_passed = True
                ConsoleOutput.success(f"All tests passed in iteration {iteration}!")
                break
            else:
                ConsoleOutput.warning(f"Tests failed in iteration {iteration}. Requesting fix.")
                if iteration == self.config.max_iterations:
                    ConsoleOutput.error("Max test iterations reached.")
                    break

                dev_fix = Conversation(agent=developer_agent, workspace=str(self.workspace_path))
                dev_fix.send_message(
                    f"Pytest output:\n{test_run.stdout}\n{test_run.stderr}\n"
                    "Fix issues following systematic-debugging protocol."
                )
                dev_fix.run()

            iteration += 1

        if not tests_passed:
            ConsoleOutput.error("Pipeline aborted: Tests failed.")
            return {"status": "FAILED_TESTS", "iterations": iteration}

        # -------------------------------------------------------------------
        # Phase 3: Independent Review
        # -------------------------------------------------------------------
        ConsoleOutput.agent_step("Reviewer", f"Auditing code with model '{self.config.reviewer.model}'...")
        git_diff = self.git.get_diff() or self.git.get_status()
        reviewer_conv = Conversation(agent=reviewer_agent, workspace=str(self.workspace_path))
        reviewer_conv.send_message(
            f"Task: {task_description}\n\n"
            f"Git Changes:\n{git_diff}\n\n"
            "Perform an independent review according to code-review-standards. "
            "Inspect workspace files and conclude with VERDICT: APPROVED or VERDICT: REJECTED."
        )
        reviewer_conv.run()

        # Check last message from reviewer
        review_approved = True
        if reviewer_conv.state and reviewer_conv.state.events:
            for ev in reversed(reviewer_conv.state.events):
                text = str(getattr(ev, "content", "") or getattr(ev, "text", ""))
                if "VERDICT: REJECTED" in text:
                    review_approved = False
                    ConsoleOutput.warning("Reviewer rejected current code.")
                    break
                elif "VERDICT: APPROVED" in text:
                    review_approved = True
                    ConsoleOutput.success("Reviewer approved code.")
                    break

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
            "workspace": str(self.workspace_path)
        }
