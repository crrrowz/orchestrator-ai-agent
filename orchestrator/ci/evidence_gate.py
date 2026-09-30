"""Evidence Gate: Deterministic barrier preventing Developer Agent from modifying code on incomplete data."""

from typing import List, Optional
from orchestrator.ci.models import (
    EvidenceGateDecision,
    FailureCategory,
    FailureItem,
    RootCauseHypothesis,
    RootCauseStatus,
)


class EvidenceGate:
    """Enforces evidence sufficiency before delegating tasks to Developer / Code-writing agents."""

    @classmethod
    def evaluate(
        cls,
        failures: List[FailureItem],
        hypothesis: RootCauseHypothesis,
    ) -> EvidenceGateDecision:
        """Evaluate evidence integrity and decide whether to block Developer Agent."""
        blocking_failures = [f for f in failures if f.blocking]
        if not blocking_failures:
            return EvidenceGateDecision(
                can_proceed_to_developer=False,
                status="PASSED",
                reason="No blocking failures detected in CI run. Developer action not required.",
                required_evidence=[],
                actionable_failures=[],
            )

        # 1. If Root Cause status is explicitly INSUFFICIENT_EVIDENCE
        if hypothesis.status == RootCauseStatus.INSUFFICIENT_EVIDENCE:
            return EvidenceGateDecision(
                can_proceed_to_developer=False,
                status="BLOCKED",
                reason="Insufficient evidence to safely localize root cause or identify affected component.",
                required_evidence=hypothesis.required_additional_evidence or [
                    "pytest traceback",
                    "failed test name",
                ],
                actionable_failures=blocking_failures,
            )

        # 2. Check for missing affected component when test or lint failures exist
        has_test_or_lint = any(
            f.category in (FailureCategory.TEST_FAILURE, FailureCategory.LINT_FAILURE)
            for f in blocking_failures
        )
        if has_test_or_lint and not hypothesis.affected_component:
            return EvidenceGateDecision(
                can_proceed_to_developer=False,
                status="BLOCKED",
                reason="Failing component or source module could not be identified with certainty.",
                required_evidence=["failed test name", "traceback with file and line number"],
                actionable_failures=blocking_failures,
            )

        # 3. Check for runner/infrastructure/cache failure where code modification is invalid
        infra_only = all(
            f.category in (FailureCategory.INFRASTRUCTURE_FAILURE, FailureCategory.CACHE_FAILURE, FailureCategory.TIMEOUT)
            for f in blocking_failures
        )
        if infra_only:
            return EvidenceGateDecision(
                can_proceed_to_developer=False,
                status="BLOCKED",
                reason="Failures are infrastructure or environmental; code changes by Developer Agent would be speculative.",
                required_evidence=["CI runner logs", "workflow configuration inspection"],
                actionable_failures=blocking_failures,
            )

        # 4. Sufficient evidence confirmed!
        return EvidenceGateDecision(
            can_proceed_to_developer=True,
            status="PASSED",
            reason=f"Sufficient evidence available for {hypothesis.affected_component or 'identified failure'}.",
            required_evidence=[],
            actionable_failures=blocking_failures,
        )
