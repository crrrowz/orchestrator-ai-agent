"""Full 4-Agent Pipeline: Architect -> Developer (Milestone DAG) -> Tester -> Reviewer."""

import time
from pathlib import Path
from typing import Any, Dict, Optional

from openhands.sdk import Conversation

from orchestrator.agents import (
    create_architect_agent,
    create_developer_agent,
    create_reviewer_agent,
    create_tester_agent,
)
from orchestrator.analysis.pytest_parser import TestExecutionStatus
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.control import PipelineController
from orchestrator.pipeline.base_pipeline import BasePipeline
from orchestrator.pipeline.checkpoint import (
    PipelineCheckpoint,
    PipelineCheckpointManager,
)
from orchestrator.pipeline.milestone_dag import MilestoneParser
from orchestrator.pipeline.reviewer_parser import ReviewerVerdict
from orchestrator.pipeline.state_machine import PipelinePhase
from orchestrator.utils import ConsoleOutput, PytestOutputParser
from orchestrator.telemetry import get_llm_usage


class FullPipeline(BasePipeline):
    """Full 4-Agent Software Development Pipeline coordinating Architect, Developer, Tester, and Reviewer."""

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

    def run(self, task_description: str) -> Dict[str, Any]:
        """Execute the complete 4-agent architectural pipeline."""
        recorder, memory_store, log_store, visualizer, graft_map = self._setup_run(
            task_description=task_description,
            mode="full",
            banner_title="Starting Full 4-Agent Software Engineering Pipeline",
        )

        architect_agent = create_architect_agent(
            self.config, self.skill_manager, self.workspace_path
        )
        developer_agent = create_developer_agent(
            self.config, self.skill_manager, self.workspace_path
        )
        tester_agent = create_tester_agent(
            self.config, self.skill_manager, self.workspace_path
        )
        reviewer_agent = create_reviewer_agent(
            self.config, self.skill_manager, self.workspace_path
        )

        def _get_total_cost() -> float:
            return (
                get_llm_usage(architect_agent.llm)["estimated_cost_usd"]
                + get_llm_usage(developer_agent.llm)["estimated_cost_usd"]
                + get_llm_usage(tester_agent.llm)["estimated_cost_usd"]
                + get_llm_usage(reviewer_agent.llm)["estimated_cost_usd"]
            )

        try:
            # -------------------------------------------------------------------
            # Phase 1: Architecture Blueprint (PLAN.md)
            # -------------------------------------------------------------------
            if not self.controller.check_should_continue():
                ConsoleOutput.warning(
                    "Execution stopped by controller before architect phase."
                )
                diag_report = recorder.finalize(completed_successfully=False)
                return {"status": "STOPPED", "report_id": diag_report.report_id}

            self.state_machine.transition_to(PipelinePhase.ARCHITECT)
            ConsoleOutput.pipeline_stage(
                "SYSTEM ARCHITECTURE BLUEPRINT",
                1,
                4,
                "Designing system design & PLAN.md",
            )

            if self.checkpoint and "architect" in self.checkpoint.completed_phases:
                ConsoleOutput.success(
                    "Architect phase already completed in checkpoint. Skipping..."
                )
                log_store.add_step("Skipped architect phase (loaded from checkpoint).")
            else:
                t0 = time.perf_counter()
                log_store.set_agent_context(
                    "Architect",
                    "System Architecture Blueprint",
                    model=architect_agent.llm.model,
                    llm=architect_agent.llm,
                )
                ConsoleOutput.agent_step(
                    "Architect",
                    "Designing system blueprint and PLAN.md...",
                    model=architect_agent.llm.model,
                )

                architect_conv = Conversation(
                    agent=architect_agent,
                    workspace=str(self.workspace_path),
                    visualizer=visualizer,
                )
                architect_prompt = self.build_prompt(
                    task=task_description,
                    role="architect",
                    extra_instructions=(
                        "Decompose this task into a clean technical design and write `PLAN.md` into the workspace using your file tool (workspace_file with operation='write', path='PLAN.md').\n"
                        "Structure your PLAN.md with clear milestones (e.g. '## Milestone 1: ...', '## Milestone 2: ...') so the Developer can execute them iteratively."
                    ),
                )
                architect_conv.send_message(
                    self.human_channel.inject_into_prompt(architect_prompt)
                )
                self._run_conv(architect_conv, "Architect")
                dur_arch = time.perf_counter() - t0
                u_arch = get_llm_usage(architect_agent.llm)
                recorder.record_step(
                    "architect",
                    "design_plan",
                    1,
                    dur_arch,
                    True,
                    prompt_tokens=u_arch["prompt_tokens"],
                    completion_tokens=u_arch["completion_tokens"],
                    total_tokens=u_arch["total_tokens"],
                    estimated_cost_usd=u_arch["estimated_cost_usd"],
                )

                # Auto-recover PLAN.md from architect conversation output if not written via tools
                plan_file = self.workspace_path / "PLAN.md"
                if (
                    not plan_file.exists()
                    or not plan_file.read_text(
                        encoding="utf-8", errors="replace"
                    ).strip()
                ) and architect_conv:
                    recovered_plan = ""
                    if (
                        hasattr(architect_conv, "state")
                        and architect_conv.state
                        and hasattr(architect_conv.state, "events")
                    ):
                        for ev in reversed(architect_conv.state.events):
                            text = str(
                                getattr(ev, "content", "")
                                or getattr(ev, "text", "")
                                or ""
                            ).strip()
                            if text and (
                                "#" in text
                                or "milestone" in text.lower()
                                or "architecture" in text.lower()
                                or len(text) > 80
                            ):
                                recovered_plan = text
                                break
                    if recovered_plan:
                        try:
                            plan_file.write_text(recovered_plan, encoding="utf-8")
                            ConsoleOutput.info(
                                "Auto-recovered PLAN.md from Architect response stream."
                            )
                        except Exception:
                            pass

                if (
                    plan_file.exists()
                    and plan_file.read_text(encoding="utf-8", errors="replace").strip()
                ):
                    ConsoleOutput.success(
                        f"Architect generated PLAN.md (Tokens: {u_arch['total_tokens']:,}, Cost: ${u_arch['estimated_cost_usd']:.4f})."
                    )
                else:
                    ConsoleOutput.info(
                        f"Architect completed design pass (Tokens: {u_arch['total_tokens']:,}, Cost: ${u_arch['estimated_cost_usd']:.4f})."
                    )

            if recorder.check_budget(_get_total_cost()):
                ConsoleOutput.error(
                    "Budget ceiling reached after architect phase. Halting."
                )
                diag_report = recorder.finalize(completed_successfully=False)
                log_store.save_to_file()
                return {
                    "status": "BUDGET_EXHAUSTED",
                    "iterations": 1,
                    "report_id": diag_report.report_id,
                }

            # Checkpoint save
            PipelineCheckpointManager.save(
                workspace=self.workspace_path,
                run_id=recorder.report_id,
                task=task_description,
                mode="full",
                current_phase="after_architect",
                completed_phases=["architect"],
            )

            # Approval Gate: after_architect
            if "after_architect" in self.config.approval_gates:
                plan_file = self.workspace_path / "PLAN.md"
                plan_preview = (
                    plan_file.read_text(encoding="utf-8", errors="replace")
                    if plan_file.exists()
                    else "No PLAN.md found."
                )
                gate_decision = self.human_channel.prompt_gate(
                    "after_architect", context_preview=plan_preview[:2000]
                )
                if gate_decision == "rejected":
                    if self.state_machine.can_transition(PipelinePhase.FAILED):
                        self.state_machine.transition_to(PipelinePhase.FAILED)
                    ConsoleOutput.error(
                        "Execution halted: human operator rejected PLAN.md at 'after_architect' gate."
                    )
                    log_store.add_step(
                        "PLAN.md rejected by human operator.", is_error=True
                    )
                    diag_report = recorder.finalize(completed_successfully=False)
                    log_store.save_to_file()
                    return {
                        "status": "HUMAN_REJECTED",
                        "phase": "architect",
                        "report_id": diag_report.report_id,
                    }

            # Milestone DAG Decomposition from PLAN.md
            plan_path = self.workspace_path / "PLAN.md"
            plan_content = (
                plan_path.read_text(encoding="utf-8", errors="replace")
                if plan_path.exists()
                else ""
            )
            if not plan_path.exists() or not plan_content.strip():
                ConsoleOutput.warning(
                    "PLAN.md not found or empty. Developer will implement from raw task description."
                )
                recorder.record_incident(
                    "PLAN.md", "missing_plan", "Architect did not produce PLAN.md"
                )
            milestones = MilestoneParser.parse_plan(plan_content)

            # -------------------------------------------------------------------
            # Phase 2: Implementation & Milestone DAG Execution
            # -------------------------------------------------------------------
            if not self.controller.check_should_continue():
                ConsoleOutput.warning(
                    "Execution stopped by controller before developer phase."
                )
                diag_report = recorder.finalize(completed_successfully=False)
                return {"status": "STOPPED", "report_id": diag_report.report_id}

            self.state_machine.transition_to(PipelinePhase.DEVELOP)
            ConsoleOutput.pipeline_stage(
                "DEVELOPER IMPLEMENTATION",
                2,
                4,
                "Executing milestone DAG implementation",
            )
            dev_conv = Conversation(
                agent=developer_agent,
                workspace=str(self.workspace_path),
                visualizer=visualizer,
            )

            if self.checkpoint and "developer" in self.checkpoint.completed_phases:
                ConsoleOutput.success(
                    "Developer phase already completed in checkpoint. Skipping initial implementation."
                )
                log_store.add_step(
                    "Skipped developer initial implementation (loaded from checkpoint)."
                )
            else:
                t_dev = time.perf_counter()
                log_store.set_agent_context(
                    "Developer",
                    "Implementation",
                    model=developer_agent.llm.model,
                    llm=developer_agent.llm,
                )

                if len(milestones) > 1:
                    ConsoleOutput.info(
                        f"Decomposed PLAN.md into {len(milestones)} structured milestones for developer implementation."
                    )
                    for ms in milestones:
                        if not self.controller.check_should_continue():
                            break
                        ConsoleOutput.agent_step(
                            "Developer",
                            f"Executing Milestone {ms.index}: {ms.title}...",
                            model=developer_agent.llm.model,
                        )
                        target_str = (
                            f"Target files: {', '.join(ms.target_files)}"
                            if ms.target_files
                            else ""
                        )
                        ms_prompt = (
                            f"Implement Milestone {ms.index}: {ms.title}\n\n"
                            f"{ms.content}\n\n"
                            f"{target_str}\n\n"
                            "Follow clean-python-architecture principles and implement required files."
                        )
                        dev_conv.send_message(
                            self.human_channel.inject_into_prompt(ms_prompt)
                        )
                        self._run_conv(dev_conv, f"Developer (Milestone {ms.index})")
                else:
                    ConsoleOutput.agent_step(
                        "Developer",
                        "Implementing specification from PLAN.md...",
                        model=developer_agent.llm.model,
                    )
                    dev_prompt = self.build_prompt(
                        task=task_description,
                        role="developer",
                        extra_instructions="Read PLAN.md and implement the complete solution adhering to clean-python-architecture.",
                    )
                    dev_conv.send_message(
                        self.human_channel.inject_into_prompt(dev_prompt)
                    )
                    self._run_conv(dev_conv, "Developer")

                dur_dev = time.perf_counter() - t_dev
                curr_diff = self.git.get_diff() or self.git.get_status()
                u_dev = get_llm_usage(developer_agent.llm)
                recorder.record_step(
                    "developer",
                    "initial_implementation",
                    1,
                    dur_dev,
                    True,
                    curr_diff,
                    prompt_tokens=u_dev["prompt_tokens"],
                    completion_tokens=u_dev["completion_tokens"],
                    total_tokens=u_dev["total_tokens"],
                    estimated_cost_usd=u_dev["estimated_cost_usd"],
                )
                ConsoleOutput.success(
                    f"Developer completed initial code (Tokens: {u_dev['total_tokens']:,}, Cost: ${u_dev['estimated_cost_usd']:.4f})."
                )

            if recorder.check_budget(_get_total_cost()):
                ConsoleOutput.error(
                    "Budget ceiling reached after initial developer phase. Halting."
                )
                diag_report = recorder.finalize(completed_successfully=False)
                log_store.save_to_file()
                return {
                    "status": "BUDGET_EXHAUSTED",
                    "iterations": 1,
                    "report_id": diag_report.report_id,
                }

            # Persist checkpoint after developer phase
            PipelineCheckpointManager.save(
                workspace=self.workspace_path,
                run_id=recorder.report_id,
                task=task_description,
                mode="full",
                current_phase="after_developer",
                completed_phases=["architect", "developer"],
            )

            # Approval Gate: after_developer
            if "after_developer" in self.config.approval_gates:
                diff_preview = curr_diff or self.git.get_diff() or self.git.get_status()
                gate_decision = self.human_channel.prompt_gate(
                    "after_developer", context_preview=diff_preview[:1500]
                )
                if gate_decision == "rejected":
                    ConsoleOutput.error(
                        "Execution halted: human operator rejected changes at 'after_developer' gate."
                    )
                    log_store.add_step(
                        "Changes rejected at after_developer approval gate.",
                        is_error=True,
                    )
                    diag_report = recorder.finalize(completed_successfully=False)
                    log_store.save_to_file()
                    return {
                        "status": "HUMAN_REJECTED",
                        "phase": "developer",
                        "report_id": diag_report.report_id,
                    }

            # -------------------------------------------------------------------
            # Phase 3: Iterative Test & Fix Loop
            # -------------------------------------------------------------------
            raw_max_iter = getattr(self.config, "max_iterations", "auto")
            if str(raw_max_iter).lower() == "auto":
                effective_max_iterations = (
                    max(min(len(milestones) * 2, 12), 4) if milestones else 4
                )
                ConsoleOutput.info(
                    f"Auto-iteration scaling engaged: dynamically allocated {effective_max_iterations} iteration(s)."
                )
            else:
                try:
                    effective_max_iterations = int(raw_max_iter)
                except (ValueError, TypeError):
                    effective_max_iterations = self.config.numeric_max_iterations

            iteration = 1
            tests_passed = False
            status_override: Optional[str] = None
            tester_conv = Conversation(
                agent=tester_agent,
                workspace=str(self.workspace_path),
                visualizer=visualizer,
            )

            while iteration <= effective_max_iterations:
                if not self.controller.check_should_continue():
                    ConsoleOutput.warning(
                        f"Execution stopped by controller before test iteration {iteration}."
                    )
                    break

                ConsoleOutput.pipeline_stage(
                    f"TEST SUITE VERIFICATION (Iteration {iteration}/{effective_max_iterations})",
                    3,
                    4,
                    "Automated pytest verification & edge cases",
                )

                log_store.set_agent_context(
                    "Tester",
                    f"Test Iteration {iteration}",
                    model=tester_agent.llm.model,
                    llm=tester_agent.llm,
                )

                # Preflight check
                self._run_preflight(
                    iteration, dev_conv, developer_agent, recorder, log_store
                )

                if self.state_machine.can_transition(PipelinePhase.TEST):
                    self.state_machine.transition_to(PipelinePhase.TEST)

                t_test = time.perf_counter()
                if iteration == 1:
                    ConsoleOutput.agent_step(
                        "Tester",
                        f"Generating & executing tests (Iteration {iteration})...",
                        model=tester_agent.llm.model,
                    )
                    test_prompt = (
                        f"Task: {task_description}\n\n"
                        "Inspect PLAN.md and implementation. Write comprehensive pytest unit tests and execute via `pytest tests/ -v`."
                    )
                    tester_conv.send_message(
                        self.human_channel.inject_into_prompt(test_prompt)
                    )
                    self._run_conv(tester_conv, "Tester")
                    dur_test = time.perf_counter() - t_test
                    u_test = get_llm_usage(tester_agent.llm)
                    recorder.record_step(
                        "tester",
                        "write_and_run_tests",
                        iteration,
                        dur_test,
                        True,
                        prompt_tokens=u_test["prompt_tokens"],
                        completion_tokens=u_test["completion_tokens"],
                        total_tokens=u_test["total_tokens"],
                        estimated_cost_usd=u_test["estimated_cost_usd"],
                    )
                else:
                    ConsoleOutput.info(
                        f"Iteration {iteration}: Re-verifying fix directly via pytest (Zero-Token Tester Skip)."
                    )

                # Verify test results
                test_run = self._execute_pytest()
                test_result = self.classify_test_run(test_run)

                if test_result.status == TestExecutionStatus.PASSED:
                    tests_passed = True
                    ConsoleOutput.success(f"All tests passed in iteration {iteration}!")
                    break

                if test_result.is_infra_or_env:
                    ConsoleOutput.error(
                        f"Test Infrastructure / Environment Failure ({test_result.status.value}): {test_result.summary}. "
                        "Halting loop to prevent wasteful code modifications."
                    )
                    recorder.record_incident(
                        f"Iteration_{iteration}_Pytest_Infra",
                        "test_infra_error",
                        test_result.failure_details or test_result.summary,
                    )
                    status_override = test_result.status.value
                    break

                # Tests failed - route to developer
                if self.state_machine.can_transition(PipelinePhase.FIX):
                    self.state_machine.transition_to(PipelinePhase.FIX)

                log_store.add_step(
                    f"Tests failed in iteration {iteration}",
                    is_error=True,
                    observation=test_run.stdout,
                )
                compact_failure = (
                    test_result.failure_details
                    or PytestOutputParser.extract_compact_failures(
                        test_run.stdout, test_run.stderr
                    )
                )
                curr_diff = self.git.get_diff() or self.git.get_status()
                circuit_broken = recorder.check_circuit_breaker(
                    curr_diff, compact_failure
                )
                recorder.record_incident(
                    f"Iteration_{iteration}_Pytest", "test_failure", compact_failure
                )

                if circuit_broken:
                    ConsoleOutput.error(
                        "Circuit Breaker Tripped! Detected repeated failures without progress. Aborting loop."
                    )
                    break

                if iteration < effective_max_iterations:
                    test_cmd = (
                        self.adapter.get_test_command(self.workspace_path)
                        or "pytest -v"
                    )
                    ConsoleOutput.test_failure_callout(test_cmd, compact_failure)
                    ConsoleOutput.warning(
                        f"Tests failed in iteration {iteration}. Developer applying targeted fixes..."
                    )
                    log_store.set_agent_context(
                        "Developer",
                        f"Fix Iteration {iteration}",
                        model=developer_agent.llm.model,
                        llm=developer_agent.llm,
                    )
                    t_fix = time.perf_counter()
                    failure_summary = (
                        f"Pytest execution failed with exit code {test_run.exit_code}.\n\n"
                        f"{compact_failure}\n\n"
                        "Please diagnose the failure using the systematic-debugging skill and update the code."
                    )
                    dev_conv.send_message(
                        self.human_channel.inject_into_prompt(failure_summary)
                    )
                    self._run_conv(dev_conv, "Developer")
                    dur_fix = time.perf_counter() - t_fix
                    new_diff = self.git.get_diff() or self.git.get_status()
                    u_dev_fix = get_llm_usage(developer_agent.llm)
                    recorder.record_step(
                        "developer",
                        "fix_code",
                        iteration,
                        dur_fix,
                        True,
                        new_diff,
                        prompt_tokens=u_dev_fix["prompt_tokens"],
                        completion_tokens=u_dev_fix["completion_tokens"],
                        total_tokens=u_dev_fix["total_tokens"],
                        estimated_cost_usd=u_dev_fix["estimated_cost_usd"],
                    )

                    if recorder.check_budget(_get_total_cost()):
                        ConsoleOutput.error(
                            "Budget ceiling reached after developer fix. Halting."
                        )
                        break

                iteration += 1

            # -------------------------------------------------------------------
            # Phase 4: Independent Reviewer Audit
            # -------------------------------------------------------------------
            review_approved = False
            if tests_passed:
                if self.state_machine.can_transition(PipelinePhase.REVIEW):
                    self.state_machine.transition_to(PipelinePhase.REVIEW)
                ConsoleOutput.pipeline_stage(
                    "INDEPENDENT REVIEW & AUDIT",
                    4,
                    4,
                    "Security, performance & code quality verification",
                )

                t_rev = time.perf_counter()
                log_store.set_agent_context(
                    "Reviewer",
                    "Independent Code Review",
                    model=reviewer_agent.llm.model,
                    llm=reviewer_agent.llm,
                )
                ConsoleOutput.agent_step(
                    "Reviewer",
                    "Conducting independent audit and security review...",
                    model=reviewer_agent.llm.model,
                )

                reviewer_conv = Conversation(
                    agent=reviewer_agent,
                    workspace=str(self.workspace_path),
                    visualizer=visualizer,
                )
                git_diff = (
                    self.git.get_compact_diff(max_chars=4000) or self.git.get_status()
                )
                review_prompt = (
                    f"Task: {task_description}\n\n"
                    f"Git Changes:\n{git_diff}\n\n"
                    "Evaluate against code-review-standards and conclude with a valid JSON verdict block."
                )
                reviewer_conv.send_message(
                    self.human_channel.inject_into_prompt(review_prompt)
                )
                self._run_conv(reviewer_conv, "Reviewer")
                dur_rev = time.perf_counter() - t_rev
                u_rev = get_llm_usage(reviewer_agent.llm)

                verdict = ReviewerVerdict(approved=False, verdict="REJECTED")
                if reviewer_conv.state and reviewer_conv.state.events:
                    for ev in reversed(reviewer_conv.state.events):
                        text = str(
                            getattr(ev, "content", "") or getattr(ev, "text", "")
                        )
                        verdict = ReviewerVerdict.parse(text)
                        if verdict.verdict in ("APPROVED", "REJECTED"):
                            break

                review_approved = verdict.approved
                recorder.record_step(
                    "reviewer",
                    "audit_code",
                    iteration,
                    dur_rev,
                    review_approved,
                    prompt_tokens=u_rev["prompt_tokens"],
                    completion_tokens=u_rev["completion_tokens"],
                    total_tokens=u_rev["total_tokens"],
                    estimated_cost_usd=u_rev["estimated_cost_usd"],
                )

                if review_approved:
                    ConsoleOutput.success("Reviewer approved the code!")
                else:
                    ConsoleOutput.warning(
                        f"Reviewer requested fixes: {verdict.required_fixes or 'See review report'}"
                    )

                # Optional review fix cycle
                review_cycle = 1
                while not review_approved and review_cycle <= 2:
                    if not self.controller.check_should_continue():
                        break

                    ConsoleOutput.agent_step(
                        "Developer",
                        f"Addressing Reviewer critique (Cycle {review_cycle})...",
                        model=developer_agent.llm.model,
                    )
                    t_rev_fix = time.perf_counter()
                    fixes_str = (
                        "\n".join(f"- {f}" for f in verdict.required_fixes)
                        if verdict.required_fixes
                        else verdict.raw_text[:1000]
                    )
                    dev_conv.send_message(
                        f"Reviewer rejected the code. Required fixes:\n{fixes_str}\n\nPlease apply fixes."
                    )
                    self._run_conv(dev_conv, "Developer")
                    dur_rev_fix = time.perf_counter() - t_rev_fix
                    new_diff = self.git.get_diff() or self.git.get_status()
                    u_dev_rf = get_llm_usage(developer_agent.llm)
                    recorder.record_step(
                        "developer",
                        "review_fix",
                        iteration + review_cycle,
                        dur_rev_fix,
                        True,
                        new_diff,
                        prompt_tokens=u_dev_rf["prompt_tokens"],
                        completion_tokens=u_dev_rf["completion_tokens"],
                        total_tokens=u_dev_rf["total_tokens"],
                        estimated_cost_usd=u_dev_rf["estimated_cost_usd"],
                    )

                    test_run = self._execute_pytest()
                    if test_run.exit_code != 0:
                        ConsoleOutput.warning(
                            "Tests failed after review fixes. Attempting quick fix..."
                        )
                        dev_conv.send_message(
                            f"Pytest failed after review fixes:\n{test_run.stdout}\n{test_run.stderr}\nFix code to pass tests."
                        )
                        self._run_conv(dev_conv, "Developer")

                    # Re-audit
                    t_re_audit = time.perf_counter()
                    git_diff = (
                        self.git.get_compact_diff(max_chars=4000)
                        or self.git.get_status()
                    )
                    reviewer_conv.send_message(
                        f"Developer applied fixes.\n\nUpdated Git Changes:\n{git_diff}\n\nRe-evaluate and conclude with JSON verdict."
                    )
                    self._run_conv(reviewer_conv, "Reviewer")
                    dur_re_audit = time.perf_counter() - t_re_audit
                    u_re_audit = get_llm_usage(reviewer_agent.llm)

                    if reviewer_conv.state and reviewer_conv.state.events:
                        for ev in reversed(reviewer_conv.state.events):
                            text = str(
                                getattr(ev, "content", "") or getattr(ev, "text", "")
                            )
                            verdict = ReviewerVerdict.parse(text)
                            if verdict.verdict in ("APPROVED", "REJECTED"):
                                break

                    review_approved = verdict.approved
                    recorder.record_step(
                        "reviewer",
                        "re_audit",
                        iteration + review_cycle,
                        dur_re_audit,
                        review_approved,
                        prompt_tokens=u_re_audit["prompt_tokens"],
                        completion_tokens=u_re_audit["completion_tokens"],
                        total_tokens=u_re_audit["total_tokens"],
                        estimated_cost_usd=u_re_audit["estimated_cost_usd"],
                    )

                    if review_approved:
                        ConsoleOutput.success("Reviewer approved code after fixes!")
                        break

                    review_cycle += 1
                    if recorder.check_budget(_get_total_cost()):
                        ConsoleOutput.error(
                            "Budget ceiling reached during review fix cycles. Halting."
                        )
                        break

            final_success = tests_passed and review_approved
            if not status_override:
                status_override = (
                    "SUCCESS"
                    if final_success
                    else ("REVIEW_REJECTED" if tests_passed else "TESTS_FAILED")
                )

            return self._finalize_pipeline(
                task_description=task_description,
                success=final_success,
                iteration=iteration,
                recorder=recorder,
                memory_store=memory_store,
                log_store=log_store,
                commit_msg_prefix="feat",
                status_override=status_override,
            )

        except Exception as e:
            if self.state_machine.can_transition(PipelinePhase.FAILED):
                self.state_machine.transition_to(PipelinePhase.FAILED)
            ConsoleOutput.error(f"Pipeline crashed: {e}")
            log_store.add_step(f"Fatal pipeline crash: {str(e)}", is_error=True)
            log_store.save_to_file()
            return {"status": "CRASHED", "error": str(e)}
