"""Guarded Finite State Machine Engine core implementation.

Executes unified, event-driven multi-agent lifecycles with pure semantic query gates,
Inversion of Control over OpenHands runtime bridge, bounded turn envelopes, and
cryptographically verified checkpoints.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from orchestrator.adapters import ProjectAdapter, detect_adapter
from orchestrator.analysis.pytest_parser import PytestOutputParser, TestExecutionResult
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.control.adaptive import (
    AdaptiveResourceGovernor,
    ResourceGovernorConfig,
    ResourcePhase,
)
from orchestrator.control.human_channel import HumanChannel, get_active_channel
from orchestrator.control.pipeline_controller import PipelineController
from orchestrator.engine.openhands_bridge import (
    AgentExecutionOutcome as BridgeAgentOutcome,
    AgentExitReason,
    OpenHandsRuntimeBridge,
    PromptView,
    TurnEnvelope,
)
from orchestrator.guards.preflight import PreFlightGuard
from orchestrator.pipeline.fsm.checkpoint import FSMCheckpointManager
from orchestrator.pipeline.fsm.events import (
    AgentExecutionOutcome,
    EventType,
    PipelineEvent,
)
from orchestrator.pipeline.fsm.guards import (
    CompletionDecision,
    CompletionStatus,
    FSMGuards,
    ImplementationState,
    RequirementStatus,
    TaskTruthSemanticQueries,
    VerificationState,
    evaluate_task_completion,
)
from orchestrator.pipeline.fsm.profiles import LifecycleProfile, PipelineMode, get_profile
from orchestrator.pipeline.fsm.states import FSMState
from orchestrator.governance.models import (
    ExecutionHealth,
    GovernanceAction,
    GovernanceDecision,
)
from orchestrator.governance.iteration_governor import IterationGovernor
from orchestrator.pipeline.fsm.transitions import (
    TransitionMatrix,
    TransitionResult,
    TransitionRule,
)
from orchestrator.pipeline.milestone_dag import MilestoneParser, SubtaskMilestone
from orchestrator.pipeline.reviewer_parser import ReviewerVerdict
from orchestrator.rendering.output import ConsoleOutput
from orchestrator.tools.hardened.manager import ToolSandboxManager
from orchestrator.vcs.git_ops import GitOps

if TYPE_CHECKING:
    from orchestrator.analysis.schemas import AuditResult
    from orchestrator.llm.manager import LLMManager
    from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB
    from orchestrator.ui.session_store import SessionLogStore
    from orchestrator.ui.visualizer import OrchestratorLiveVisualizer

from orchestrator.pipeline.fsm.context import FSMContext

logger = logging.getLogger(__name__)


class GuardedFSMEngine:
    """Deterministic, event-driven state machine orchestrating agent lifecycles."""

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: Optional[SkillManager] = None,
        profile: Optional[LifecycleProfile] = None,
        workspace_path: Optional[Path] = None,
        controller: Optional[PipelineController] = None,
        human_channel: Optional[HumanChannel] = None,
        llm_manager: Optional[Any] = None,
        log_store: Optional[Any] = None,
        visualizer: Optional[Any] = None,
        diagnostics_db: Optional[Any] = None,
        governor: Optional[AdaptiveResourceGovernor] = None,
    ) -> None:
        self.config = config
        self.skill_manager = skill_manager or SkillManager()
        self.profile = profile or get_profile(PipelineMode.DEV_TEST)
        self.workspace_path = (workspace_path or config.workspace_path).resolve()
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.controller = controller or PipelineController()
        self.human_channel = human_channel or get_active_channel()
        self.llm_manager = llm_manager
        self.log_store = log_store
        self.visualizer = visualizer
        self.diagnostics_db = diagnostics_db

        # Adaptive Resource Governor initialization
        if governor is not None:
            self.governor: Optional[AdaptiveResourceGovernor] = governor
        elif self._is_adaptive_governance_enabled():
            self.governor = AdaptiveResourceGovernor()
        else:
            self.governor = None

        self.iteration_governor = IterationGovernor()

        # Initialize Sandboxes & Runtime Bridge
        self.sandbox_manager = ToolSandboxManager(workspace_root=self.workspace_path)
        if self.llm_manager is None:
            try:
                from orchestrator.llm.manager import LLMManager
                self.llm_manager = LLMManager(config=self.config)
            except Exception as e:
                logger.warning(f"Could not auto-initialize LLMManager: {e}")
                self.llm_manager = None

        self.runtime_bridge = OpenHandsRuntimeBridge(
            config=self.config,
            llm_manager=self.llm_manager,
            log_store=self.log_store,
            visualizer=self.visualizer,
            diagnostics_db=self.diagnostics_db,
        )

        # Build Context & Transition Matrix
        self.context = FSMContext(
            workspace_path=self.workspace_path,
            config=self.config,
            profile=self.profile,
            controller=self.controller,
            human_channel=self.human_channel,
            skill_manager=self.skill_manager,
            llm_manager=self.llm_manager,
            runtime_bridge=self.runtime_bridge,
            sandbox_manager=self.sandbox_manager,
            governor=self.governor,
            log_store=self.log_store,
            visualizer=self.visualizer,
            diagnostics_db=self.diagnostics_db,
            current_state=FSMState.INIT,
        )

        self.transition_matrix = TransitionMatrix.build_default()

    @staticmethod
    def _is_adaptive_governance_enabled() -> bool:
        """Check whether adaptive governance is active via migration_routing.json."""
        try:
            routing_path = (
                Path(__file__).resolve().parent.parent.parent
                / "config"
                / "migration_routing.json"
            )
            if routing_path.is_file():
                data = json.loads(routing_path.read_text(encoding="utf-8"))
                return bool(data.get("use_adaptive_governance", True))
        except Exception:
            pass
        return True

    @property
    def current_state(self) -> FSMState:
        """Active state of the FSM engine."""
        return self.context.current_state

    @property
    def state_history(self) -> List[FSMState]:
        """Chronological history of visited FSM states."""
        return list(self.context.state_history)

    def is_terminal(self) -> bool:
        """Return True if active state is COMPLETED, FAILED, or ABORTED."""
        return self.context.current_state.is_terminal

    def process_event(self, event: PipelineEvent) -> TransitionResult:
        """Evaluate active guards and execute state transition for an incoming event."""
        matching_rule = self.transition_matrix.get_matching_rule(
            current_state=self.context.current_state,
            event=event,
            context=self.context,
        )

        if not matching_rule:
            candidates = self.transition_matrix.get_candidate_rules(
                self.context.current_state, event.event_type
            )
            rejection = (
                f"Guard rejected transition from '{self.context.current_state}' on '{event.event_type}'."
                if candidates
                else f"No transition defined from '{self.context.current_state}' on '{event.event_type}'."
            )
            return TransitionResult(
                success=False,
                current_state=self.context.current_state,
                rejection_reason=rejection,
            )

        target_state = matching_rule.target_state

        # Enforce profile allowed_states boundary
        if target_state not in self.profile.allowed_states:
            return TransitionResult(
                success=False,
                current_state=self.context.current_state,
                target_state=target_state,
                rejection_reason=(
                    f"Target state '{target_state}' is disallowed under profile '{self.profile.mode.value}'."
                ),
            )

        # Execute On-Exit Action
        if matching_rule.on_exit:
            try:
                matching_rule.on_exit(self.context, event)
            except Exception as ex:
                logger.warning(f"Error in on_exit hook: {ex}")

        old_state = self.context.current_state
        self.context.current_state = target_state
        self.context.state_history.append(target_state)

        # Execute On-Entry Action
        if matching_rule.on_entry:
            try:
                matching_rule.on_entry(self.context, event)
            except Exception as ex:
                logger.warning(f"Error in on_entry hook: {ex}")

        # Checkpoint state to disk
        try:
            FSMCheckpointManager.save_checkpoint(self.context)
        except Exception as ex:
            logger.warning(f"Failed to persist FSM checkpoint: {ex}")

        return TransitionResult(
            success=True,
            current_state=self.context.current_state,
            target_state=target_state,
            previous_state=old_state,
            transition_rule=matching_rule,
        )

    def run(
        self,
        task_description: str,
        resume: bool = False,
        timeout_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute full event-driven lifecycle to terminal conclusion."""
        self.context.task_description = task_description
        start_time = time.monotonic()
        active_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else getattr(self.config, "pipeline_timeout_seconds", None)
            or getattr(self.profile, "timeout_seconds", 1800)
        )

        # Check for resume
        if resume:
            checkpoint = FSMCheckpointManager.load_checkpoint(self.workspace_path)
            if checkpoint:
                self._resume_from_checkpoint(checkpoint)

        # If still in INIT, dispatch initial START_TASK
        if self.context.current_state == FSMState.INIT:
            self.process_event(
                PipelineEvent(
                    event_type=EventType.START_TASK, source_phase=FSMState.INIT
                )
            )

        # Main Event-Driven Orchestration Loop
        while not self.is_terminal():
            # Check wall-clock timeout
            if active_timeout and (time.monotonic() - start_time > active_timeout):
                logger.error(
                    f"Pipeline execution exceeded wall-clock timeout of {active_timeout}s. Halting."
                )
                self.context.metadata["timed_out"] = True
                self.context.metadata["blocking_reason"] = f"Pipeline execution exceeded wall-clock timeout of {active_timeout}s."
                self.process_event(
                    PipelineEvent(
                        event_type=EventType.CRITICAL_ERROR,
                        source_phase=self.context.current_state,
                        error_message=f"Pipeline execution exceeded wall-clock timeout of {active_timeout}s.",
                    )
                )
                if not self.is_terminal():
                    self.context.current_state = FSMState.FAILED
                    self.context.state_history.append(FSMState.FAILED)
                break

            # Check controller abort signal
            if self.controller and not self.controller.check_should_continue():
                self.process_event(
                    PipelineEvent(
                        event_type=EventType.ABORT_REQUESTED,
                        source_phase=self.context.current_state,
                    )
                )
                break

            # If in BLOCKED or AMBIGUOUS state, check if human input is available to unblock
            if self.context.current_state in (FSMState.BLOCKED, FSMState.AMBIGUOUS):
                if self.human_channel and self.human_channel.has_message():
                    msg = self.human_channel.get_message()
                    self.process_event(
                        PipelineEvent(
                            event_type=EventType.HUMAN_INPUT_RECEIVED,
                            source_phase=self.context.current_state,
                            payload={"message": msg},
                        )
                    )
                    continue
                else:
                    block_reason = (
                        self.context.metadata.get("blocking_reason")
                        or f"Awaiting human intervention or external resolution at state {self.context.current_state.value}."
                    )
                    self.context.metadata["blocking_reason"] = block_reason
                    logger.info(
                        f"Execution halted at non-terminal state {self.context.current_state.value}: {block_reason}"
                    )
                    break

            # Execute handler for active state
            next_event = self._execute_state_handler(self.context.current_state)
            transition_res = self.process_event(next_event)

            if not transition_res.success:
                logger.warning(
                    f"Transition failed: {transition_res.rejection_reason}. Handling recovery."
                )
                if self.context.current_state == FSMState.RESOLUTION:
                    rec_res = self.process_event(
                        PipelineEvent(
                            event_type=EventType.RETRIES_EXHAUSTED,
                            source_phase=FSMState.RESOLUTION,
                            error_message=transition_res.rejection_reason,
                        )
                    )
                elif self.context.current_state == FSMState.PREFLIGHT:
                    rec_res = self.process_event(
                        PipelineEvent(
                            event_type=EventType.PREFLIGHT_FAILED,
                            source_phase=FSMState.PREFLIGHT,
                            error_message=transition_res.rejection_reason,
                        )
                    )
                else:
                    rec_res = self.process_event(
                        PipelineEvent(
                            event_type=EventType.CRITICAL_ERROR,
                            source_phase=self.context.current_state,
                            error_message=transition_res.rejection_reason,
                        )
                    )
                if not rec_res.success:
                    logger.error(
                        f"Recovery transition failed: {rec_res.rejection_reason}. Halting FSM engine."
                    )
                    self.context.current_state = FSMState.FAILED
                    self.context.state_history.append(FSMState.FAILED)
                    break

        return self._finalize_run_result()

    def _execute_state_handler(self, state: FSMState) -> PipelineEvent:
        """Dispatch execution to persona/task handler for the current state."""
        state_labels = {
            FSMState.INIT: ("System", "Initializing workspace and environment"),
            FSMState.PREFLIGHT: ("System", "Running zero-token syntax & preflight checks"),
            FSMState.PLANNING: ("Architect", "Generating architecture breakdown & PLAN.md"),
            FSMState.IMPLEMENTATION: ("Developer", "Writing code & unit tests"),
            FSMState.VERIFICATION: ("Tester", "Running pytest test suite & invariant validation"),
            FSMState.RESOLUTION: ("System", "Evaluating test outcomes and triaging remediation"),
            FSMState.REVIEW: ("Reviewer", "Security audit, quality gate & final review"),
            FSMState.COMPLETED: ("System", "Task completed successfully"),
            FSMState.FAILED: ("System", "Task execution terminated with failure"),
        }
        if state in state_labels:
            role, action = state_labels[state]
            ConsoleOutput.agent_step(role, action)

        if state == FSMState.INIT:
            return self._handle_init()
        elif state == FSMState.PREFLIGHT:
            return self._handle_preflight()
        elif state == FSMState.PLANNING:
            return self._handle_planning()
        elif state == FSMState.IMPLEMENTATION:
            return self._handle_implementation()
        elif state == FSMState.VERIFICATION:
            return self._handle_verification()
        elif state == FSMState.RESOLUTION:
            return self._handle_resolution()
        elif state == FSMState.REVIEW:
            return self._handle_review()
        elif state == FSMState.BLOCKED:
            return self._handle_blocked()
        elif state == FSMState.AMBIGUOUS:
            return self._handle_ambiguous()
        elif state == FSMState.COMPLETED:
            return self._handle_completed()
        elif state == FSMState.FAILED:
            return self._handle_failed()
        elif state == FSMState.ABORTED:
            return self._handle_aborted()
        return PipelineEvent(
            event_type=EventType.CRITICAL_ERROR,
            source_phase=state,
            error_message=f"Unknown state: {state}",
        )

    # =========================================================================
    # State Handlers
    # =========================================================================

    def _handle_init(self) -> PipelineEvent:
        """Initialize workspace, detect adapter, and configure VCS."""
        try:
            self.context.adapter = detect_adapter(self.workspace_path)
            if self.profile.enable_git_commit:
                try:
                    self.context.git_ops = GitOps(self.workspace_path)
                    self.context.git_ops.init_repo()
                except Exception:
                    self.context.git_ops = None
            return PipelineEvent(
                event_type=EventType.START_TASK, source_phase=FSMState.INIT
            )
        except Exception as e:
            return PipelineEvent(
                event_type=EventType.CRITICAL_ERROR,
                source_phase=FSMState.INIT,
                error_message=str(e),
            )

    def _handle_preflight(self) -> PipelineEvent:
        """Run zero-token static syntax and importability compilation."""
        is_clean, err_msg = PreFlightGuard.check_syntax(
            self.workspace_path, auto_heal=True
        )
        if not is_clean:
            return PipelineEvent(
                event_type=EventType.PREFLIGHT_FAILED,
                source_phase=FSMState.PREFLIGHT,
                error_message=err_msg,
            )

        import_ok, import_err = PreFlightGuard.check_importability(
            self.workspace_path
        )
        if not import_ok:
            return PipelineEvent(
                event_type=EventType.PREFLIGHT_FAILED,
                source_phase=FSMState.PREFLIGHT,
                error_message=import_err,
            )

        return PipelineEvent(
            event_type=EventType.PREFLIGHT_PASSED,
            source_phase=FSMState.PREFLIGHT,
        )

    def _handle_planning(self) -> PipelineEvent:
        """Execute Architect agent turn to generate requirements and Milestone DAG."""
        if not self.profile.enable_planning:
            # Synthetic single milestone if planning is disabled in profile
            self.context.milestone_dag = [
                SubtaskMilestone(
                    index=1,
                    title="Direct Implementation",
                    content=self.context.task_description,
                )
            ]
            return PipelineEvent(
                event_type=EventType.PLAN_GENERATED,
                source_phase=FSMState.PLANNING,
            )

        # If planning is enabled, invoke Architect agent or parse PLAN.md
        plan_file = self.workspace_path / "PLAN.md"
        plan_content = ""
        if plan_file.exists():
            plan_content = plan_file.read_text(encoding="utf-8")

        allocated_turns = self.profile.default_agent_turn_limit
        if self.governor:
            turn_res = self.governor.pre_dispatch_allocate(
                phase=ResourcePhase.PLANNING,
                acceptance_criteria_count=1,
            )
            allocated_turns = turn_res.allocated_turns
            if self.governor.is_tripped:
                return PipelineEvent(
                    event_type=EventType.HUMAN_INTERVENTION_REQUIRED,
                    source_phase=FSMState.PLANNING,
                    error_message=f"Monetary/Resource circuit breaker tripped: {self.governor.status.trip_reason}",
                )

        if not plan_content and self.runtime_bridge and self.llm_manager:
            prompt = (
                f"Decompose the following task into discrete milestones and acceptance criteria:\n\n"
                f"{self.context.task_description}\n\n"
                f"Write your formal architectural breakdown to PLAN.md."
            )
            outcome = self.runtime_bridge.execute_bounded_turn(
                role_name="architect",
                workspace_path=self.workspace_path,
                prompt_view=PromptView(compiled_prompt=prompt),
                turn_envelope=TurnEnvelope(
                    max_turns=allocated_turns
                ),
                sandbox_manager=self.sandbox_manager,
            )
            self._accumulate_outcome(outcome, phase=ResourcePhase.PLANNING)
            if outcome and outcome.exit_reason == AgentExitReason.FATAL_ERROR:
                return PipelineEvent(
                    event_type=EventType.CRITICAL_ERROR,
                    source_phase=FSMState.PLANNING,
                    error_message=outcome.error_message or "Architect turn failed with fatal error.",
                )
            if plan_file.exists():
                plan_content = plan_file.read_text(encoding="utf-8")

        if plan_content:
            milestones = MilestoneParser.parse_plan(plan_content)
            self.context.milestone_dag = milestones
            self.context.metadata["plan_text"] = plan_content
            return PipelineEvent(
                event_type=EventType.PLAN_GENERATED,
                source_phase=FSMState.PLANNING,
            )

        # Fallback to direct milestone
        self.context.milestone_dag = [
            SubtaskMilestone(
                index=1,
                title="Task Implementation",
                content=self.context.task_description,
            )
        ]
        return PipelineEvent(
            event_type=EventType.PLAN_GENERATED,
            source_phase=FSMState.PLANNING,
        )

    def _handle_implementation(self) -> PipelineEvent:
        """Execute Developer, Auditor, or Fixer agent turn within bounded turn envelope."""
        role_name = "developer"
        if self.profile.mode == PipelineMode.AUDIT:
            role_name = "auditor"
        elif self.profile.mode == PipelineMode.DOCS:
            role_name = "developer"

        # Select active milestone
        active_ms = None
        if self.context.milestone_dag:
            idx = min(
                self.context.active_milestone_index,
                len(self.context.milestone_dag) - 1,
            )
            active_ms = self.context.milestone_dag[idx]
            self.context.active_milestone_id = str(active_ms.index)

        # Build Prompt
        prompt_lines = [
            f"# Task Objective:\n{self.context.task_description}\n",
        ]
        if self.profile.mode == PipelineMode.AUDIT:
            prompt_lines.append(
                "STRICT 2-PHASE AUDIT WORKFLOW:\n"
                "1. Phase 1 (Inspection - Max 2-3 steps): Read key architectural files only.\n"
                "2. Phase 2 (Report Synthesis - MANDATORY): First, write the comprehensive, multi-section Markdown report to `docs/AUDIT_REPORT.md` (MUST include detailed findings, line numbers, and architectural analysis). Then write the structured JSON findings to `docs/audit_findings.json` using `workspace_file` with operation='write'.\n"
                "3. Conclude your turn immediately after writing both files. Do NOT get stuck in endless read loops."
            )
        elif active_ms:
            prompt_lines.append(
                f"## Active Milestone ({active_ms.title}):\n{active_ms.content}\n"
            )

        # If recovering from failure, inject failure diagnostics
        if self.context.last_verification_decision:
            d = self.context.last_verification_decision
            if d.failed_criteria or d.unsatisfied_requirements or d.violated_invariants:
                prompt_lines.append(
                    f"## Previous Verification Issues to Fix:\n"
                    f"- Unsatisfied: {', '.join(d.unsatisfied_requirements)}\n"
                    f"- Failed: {', '.join(d.failed_criteria)}\n"
                    f"- Invariants: {', '.join(d.violated_invariants)}\n"
                    f"- Required Actions: {', '.join(d.required_next_actions)}\n"
                )

        if self.context.last_test_result and not self.context.last_test_result.passed:
            prompt_lines.append(
                f"## Pytest Failure Diagnostics:\n{self.context.last_test_result.stdout or self.context.last_test_result.stderr}\n"
            )

        if self.context.metadata.get("governance_directive"):
            prompt_lines.append(
                f"## Strategic Directive from Governance Watchdog:\n"
                f"{self.context.metadata['governance_directive']}\n"
            )

        compiled_prompt = "\n".join(prompt_lines)

        allocated_turns = self.iteration_governor.allocate_initial_budget(
            task_description=self.context.task_description,
            role=role_name,
            mode=self.profile.mode.value if hasattr(self.profile.mode, "value") else str(self.profile.mode),
            workspace_path=self.workspace_path,
        )
        if self.governor:
            ac_count = len(self.context.milestone_dag) if self.context.milestone_dag else 1
            if self.context.task_truth_graph and hasattr(self.context.task_truth_graph, "acceptance_criteria"):
                ac_count = max(1, len(self.context.task_truth_graph.acceptance_criteria))
            dag_depth = max(1, len(self.context.milestone_dag))
            target_files = max(1, len(self.context.mutated_files))

            turn_res = self.governor.pre_dispatch_allocate(
                phase=ResourcePhase.IMPLEMENTATION,
                acceptance_criteria_count=ac_count,
                dag_depth=dag_depth,
                target_files_count=target_files,
            )
            allocated_turns = max(allocated_turns, turn_res.allocated_turns)
            if self.governor.is_tripped:
                return PipelineEvent(
                    event_type=EventType.HUMAN_INTERVENTION_REQUIRED,
                    source_phase=FSMState.IMPLEMENTATION,
                    error_message=f"Monetary/Resource circuit breaker tripped: {self.governor.status.trip_reason}",
                )

        outcome = None
        if self.runtime_bridge and self.llm_manager:
            outcome = self.runtime_bridge.execute_bounded_turn(
                role_name=role_name,
                workspace_path=self.workspace_path,
                prompt_view=PromptView(compiled_prompt=compiled_prompt),
                turn_envelope=TurnEnvelope(
                    max_turns=allocated_turns
                ),
                sandbox_manager=self.sandbox_manager,
                progress_monitor=self.iteration_governor.monitor,
            )
            self._accumulate_outcome(outcome, phase=ResourcePhase.IMPLEMENTATION)

            # Evaluate Governance outcome
            task_profile = self.iteration_governor.get_task_profile(
                task_description=self.context.task_description,
                role=role_name,
                mode=self.profile.mode.value if hasattr(self.profile.mode, "value") else str(self.profile.mode),
            )
            gov_decision = self.iteration_governor.evaluate_turn_yield(
                profile=task_profile,
                turns_used=outcome.iterations_executed if outcome else 0,
                turns_allocated=allocated_turns,
                completed_naturally=bool(outcome and outcome.completed_naturally),
                has_prior_mutations=bool(self.context.mutated_files),
            )
            self.context.metadata["governance_decision"] = gov_decision.model_dump()
            if gov_decision.recommended_directive:
                self.context.metadata["governance_directive"] = gov_decision.recommended_directive
        elif not self.llm_manager or not self.runtime_bridge:
            return PipelineEvent(
                event_type=EventType.CRITICAL_ERROR,
                source_phase=FSMState.IMPLEMENTATION,
                error_message="LLMManager or RuntimeBridge unavailable during implementation phase.",
            )

        if outcome and outcome.exit_reason == AgentExitReason.FATAL_ERROR:
            return PipelineEvent(
                event_type=EventType.CRITICAL_ERROR,
                source_phase=FSMState.IMPLEMENTATION,
                error_message=outcome.error_message or "Developer turn failed with fatal error.",
            )

        exec_outcome = AgentExecutionOutcome.NATURAL_COMPLETION
        if outcome and outcome.exit_reason:
            reason_name = outcome.exit_reason.name
            if hasattr(AgentExecutionOutcome, reason_name):
                exec_outcome = AgentExecutionOutcome[reason_name]

        return PipelineEvent(
            event_type=EventType.AGENT_YIELDED,
            source_phase=FSMState.IMPLEMENTATION,
            execution_outcome=exec_outcome,
            payload={"mutated_files": list(self.context.mutated_files)},
        )

    def _handle_verification(self) -> PipelineEvent:
        """Execute static checks, test suites, and P2.1 Task Truth evaluation."""
        # 1. Zero-token PreFlight syntax check
        preflight_ok, preflight_msg = PreFlightGuard.check_syntax(
            self.workspace_path, auto_heal=False
        )

        # 2. Run Test Suite if adapter available
        test_res = None
        if self.context.adapter:
            try:
                test_res = self.context.adapter.run_tests(self.workspace_path)
                self.context.last_test_result = test_res
            except Exception as ex:
                logger.warning(f"Test runner error: {ex}")

        # Check if previous agent turn was incomplete or hit iteration limit
        last_outcome = self.context.last_outcome
        agent_incomplete = (
            last_outcome is not None
            and (
                not last_outcome.completed_naturally
                or last_outcome.exit_reason in (
                    AgentExitReason.STEP_LIMIT_REACHED,
                    AgentExitReason.TOKEN_LIMIT_REACHED,
                    AgentExitReason.AGENT_STUCK,
                    AgentExitReason.FATAL_ERROR,
                    AgentExitReason.TOOL_REJECTION,
                    AgentExitReason.ABORTED,
                )
            )
        )

        # 3. Evaluate Canonical Task Completion
        decision = evaluate_task_completion(
            self.context.task_truth_graph, self.workspace_path
        )

        # If no task_truth_graph is attached (e.g. dev-test mode), derive decision from tests & syntax
        if not self.context.task_truth_graph:
            has_more_milestones = (
                bool(self.context.milestone_dag)
                and self.context.active_milestone_index + 1 < len(self.context.milestone_dag)
            )

            gov_meta = self.context.metadata.get("governance_decision")
            gov_blocked = False
            gov_reason = ""
            if gov_meta and isinstance(gov_meta, dict):
                act = gov_meta.get("action")
                hlth = gov_meta.get("health")
                if act in ("FAIL", "PAUSE_BLOCK") or hlth in ("CHAOTIC", "STAGNANT", "EXHAUSTED", "CRITICAL_FAILURE"):
                    gov_blocked = True
                    gov_reason = str(gov_meta.get("reason") or "Governance watchdog detected unhealthy execution")

            if not preflight_ok:
                decision = CompletionDecision(
                    status=CompletionStatus.FAILED,
                    violated_invariants=[preflight_msg],
                    blocking_reasons=[f"Syntax Error: {preflight_msg}"],
                )
            elif agent_incomplete and last_outcome is not None:
                err_msg = (
                    last_outcome.error_message
                    or f"Agent reached iteration or resource limit ({last_outcome.exit_reason.value if hasattr(last_outcome.exit_reason, 'value') else last_outcome.exit_reason})."
                )
                decision = CompletionDecision(
                    status=CompletionStatus.FAILED,
                    failed_criteria=[
                        f"Developer agent did not complete naturally: {last_outcome.exit_reason.value if hasattr(last_outcome.exit_reason, 'value') else last_outcome.exit_reason}"
                    ],
                    blocking_reasons=[err_msg],
                )
            elif gov_blocked:
                decision = CompletionDecision(
                    status=CompletionStatus.FAILED,
                    failed_criteria=[f"Iteration Governance Blocked: {gov_reason}"],
                    blocking_reasons=[gov_reason],
                )
            elif test_res and not test_res.passed:
                err_detail = ""
                if hasattr(test_res, "summary") and isinstance(test_res.summary, str) and test_res.summary:
                    err_detail = test_res.summary
                elif hasattr(test_res, "failure_details") and isinstance(test_res.failure_details, str) and test_res.failure_details:
                    err_detail = test_res.failure_details
                elif hasattr(test_res, "stderr") and isinstance(test_res.stderr, str) and test_res.stderr:
                    err_detail = test_res.stderr
                elif hasattr(test_res, "raw_stderr") and isinstance(test_res.raw_stderr, str) and test_res.raw_stderr:
                    err_detail = test_res.raw_stderr
                else:
                    err_detail = "Tests failed"

                decision = CompletionDecision(
                    status=CompletionStatus.FAILED,
                    failed_criteria=["Pytest execution failed"],
                    blocking_reasons=[str(err_detail)],
                )
            elif has_more_milestones:
                active_ms_label = self.context.active_milestone_id or str(self.context.active_milestone_index + 1)
                decision = CompletionDecision(
                    status=CompletionStatus.INCOMPLETE,
                    satisfied_requirements=[f"Milestone {active_ms_label} verified clean"],
                    blocking_reasons=[f"Milestone {active_ms_label} completed; subsequent milestones pending"],
                )
            elif test_res and test_res.passed:
                decision = CompletionDecision(
                    status=CompletionStatus.COMPLETE,
                    satisfied_requirements=["Task Execution", "All Tests Passed"],
                )
            elif self.profile.mode in (PipelineMode.AUDIT, PipelineMode.DOCS) and self.context.mutated_files:
                # If audit mode wrote audit_findings.json but AUDIT_REPORT.md is missing/empty, auto-render report from findings
                if self.profile.mode == PipelineMode.AUDIT:
                    findings_json = self.workspace_path / "docs" / "audit_findings.json"
                    report_md = self.workspace_path / "docs" / "AUDIT_REPORT.md"
                    if findings_json.exists() and (not report_md.exists() or report_md.stat().st_size == 0):
                        try:
                            from orchestrator.analysis.schemas import AuditResult
                            loaded = AuditResult.load_json(findings_json)
                            if loaded and loaded.findings:
                                lines = [
                                    "# ORAGAI Codebase Architecture & Security Audit Report",
                                    "",
                                    "## 1. Executive Summary",
                                    f"- **Status:** {loaded.status}",
                                    f"- **Total Findings:** {len(loaded.findings)}",
                                    "",
                                    "## 2. Actionable Findings & Defects",
                                    "",
                                    "| ID | Severity | Type | Target File | Problem Statement | Recommended Fix |",
                                    "| :--- | :--- | :--- | :--- | :--- | :--- |",
                                ]
                                for f in loaded.findings:
                                    f_id = getattr(f, "id", "") or "AUD"
                                    f_sev = getattr(f, "severity", "") or "MEDIUM"
                                    f_type = getattr(f, "type", "") or "DEFECT"
                                    f_file = getattr(f, "file", "") or "unknown"
                                    f_prob = str(getattr(f, "problem", "")).replace("|", "\\|")
                                    f_fix = str(getattr(f, "recommended_fix", "")).replace("|", "\\|")
                                    lines.append(f"| **{f_id}** | {f_sev} | {f_type} | `{f_file}` | {f_prob} | {f_fix} |")
                                lines.append("")
                                report_md.write_text("\n".join(lines), encoding="utf-8")
                        except Exception as e:
                            logger.warning(f"Could not synthesize markdown report from findings: {e}")

                decision = CompletionDecision(
                    status=CompletionStatus.COMPLETE,
                    satisfied_requirements=["Syntax clean", f"{self.profile.mode.value} execution verified"],
                )
            else:
                decision = CompletionDecision(
                    status=CompletionStatus.INCOMPLETE,
                    blocking_reasons=["No test results or verification evidence produced for completion."],
                )
        elif agent_incomplete and last_outcome is not None:
            err_msg = (
                last_outcome.error_message
                or f"Agent reached iteration or resource limit ({last_outcome.exit_reason.value if hasattr(last_outcome.exit_reason, 'value') else last_outcome.exit_reason})."
            )
            decision = CompletionDecision(
                status=CompletionStatus.FAILED,
                failed_criteria=[
                    f"Developer agent did not complete naturally: {last_outcome.exit_reason.value if hasattr(last_outcome.exit_reason, 'value') else last_outcome.exit_reason}"
                ],
                blocking_reasons=[err_msg],
            )

        self.context.last_verification_decision = decision

        # 4. Check Workspace SHA-256 Stagnation
        current_hash = FSMCheckpointManager.compute_workspace_hash(
            self.workspace_path
        )
        self.context.current_workspace_hash = current_hash
        if self.context.last_workspace_hash == current_hash and not decision.is_complete:
            self.context.stagnation_counter += 1
        else:
            self.context.stagnation_counter = 0
        self.context.last_workspace_hash = current_hash

        return PipelineEvent(
            event_type=EventType.VERIFICATION_COMPLETED,
            source_phase=FSMState.VERIFICATION,
            payload={"decision": decision},
        )

    def _handle_resolution(self) -> PipelineEvent:
        """Triage verification failure, increment retries, and route remediation."""
        self.context.iteration_count += 1
        self.context.total_iterations += 1
        max_fix = self.profile.max_fix_iterations
        max_total = getattr(self.profile, "max_total_iterations", 25)

        if self.context.total_iterations >= max_total:
            return PipelineEvent(
                event_type=EventType.RETRIES_EXHAUSTED,
                source_phase=FSMState.RESOLUTION,
                error_message=f"Global iteration ceiling ({max_total}) exhausted across milestones.",
            )

        if self.context.iteration_count >= max_fix:
            return PipelineEvent(
                event_type=EventType.RETRIES_EXHAUSTED,
                source_phase=FSMState.RESOLUTION,
            )

        if self.context.stagnation_counter >= getattr(
            self.config, "circuit_breaker_threshold", 2
        ):
            return PipelineEvent(
                event_type=EventType.STAGNATION_DETECTED,
                source_phase=FSMState.RESOLUTION,
            )

        decision = self.context.last_verification_decision
        if decision and decision.status == CompletionStatus.AMBIGUOUS:
            return PipelineEvent(
                event_type=EventType.REPLAN_TRIGGERED,
                source_phase=FSMState.RESOLUTION,
            )

        return PipelineEvent(
            event_type=EventType.REMEDIATION_ROUTED,
            source_phase=FSMState.RESOLUTION,
        )

    def _handle_review(self) -> PipelineEvent:
        """Run Reviewer agent assessment or validate verdict."""
        if not self.profile.enable_review:
            return PipelineEvent(
                event_type=EventType.REVIEW_APPROVED,
                source_phase=FSMState.REVIEW,
            )

        allocated_turns = 5
        if self.governor:
            turn_res = self.governor.pre_dispatch_allocate(
                phase=ResourcePhase.REVIEW,
                acceptance_criteria_count=max(1, len(self.context.milestone_dag)),
            )
            allocated_turns = turn_res.allocated_turns
            if self.governor.is_tripped:
                return PipelineEvent(
                    event_type=EventType.HUMAN_INTERVENTION_REQUIRED,
                    source_phase=FSMState.REVIEW,
                    error_message=f"Monetary/Resource circuit breaker tripped: {self.governor.status.trip_reason}",
                )

        verdict = ReviewerVerdict(approved=True, verdict="APPROVED")
        if self.runtime_bridge and self.llm_manager:
            prompt = (
                f"Review the code modifications for task: {self.context.task_description}\n"
                f"Output your verdict as ```json {{ \"verdict\": \"APPROVED\" }} ```"
            )
            outcome = self.runtime_bridge.execute_bounded_turn(
                role_name="reviewer",
                workspace_path=self.workspace_path,
                prompt_view=PromptView(compiled_prompt=prompt),
                turn_envelope=TurnEnvelope(max_turns=allocated_turns),
                sandbox_manager=self.sandbox_manager,
            )
            self._accumulate_outcome(outcome, phase=ResourcePhase.REVIEW)
            if outcome and outcome.exit_reason == AgentExitReason.FATAL_ERROR:
                return PipelineEvent(
                    event_type=EventType.CRITICAL_ERROR,
                    source_phase=FSMState.REVIEW,
                    error_message=outcome.error_message or "Reviewer turn failed with fatal error.",
                )
            verdict = ReviewerVerdict.parse(outcome.final_thought or "APPROVED")

        self.context.review_verdict = verdict
        if verdict.approved:
            return PipelineEvent(
                event_type=EventType.REVIEW_APPROVED,
                source_phase=FSMState.REVIEW,
            )
        return PipelineEvent(
            event_type=EventType.REVIEW_REJECTED,
            source_phase=FSMState.REVIEW,
            error_message="Reviewer requested revisions.",
        )

    def _handle_completed(self) -> PipelineEvent:
        """Perform atomic commit and cleanup on successful completion."""
        if self.profile.enable_git_commit and self.context.git_ops:
            try:
                self.context.git_ops.commit_all(
                    f"feat: completed task '{self.context.task_description[:50]}'"
                )
            except Exception:
                pass
        FSMCheckpointManager.clear_checkpoint(self.workspace_path)
        return PipelineEvent(
            event_type=EventType.VERIFICATION_COMPLETED, source_phase=FSMState.COMPLETED
        )

    def _handle_failed(self) -> PipelineEvent:
        """Handle terminal failure."""
        return PipelineEvent(
            event_type=EventType.CRITICAL_ERROR, source_phase=FSMState.FAILED
        )

    def _handle_blocked(self) -> PipelineEvent:
        """Handle blocked execution."""
        return PipelineEvent(
            event_type=EventType.HUMAN_INTERVENTION_REQUIRED, source_phase=FSMState.BLOCKED
        )

    def _handle_ambiguous(self) -> PipelineEvent:
        """Handle ambiguous requirements."""
        return PipelineEvent(
            event_type=EventType.REPLAN_TRIGGERED, source_phase=FSMState.AMBIGUOUS
        )

    def _handle_aborted(self) -> PipelineEvent:
        """Handle user abort."""
        return PipelineEvent(
            event_type=EventType.ABORT_REQUESTED, source_phase=FSMState.ABORTED
        )

    # =========================================================================
    # Helpers & Checkpointing
    # =========================================================================

    def _accumulate_outcome(
        self,
        outcome: BridgeAgentOutcome,
        phase: ResourcePhase = ResourcePhase.IMPLEMENTATION,
    ) -> None:
        """Record telemetry and mutated files from an agent turn."""
        self.context.last_outcome = outcome
        self.context.total_tokens_consumed += outcome.total_tokens
        self.context.total_cost_usd += outcome.cost_usd
        for f in outcome.mutated_files:
            self.context.mutated_files.add(f)

        if self.governor:
            made_progress = (
                bool(outcome.mutated_files)
                or phase in (ResourcePhase.PLANNING, ResourcePhase.REVIEW, ResourcePhase.AUDIT)
                or getattr(outcome, "completed_naturally", False)
                or getattr(outcome, "exit_reason", None) == AgentExitReason.NATURAL_COMPLETION
            )
            self.governor.post_yield_record(
                phase=phase,
                cost_usd=outcome.cost_usd,
                tokens_consumed=outcome.total_tokens,
                turns_used=outcome.iterations_executed or 1,
                made_meaningful_progress=made_progress,
            )

    def _resume_from_checkpoint(self, checkpoint: Any) -> None:
        """Restore FSMContext from a serialized FSMCheckpoint."""
        self.context.run_id = checkpoint.run_id
        self.context.iteration_count = checkpoint.iteration_count
        self.context.total_iterations = getattr(checkpoint, "total_iterations", checkpoint.iteration_count)
        self.context.total_tokens_consumed = checkpoint.total_tokens_consumed
        self.context.total_cost_usd = checkpoint.total_cost_usd
        self.context.metadata = checkpoint.metadata or {}

        try:
            target_st = FSMState(checkpoint.current_state)
            if target_st in (FSMState.FAILED, FSMState.ABORTED):
                # When resuming after failure or abort, reset to a runnable state for retry/recovery
                if checkpoint.milestones:
                    target_st = FSMState.IMPLEMENTATION
                elif getattr(self.profile, "enable_planning", False):
                    target_st = FSMState.PLANNING
                else:
                    target_st = FSMState.PREFLIGHT
                logger.info(
                    f"Resuming failed/aborted checkpoint: resetting state from {checkpoint.current_state} to {target_st.value} for recovery attempt."
                )
            self.context.current_state = target_st
            self.context.state_history = [
                FSMState(s) for s in checkpoint.state_history
            ]
            if not self.context.state_history or self.context.state_history[-1] != target_st:
                self.context.state_history.append(target_st)
        except Exception:
            self.context.current_state = FSMState.INIT

        logger.info(
            f"Resumed GuardedFSMEngine from checkpoint at state: {self.context.current_state}"
        )

    def _finalize_run_result(self) -> Dict[str, Any]:
        """Synthesize final execution dictionary."""
        is_success = self.context.current_state == FSMState.COMPLETED
        is_blocked = self.context.current_state in (FSMState.BLOCKED, FSMState.AMBIGUOUS)
        is_timed_out = bool(self.context.metadata.get("timed_out", False))
        error_msg = None
        if self.context.metadata.get("blocking_reason"):
            error_msg = self.context.metadata["blocking_reason"]
        elif (
            self.context.last_verification_decision
            and self.context.last_verification_decision.blocking_reasons
        ):
            error_msg = self.context.last_verification_decision.blocking_reasons[0]

        return {
            "success": is_success,
            "blocked": is_blocked,
            "timed_out": is_timed_out,
            "status": self.context.current_state.value,
            "run_id": self.context.run_id,
            "iterations": self.context.iteration_count,
            "state_history": [s.value for s in self.context.state_history],
            "tokens_consumed": self.context.total_tokens_consumed,
            "cost_usd": self.context.total_cost_usd,
            "mutated_files": list(self.context.mutated_files),
            "error_message": error_msg,
        }
