"""Unit tests verifying Phase 4: Reliability, Git Branch Isolation & Smart Circuit Breaker."""

from pathlib import Path
import pytest

from orchestrator.telemetry.recorder import TelemetryRecorder
from orchestrator.utils.git_ops import GitOps


def test_git_ops_create_task_branch(tmp_path: Path):
    """GitOps should create isolated agent task branches per run."""
    git = GitOps(tmp_path)
    git.init_repo()

    # Create dummy initial file & commit to establish HEAD
    dummy_file = tmp_path / "README.md"
    dummy_file.write_text("# Project Root\n", encoding="utf-8")
    git.commit("Initial commit")

    branch = git.create_task_branch("Implement JWT Auth Service")
    assert branch is not None
    assert branch.startswith("agent/implement-jwt-auth-serv")
    assert git.get_current_branch() == branch


def test_smart_circuit_breaker_semantic_test_failure_loop():
    """Smart circuit breaker must trip when the same tests fail repeatedly, even if diff changes slightly."""
    recorder = TelemetryRecorder(
        task_description="Build feature",
        circuit_breaker_threshold=2,
    )

    diff1 = "+ def add(a, b): return a + b\n"
    diff2 = "+ def add(a, b):\n+     # slightly different whitespace\n+     return a + b\n"

    error_out1 = """
=================================== FAILURES ===================================
FAILED tests/test_calc.py::test_add - AssertionError: 0 == 5
============================== 1 failed in 0.05s ===============================
"""
    error_out2 = """
=================================== FAILURES ===================================
FAILED tests/test_calc.py::test_add - AssertionError: 1 == 5
============================== 1 failed in 0.04s ===============================
"""

    # First iteration: records failure, doesn't trip
    tripped1 = recorder.check_circuit_breaker(diff1, error_out1)
    assert tripped1 is False
    assert recorder.circuit_breaker_triggered is False

    # Second iteration: diff is different, but same failing test (tests/test_calc.py::test_add) -> trips!
    tripped2 = recorder.check_circuit_breaker(diff2, error_out2)
    assert tripped2 is True
    assert recorder.circuit_breaker_triggered is True


def test_smart_circuit_breaker_error_similarity_ratio():
    """Smart circuit breaker must trip when error similarity is high (>0.88) even if diff changes."""
    recorder = TelemetryRecorder(
        task_description="Refactor service",
        circuit_breaker_threshold=2,
    )

    diff1 = "+ a = 10"
    diff2 = "+ a = 20"

    # Similar tracebacks with slight timestamp or line variations
    error1 = "DatabaseConnectionTimeout: Failed to connect to postgresql://localhost:5432/test after 30 seconds."
    error2 = "DatabaseConnectionTimeout: Failed to connect to postgresql://localhost:5432/test after 31 seconds."

    assert recorder.check_circuit_breaker(diff1, error1) is False
    assert recorder.check_circuit_breaker(diff2, error2) is True
    assert recorder.circuit_breaker_triggered is True


def test_smart_circuit_breaker_resets_on_progress():
    """Smart circuit breaker should reset failure count when new/different errors occur."""
    recorder = TelemetryRecorder(
        task_description="Build feature",
        circuit_breaker_threshold=2,
    )

    error1 = "FAILED tests/test_app.py::test_login - AssertionError"
    error2 = "FAILED tests/test_app.py::test_checkout - KeyError: 'cart_id'"

    assert recorder.check_circuit_breaker("diff1", error1) is False
    assert recorder.check_circuit_breaker("diff2", error2) is False
    assert recorder.circuit_breaker_triggered is False
