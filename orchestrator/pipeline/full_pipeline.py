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


class FullPipeline:
    """End-to-end 4-role multi-agent pipeline with circuit breaker and independent review."""

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
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.git.init_repo()
        task_branch = self.git.create_task_branch(task_description)
        if task_branch:
            ConsoleOutput.agent_step("Git", f"Isolated task branch created: [bold cyan]{task_branch}[/bold cyan]")

        recorder = TelemetryRecorder(
            task_description=task_description,
            pipeline_mode="full",
            circuit_breaker_threshold=self.config.circuit_breaker_threshold,
            max_budget_usd=self.config.max_budget_usd,
        )

        log_store = SessionLogStore(self.workspace_path)
        visualizer = OrchestratorLiveVisualizer(log_store, verbosity=self.config.verbosity)

        ConsoleOutput.banner(
            "Starting Full 4-Agent Pipeline",
            f"Workspace: {self.workspace_path} | Max Iterations: {self.config.max_iterations} | Budget: ${self.config.max_budget_usd:.2f}"
        )
        ConsoleOutput.agent_step("System", f"Loaded Skills: {', '.join(self.skill_manager.available_skills)}")

        # Agents
        architect_agent = create_architect_agent(self.config, self.skill_manager, self.workspace_path)
        developer_agent = create_developer_agent(self.config, self.skill_manager, self.workspace_path)
        tester_agent = create_tester_agent(self.config, self.skill_manager, self.workspace_path)
        reviewer_agent = create_reviewer_agent(self.config, self.skill_manager, self.workspace_path)

        def _get_total_cost() -> float:
            return sum(
                get_llm_usage(ag.llm)["estimated_cost_usd"]
                for ag in [architect_agent, developer_agent, tester_agent, reviewer_agent]
            )

        try:
            # -------------------------------------------------------------------
            # Phase 1: Architectural Decomposition
            # -------------------------------------------------------------------
            t0 = time.perf_counter()
            log_store.set_agent_context("Architect", "Decomposition", model=architect_agent.llm.model, llm=architect_agent.llm)
            ConsoleOutput.agent_step("Architect", "Designing modular blueprint and PLAN.md...", model=architect_agent.llm.model)
            # Graft zero-token codebase context injection
            graft_map = GraftContextProvider.get_compact_map(self.workspace_path)
            graft_part = f"\n\n[Codebase Architecture Map (Graft)]:\n{graft_map}" if graft_map else ""

            # Memory cross-run intelligence injection
            memory_store = ConversationStore()
            memory_ctx = memory_store.format_memory_context(task_description)
            memory_part = f"\n\n{memory_ctx}" if memory_ctx else ""

            arch_conv = Conversation(agent=architect_agent, workspace=str(self.workspace_path), visualizer=visualizer)
            arch_prompt = (
                f"User Task:\n{task_description}\n\n"
                "Decompose this task according to architectural-decomposition skill. "
                "Write the complete specification into PLAN.md in the workspace root."
                f"{graft_part}"
                f"{memory_part}"
            )
            arch_conv.send_message(self.human_channel.inject_into_prompt(arch_prompt))
            arch_conv.run()
            dur_arch = time.perf_counter() - t0
            u_arch = get_llm_usage(architect_agent.llm)
            recorder.record_step(
                "architect", "plan_generation", 1, dur_arch, True,
                prompt_tokens=u_arch["prompt_tokens"],
                completion_tokens=u_arch["completion_tokens"],
                total_tokens=u_arch["total_tokens"],
                estimated_cost_usd=u_arch["estimated_cost_usd"],
            )
            ConsoleOutput.success(f"Architect generated PLAN.md (Tokens: {u_arch['total_tokens']:,}, Cost: ${u_arch['estimated_cost_usd']:.4f}).")

            if recorder.check_budget(_get_total_cost()):
                ConsoleOutput.error("Budget ceiling reached after architect phase. Halting.")
                diag_report = recorder.finalize(completed_successfully=False)
                log_store.save_to_file()
                return {"status": "BUDGET_EXHAUSTED", "iterations": 1, "report_id": diag_report.report_id}

            # Persist checkpoint after architect phase
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
                plan_path = self.workspace_path / "PLAN.md"
                plan_preview = plan_path.read_text(encoding="utf-8", errors="replace") if plan_path.exists() else "No PLAN.md generated."
                gate_decision = self.human_channel.prompt_gate("after_architect", context_preview=plan_preview[:2000])
                if gate_decision == "rejected":
                    ConsoleOutput.error("Execution halted: human operator rejected PLAN.md at 'after_architect' gate.")
                    log_store.add_step("PLAN.md rejected by human operator.", is_error=True)
                    diag_report = recorder.finalize(completed_successfully=False)
                    log_store.save_to_file()
                    return {"status": "HUMAN_REJECTED", "phase": "architect", "report_id": diag_report.report_id}

            # -------------------------------------------------------------------
            # Phase 2: Implementation & Rigorous Testing Loop
            # -------------------------------------------------------------------
            t_dev = time.perf_counter()
            log_store.set_agent_context("Developer", "Implementation", model=developer_agent.llm.model, llm=developer_agent.llm)
            ConsoleOutput.agent_step("Developer", "Implementing specification from PLAN.md...", model=developer_agent.llm.model)
            dev_conv = Conversation(agent=developer_agent, workspace=str(self.workspace_path), visualizer=visualizer)
            dev_prompt = (
                f"Task: {task_description}\n\n"
                "Read PLAN.md and implement the complete solution adhering to clean-python-architecture."
                f"{graft_part}"
            )
            dev_conv.send_message(self.human_channel.inject_into_prompt(dev_prompt))
            dev_conv.run()
            dur_dev = time.perf_counter() - t_dev
            curr_diff = self.git.get_diff() or self.git.get_status()
            u_dev = get_llm_usage(developer_agent.llm)
            recorder.record_step(
                "developer", "initial_implementation", 1, dur_dev, True, curr_diff,
                prompt_tokens=u_dev["prompt_tokens"],
                completion_tokens=u_dev["completion_tokens"],
                total_tokens=u_dev["total_tokens"],
                estimated_cost_usd=u_dev["estimated_cost_usd"],
            )
            ConsoleOutput.success(f"Developer completed initial code (Tokens: {u_dev['total_tokens']:,}, Cost: ${u_dev['estimated_cost_usd']:.4f}).")

            if recorder.check_budget(_get_total_cost()):
                ConsoleOutput.error("Budget ceiling reached after initial developer phase. Halting.")
                diag_report = recorder.finalize(completed_successfully=False)
                log_store.save_to_file()
                return {"status": "BUDGET_EXHAUSTED", "iterations": 1, "report_id": diag_report.report_id}

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
                diff_preview = self.git.get_diff() or self.git.get_status()
                gate_decision = self.human_channel.prompt_gate("after_developer", context_preview=diff_preview[:1500])
                if gate_decision == "rejected":
                    ConsoleOutput.error("Execution halted: human operator rejected changes at 'after_developer' gate.")
                    log_store.add_step("Changes rejected at after_developer approval gate.", is_error=True)
                    diag_report = recorder.finalize(completed_successfully=False)
                    log_store.save_to_file()
                    return {"status": "HUMAN_REJECTED", "phase": "developer", "report_id": diag_report.report_id}

            iteration = 1
            tests_passed = False
            tester_conv = Conversation(agent=tester_agent, workspace=str(self.workspace_path), visualizer=visualizer)

            while iteration <= self.config.max_iterations:
                log_store.set_agent_context("Tester", f"Test Iteration {iteration}", model=tester_agent.llm.model, llm=tester_agent.llm)
                # Step 2a: Zero-Token Pre-flight Syntax Check (<50ms)
                syntax_ok, syntax_err = PreFlightGuard.check_syntax(self.workspace_path)
                if not syntax_ok:
                    ConsoleOutput.warning(f"Pre-flight syntax check failed in iteration {iteration}! Routing syntax error to Developer immediately.")
                    log_store.add_step(f"Pre-flight syntax error in iteration {iteration}", is_error=True, observation=syntax_err)
                    recorder.record_incident(f"Iteration_{iteration}_Syntax", "syntax_error", syntax_err[:300])
                    t_syntax_fix = time.perf_counter()
                    dev_conv.send_message(
                        f"Pre-flight syntax validation detected syntax errors in workspace:\n\n{syntax_err}\n\n"
                        "Please fix these syntax errors immediately."
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
                    tester_conv.send_message(
                        f"Task: {task_description}\n\n"
                        "Read PLAN.md and source files. Write and execute complete pytest tests as per pytest-rigorous-testing."
                    )
                    tester_conv.run()
                else:
                    tester_conv.send_message(
                        f"Iteration {iteration}: Developer updated the code to fix failures. Run pytest -v to verify."
                    )
                    tester_conv.run()

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

                    curr_diff = self.git.get_diff() or self.git.get_status()
                    if recorder.check_circuit_breaker(curr_diff, error_output):
                        ConsoleOutput.error("Circuit Breaker Tripped! Runaway loop detected with identical failure. Halting.")
                        break

                    if recorder.check_budget(_get_total_cost()):
                        ConsoleOutput.error("Budget ceiling reached during test iterations. Halting.")
                        break

                    if iteration == self.config.max_iterations:
                        ConsoleOutput.error("Max test iterations reached.")
                        break

                    ConsoleOutput.warning(f"Tests failed in iteration {iteration}. Requesting Developer fix (reusing conversation context).")
                    t_fix = time.perf_counter()
                    log_store.set_agent_context("Developer", f"Fix Iteration {iteration}", model=developer_agent.llm.model, llm=developer_agent.llm)
                    compact_failure = PytestOutputParser.extract_compact_failures(test_run.stdout, test_run.stderr)
                    dev_fix_prompt = (
                        f"Pytest execution failed with exit code {test_run.exit_code}.\n\n"
                        f"{compact_failure}\n\n"
                        "Fix issues following systematic-debugging protocol."
                    )
                    dev_conv.send_message(self.human_channel.inject_into_prompt(dev_fix_prompt))
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

            if not tests_passed:
                diag_report = recorder.finalize(completed_successfully=False)
                ConsoleOutput.error("Pipeline aborted: Tests failed.")
                log_store.save_to_file()
                InteractiveLogExplorer(log_store).run()
                return {"status": "FAILED_TESTS", "iterations": iteration, "report_id": diag_report.report_id}

            # -------------------------------------------------------------------
            # Phase 3: Independent Review & Review-Fix Loop
            # -------------------------------------------------------------------
            t_rev = time.perf_counter()
            log_store.set_agent_context("Reviewer", "Code Audit", model=reviewer_agent.llm.model, llm=reviewer_agent.llm)
            ConsoleOutput.agent_step("Reviewer", "Auditing code with independent model...", model=reviewer_agent.llm.model)
            git_diff = self.git.get_diff() or self.git.get_status()
            reviewer_conv = Conversation(agent=reviewer_agent, workspace=str(self.workspace_path), visualizer=visualizer)
            reviewer_conv.send_message(
                f"Task: {task_description}\n\n"
                f"Git Changes:\n{git_diff}\n\n"
                "Perform an independent review according to code-review-standards and security-audit-hardening. "
                "Inspect workspace files and conclude with VERDICT: APPROVED or VERDICT: REJECTED."
            )
            reviewer_conv.run()
            dur_rev = time.perf_counter() - t_rev
            u_rev = get_llm_usage(reviewer_agent.llm)

            review_approved = False
            critique_text = ""
            if reviewer_conv.state and reviewer_conv.state.events:
                for ev in reversed(reviewer_conv.state.events):
                    text = str(getattr(ev, "content", "") or getattr(ev, "text", ""))
                    if "VERDICT: REJECTED" in text:
                        review_approved = False
                        critique_text = text
                        recorder.record_step(
                            "reviewer", "code_audit", iteration, dur_rev, False,
                            error_summary="Reviewer rejected code",
                            prompt_tokens=u_rev["prompt_tokens"],
                            completion_tokens=u_rev["completion_tokens"],
                            total_tokens=u_rev["total_tokens"],
                            estimated_cost_usd=u_rev["estimated_cost_usd"],
                        )
                        ConsoleOutput.warning("Reviewer rejected current code.")
                        break
                    elif "VERDICT: APPROVED" in text:
                        review_approved = True
                        recorder.record_step(
                            "reviewer", "code_audit", iteration, dur_rev, True,
                            prompt_tokens=u_rev["prompt_tokens"],
                            completion_tokens=u_rev["completion_tokens"],
                            total_tokens=u_rev["total_tokens"],
                            estimated_cost_usd=u_rev["estimated_cost_usd"],
                        )
                        ConsoleOutput.success("Reviewer approved code.")
                        break

            # Outer Review -> Developer Feedback Loop
            max_review_cycles = 2
            review_cycle = 1
            while not review_approved and review_cycle <= max_review_cycles:
                ConsoleOutput.warning(f"Routing Reviewer feedback to Developer (Fix Cycle {review_cycle}/{max_review_cycles})...")
                t_rev_fix = time.perf_counter()
                log_store.set_agent_context("Developer", f"Review Fix Cycle {review_cycle}", model=developer_agent.llm.model, llm=developer_agent.llm)
                dev_conv.send_message(
                    f"The independent Reviewer rejected the code with following feedback:\n\n"
                    f"{critique_text[:2500]}\n\n"
                    "Address all required fixes, security concerns, and code standards."
                )
                dev_conv.run()
                dur_rev_fix = time.perf_counter() - t_rev_fix
                new_diff = self.git.get_diff() or self.git.get_status()
                u_dev_rf = get_llm_usage(developer_agent.llm)
                recorder.record_step(
                    "developer", "review_fix", iteration + review_cycle, dur_rev_fix, True, new_diff,
                    prompt_tokens=u_dev_rf["prompt_tokens"],
                    completion_tokens=u_dev_rf["completion_tokens"],
                    total_tokens=u_dev_rf["total_tokens"],
                    estimated_cost_usd=u_dev_rf["estimated_cost_usd"],
                )

                # Re-verify tests after review fix
                test_run = execute_terminal_action(
                    WorkspaceTerminalAction(command="pytest -v", timeout_seconds=60),
                    base_dir=self.workspace_path,
                )
                if test_run.exit_code != 0:
                    ConsoleOutput.warning("Tests failed after review fixes. Attempting quick fix...")
                    dev_conv.send_message(f"Pytest failed after review fixes:\n{test_run.stdout}\n{test_run.stderr}\nFix code to pass tests.")
                    dev_conv.run()

                # Re-audit with Reviewer
                t_re_audit = time.perf_counter()
                log_store.set_agent_context("Reviewer", f"Re-Audit Cycle {review_cycle}", model=reviewer_agent.llm.model, llm=reviewer_agent.llm)
                git_diff = self.git.get_diff() or self.git.get_status()
                reviewer_conv.send_message(
                    f"Developer applied fixes addressing your feedback.\n\nUpdated Git Changes:\n{git_diff}\n\n"
                    "Re-evaluate the codebase and conclude strictly with VERDICT: APPROVED or VERDICT: REJECTED."
                )
                reviewer_conv.run()
                dur_re_audit = time.perf_counter() - t_re_audit
                u_re_audit = get_llm_usage(reviewer_agent.llm)

                if reviewer_conv.state and reviewer_conv.state.events:
                    for ev in reversed(reviewer_conv.state.events):
                        text = str(getattr(ev, "content", "") or getattr(ev, "text", ""))
                        if "VERDICT: APPROVED" in text:
                            review_approved = True
                            recorder.record_step(
                                "reviewer", "re_audit", iteration + review_cycle, dur_re_audit, True,
                                prompt_tokens=u_re_audit["prompt_tokens"],
                                completion_tokens=u_re_audit["completion_tokens"],
                                total_tokens=u_re_audit["total_tokens"],
                                estimated_cost_usd=u_re_audit["estimated_cost_usd"],
                            )
                            ConsoleOutput.success("Reviewer approved code after fixes!")
                            break
                        elif "VERDICT: REJECTED" in text:
                            review_approved = False
                            critique_text = text
                            recorder.record_step(
                                "reviewer", "re_audit", iteration + review_cycle, dur_re_audit, False,
                                prompt_tokens=u_re_audit["prompt_tokens"],
                                completion_tokens=u_re_audit["completion_tokens"],
                                total_tokens=u_re_audit["total_tokens"],
                                estimated_cost_usd=u_re_audit["estimated_cost_usd"],
                            )
                            ConsoleOutput.warning("Reviewer rejected code after fixes.")
                            break

                review_cycle += 1
                if recorder.check_budget(_get_total_cost()):
                    ConsoleOutput.error("Budget ceiling reached during review fix cycles. Halting.")
                    break

            diag_report = recorder.finalize(completed_successfully=review_approved)
            ConsoleOutput.success(f"Telemetry report logged: {diag_report.report_id}")

            # -------------------------------------------------------------------
            # Phase 4: Commit on Success
            # -------------------------------------------------------------------
            commit_hash = ""
            if review_approved and self.config.auto_commit:
                can_commit = True
                if "before_commit" in self.config.approval_gates:
                    gate_decision = self.human_channel.prompt_gate("before_commit", context_preview="Review approved and tests passed. Confirm Git commit.")
                    if gate_decision == "rejected":
                        ConsoleOutput.warning("Git commit cancelled by human operator.")
                        can_commit = False

                if can_commit:
                    commit_msg = f"feat: {task_description[:50]} (Architect -> Dev -> Test -> Review)"
                    commit_res = self.git.commit(commit_msg)
                    if commit_res:
                        commit_hash = commit_res
                        ConsoleOutput.success(f"Created Git commit: {commit_hash[:8]}")

            status_str = "SUCCESS" if review_approved else "REVIEW_REJECTED"
            ConsoleOutput.summary_table(iteration, status_str, commit_hash)

            # Persist execution memory for cross-run learning
            try:
                memory_store.save_run_memory(
                    task=task_description,
                    summary=f"Full pipeline run concluded with {status_str} in {iteration} iteration(s).",
                    tests_passed=tests_passed,
                    lessons=recorder.recommendations[0] if recorder.recommendations else None,
                )
            except Exception:
                pass

            if review_approved:
                PipelineCheckpointManager.clear(self.workspace_path)

            InteractiveLogExplorer(log_store).run()

            return {
                "status": status_str,
                "iterations": iteration,
                "tests_passed": tests_passed,
                "review_approved": review_approved,
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

