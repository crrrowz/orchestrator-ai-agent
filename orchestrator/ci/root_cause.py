"""Evidence-driven Root Cause Analyzer for CI pipelines."""

import re
from typing import List, Optional
from orchestrator.ci.models import (
    CorrelationPattern,
    FailureCategory,
    FailureItem,
    RootCauseHypothesis,
    RootCauseStatus,
)


class RootCauseAnalyzer:
    """Evaluates observed facts and correlation patterns against empirical evidence to assess root cause."""

    @classmethod
    def analyze(
        cls,
        failures: List[FailureItem],
        patterns: List[CorrelationPattern],
    ) -> RootCauseHypothesis:
        """Derive root cause hypothesis strictly guarded by empirical evidence sufficiency."""
        if not failures:
            return RootCauseHypothesis(
                status=RootCauseStatus.UNKNOWN,
                candidate_cause="No failures reported in workflow run.",
                confidence=1.0,
            )

        blocking_failures = [f for f in failures if f.blocking]
        if not blocking_failures:
            # Only non-blocking warnings/cache misses occurred
            candidate = "All recorded issues are non-blocking warnings or transient cache operations."
            return RootCauseHypothesis(
                status=RootCauseStatus.CONFIRMED,
                candidate_cause=candidate,
                supporting_evidence=[f.message for f in failures],
                confidence=0.95,
            )

        # 1. Inspect evidence depth of blocking failures
        primary = blocking_failures[0]
        evidence_text = f"{primary.raw_evidence}\n{primary.normalized_evidence}\n{primary.message}"

        # 2. Check for Pytest test failures
        if primary.category == FailureCategory.TEST_FAILURE:
            # Check if we have exact traceback or failed test name
            test_fail_match = re.search(r"FAILED\s+([^\s:]+\.py::[^\s]+)", evidence_text)
            tb_match = re.search(r"Traceback \(most recent call last\):", evidence_text)
            assertion_match = re.search(r"(AssertionError:[^\n]+)", evidence_text)

            if not (test_fail_match or (tb_match and assertion_match)):
                # We know pytest failed (e.g. exit code 1), but lack the actual traceback or failed test name
                return RootCauseHypothesis(
                    status=RootCauseStatus.INSUFFICIENT_EVIDENCE,
                    candidate_cause="Test runner exited with failure but specific traceback or failed test names are absent.",
                    supporting_evidence=[f"{primary.step}: {primary.message}"],
                    required_additional_evidence=[
                        "pytest traceback",
                        "failed test name",
                    ],
                    affected_component=None,
                    confidence=0.3,
                )

            # Traceback or failing test is present!
            failed_test = test_fail_match.group(1) if test_fail_match else ""
            assertion_msg = assertion_match.group(1) if assertion_match else ""
            supporting = [f"Failing test: {failed_test}"] if failed_test else []
            if assertion_msg:
                supporting.append(assertion_msg)

            # Check if correlation indicates an OS-specific pattern
            os_pattern = next((p for p in patterns if p.pattern_type == "OS_SPECIFIC"), None)
            candidate_cause = (
                f"Test failure in {failed_test or 'test suite'} (Environment: {primary.environment.display_name()})."
            )
            if os_pattern:
                candidate_cause += f" Note: Correlated with OS-specific pattern on {', '.join(os_pattern.affected_environments)}."

            affected_comp = failed_test.split("::")[0] if failed_test else None
            return RootCauseHypothesis(
                status=RootCauseStatus.CONFIRMED if assertion_msg else RootCauseStatus.LIKELY,
                candidate_cause=candidate_cause,
                supporting_evidence=supporting or [primary.message],
                required_additional_evidence=[],
                affected_component=affected_comp,
                confidence=0.9 if assertion_msg else 0.75,
            )

        # 3. Check for Lint / Ruff failures
        if primary.category == FailureCategory.LINT_FAILURE:
            file_match = re.search(r"([a-zA-Z0-9_\-/\\]+\.py):\d+:\d+:\s+([A-Z0-9]+)\s+(.+)", evidence_text)
            if file_match:
                fpath, code, msg = file_match.groups()
                return RootCauseHypothesis(
                    status=RootCauseStatus.CONFIRMED,
                    candidate_cause=f"Linter rule violation {code} in {fpath}: {msg}",
                    supporting_evidence=[file_match.group(0)],
                    affected_component=fpath,
                    confidence=1.0,
                )
            return RootCauseHypothesis(
                status=RootCauseStatus.LIKELY,
                candidate_cause="Linter reported errors across codebase.",
                supporting_evidence=[primary.message],
                confidence=0.8,
            )

        # 4. Dependency resolution failure
        if primary.category == FailureCategory.DEPENDENCY_FAILURE:
            dep_match = re.search(r"No matching distribution found for\s+([a-zA-Z0-9_\-]+)", evidence_text)
            package_name = dep_match.group(1) if dep_match else None
            return RootCauseHypothesis(
                status=RootCauseStatus.CONFIRMED if package_name else RootCauseStatus.LIKELY,
                candidate_cause=f"Dependency installation failed for {package_name or 'required packages'}.",
                supporting_evidence=[primary.message],
                affected_component="pyproject.toml" if package_name else None,
                confidence=0.95 if package_name else 0.7,
            )

        # 5. Environment failure (runner crash)
        if primary.category == FailureCategory.ENVIRONMENT_FAILURE:
            return RootCauseHypothesis(
                status=RootCauseStatus.LIKELY,
                candidate_cause=f"Runner/Environment crash: {primary.message}",
                supporting_evidence=[primary.message],
                confidence=0.85,
            )

        # 6. Default fallback
        return RootCauseHypothesis(
            status=RootCauseStatus.POSSIBLE,
            candidate_cause=f"Unverified candidate cause for {primary.category.value}: {primary.message}",
            supporting_evidence=[primary.message],
            required_additional_evidence=["detailed job execution logs"],
            confidence=0.4,
        )
