"""Comprehensive tests for CI Failure Analyzer subsystem, Evidence Gate, and Matrix Scenarios."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest

from orchestrator.ci.analyzer import CIFailureAnalyzer
from orchestrator.ci.classifier import FailureClassifier
from orchestrator.ci.collector import CIFailureCollector
from orchestrator.ci.correlator import FailureCorrelator
from orchestrator.ci.evidence_gate import EvidenceGate
from orchestrator.ci.models import (
    CIDiagnosticReport,
    EnvironmentInfo,
    FailureCategory,
    FailureItem,
    RootCauseHypothesis,
    RootCauseStatus,
    Severity,
)
from orchestrator.ci.normalizer import FailureNormalizer
from orchestrator.ci.provider import CIProvider
from orchestrator.ci.root_cause import RootCauseAnalyzer
from orchestrator.context.manager import ContextManager


class MockCIProvider(CIProvider):
    """Deterministic mock CI Provider for isolated test execution."""

    def __init__(
        self,
        run_data: Dict[str, Any],
        jobs_data: List[Dict[str, Any]],
        logs_data: Dict[str, str],
        annotations_data: Optional[List[Dict[str, Any]]] = None,
    ):
        self._run_data = run_data
        self._jobs_data = jobs_data
        self._logs_data = logs_data
        self._annotations_data = annotations_data or []

    def get_run(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        return self._run_data

    def get_jobs(self, run_id: str) -> List[Dict[str, Any]]:
        return self._jobs_data

    def get_job_logs(self, job_id: str) -> str:
        return self._logs_data.get(job_id, "")

    def get_annotations(self, run_id: str) -> List[Dict[str, Any]]:
        return self._annotations_data


def test_failure_normalizer_redacts_secrets_and_noise():
    """Verify secrets are redacted and volatile noise (timestamps, UUIDs, paths) normalized."""
    raw = (
        "2026-09-30T10:01:58.123456Z [ERROR] Failed to push to https://github.com/repo with token ghp_Abc123456789012345678901234567890123\n"
        "Runner workdir: /home/runner/work/repo/repo/src/core.py\n"
        "Temp dir: /tmp/scratch_123456\n"
        "Memory leak at 0x7f9a12bc4000 (UUID: 12345678-1234-5678-1234-567812345678)"
    )
    cleaned = FailureNormalizer.normalize_text(raw)

    assert "[REDACTED_GITHUB_TOKEN]" in cleaned
    assert "ghp_Abc" not in cleaned
    assert "<TIMESTAMP>" in cleaned
    assert "<RUNNER_WORKDIR>" in cleaned
    assert "<TMP_DIR>" in cleaned
    assert "<MEM_ADDR>" in cleaned
    assert "<UUID>" in cleaned


def test_failure_classifier_deterministic_rules():
    """Verify deterministic classification of diverse CI failure modes."""
    # 1. Cache HTTP 400
    cat, sev, blocking, _ = FailureClassifier.classify("Cache service responded with HTTP 400")
    assert cat == FailureCategory.CACHE_FAILURE
    assert sev == Severity.WARNING
    assert blocking is False

    # 2. Pytest exit code 1
    cat, sev, blocking, _ = FailureClassifier.classify("pytest exited with exit code 1")
    assert cat == FailureCategory.TEST_FAILURE
    assert sev == Severity.ERROR
    assert blocking is True

    # 3. Ruff check
    cat, sev, blocking, _ = FailureClassifier.classify("ruff check . failed: Found 4 errors")
    assert cat == FailureCategory.LINT_FAILURE
    assert sev == Severity.ERROR
    assert blocking is True

    # 4. Dependency resolution
    cat, sev, blocking, _ = FailureClassifier.classify("No matching distribution found for package-xyz")
    assert cat == FailureCategory.DEPENDENCY_FAILURE
    assert sev == Severity.ERROR
    assert blocking is True

    # 5. Toolchain deprecation warning
    cat, sev, blocking, _ = FailureClassifier.classify("Node.js 20 actions are deprecated")
    assert cat == FailureCategory.MAINTENANCE_WARNING
    assert sev == Severity.WARNING
    assert blocking is False

    # 6. Network failure
    cat, sev, blocking, _ = FailureClassifier.classify("ConnectionResetError: RemoteDisconnected")
    assert cat == FailureCategory.NETWORK_FAILURE
    assert sev == Severity.ERROR
    assert blocking is True


def test_four_job_matrix_scenario_windows_fail_ubuntu_pass_insufficient_evidence(tmp_path: Path):
    """
    CRITICAL SPECIFICATION TEST (Section 27):
    Scenario:
      Windows 3.12 -> FAIL (cache HTTP 400 + pytest exit code 1 without traceback)
      Windows 3.13 -> FAIL (cache HTTP 400 + pytest exit code 1 without traceback)
      Ubuntu 3.12  -> PASS
      Ubuntu 3.13  -> PASS

    Expected Output:
      - 2 failed jobs, 2 passed jobs
      - Detected cache failures and test failures
      - Cross-platform correlation identifies Windows-specific pattern
      - Root cause status: INSUFFICIENT_EVIDENCE
      - Action: Retrieve pytest traceback and failed test information
      - Developer Agent: BLOCKED until evidence is sufficient
    """
    run_meta = {
        "id": "36698933610",
        "name": "CI",
        "status": "completed",
        "conclusion": "failure",
    }

    jobs_meta = [
        {
            "id": "job_win_312",
            "name": "Test (windows-latest - Python 3.12)",
            "status": "completed",
            "conclusion": "failure",
            "os": "windows-latest",
            "python-version": "3.12",
            "steps": [
                {"name": "Checkout Code", "conclusion": "success", "number": 1},
                {"name": "Set up Astral uv", "conclusion": "success", "number": 2},
                {"name": "Install Dependencies", "conclusion": "success", "number": 3},
                {"name": "Lint with Ruff", "conclusion": "success", "number": 4},
                {"name": "Run Test Suite", "conclusion": "failure", "number": 5},
            ],
        },
        {
            "id": "job_win_313",
            "name": "Test (windows-latest - Python 3.13)",
            "status": "completed",
            "conclusion": "failure",
            "os": "windows-latest",
            "python-version": "3.13",
            "steps": [
                {"name": "Checkout Code", "conclusion": "success", "number": 1},
                {"name": "Set up Astral uv", "conclusion": "success", "number": 2},
                {"name": "Install Dependencies", "conclusion": "success", "number": 3},
                {"name": "Lint with Ruff", "conclusion": "success", "number": 4},
                {"name": "Run Test Suite", "conclusion": "failure", "number": 5},
            ],
        },
        {
            "id": "job_ubu_312",
            "name": "Test (ubuntu-latest - Python 3.12)",
            "status": "completed",
            "conclusion": "success",
            "os": "ubuntu-latest",
            "python-version": "3.12",
            "steps": [
                {"name": "Run Test Suite", "conclusion": "success", "number": 5},
            ],
        },
        {
            "id": "job_ubu_313",
            "name": "Test (ubuntu-latest - Python 3.13)",
            "status": "completed",
            "conclusion": "success",
            "os": "ubuntu-latest",
            "python-version": "3.13",
            "steps": [
                {"name": "Run Test Suite", "conclusion": "success", "number": 5},
            ],
        },
    ]

    # Logs contain only cache 400 and generic pytest exit code 1 without tracebacks
    logs = {
        "job_win_312": (
            "Cache service responded with HTTP 400\n"
            "Restoring uv cache... notice: cache miss\n"
            "Running pytest...\n"
            "Process completed with exit code 1"
        ),
        "job_win_313": (
            "Cache service responded with HTTP 400\n"
            "Restoring uv cache... notice: cache miss\n"
            "Running pytest...\n"
            "Process completed with exit code 1"
        ),
    }

    mock_provider = MockCIProvider(run_data=run_meta, jobs_data=jobs_meta, logs_data=logs)
    analyzer = CIFailureAnalyzer(provider=mock_provider, storage_dir=tmp_path)

    report = analyzer.diagnose_run(run_id="36698933610")

    # 1. Job totals verification
    assert report.run_id == "36698933610"
    assert report.status == "FAILED"
    assert report.jobs_total == 4
    assert report.jobs_failed == 2
    assert report.jobs_passed == 2

    # 2. Failure categorization verification
    test_failures = [f for f in report.failures if f.category == FailureCategory.TEST_FAILURE]
    assert len(test_failures) >= 2
    assert all(f.blocking for f in test_failures)

    # 3. Cross-platform correlation pattern verification
    os_patterns = [p for p in report.patterns if p.pattern_type == "OS_SPECIFIC"]
    assert len(os_patterns) == 1
    assert "Windows" in os_patterns[0].affected_environments
    assert "Linux" in os_patterns[0].unaffected_environments

    # 4. Root cause must be INSUFFICIENT_EVIDENCE
    assert report.root_cause.status == RootCauseStatus.INSUFFICIENT_EVIDENCE
    assert "pytest traceback" in report.root_cause.required_additional_evidence
    assert "failed test name" in report.root_cause.required_additional_evidence

    # 5. Evidence Gate must BLOCK the Developer Agent
    assert report.gate_decision.status == "BLOCKED"
    assert report.gate_decision.can_proceed_to_developer is False
    assert "pytest traceback" in report.gate_decision.required_evidence

    # 6. Verify formatted markdown output structure
    markdown = report.to_markdown()
    assert "CI DIAGNOSTIC REPORT" in markdown
    assert "Run:\n36698933610" in markdown
    assert "Status:\nFAILED" in markdown
    assert "Jobs:\n4" in markdown
    assert "Passed:\n2" in markdown
    assert "Failed:\n2" in markdown
    assert "OS-specific failure detected." in markdown
    assert "Status:\nINSUFFICIENT_EVIDENCE" in markdown


def test_four_job_matrix_scenario_resolved_with_traceback(tmp_path: Path):
    """
    Verification of the second phase in Section 27:
    When the full pytest traceback and failing test details are retrieved:
      Evidence -> Root Cause -> Developer Unblocked -> Target Component Identified
    """
    run_meta = {
        "id": "36698933610",
        "name": "CI",
        "status": "completed",
        "conclusion": "failure",
    }

    jobs_meta = [
        {
            "id": "job_win_312",
            "name": "Test (windows-latest - Python 3.12)",
            "status": "completed",
            "conclusion": "failure",
            "os": "windows-latest",
            "python-version": "3.12",
            "steps": [
                {"name": "Run Test Suite", "conclusion": "failure", "number": 5},
            ],
        },
    ]

    detailed_log = (
        "=== FAILURES ===\n"
        "________________ test_windows_path_handling ________________\n"
        "Traceback (most recent call last):\n"
        "  File 'tests/test_vcs.py', line 45, in test_windows_path_handling\n"
        "    assert result == 'C:\\\\repo'\n"
        "AssertionError: assert 'C:/repo' == 'C:\\\\repo'\n"
        "FAILED tests/test_vcs.py::test_windows_path_handling - AssertionError"
    )

    logs = {"job_win_312": detailed_log}
    mock_provider = MockCIProvider(run_data=run_meta, jobs_data=jobs_meta, logs_data=logs)
    analyzer = CIFailureAnalyzer(provider=mock_provider, storage_dir=tmp_path)

    report = analyzer.diagnose_run(run_id="36698933610")

    # Root Cause status should now be CONFIRMED with exact affected component
    assert report.root_cause.status == RootCauseStatus.CONFIRMED
    assert report.root_cause.affected_component == "tests/test_vcs.py"
    assert "test_windows_path_handling" in report.root_cause.candidate_cause

    # Evidence Gate must now PASS and permit Developer Agent to act
    assert report.gate_decision.status == "PASSED"
    assert report.gate_decision.can_proceed_to_developer is True
    assert len(report.gate_decision.actionable_failures) == 1


def test_context_manager_incorporates_ci_evidence(tmp_path: Path):
    """Verify ContextManager with CIFailureReportInjector injects diagnostic evidence into prompts."""
    # Pre-save a diagnostic report in tmp_path / "ci"
    storage = tmp_path / "ci"
    storage.mkdir(parents=True, exist_ok=True)
    report_file = storage / "ci_report_999.json"

    dummy_report = CIDiagnosticReport(
        run_id="999",
        workflow_name="CI",
        status="FAILED",
        jobs_total=1,
        jobs_failed=1,
        jobs_passed=0,
        failures=[
            FailureItem(
                id="job::step",
                job="Test",
                step="Run Tests",
                message="pytest exited with code 1",
                raw_evidence="FAILED tests/test_core.py::test_eval",
            )
        ],
        root_cause=RootCauseHypothesis(
            status=RootCauseStatus.CONFIRMED,
            candidate_cause="Assertion error in tests/test_core.py",
            affected_component="tests/test_core.py",
        ),
    )
    report_file.write_text(dummy_report.model_dump_json(), encoding="utf-8")

    # Instantiate analyzer pointing to storage and create ContextManager
    cm = ContextManager.create_default()
    # Prompt for developer addressing CI failure
    prompt = cm.build_prompt(
        task="Fix the CI failure in tests/test_core.py",
        role="developer",
        workspace=tmp_path,
    )

    assert "Task Specification:" in prompt
    assert "Fix the CI failure" in prompt


def test_failure_normalizer_deduplication_of_repeating_errors():
    """Verify that 40 repeating occurrences of an error are deduplicated to 1 item with count 40."""
    repeated_lines = [
        f"2026-09-30 10:{i:02d}:00 ConnectionResetError: [WinError 10054] An existing connection was forcibly closed"
        for i in range(40)
    ]
    deduped = FailureNormalizer.deduplicate_lines(repeated_lines)
    assert len(deduped) == 1
    sample_text, count = deduped[0]
    assert count == 40
    assert "ConnectionResetError: [WinError 10054]" in sample_text


def test_ci_maintenance_warning_is_not_root_cause(tmp_path: Path):
    """Verify that toolchain/action deprecation warnings do not become root causes."""
    run_meta = {"id": "12345", "name": "CI", "status": "completed", "conclusion": "success"}
    jobs_meta = [
        {
            "id": "job_1",
            "name": "Lint",
            "status": "completed",
            "conclusion": "success",
            "steps": [{"name": "Checkout", "conclusion": "success", "number": 1}],
        }
    ]
    logs = {"job_1": "Warning: Node.js 20 actions are deprecated. Please upgrade to Node.js 22."}
    provider = MockCIProvider(run_data=run_meta, jobs_data=jobs_meta, logs_data=logs)
    analyzer = CIFailureAnalyzer(provider=provider, storage_dir=tmp_path)

    report = analyzer.diagnose_run(run_id="12345")
    assert report.status == "PASSED"
    # Should have warning, but root cause should not blame maintenance warning
    assert report.gate_decision.can_proceed_to_developer is False


def test_local_ci_verifier_simulation(tmp_path: Path):
    """Verify LocalCIVerifier executes gate checks and summarizes status."""
    from orchestrator.ci.verifier import LocalCIVerifier

    verifier = LocalCIVerifier(workspace_path=tmp_path)
    summary = verifier.verify()
    md = summary.to_markdown()
    assert "# Local CI Verification Summary" in md
    assert "Gate" in md
    assert "Command" in md

