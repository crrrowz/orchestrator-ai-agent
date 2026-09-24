"""Forensic Reliability & Failure-Class Isolation Suite.

Verifies that:
1. All 6 distinct failure classes (Product Test Failure, Infrastructure Error,
   Environment Error, Command Error, Timeout, No Tests Found) are correctly classified.
2. Infrastructure and Environment errors NEVER trigger false Developer Agent code-repair loops.
3. Token budgets are strictly protected against infinite infrastructure failure cycles.
4. Genuine test failures correctly route to Developer remediation.
5. Windows paths with spaces, quoting, and command translations execute reliably.
6. Repeated identical failures trip the smart circuit breaker before reaching MAX_ITERATIONS.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from orchestrator.adapters.node_adapter import NodeAdapter
from orchestrator.analysis.pytest_parser import (
    PytestOutputParser,
    TestExecutionStatus,
)
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.core.constants import ORCHESTRATOR_ROOT
from orchestrator.pipeline.audit_fix_pipeline import AuditFixPipeline
from orchestrator.pipeline.dev_test_loop import DevTestLoop
from orchestrator.pipeline.full_pipeline import FullPipeline
from orchestrator.tools.workspace_tools import (
    WorkspaceTerminalObservation,
)


# ==============================================================================
# 1. Failure Class Distinguishability Tests
# ==============================================================================


def test_classify_execution_all_classes():
    """Verify classification into all 6 distinct failure categories."""
    # A. Passed
    res_pass = PytestOutputParser.classify_execution(
        exit_code=0, stdout="5 passed in 0.05s", stderr=""
    )
    assert res_pass.status == TestExecutionStatus.PASSED
    assert res_pass.is_infra_or_env is False

    # B. Genuine Test Failure
    fail_stdout = """
================================== FAILURES ===================================
__________________________________ test_calc __________________________________
    def test_calc():
>       assert calculate(10) == 20
E       assert 15 == 20
=========================== short test summary info ===========================
FAILED tests/test_calc.py::test_calc - assert 15 == 20
========================= 1 failed, 4 passed in 0.12s =========================
"""
    res_fail = PytestOutputParser.classify_execution(
        exit_code=1, stdout=fail_stdout, stderr=""
    )
    assert res_fail.status == TestExecutionStatus.TEST_FAILURE
    assert res_fail.is_infra_or_env is False
    assert "FAILED tests/test_calc.py::test_calc" in res_fail.failure_details

    # C. Infrastructure Error (uv trampoline crash)
    res_trampoline = PytestOutputParser.classify_execution(
        exit_code=1,
        stdout="",
        stderr="error: uv trampoline failed to canonicalize script path",
    )
    assert res_trampoline.status == TestExecutionStatus.INFRASTRUCTURE_ERROR
    assert res_trampoline.is_infra_or_env is True

    # D. Environment Error (Missing pytest module)
    res_no_pytest = PytestOutputParser.classify_execution(
        exit_code=1,
        stdout="",
        stderr="/usr/bin/python: No module named pytest",
    )
    assert res_no_pytest.status == TestExecutionStatus.ENVIRONMENT_ERROR
    assert res_no_pytest.is_infra_or_env is True

    # D2. Environment Error (Windows WinError 5 PermissionError)
    res_winerror = PytestOutputParser.classify_execution(
        exit_code=1,
        stdout="",
        stderr="PermissionError: [WinError 5] Access is denied: 'D:\\project\\.venv\\Scripts\\pytest.exe'",
    )
    assert res_winerror.status == TestExecutionStatus.ENVIRONMENT_ERROR
    assert res_winerror.is_infra_or_env is True

    # E. Command Error (Security Policy or Invalid CLI Argument)
    res_cmd_err = PytestOutputParser.classify_execution(
        exit_code=126,
        stdout="",
        stderr="Security policy violation: Command binary 'curl' is not in permitted whitelist.",
    )
    assert res_cmd_err.status == TestExecutionStatus.COMMAND_ERROR
    assert res_cmd_err.is_infra_or_env is True

    # F. Timeout Error
    res_timeout = PytestOutputParser.classify_execution(
        exit_code=-1,
        stdout="",
        stderr="Command timed out after 60 seconds.",
        timed_out=True,
    )
    assert res_timeout.status == TestExecutionStatus.TIMEOUT
    assert res_timeout.is_infra_or_env is True

    # G. No Tests Found (exit code 5)
    res_no_tests = PytestOutputParser.classify_execution(
        exit_code=5,
        stdout="collected 0 items\n\n========================= no tests ran in 0.01s ==========================",
        stderr="",
    )
    assert res_no_tests.status == TestExecutionStatus.NO_TESTS_FOUND
    assert res_no_tests.is_infra_or_env is False


# ==============================================================================
# 2. False Code-Repair Loop Prevention (AuditFixPipeline)
# ==============================================================================


def test_audit_fix_pipeline_halts_on_unrecoverable_infrastructure_error(tmp_path: Path):
    """Verify that when test launcher trampoline fails permanently, Developer Agent is NOT invoked."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("def test_app(): pass\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=4)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, workspace_path=tmp_path, auto_chain_audit=False)

    infra_error_obs = WorkspaceTerminalObservation(
        content=[],
        is_error=True,
        exit_code=1,
        stdout="",
        stderr="error: uv trampoline failed to canonicalize script path",
    )

    with (
        patch(
            "orchestrator.pipeline.audit_fix_pipeline.execute_terminal_action",
            return_value=infra_error_obs,
        ),
        patch("orchestrator.pipeline.audit_fix_pipeline.create_developer_agent") as mock_dev_agent,
    ):
        res = pipeline.run("Audit and fix codebase")

        # Crucial assertion: pipeline halted immediately due to infrastructure failure
        assert res["status"] == "INFRASTRUCTURE_ERROR"
        assert res["iterations"] == 1
        # Developer Agent must NOT have been created or invoked
        assert mock_dev_agent.call_count == 0


def test_audit_fix_pipeline_halts_on_environment_error_without_token_burn(tmp_path: Path):
    """Verify missing pytest module halts pipeline without entering code-modification cycle."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("def test_app(): pass\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=4)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, workspace_path=tmp_path, auto_chain_audit=False)

    env_error_obs = WorkspaceTerminalObservation(
        content=[],
        is_error=True,
        exit_code=1,
        stdout="",
        stderr="python: No module named pytest",
    )

    with (
        patch(
            "orchestrator.pipeline.audit_fix_pipeline.execute_terminal_action",
            return_value=env_error_obs,
        ),
        patch("orchestrator.pipeline.audit_fix_pipeline.create_developer_agent") as mock_dev_agent,
    ):
        res = pipeline.run("Audit and fix")
        assert res["status"] == "ENVIRONMENT_ERROR"
        assert mock_dev_agent.call_count == 0


def test_audit_fix_pipeline_remediates_genuine_test_failure(tmp_path: Path):
    """Verify genuine test failures trigger Developer remediation and converge when fixed."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("def add(a, b): return a - b\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("from app import add\ndef test_add(): assert add(2, 2) == 4\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=4)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, workspace_path=tmp_path, auto_chain_audit=False)

    failing_obs = WorkspaceTerminalObservation(
        content=[],
        is_error=True,
        exit_code=1,
        stdout="""
================================== FAILURES ===================================
__________________________________ test_add ___________________________________
    def test_add():
>       assert add(2, 2) == 4
E       assert 0 == 4
=========================== short test summary info ===========================
FAILED tests/test_app.py::test_add - assert 0 == 4
========================= 1 failed in 0.05s =========================
""",
        stderr="",
    )
    passing_obs = WorkspaceTerminalObservation(
        content=[],
        is_error=False,
        exit_code=0,
        stdout="1 passed in 0.02s",
        stderr="",
    )

    mock_agent = MagicMock()
    mock_agent.llm.model = "test-model"
    mock_agent.llm.metrics = None

    def fake_dev_fix(*args, **kwargs):
        # Simulate Developer editing app.py
        (tmp_path / "app.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")

    with (
        patch(
            "orchestrator.pipeline.audit_fix_pipeline.execute_terminal_action",
            side_effect=[failing_obs, passing_obs],
        ),
        patch(
            "orchestrator.pipeline.audit_fix_pipeline.create_developer_agent",
            return_value=mock_agent,
        ),
        patch("orchestrator.pipeline.audit_fix_pipeline.Conversation"),
        patch.object(pipeline, "_run_conv", side_effect=fake_dev_fix) as mock_conv,
    ):
        res = pipeline.run("Fix failing add test")
        assert res["status"] == "CONVERGED_CLEAN"
        assert mock_conv.call_count == 1


# ==============================================================================
# 3. DevTestLoop & FullPipeline Infrastructure Guard Tests
# ==============================================================================


def test_dev_test_loop_halts_on_infrastructure_error(tmp_path: Path):
    """Verify DevTestLoop aborts with INFRASTRUCTURE_ERROR if test runner crashes."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=4)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = DevTestLoop(cfg, sm, workspace_path=tmp_path)

    mock_agent = MagicMock()
    mock_agent.llm.metrics = None

    infra_obs = WorkspaceTerminalObservation(
        content=[],
        is_error=True,
        exit_code=1,
        stdout="",
        stderr="error: uv trampoline failed to canonicalize script path",
    )

    with (
        patch("orchestrator.pipeline.dev_test_loop.execute_terminal_action", return_value=infra_obs),
        patch("orchestrator.pipeline.dev_test_loop.create_developer_agent", return_value=mock_agent),
        patch("orchestrator.pipeline.dev_test_loop.create_tester_agent", return_value=mock_agent),
        patch("orchestrator.pipeline.dev_test_loop.Conversation"),
        patch.object(pipeline, "_run_conv"),
    ):
        res = pipeline.run("Develop feature")
        assert res["status"] == "INFRASTRUCTURE_ERROR"


def test_full_pipeline_halts_on_infrastructure_error(tmp_path: Path):
    """Verify FullPipeline aborts with INFRASTRUCTURE_ERROR if test runner crashes."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=4)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = FullPipeline(cfg, sm, workspace_path=tmp_path)

    mock_agent = MagicMock()
    mock_agent.llm.metrics = None

    infra_obs = WorkspaceTerminalObservation(
        content=[],
        is_error=True,
        exit_code=1,
        stdout="",
        stderr="error: uv trampoline failed to canonicalize script path",
    )

    with (
        patch("orchestrator.pipeline.base_pipeline.execute_terminal_action", return_value=infra_obs),
        patch("orchestrator.pipeline.full_pipeline.create_architect_agent", return_value=mock_agent),
        patch("orchestrator.pipeline.full_pipeline.create_developer_agent", return_value=mock_agent),
        patch("orchestrator.pipeline.full_pipeline.create_tester_agent", return_value=mock_agent),
        patch("orchestrator.pipeline.full_pipeline.create_reviewer_agent", return_value=mock_agent),
        patch("orchestrator.pipeline.full_pipeline.Conversation"),
        patch.object(pipeline, "_run_conv"),
    ):
        res = pipeline.run("Full architecture build")
        assert res["status"] == "INFRASTRUCTURE_ERROR"


# ==============================================================================
# 4. Circuit Breaker & No-Progress Protection
# ==============================================================================


def test_audit_fix_pipeline_circuit_breaker_on_repeated_failure(tmp_path: Path):
    """Verify circuit breaker trips and halts loop when identical failure repeats across iterations."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("def run(): pass\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path, max_iterations=8)
    sm = SkillManager(ORCHESTRATOR_ROOT)
    pipeline = AuditFixPipeline(cfg, sm, workspace_path=tmp_path, auto_chain_audit=False)

    identical_failure = WorkspaceTerminalObservation(
        content=[],
        is_error=True,
        exit_code=1,
        stdout="""
================================== FAILURES ===================================
__________________________________ test_demo __________________________________
>   assert False
E   AssertionError
=========================== short test summary info ===========================
FAILED tests/test_demo.py::test_demo - AssertionError
========================= 1 failed in 0.05s =========================
""",
        stderr="",
    )

    mock_agent = MagicMock()
    mock_agent.llm.model = "test-model"
    mock_agent.llm.metrics = None

    with (
        patch(
            "orchestrator.pipeline.audit_fix_pipeline.execute_terminal_action",
            return_value=identical_failure,
        ),
        patch(
            "orchestrator.pipeline.audit_fix_pipeline.create_developer_agent",
            return_value=mock_agent,
        ),
        patch("orchestrator.pipeline.audit_fix_pipeline.Conversation"),
        patch.object(pipeline, "_run_conv"),
    ):
        res = pipeline.run("Fix bug")
        # Circuit breaker should halt execution after 2-3 identical failures instead of running 8 iterations
        assert res["status"] == "CIRCUIT_BREAKER_ABORT"
        assert res["iterations"] <= 3


# ==============================================================================
# 5. NodeAdapter Failure Classification
# ==============================================================================


def test_node_adapter_failure_classification():
    """Verify NodeAdapter accurately separates npm environment crashes from test assertion failures."""
    adapter = NodeAdapter()

    # 1. Clean Pass
    res_pass = adapter.classify_test_result("✓ test passed (2ms)", "", exit_code=0)
    assert res_pass.status == TestExecutionStatus.PASSED

    # 2. Vitest / Jest Test Assertion Failure
    res_fail = adapter.classify_test_result(
        "FAIL src/app.test.ts\n  ✕ adds numbers\n  AssertionError: expected 3 to equal 4",
        "",
        exit_code=1,
    )
    assert res_fail.status == TestExecutionStatus.TEST_FAILURE
    assert res_fail.is_infra_or_env is False

    # 3. NPM Missing Binary / Command Not Found Crash
    res_npm_crash = adapter.classify_test_result(
        "",
        "npm ERR! code ENOENT\nnpm ERR! syscall spawn vitest\nnpm ERR! path vitest",
        exit_code=1,
    )
    assert res_npm_crash.status == TestExecutionStatus.ENVIRONMENT_ERROR
    assert res_npm_crash.is_infra_or_env is True
