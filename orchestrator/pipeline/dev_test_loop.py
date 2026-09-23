"""Developer -> Tester loop with Circuit Breaker and Telemetry logging."""

import time
from pathlib import Path
from typing import Any, Dict, Optional

from openhands.sdk import Conversation

from orchestrator.agents import create_developer_agent, create_tester_agent
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.control import PipelineController
from orchestrator.pipeline.base_pipeline import BasePipeline, PipelinePhase
from orchestrator.pipeline.checkpoint import PipelineCheckpoint, PipelineCheckpointManager
from orchestrator.telemetry import get_llm_usage
from orchestrator.tools import WorkspaceTerminalAction, execute_terminal_action
from orchestrator.utils import ConsoleOutput, PytestOutputParser


class DevTestLoop(BasePipeline):
    """Manages the iteration loop between Developer and Tester agents with cost protection."""

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
        human_channel: Optional[Any] = None,
        controller: Optional[PipelineController] = None,
        checkpoint: Optional[PipelineCheckpoint] = None,
    ):
        super().__init__(
            config=config,
            skill_manager=skill_manager,
            workspace_path=workspace_path,
            checkpoint=checkpoint,
            controller=controller,
            human_channel=human_channel,
        )

    def _execute_pytest(self, timeout_seconds: int = 60):
        """Execute pytest using module-level execute_terminal_action for mock compatibility."""
        if (self.workspace_path / "pyproject.toml").exists():
            pytest_cmd = "pytest -v"
        elif (self.workspace_path / "tests").exists():
            pytest_cmd = "pytest tests/ -v"
        else:
            pytest_cmd = "pytest -v"

        return execute_terminal_action(
            WorkspaceTerminalAction(command=pytest_cmd, timeout_seconds=timeout_seconds),
            base_dir=self.workspace_path,
        )

    def run(self, task_description: str) -> Dict[str, Any]:
        """Execute the Dev-Test pipeline with circuit breaker protection."""
        recorder, memory_store, log_store, visualizer, graft_map = self._setup_run(
            task_description=task_description,
            mode="dev-test",
            banner_title="Starting Developer-Tester Pipeline",
        )

        developer_agent = create_developer_agent(self.config, self.skill_manager, self.workspace_path)
        tester_agent = create_tester_agent(self.config, self.skill_manager, self.workspace_path)

        def _get_total_cost() -> float:
            return get_llm_usage(developer_agent.llm)["estimated_cost_usd"] + get_llm_usage(tester_agent.llm)["estimated_cost_usd"]

        try:
            if not self.controller.check_should_continue():
                ConsoleOutput.warning("Execution stopped by controller before developer phase.")
                diag_report = recorder.finalize(completed_successfully=False)
                return {"status": "STOPPED", "report_id": diag_report.report_id}

            self.state_machine.transition_to(PipelinePhase.DEVELOP)

            # Step 1: Initial Implementation by Developer
            dev_conv = Conversation(agent=developer_agent, workspace=str(self.workspace_path), visualizer=visualizer)

            if self.checkpoint and "developer" in self.checkpoint.completed_phases:
                ConsoleOutput.success("Developer phase already completed in checkpoint. Skipping initial implementation.")
                log_store.add_step("Skipped developer initial implementation (loaded from checkpoint).")
            else:
                t0 = time.perf_counter()
                log_store.set_agent_context("Developer", "Initial Implementation", model=developer_agent.llm.model, llm=developer_agent.llm)
                ConsoleOutput.agent_step("Developer", "Implementing solution based on skills...", details=f"Task: {task_description}", model=developer_agent.llm.model)

                graft_part = f"\n\n[Codebase Architecture Map (Graft)]:\n{graft_map}" if graft_map else ""
                memory_part = ""
                if self.config.enable_memory:
                    memory_ctx = memory_store.format_memory_context(task_description)
                    if memory_ctx:
                        memory_part = f"\n\n{memory_ctx}"

                dev_prompt = (
                    f"Implement the following software task:\n\n{task_description}\n\n"
                    "Ensure full implementation, type safety, and adhere to clean-python-architecture."
                    f"{graft_part}"
                    f"{memory_part}"
                )
                dev_conv.send_message(self.human_channel.inject_into_prompt(dev_prompt))
                self._run_conv(dev_conv, "Developer")
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
                if not self.controller.check_should_continue():
                    ConsoleOutput.warning(f"Execution stopped by controller before test iteration {iteration}.")
                    break

                log_store.set_agent_context("Tester", f"Test Iteration {iteration}", model=tester_agent.llm.model, llm=tester_agent.llm)

                # Preflight check
                self._run_preflight(iteration, dev_conv, developer_agent, recorder, log_store)

                if self.state_machine.can_transition(PipelinePhase.TEST):
                    self.state_machine.transition_to(PipelinePhase.TEST)

                # Test Execution (Zero-Token Skip on fix iterations > 1)
                t_test = time.perf_counter()
                if iteration == 1:
                    ConsoleOutput.agent_step("Tester", f"Generating & executing tests (Iteration {iteration})...", model=tester_agent.llm.model)
                    test_prompt = (
                        f"Target Task: {task_description}\n\n"
                        "Inspect the implemented code using workspace tools. Write comprehensive pytest unit tests "
                        "covering edge cases and execute them using your terminal tool (`pytest tests/ -v`)."
                    )
                    tester_conv.send_message(self.human_channel.inject_into_prompt(test_prompt))
                    self._run_conv(tester_conv, "Tester")
                    dur_test = time.perf_counter() - t_test
                    u_test = get_llm_usage(tester_agent.llm)
                    recorder.record_step(
                        "tester", "write_and_run_tests", iteration, dur_test, True,
                        prompt_tokens=u_test["prompt_tokens"],
                        completion_tokens=u_test["completion_tokens"],
                        total_tokens=u_test["total_tokens"],
                        estimated_cost_usd=u_test["estimated_cost_usd"],
                    )
                else:
                    ConsoleOutput.info(f"Iteration {iteration}: Re-verifying fix directly via pytest (Zero-Token Tester Skip).")

                # Verify test results
                test_run = self._execute_pytest()

                if test_run.exit_code == 0:
                    tests_passed = True
                    ConsoleOutput.success(f"All tests passed in iteration {iteration}!")
                    break

                # Tests failed - analyze & route to Developer
                if self.state_machine.can_transition(PipelinePhase.FIX):
                    self.state_machine.transition_to(PipelinePhase.FIX)

                log_store.add_step(f"Tests failed in iteration {iteration}", is_error=True, observation=test_run.stdout)
                compact_failure = PytestOutputParser.extract_compact_failures(test_run.stdout, test_run.stderr)
                circuit_broken = recorder.check_circuit_breaker(compact_failure)
                recorder.record_incident(f"Iteration_{iteration}_Pytest", "test_failure", compact_failure)

                if circuit_broken:
                    ConsoleOutput.error("Circuit Breaker Tripped! Detected repeated failures without progress. Aborting loop.")
                    break

                if iteration < self.config.max_iterations:
                    ConsoleOutput.warning(f"Tests failed (Iteration {iteration}). Developer fixing...")
                    log_store.set_agent_context("Developer", f"Fix Iteration {iteration}", model=developer_agent.llm.model, llm=developer_agent.llm)
                    t_fix = time.perf_counter()
                    failure_summary = (
                        f"Pytest execution failed with exit code {test_run.exit_code}.\n\n"
                        f"{compact_failure}\n\n"
                        "Please diagnose the failure using the systematic-debugging skill and update the code."
                    )
                    dev_conv.send_message(self.human_channel.inject_into_prompt(failure_summary))
                    self._run_conv(dev_conv, "Developer")
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

            status_override = None
            if not tests_passed and recorder.circuit_breaker_triggered:
                status_override = "CIRCUIT_BREAKER_ABORT"

            return self._finalize_pipeline(
                task_description=task_description,
                success=tests_passed,
                iteration=iteration,
                recorder=recorder,
                memory_store=memory_store,
                log_store=log_store,
                commit_msg_prefix="feat",
                status_override=status_override,
            )

        except Exception as e:
            ConsoleOutput.error(f"Pipeline crashed: {e}")
            log_store.add_step(f"Fatal pipeline crash: {str(e)}", is_error=True)
            log_store.save_to_file()
            return {"status": "CRASHED", "error": str(e)}
