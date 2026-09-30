"""Deterministic Rule-Based Failure Classifier for CI pipelines."""

import re
from typing import List, Optional, Tuple
from orchestrator.ci.models import FailureCategory, Severity
from orchestrator.ci.normalizer import FailureNormalizer


class FailureClassifier:
    """Classifies CI errors deterministically into formal taxonomies."""

    # Rules map regex patterns -> (FailureCategory, Severity, is_blocking, description)
    DETERMINISTIC_RULES = [
        # 1. Cache Failures (non-blocking in most modern setups unless critical)
        (
            re.compile(r"cache service responded with (?:status |http )?400", re.IGNORECASE),
            FailureCategory.CACHE_FAILURE,
            Severity.WARNING,
            False,
            "Cache service responded with HTTP 400",
        ),
        (
            re.compile(r"failed to (?:restore|save) cache", re.IGNORECASE),
            FailureCategory.CACHE_FAILURE,
            Severity.WARNING,
            False,
            "Cache save or restore failed",
        ),
        (
            re.compile(r"setup-uv@.*cache.*error", re.IGNORECASE),
            FailureCategory.CACHE_FAILURE,
            Severity.WARNING,
            False,
            "Astral setup-uv cache operation error",
        ),

        # 2. Test Failures
        (
            re.compile(r"(?:pytest.*(?:exit code 1|failed)|===+ FAILURES ===+|FAILED tests/|Process completed with exit code [1-9]|exit code 1)", re.IGNORECASE),
            FailureCategory.TEST_FAILURE,
            Severity.ERROR,
            True,
            "pytest test suite execution failed",
        ),
        (
            re.compile(r"(?:AssertionError|Expected .* but got|assert .* ==)", re.IGNORECASE),
            FailureCategory.TEST_FAILURE,
            Severity.ERROR,
            True,
            "Assertion failure detected in test run",
        ),

        # 3. Lint / Style Failures
        (
            re.compile(r"(?:ruff check .* failed|Found \d+ errors?|ruff: error)", re.IGNORECASE),
            FailureCategory.LINT_FAILURE,
            Severity.ERROR,
            True,
            "Ruff linter detected formatting or code quality errors",
        ),
        (
            re.compile(r"(?:flake8|pylint|black --check).*failed", re.IGNORECASE),
            FailureCategory.LINT_FAILURE,
            Severity.ERROR,
            True,
            "Linter/formatter detected rule violations",
        ),

        # 4. Type Check Failures
        (
            re.compile(r"(?:mypy|pyright|tsc).*(?:error:|found \d+ errors?)", re.IGNORECASE),
            FailureCategory.TYPE_CHECK_FAILURE,
            Severity.ERROR,
            True,
            "Static type checker detected type violations",
        ),

        # 5. Dependency / Package Resolution
        (
            re.compile(r"(?:ResolutionImpossible|No matching distribution found|Could not find a version that satisfies the requirement)", re.IGNORECASE),
            FailureCategory.DEPENDENCY_FAILURE,
            Severity.ERROR,
            True,
            "Dependency solver failed to resolve package requirements",
        ),
        (
            re.compile(r"(?:uv pip compile|uv sync).*failed", re.IGNORECASE),
            FailureCategory.DEPENDENCY_FAILURE,
            Severity.ERROR,
            True,
            "uv package sync failed to resolve dependencies",
        ),

        # 6. Environment & Runner Crashes
        (
            re.compile(r"(?:uv trampoline failed to canonicalize script path|fatal error C1083|WinError 5|The system cannot find the path specified)", re.IGNORECASE),
            FailureCategory.ENVIRONMENT_FAILURE,
            Severity.ERROR,
            True,
            "Operating system environment runner crash or missing system path",
        ),
        (
            re.compile(r"(?:No module named ['\"][a-zA-Z0-9_\-]+['\"]|ModuleNotFoundError:)", re.IGNORECASE),
            FailureCategory.ENVIRONMENT_FAILURE,
            Severity.ERROR,
            True,
            "Python module missing from runtime environment",
        ),

        # 7. Network / Remote Resource Failures
        (
            re.compile(r"(?:ConnectionResetError|ConnectTimeout|RemoteDisconnected|curl: \(56\)|HTTP 502|HTTP 503|HTTP 504)", re.IGNORECASE),
            FailureCategory.NETWORK_FAILURE,
            Severity.ERROR,
            True,
            "Network connectivity or remote server unavailability",
        ),

        # 8. Permissions / Authentication
        (
            re.compile(r"(?:Permission denied|HTTP 401|HTTP 403|Unauthorized|Forbidden|git-upload-pack: not found)", re.IGNORECASE),
            FailureCategory.PERMISSION_FAILURE,
            Severity.ERROR,
            True,
            "Permission or access credentials denied",
        ),

        # 9. Timeouts
        (
            re.compile(r"(?:The job running on runner .* has exceeded the maximum execution time|timed out after \d+)", re.IGNORECASE),
            FailureCategory.TIMEOUT,
            Severity.ERROR,
            True,
            "Execution timeout exceeded threshold",
        ),

        # 10. Toolchain & Deprecation Warnings (Non-blocking)
        (
            re.compile(r"(?:Node\.js \d+ actions are deprecated|DeprecationWarning: .* is deprecated)", re.IGNORECASE),
            FailureCategory.MAINTENANCE_WARNING,
            Severity.WARNING,
            False,
            "Deprecation warning in CI toolchain or runtime actions",
        ),
    ]

    @classmethod
    def classify_all(
        cls,
        message: str,
        step_name: str = "",
        exit_code: Optional[int] = None,
    ) -> List[Tuple[FailureCategory, Severity, bool, str]]:
        """Extract all distinct failure categories and warnings present in log text."""
        combined = f"{step_name}\n{message}".strip()
        normalized = FailureNormalizer.normalize_text(combined)

        found: dict[FailureCategory, Tuple[FailureCategory, Severity, bool, str]] = {}

        for pattern, cat, sev, blocking, desc in cls.DETERMINISTIC_RULES:
            if cat not in found and pattern.search(normalized):
                found[cat] = (cat, sev, blocking, desc)

        if not found:
            # Fall back to single classification
            return [cls.classify(message, step_name=step_name, exit_code=exit_code)]

        # Order by severity: ERROR (blocking) first, then WARNING / NOTICE
        ordered = sorted(
            found.values(),
            key=lambda x: (not x[2], x[1] != Severity.ERROR),
        )
        return ordered

    @classmethod
    def classify(
        cls,
        message: str,
        step_name: str = "",
        exit_code: Optional[int] = None,
    ) -> Tuple[FailureCategory, Severity, bool, str]:
        """Classify failure deterministically, prioritizing blocking errors over non-blocking warnings."""
        combined = f"{step_name}\n{message}".strip()
        normalized = FailureNormalizer.normalize_text(combined)

        matched: List[Tuple[FailureCategory, Severity, bool, str]] = []
        for pattern, cat, sev, blocking, desc in cls.DETERMINISTIC_RULES:
            if pattern.search(normalized):
                matched.append((cat, sev, blocking, desc))

        if matched:
            # Prioritize blocking errors over non-blocking warnings
            blocking_matches = [m for m in matched if m[2]]
            return blocking_matches[0] if blocking_matches else matched[0]

        # Step-based heuristics if message didn't trigger rule
        step_lower = step_name.lower()
        if "cache" in step_lower:
            return FailureCategory.CACHE_FAILURE, Severity.WARNING, False, "Cache operation notice/failure"
        if "test" in step_lower:
            return FailureCategory.TEST_FAILURE, Severity.ERROR, True, f"Failure during {step_name}"
        if "lint" in step_lower or "ruff" in step_lower:
            return FailureCategory.LINT_FAILURE, Severity.ERROR, True, f"Linter failure in {step_name}"
        if "type" in step_lower or "mypy" in step_lower:
            return FailureCategory.TYPE_CHECK_FAILURE, Severity.ERROR, True, f"Type check failure in {step_name}"
        if "install" in step_lower or "sync" in step_lower or "dependencies" in step_lower:
            return FailureCategory.DEPENDENCY_FAILURE, Severity.ERROR, True, f"Dependency installation failure in {step_name}"

        if exit_code == 0:
            return FailureCategory.WARNING, Severity.INFO, False, "Process succeeded with notices"

        return FailureCategory.UNKNOWN, Severity.ERROR, True, f"Unclassified failure in step: {step_name or 'unknown'}"
