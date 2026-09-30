"""Deterministic Transition Matrix and Transition Rule definitions for Guarded FSM Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, List, Optional, Sequence

from orchestrator.pipeline.fsm.events import EventType, PipelineEvent
from orchestrator.pipeline.fsm.guards import CompletionStatus, FSMGuards
from orchestrator.pipeline.fsm.states import FSMState

# FSMContext is referenced by forward-ref string in transition callables


GuardCallable = Callable[["FSMContext", PipelineEvent], bool]
ActionCallable = Callable[["FSMContext", PipelineEvent], None]


@dataclass
class TransitionRule:
    """Deterministic rule governing a single permissible state transition."""

    source_state: FSMState
    trigger_event: EventType
    target_state: FSMState
    guard: Optional[GuardCallable] = None
    on_entry: Optional[ActionCallable] = None
    on_exit: Optional[ActionCallable] = None
    description: str = ""


@dataclass
class TransitionResult:
    """Outcome of attempting a state transition via the Guarded FSM Engine."""

    success: bool
    current_state: FSMState
    target_state: Optional[FSMState] = None
    previous_state: Optional[FSMState] = None
    rejection_reason: Optional[str] = None
    transition_rule: Optional[TransitionRule] = None


class TransitionMatrix:
    """Deterministic registry of transition rules governing state progression."""

    def __init__(self, rules: Optional[Sequence[TransitionRule]] = None) -> None:
        self._rules: List[TransitionRule] = list(rules or [])

    def add_rule(self, rule: TransitionRule) -> None:
        """Register a transition rule."""
        self._rules.append(rule)

    def get_matching_rule(
        self,
        current_state: FSMState,
        event: PipelineEvent,
        context: "FSMContext",
    ) -> Optional[TransitionRule]:
        """Find the first matching rule whose source, trigger, and guard match."""
        # 1. Check state-specific rules
        for rule in self._rules:
            if rule.source_state == current_state and rule.trigger_event == event.event_type:
                if rule.guard is None or rule.guard(context, event):
                    return rule

        # 2. Check universal wildcard rules (e.g. ABORT_REQUESTED from any state)
        for rule in self._rules:
            if rule.source_state is None and rule.trigger_event == event.event_type:
                if rule.guard is None or rule.guard(context, event):
                    return rule

        return None

    def get_candidate_rules(
        self, current_state: FSMState, event_type: EventType
    ) -> List[TransitionRule]:
        """Return all rules registered for the given source state and trigger event."""
        return [
            r
            for r in self._rules
            if (r.source_state == current_state or r.source_state is None)
            and r.trigger_event == event_type
        ]

    @classmethod
    def build_default(cls) -> "TransitionMatrix":
        """Construct the canonical transition matrix specified in P3."""
        matrix = cls()

        # ==========================================
        # 1. INIT State Transitions
        # ==========================================
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.INIT,
                trigger_event=EventType.START_TASK,
                target_state=FSMState.PREFLIGHT,
                guard=FSMGuards.guard_workspace_exists,
                description="Initialize task and advance to preflight static checks.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.INIT,
                trigger_event=EventType.CRITICAL_ERROR,
                target_state=FSMState.FAILED,
                description="Critical error or initialization failure in INIT state.",
            )
        )

        # ==========================================
        # 2. PREFLIGHT State Transitions
        # ==========================================
        def guard_preflight_to_planning(ctx: "FSMContext", ev: PipelineEvent) -> bool:
            return FSMGuards.guard_preflight_passed(ctx, ev) and getattr(ctx.profile, "enable_planning", True)

        def guard_preflight_to_impl(ctx: "FSMContext", ev: PipelineEvent) -> bool:
            return FSMGuards.guard_preflight_passed(ctx, ev) and not getattr(ctx.profile, "enable_planning", True)

        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.PREFLIGHT,
                trigger_event=EventType.PREFLIGHT_PASSED,
                target_state=FSMState.PLANNING,
                guard=guard_preflight_to_planning,
                description="Preflight passed: proceed to architect planning.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.PREFLIGHT,
                trigger_event=EventType.PREFLIGHT_PASSED,
                target_state=FSMState.IMPLEMENTATION,
                guard=guard_preflight_to_impl,
                description="Preflight passed (planning disabled in profile): proceed directly to implementation.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.PREFLIGHT,
                trigger_event=EventType.PREFLIGHT_FAILED,
                target_state=FSMState.BLOCKED,
                guard=lambda ctx, ev: ev.payload.get("requires_human", False),
                description="Preflight failed due to missing human input/credentials.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.PREFLIGHT,
                trigger_event=EventType.PREFLIGHT_FAILED,
                target_state=FSMState.FAILED,
                guard=None,
                description="Preflight static checks failed unrecoverably.",
            )
        )

        # ==========================================
        # 3. PLANNING State Transitions
        # ==========================================
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.PLANNING,
                trigger_event=EventType.PLAN_GENERATED,
                target_state=FSMState.IMPLEMENTATION,
                guard=FSMGuards.guard_plan_valid,
                description="Architect plan validated: proceed to milestone implementation.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.PLANNING,
                trigger_event=EventType.PLAN_REJECTED,
                target_state=FSMState.PLANNING,
                guard=FSMGuards.guard_can_retry_remediation,
                description="Plan rejected: retry planning within budget.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.PLANNING,
                trigger_event=EventType.PLAN_REJECTED,
                target_state=FSMState.FAILED,
                guard=FSMGuards.guard_retries_exhausted,
                description="Plan rejected and retries exhausted.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.PLANNING,
                trigger_event=EventType.CRITICAL_ERROR,
                target_state=FSMState.FAILED,
                description="Critical error during planning.",
            )
        )

        # ==========================================
        # 4. IMPLEMENTATION State Transitions
        # ==========================================
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.IMPLEMENTATION,
                trigger_event=EventType.AGENT_YIELDED,
                target_state=FSMState.VERIFICATION,
                guard=FSMGuards.guard_can_enter_verification,
                description="Ephemeral agent turn yielded: advance to empirical verification.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.IMPLEMENTATION,
                trigger_event=EventType.CRITICAL_ERROR,
                target_state=FSMState.FAILED,
                description="Critical unrecoverable error during implementation.",
            )
        )

        # ==========================================
        # 5. VERIFICATION State Transitions
        # ==========================================
        def guard_verif_to_next_milestone(ctx: "FSMContext", ev: PipelineEvent) -> bool:
            decision = getattr(ctx, "last_verification_decision", None)
            if decision is None or decision.status in (
                CompletionStatus.FAILED,
                CompletionStatus.BLOCKED,
                CompletionStatus.AMBIGUOUS,
            ):
                return False
            return (
                bool(ctx.milestone_dag)
                and ctx.active_milestone_index + 1 < len(ctx.milestone_dag)
            )

        def action_advance_milestone(ctx: "FSMContext", ev: PipelineEvent) -> None:
            if ctx.milestone_dag and ctx.active_milestone_index < len(ctx.milestone_dag):
                ctx.milestone_dag[ctx.active_milestone_index].is_completed = True
            ctx.active_milestone_index += 1
            if ctx.active_milestone_index < len(ctx.milestone_dag):
                ctx.active_milestone_id = str(ctx.milestone_dag[ctx.active_milestone_index].index)
            ctx.iteration_count = 0
            ctx.stagnation_counter = 0

        def action_mark_final_milestone_completed(ctx: "FSMContext", ev: PipelineEvent) -> None:
            if ctx.milestone_dag and ctx.active_milestone_index < len(ctx.milestone_dag):
                ctx.milestone_dag[ctx.active_milestone_index].is_completed = True

        def guard_verif_to_review(ctx: "FSMContext", ev: PipelineEvent) -> bool:
            return FSMGuards.guard_can_complete(ctx, ev) and getattr(ctx.profile, "enable_review", True)

        def guard_verif_to_completed(ctx: "FSMContext", ev: PipelineEvent) -> bool:
            return FSMGuards.guard_can_complete(ctx, ev) and not getattr(ctx.profile, "enable_review", True)

        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.VERIFICATION,
                trigger_event=EventType.VERIFICATION_COMPLETED,
                target_state=FSMState.IMPLEMENTATION,
                guard=guard_verif_to_next_milestone,
                on_entry=action_advance_milestone,
                description="Milestone verified: advance to next milestone implementation.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.VERIFICATION,
                trigger_event=EventType.VERIFICATION_COMPLETED,
                target_state=FSMState.REVIEW,
                guard=guard_verif_to_review,
                on_entry=action_mark_final_milestone_completed,
                description="Verification passed: proceed to independent reviewer assessment.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.VERIFICATION,
                trigger_event=EventType.VERIFICATION_COMPLETED,
                target_state=FSMState.COMPLETED,
                guard=guard_verif_to_completed,
                on_entry=action_mark_final_milestone_completed,
                description="Verification passed (review disabled): mark task completed.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.VERIFICATION,
                trigger_event=EventType.VERIFICATION_COMPLETED,
                target_state=FSMState.BLOCKED,
                guard=FSMGuards.guard_must_block,
                description="Verification blocked on external dependency or environment.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.VERIFICATION,
                trigger_event=EventType.VERIFICATION_COMPLETED,
                target_state=FSMState.AMBIGUOUS,
                guard=FSMGuards.guard_must_clarify,
                description="Verification identified contradictory requirements.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.VERIFICATION,
                trigger_event=EventType.VERIFICATION_COMPLETED,
                target_state=FSMState.RESOLUTION,
                guard=None,
                description="Verification incomplete or failed: route to resolution for triage.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.VERIFICATION,
                trigger_event=EventType.CRITICAL_ERROR,
                target_state=FSMState.FAILED,
                description="Critical error during verification.",
            )
        )

        # ==========================================
        # 6. RESOLUTION State Transitions
        # ==========================================
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.RESOLUTION,
                trigger_event=EventType.REMEDIATION_ROUTED,
                target_state=FSMState.IMPLEMENTATION,
                guard=FSMGuards.guard_can_retry_remediation,
                description="Remediation vector computed: return to implementation with targeted fix.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.RESOLUTION,
                trigger_event=EventType.REPLAN_TRIGGERED,
                target_state=FSMState.PLANNING,
                description="Architectural conflict detected: trigger plan revision.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.RESOLUTION,
                trigger_event=EventType.STAGNATION_DETECTED,
                target_state=FSMState.FAILED,
                guard=FSMGuards.guard_stagnation_detected,
                description="Stagnation circuit breaker tripped: halt execution.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.RESOLUTION,
                trigger_event=EventType.RETRIES_EXHAUSTED,
                target_state=FSMState.FAILED,
                description="Retry limit reached without satisfying verification gates.",
            )
        )

        # ==========================================
        # 7. REVIEW State Transitions
        # ==========================================
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.REVIEW,
                trigger_event=EventType.REVIEW_APPROVED,
                target_state=FSMState.COMPLETED,
                description="Reviewer approved changes: advance to completed terminal state.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.REVIEW,
                trigger_event=EventType.REVIEW_REJECTED,
                target_state=FSMState.RESOLUTION,
                description="Reviewer requested changes: route to resolution triage.",
            )
        )

        # ==========================================
        # 8. BLOCKED & AMBIGUOUS State Transitions
        # ==========================================
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.BLOCKED,
                trigger_event=EventType.HUMAN_INPUT_RECEIVED,
                target_state=FSMState.PREFLIGHT,
                description="Human unblocked execution: restart preflight verification.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=FSMState.AMBIGUOUS,
                trigger_event=EventType.REPLAN_TRIGGERED,
                target_state=FSMState.PLANNING,
                description="Ambiguity resolved: re-enter planning phase.",
            )
        )

        # ==========================================
        # 9. Universal Interruption & Abort Rules
        # ==========================================
        matrix.add_rule(
            TransitionRule(
                source_state=None,  # Wildcard matches any state
                trigger_event=EventType.HUMAN_INTERVENTION_REQUIRED,
                target_state=FSMState.BLOCKED,
                description="Circuit breaker or human intervention halted execution to BLOCKED state.",
            )
        )
        matrix.add_rule(
            TransitionRule(
                source_state=None,  # Wildcard matches any state
                trigger_event=EventType.ABORT_REQUESTED,
                target_state=FSMState.ABORTED,
                description="User or controller requested immediate pipeline abort.",
            )
        )

        return matrix
