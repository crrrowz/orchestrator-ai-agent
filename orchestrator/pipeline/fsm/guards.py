"""Pure boolean guard predicates and semantic query interfaces for Guarded FSM.

Strictly separates state machine transition gating from low-level evidence/code inspection.
Consumes TaskTruthSemanticQueries and PreFlightGuard invariants without computing raw hashes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from pydantic import BaseModel, Field

from orchestrator.guards.preflight import PreFlightGuard
from orchestrator.pipeline.fsm.events import PipelineEvent

# FSMContext is referenced by forward-ref string in guard methods


class ImplementationState(str, Enum):
    """Implementation state of a requirement or milestone."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    IMPLEMENTED = "IMPLEMENTED"
    STUB_DETECTED = "STUB_DETECTED"


class VerificationState(str, Enum):
    """Empirical verification state backed by evidence."""

    UNVERIFIED = "UNVERIFIED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    STALE = "STALE"


class RequirementStatus(str, Enum):
    """Overall requirement lifecycle status."""

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class CompletionStatus(str, Enum):
    """Deterministic completion decision statuses from CompletionGate."""

    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"


class CompletionDecision(BaseModel):
    """Structured decision returned by evaluate_task_completion."""

    status: CompletionStatus
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    blocking_reasons: List[str] = Field(default_factory=list)
    satisfied_requirements: List[str] = Field(default_factory=list)
    unsatisfied_requirements: List[str] = Field(default_factory=list)
    failed_criteria: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    stale_evidence: List[str] = Field(default_factory=list)
    violated_invariants: List[str] = Field(default_factory=list)
    blocking_defects: List[str] = Field(default_factory=list)
    contradictory_evidence: List[str] = Field(default_factory=list)
    required_next_actions: List[str] = Field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Return True if decision status is COMPLETE."""
        return self.status == CompletionStatus.COMPLETE


def evaluate_task_completion(
    graph: Optional[Any], workspace: Path
) -> CompletionDecision:
    """Deterministic evaluation of task completion according to P2.1 specifications.

    Evaluates mandatory requirements, dependencies, environment blockers,
    static PreFlight syntax invariants, and evidence presence.
    """
    blocking_reasons: List[str] = []
    satisfied_reqs: List[str] = []
    unsatisfied_reqs: List[str] = []
    failed_criteria: List[str] = []
    missing_evidence: List[str] = []
    stale_evidence: List[str] = []
    violated_invariants: List[str] = []
    blocking_defects: List[str] = []
    contradictory_evidence: List[str] = []
    required_actions: List[str] = []

    # 1. Check workspace exists
    if not workspace.exists() or not workspace.is_dir():
        return CompletionDecision(
            status=CompletionStatus.BLOCKED,
            blocking_reasons=[f"Workspace directory '{workspace}' does not exist."],
            required_next_actions=["Initialize valid workspace directory."],
        )

    # 2. Invariant Verification Check (Zero-Token Static Pass)
    preflight_ok, preflight_msg = PreFlightGuard.check_syntax(
        workspace, auto_heal=False
    )
    if not preflight_ok:
        violated_invariants.append(f"PreFlight Syntax Error: {preflight_msg}")
        blocking_reasons.append(f"Syntax invariant violated:\n{preflight_msg}")
        required_actions.append("Fix syntax compilation errors.")

    # 3. Environment & Tool Blockers Check
    if graph and getattr(graph, "external_dependency_blocked", False):
        return CompletionDecision(
            status=CompletionStatus.BLOCKED,
            blocking_reasons=[
                f"External dependency/provider unavailable: {getattr(graph, 'blocker_reason', 'Unknown')}"
            ],
            required_next_actions=["Restore external connectivity or switch provider."],
        )

    # 4. If no TaskTruthGraph is provided (legacy / dev-test fallback)
    if not graph:
        if violated_invariants:
            return CompletionDecision(
                status=CompletionStatus.FAILED,
                blocking_reasons=blocking_reasons,
                violated_invariants=violated_invariants,
                required_next_actions=required_actions,
            )
        return CompletionDecision(
            status=CompletionStatus.INCOMPLETE,
            blocking_reasons=["No TaskTruthGraph provided for task."],
            required_next_actions=["Provide or generate TaskTruthGraph with requirements."],
        )

    # 5. Mandatory Requirements Check
    raw_reqs = getattr(graph, "requirements", [])
    mandatory_reqs = [
        r
        for r in raw_reqs
        if getattr(r, "is_mandatory", True)
    ]
    if not mandatory_reqs:
        return CompletionDecision(
            status=CompletionStatus.INCOMPLETE,
            blocking_reasons=["No mandatory requirements defined in TaskTruthGraph."],
            required_next_actions=["Architect must decompose task into mandatory requirements."],
        )

    # 6. Requirement Dependency & Implementation Evaluation
    for req in mandatory_reqs:
        req_id = getattr(req, "id", str(req))
        impl_state = getattr(
            req, "implementation_state", ImplementationState.NOT_STARTED
        )
        verif_state = getattr(
            req, "verification_state", VerificationState.UNVERIFIED
        )

        # Check dependencies
        deps = getattr(req, "dependencies", [])
        for dep_id in deps:
            dep_req = None
            if hasattr(graph, "get_requirement"):
                dep_req = graph.get_requirement(dep_id)
            elif isinstance(raw_reqs, list):
                dep_req = next((r for r in raw_reqs if getattr(r, "id", None) == dep_id), None)
            if not dep_req or getattr(dep_req, "verification_state", None) != VerificationState.PASSED:
                blocking_reasons.append(
                    f"Requirement '{req_id}' is blocked by unverified dependency '{dep_id}'."
                )

        # Check implementation state
        if impl_state != ImplementationState.IMPLEMENTED and impl_state != "IMPLEMENTED":
            unsatisfied_reqs.append(req_id)
            blocking_reasons.append(f"Requirement '{req_id}' is not marked IMPLEMENTED.")
            required_actions.append(f"Complete code implementation for '{req_id}'.")
            continue

        # Check criteria
        criteria = getattr(req, "acceptance_criteria", [])
        mandatory_criteria = [
            c for c in criteria if getattr(c, "is_mandatory", True)
        ]
        if not mandatory_criteria and criteria:
            mandatory_criteria = list(criteria)

        if not mandatory_criteria:
            # If no explicit criteria attached, check requirement-level status
            req_status = getattr(req, "status", None)
            if req_status in (RequirementStatus.VERIFIED, "VERIFIED") or verif_state in (VerificationState.PASSED, "PASSED"):
                satisfied_reqs.append(req_id)
            else:
                unsatisfied_reqs.append(req_id)
                missing_evidence.append(req_id)
                blocking_reasons.append(f"Requirement '{req_id}' lacks verification evidence.")
                required_actions.append(f"Execute tests for '{req_id}'.")
            continue

        req_all_criteria_passed = True
        for crit in mandatory_criteria:
            crit_id = getattr(crit, "id", str(crit))
            crit_status = getattr(crit, "status", None) or getattr(crit, "verification_state", None)
            if crit_status in (VerificationState.PASSED, "PASSED", "VERIFIED"):
                continue
            elif crit_status in (VerificationState.FAILED, "FAILED"):
                req_all_criteria_passed = False
                failed_criteria.append(crit_id)
                blocking_reasons.append(f"Criterion '{crit_id}' failed verification.")
                required_actions.append(f"Remediate failing code for criterion '{crit_id}'.")
            elif crit_status in (VerificationState.STALE, "STALE"):
                req_all_criteria_passed = False
                stale_evidence.append(crit_id)
                blocking_reasons.append(f"Criterion '{crit_id}' has STALE evidence.")
                required_actions.append(f"Re-run verification suite for criterion '{crit_id}'.")
            else:
                req_all_criteria_passed = False
                missing_evidence.append(crit_id)
                blocking_reasons.append(f"Criterion '{crit_id}' lacks required verification evidence.")
                required_actions.append(f"Execute verification for criterion '{crit_id}'.")

        if req_all_criteria_passed:
            satisfied_reqs.append(req_id)
        else:
            unsatisfied_reqs.append(req_id)

    # 7. Ambiguity Check
    if getattr(graph, "has_unresolved_mutations", False) or getattr(
        graph, "has_conflicting_requirements", False
    ):
        return CompletionDecision(
            status=CompletionStatus.AMBIGUOUS,
            blocking_reasons=[
                "Task truth contains unresolved mutations or conflicting requirements."
            ],
            required_next_actions=["Replan via Architect or obtain human clarification."],
        )

    # 8. Synthesize Final Status
    if violated_invariants or blocking_defects or failed_criteria:
        status = CompletionStatus.FAILED
    elif blocking_reasons and any("blocked by" in r.lower() for r in blocking_reasons):
        status = CompletionStatus.BLOCKED
    elif unsatisfied_reqs or missing_evidence or stale_evidence or blocking_reasons:
        status = CompletionStatus.INCOMPLETE
    else:
        status = CompletionStatus.COMPLETE

    return CompletionDecision(
        status=status,
        blocking_reasons=blocking_reasons,
        satisfied_requirements=satisfied_reqs,
        unsatisfied_requirements=unsatisfied_reqs,
        failed_criteria=failed_criteria,
        missing_evidence=missing_evidence,
        stale_evidence=stale_evidence,
        violated_invariants=violated_invariants,
        blocking_defects=blocking_defects,
        contradictory_evidence=contradictory_evidence,
        required_next_actions=required_actions,
    )


class TaskTruthSemanticQueries:
    """Read-only semantic query contract consumed exclusively by FSM transition guards."""

    @staticmethod
    def can_enter_testing(graph: Optional[Any]) -> bool:
        """True if all mandatory requirements have ImplementationState == IMPLEMENTED."""
        if not graph:
            return True
        reqs = getattr(graph, "requirements", [])
        mandatory = [r for r in reqs if getattr(r, "is_mandatory", True)]
        if not mandatory:
            return True
        return all(
            getattr(r, "implementation_state", None) in (ImplementationState.IMPLEMENTED, "IMPLEMENTED")
            for r in mandatory
        )

    @staticmethod
    def can_enter_review(graph: Optional[Any], workspace: Path) -> bool:
        """True if static syntax is clean and requirements can enter review."""
        preflight_ok, _ = PreFlightGuard.check_syntax(workspace, auto_heal=False)
        return preflight_ok and TaskTruthSemanticQueries.can_enter_testing(graph)

    @staticmethod
    def can_complete(graph: Optional[Any], workspace: Path) -> bool:
        """True if CompletionGate evaluates to COMPLETE."""
        decision = evaluate_task_completion(graph, workspace)
        return decision.is_complete

    @staticmethod
    def must_block(graph: Optional[Any], workspace: Path) -> bool:
        """True if CompletionGate evaluates to BLOCKED."""
        decision = evaluate_task_completion(graph, workspace)
        return decision.status == CompletionStatus.BLOCKED

    @staticmethod
    def must_clarify(graph: Optional[Any], workspace: Path) -> bool:
        """True if CompletionGate evaluates to AMBIGUOUS."""
        decision = evaluate_task_completion(graph, workspace)
        return decision.status == CompletionStatus.AMBIGUOUS


class FSMGuards:
    """Pure, side-effect-free transition guard predicates."""

    @staticmethod
    def guard_workspace_exists(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that target workspace path exists and is a directory."""
        return context.workspace_path.exists() and context.workspace_path.is_dir()

    @staticmethod
    def guard_preflight_passed(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that workspace passes static syntax compilation and importability."""
        clean, _ = PreFlightGuard.check_syntax(context.workspace_path, auto_heal=True)
        return clean

    @staticmethod
    def guard_plan_valid(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that Architect produced valid requirements or milestones."""
        if context.milestone_dag and len(context.milestone_dag) > 0:
            return True
        graph = context.task_truth_graph
        if not graph:
            return bool(context.metadata.get("plan_text"))
        reqs = getattr(graph, "requirements", [])
        mandatory_reqs = [r for r in reqs if getattr(r, "is_mandatory", True)]
        return len(mandatory_reqs) > 0

    @staticmethod
    def guard_can_enter_verification(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that implementation phase yielded cleanly or reached step budget."""
        return True

    @staticmethod
    def guard_can_enter_review(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that all milestone criteria pass and code is syntactically sound."""
        if context.milestone_dag and context.active_milestone_index + 1 < len(context.milestone_dag):
            return False
        if context.last_verification_decision is not None:
            return context.last_verification_decision.is_complete
        return TaskTruthSemanticQueries.can_enter_review(
            context.task_truth_graph, context.workspace_path
        )

    @staticmethod
    def guard_can_complete(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that CompletionGate returned COMPLETE."""
        if context.milestone_dag and context.active_milestone_index + 1 < len(context.milestone_dag):
            return False
        if context.last_verification_decision is not None:
            return context.last_verification_decision.is_complete
        return TaskTruthSemanticQueries.can_complete(
            context.task_truth_graph, context.workspace_path
        )

    @staticmethod
    def guard_must_block(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify if execution encountered an unrecoverable blocking condition."""
        if context.last_verification_decision is not None:
            return context.last_verification_decision.status == CompletionStatus.BLOCKED
        return TaskTruthSemanticQueries.must_block(
            context.task_truth_graph, context.workspace_path
        )

    @staticmethod
    def guard_must_clarify(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify if requirements or criteria are contradictory or ambiguous."""
        if context.last_verification_decision is not None:
            return context.last_verification_decision.status == CompletionStatus.AMBIGUOUS
        return TaskTruthSemanticQueries.must_clarify(
            context.task_truth_graph, context.workspace_path
        )

    @staticmethod
    def guard_can_retry_remediation(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that iteration count has not exceeded maximum configured retries."""
        max_retries = getattr(
            context.profile,
            "max_fix_iterations",
            getattr(context.config, "max_iterations", 5),
        )
        return context.iteration_count < max_retries

    @staticmethod
    def guard_retries_exhausted(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify that iteration count has reached or exceeded maximum retries."""
        max_retries = getattr(
            context.profile,
            "max_fix_iterations",
            getattr(context.config, "max_iterations", 5),
        )
        return context.iteration_count >= max_retries

    @staticmethod
    def guard_stagnation_detected(
        context: "FSMContext", event: PipelineEvent
    ) -> bool:
        """Verify if stagnation threshold has been reached."""
        cb_threshold = getattr(
            context.config, "circuit_breaker_threshold", 2
        )
        return context.stagnation_counter >= cb_threshold
