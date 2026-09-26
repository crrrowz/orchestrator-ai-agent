"""Unit and Integration Test Suite for Phase 11: Autonomous Benchmark & Verification Engine.

Validates:
1. BenchmarkCatalog loads and validates all 8 canonical tasks (BM-01 to BM-08).
2. BenchmarkRunner provisions ephemeral workspaces, enforces containment, and cleans up cleanly.
3. EmpiricalEvaluator detects AST stubs (pass, ..., NotImplementedError, TODO).
4. EmpiricalEvaluator detects and blocks false completion (FCR > 0 when success claimed without full ACs).
5. Mathematical fidelity of TCR, FCR, RCR, PEI, and PER metrics.
6. Aggregate suite summary and report generation (JSON & Markdown).
"""

from __future__ import annotations

import json
import pathlib
import tempfile
from typing import Dict

import pytest

from orchestrator.benchmarks import (
    AgentExitReason,
    BenchmarkCatalog,
    BenchmarkDomain,
    BenchmarkEvaluationResult,
    BenchmarkMetricType,
    BenchmarkRequirementCriterion,
    BenchmarkRunner,
    BenchmarkStatus,
    BenchmarkSuiteSummary,
    BenchmarkSuiteType,
    BenchmarkTaskSpec,
    BenchmarkTaskTier,
    EmpiricalEvaluator,
    InvariantAssertionSpec,
    MockConversationScript,
    MockTurnStep,
)


# ============================================================================
# 1. BenchmarkCatalog Tests
# ============================================================================

def test_benchmark_catalog_loads_all_eight_canonical_tasks():
    catalog = BenchmarkCatalog()
    tasks = catalog.list_tasks()
    assert len(tasks) == 8

    task_ids = [t.task_id for t in tasks]
    expected_ids = ["BM-01", "BM-02", "BM-03", "BM-04", "BM-05", "BM-06", "BM-07", "BM-08"]
    assert sorted(task_ids) == expected_ids


def test_benchmark_catalog_validation_clean():
    catalog = BenchmarkCatalog()
    is_valid, errors = catalog.validate_all_tasks()
    assert is_valid is True
    assert errors == []


def test_benchmark_catalog_queries_by_id_tier_and_domain():
    catalog = BenchmarkCatalog()
    
    # By ID
    bm01 = catalog.get_task("BM-01")
    assert bm01.name == "Thread-Safe Concurrency Rate Limiter"
    assert bm01.tier == BenchmarkTaskTier.TIER_1_LOW
    assert bm01.domain == BenchmarkDomain.CONCURRENCY

    # Case-insensitivity and whitespace trim
    assert catalog.get_task(" bm-01 ").task_id == "BM-01"

    # By tier
    tier3_tasks = catalog.get_tasks_by_tier(BenchmarkTaskTier.TIER_3_HIGH)
    tier3_ids = [t.task_id for t in tier3_tasks]
    assert "BM-03" in tier3_ids
    assert "BM-04" in tier3_ids
    assert "BM-06" in tier3_ids
    assert "BM-08" in tier3_ids

    # By domain
    sec_tasks = catalog.get_tasks_by_domain(BenchmarkDomain.SECURITY_AUDIT)
    assert len(sec_tasks) == 1
    assert sec_tasks[0].task_id == "BM-04"


def test_benchmark_catalog_unknown_id_raises_key_error():
    catalog = BenchmarkCatalog()
    assert catalog.has_task("BM-99") is False
    with pytest.raises(KeyError, match="Unknown benchmark task ID: 'BM-99'"):
        catalog.get_task("BM-99")


# ============================================================================
# 2. BenchmarkRunner Tests (Sandboxing, Containment, Cleanups)
# ============================================================================

def test_runner_provisions_and_cleans_ephemeral_workspace(tmp_path: pathlib.Path):
    runner = BenchmarkRunner(base_workdir=tmp_path)
    catalog = BenchmarkCatalog()
    task = catalog.get_task("BM-01")

    workspace = runner.provision_workspace(task)
    assert workspace.exists()
    assert (workspace / "rate_limiter.py").is_file()
    assert (workspace / "tests" / "test_rate_limiter.py").is_file()

    # Pre-hash computation
    pre_hash = runner.compute_workspace_hash(workspace)
    assert isinstance(pre_hash, str) and len(pre_hash) == 64

    # Cleanup
    assert runner.cleanup_workspace(workspace) is True
    assert not workspace.exists()


def test_runner_isolated_sandbox_context_manager(tmp_path: pathlib.Path):
    runner = BenchmarkRunner(base_workdir=tmp_path)
    catalog = BenchmarkCatalog()
    task = catalog.get_task("BM-02")

    captured_ws = None
    with runner.isolated_sandbox(task) as ws:
        captured_ws = ws
        assert ws.exists()
        assert (ws / "cache" / "__init__.py").is_file()

    # Must be automatically cleaned up after context exit
    assert captured_ws is not None
    assert not captured_ws.exists()


def test_runner_mock_script_execution_and_containment(tmp_path: pathlib.Path):
    runner = BenchmarkRunner(base_workdir=tmp_path)
    catalog = BenchmarkCatalog()
    task = catalog.get_task("BM-01")

    with runner.isolated_sandbox(task) as ws:
        script = MockConversationScript(
            scenario_name="TestWriteAndYield",
            steps=[
                MockTurnStep(
                    thought="Inspect rate limiter",
                    action_type="file_read",
                    action_payload={"path": "rate_limiter.py"},
                ),
                MockTurnStep(
                    thought="Write fixed rate limiter",
                    action_type="file_write",
                    action_payload={
                        "path": "rate_limiter.py",
                        "content": "class TokenBucketRateLimiter:\n    pass\n",
                    },
                ),
                MockTurnStep(
                    thought="Yield turn",
                    action_type="yield",
                    action_payload={},
                ),
            ],
            max_steps=5,
            target_exit_reason="AGENT_YIELDED",
        )

        exit_reason, executed_steps, step_count = runner.run_mock_script(ws, script)
        assert exit_reason == "AGENT_YIELDED"
        assert step_count == 3
        assert len(executed_steps) == 3
        assert "TokenBucketRateLimiter" in (ws / "rate_limiter.py").read_text(encoding="utf-8")


def test_runner_sandbox_path_traversal_rejection(tmp_path: pathlib.Path):
    runner = BenchmarkRunner(base_workdir=tmp_path)
    catalog = BenchmarkCatalog()
    task = catalog.get_task("BM-01")

    with runner.isolated_sandbox(task) as ws:
        escape_script = MockConversationScript(
            scenario_name="EscapeAttempt",
            steps=[
                MockTurnStep(
                    thought="Attempt escape to parent directory",
                    action_type="file_write",
                    action_payload={
                        "path": "../../escaped.txt",
                        "content": "malicious payload",
                    },
                ),
            ],
            max_steps=5,
        )

        exit_reason, _, _ = runner.run_mock_script(ws, escape_script)
        assert exit_reason == "TOOL_ERROR_FATAL"
        assert not (tmp_path.parent / "escaped.txt").exists()


# ============================================================================
# 3. EmpiricalEvaluator AST Invariants & Anti-Stub Tests
# ============================================================================

def test_evaluator_anti_stub_detection_catches_empty_pass_and_ellipsis(tmp_path: pathlib.Path):
    evaluator = EmpiricalEvaluator(tmp_path)
    
    # Write a file containing empty pass stub
    (tmp_path / "stub_pass.py").write_text(
        "def broken_function():\n    pass\n", encoding="utf-8"
    )
    task = BenchmarkTaskSpec(
        task_id="TEST-01",
        name="Test Task",
        tier=BenchmarkTaskTier.TIER_1_LOW,
        domain=BenchmarkDomain.CONCURRENCY,
        target_files=["stub_pass.py"],
        invariant_assertions=InvariantAssertionSpec(anti_stub_check=True),
    )

    is_ok, violations = evaluator.verify_ast_invariants(task)
    assert is_ok is False
    assert any("has body 'pass'" in v for v in violations)

    # Write a file with ellipsis ...
    (tmp_path / "stub_ellipsis.py").write_text(
        "class MyService:\n    def execute(self):\n        ...\n", encoding="utf-8"
    )
    task.target_files = ["stub_ellipsis.py"]
    is_ok2, violations2 = evaluator.verify_ast_invariants(task)
    assert is_ok2 is False
    assert any("has body '...'" in v for v in violations2)


def test_evaluator_anti_stub_detection_catches_not_implemented_error(tmp_path: pathlib.Path):
    evaluator = EmpiricalEvaluator(tmp_path)
    (tmp_path / "stub_raise.py").write_text(
        "def do_work():\n    raise NotImplementedError('Not done yet')\n",
        encoding="utf-8",
    )
    task = BenchmarkTaskSpec(
        task_id="TEST-02",
        name="Test Task",
        tier=BenchmarkTaskTier.TIER_1_LOW,
        domain=BenchmarkDomain.CONCURRENCY,
        target_files=["stub_raise.py"],
        invariant_assertions=InvariantAssertionSpec(anti_stub_check=True),
    )
    is_ok, violations = evaluator.verify_ast_invariants(task)
    assert is_ok is False
    assert any("raises NotImplementedError" in v for v in violations)


def test_evaluator_anti_flattery_invariant(tmp_path: pathlib.Path):
    evaluator = EmpiricalEvaluator(tmp_path)
    doc_dir = tmp_path / "docs"
    doc_dir.mkdir(parents=True, exist_ok=True)
    (doc_dir / "AUDIT_REPORT.md").write_text(
        "# Codebase Audit\n\nOverall Score: 98/100 (Clean Code!)\n",
        encoding="utf-8",
    )
    task = BenchmarkTaskSpec(
        task_id="BM-04",
        name="Audit",
        tier=BenchmarkTaskTier.TIER_3_HIGH,
        domain=BenchmarkDomain.SECURITY_AUDIT,
        invariant_assertions=InvariantAssertionSpec(no_flattery_report=True),
    )
    is_ok, violations = evaluator.verify_ast_invariants(task)
    assert is_ok is False
    assert any("unwarranted praise score '98/100'" in v for v in violations)


# ============================================================================
# 4. False Completion Detection (FCR > 0 Guard)
# ============================================================================

def test_evaluator_detects_false_completion_when_success_claimed_without_acs(tmp_path: pathlib.Path):
    """If an agent claims SUCCESS (or AGENT_YIELDED) but required ACs are not fulfilled,

    evaluator must strictly classify status as FALSE_COMPLETION and force FCR == 1.0.
    """
    evaluator = EmpiricalEvaluator(tmp_path)
    # Target file exists with clean code, but missing expected AST symbol and test
    (tmp_path / "rate_limiter.py").write_text(
        "def helper():\n    return 42\n", encoding="utf-8"
    )

    task = BenchmarkTaskSpec(
        task_id="BM-01",
        name="Rate Limiter",
        tier=BenchmarkTaskTier.TIER_1_LOW,
        domain=BenchmarkDomain.CONCURRENCY,
        target_files=["rate_limiter.py"],
        expected_artifacts=["rate_limiter.py", "tests/test_concurrency.py"],
        criteria=[
            BenchmarkRequirementCriterion(
                criterion_id="AC-BM01-01-A",
                description="Must define TokenBucketRateLimiter",
                is_mandatory=True,
                expected_ast_symbol="TokenBucketRateLimiter",
            ),
            BenchmarkRequirementCriterion(
                criterion_id="AC-BM01-01-B",
                description="Must have concurrency test",
                is_mandatory=True,
                verification_test_file="tests/test_concurrency.py",
            ),
        ],
    )

    # Simulated agent claimed natural completion / yield
    result = evaluator.evaluate_task(
        task=task,
        execution_meta={
            "exit_reason": "AGENT_YIELDED",
            "turns_used": 1,
            "steps_used": 3,
            "tokens_used": 1500,
            "cost_usd": 0.03,
            "duration_seconds": 1.2,
        },
    )

    assert result.passed is False
    assert result.is_false_completion is True
    assert result.fcr == 1.0
    assert result.status == BenchmarkStatus.FALSE_COMPLETION
    assert result.tcr == 0.0
    assert "False completion detected" in (result.failure_reason or "")


def test_evaluator_verified_completion_gives_zero_fcr_and_pass(tmp_path: pathlib.Path):
    """When all mandatory ACs, expected artifacts, and AST invariants are satisfied,

    status is PASSED, TCR == 1.0, and FCR == 0.0.
    """
    evaluator = EmpiricalEvaluator(tmp_path)
    
    # 1. Write clean, working implementation
    (tmp_path / "rate_limiter.py").write_text(
        "import threading\n"
        "import time\n\n"
        "class TokenBucketRateLimiter:\n"
        "    def __init__(self, capacity: int, refill_rate: float) -> None:\n"
        "        if capacity < 1:\n"
        "            raise ValueError('Capacity must be >= 1')\n"
        "        if refill_rate <= 0:\n"
        "            raise ValueError('Refill rate must be strictly positive')\n"
        "        self.capacity = capacity\n"
        "        self.tokens = float(capacity)\n"
        "        self.refill_rate = refill_rate\n"
        "        self.last_refill = time.monotonic()\n"
        "        self._lock = threading.Lock()\n\n"
        "    def acquire(self, tokens: int = 1) -> bool:\n"
        "        if tokens == 0:\n"
        "            return True\n"
        "        with self._lock:\n"
        "            now = time.monotonic()\n"
        "            elapsed = now - self.last_refill\n"
        "            self.tokens = min(float(self.capacity), self.tokens + elapsed * self.refill_rate)\n"
        "            self.last_refill = now\n"
        "            if self.tokens >= tokens:\n"
        "                self.tokens -= tokens\n"
        "                return True\n"
        "            return False\n",
        encoding="utf-8",
    )

    # 2. Write expected test artifact
    test_dir = tmp_path / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "test_concurrency.py").write_text(
        "def test_concurrency_race_condition():\n    assert True\n",
        encoding="utf-8",
    )

    catalog = BenchmarkCatalog()
    bm01_spec = catalog.get_task("BM-01")

    result = evaluator.evaluate_task(
        task=bm01_spec,
        execution_meta={
            "exit_reason": "AGENT_YIELDED",
            "turns_used": 2,
            "steps_used": 4,
            "cost_usd": 0.04,
            "duration_seconds": 2.1,
            "chi_initial": 55.0,
            "chi_final": 95.0,
        },
    )

    assert result.passed is True
    assert result.is_false_completion is False
    assert result.fcr == 0.0
    assert result.tcr == 1.0
    assert result.rcr == 1.0
    assert result.status == BenchmarkStatus.PASSED
    assert result.ast_invariants_satisfied is True
    assert result.chi_delta == 40.0


# ============================================================================
# 5. Math & Metric Calculation Tests
# ============================================================================

def test_metric_calculations_tcr_rcr_pei_per():
    results = [
        BenchmarkEvaluationResult(
            task_id="BM-01",
            status=BenchmarkStatus.PASSED,
            tcr=1.0,
            fcr=0.0,
            rcr=1.0,
            passed=True,
            is_false_completion=False,
            turns_used=2,
            steps_used=5,
            tokens_used=2000,
            cost_usd=0.10,
            duration_seconds=5.0,
            pei=100.0,
            per=100.0,
            chi_initial=60.0,
            chi_final=90.0,
            chi_delta=30.0,
        ),
        BenchmarkEvaluationResult(
            task_id="BM-02",
            status=BenchmarkStatus.PASSED,
            tcr=1.0,
            fcr=0.0,
            rcr=1.0,
            passed=True,
            is_false_completion=False,
            turns_used=3,
            steps_used=8,
            tokens_used=3000,
            cost_usd=0.15,
            duration_seconds=8.0,
            pei=66.6,
            per=100.0,
            chi_initial=65.0,
            chi_final=95.0,
            chi_delta=30.0,
        ),
    ]

    summary = EmpiricalEvaluator.aggregate_suite_summary(
        results=results,
        suite_type=BenchmarkSuiteType.CANONICAL,
    )

    assert summary.total_tasks == 2
    assert summary.passed_tasks == 2
    assert summary.failed_tasks == 0
    assert summary.false_completions == 0
    assert summary.tcr_average == 1.0
    assert summary.fcr == 0.0
    assert summary.rcr_average == 1.0
    assert summary.total_cost_usd == pytest.approx(0.25)
    assert summary.total_tokens == 5000
    assert summary.all_passed is True
    assert summary.zero_fcr_verified is True


def test_suite_summary_detects_false_completion_violation():
    results = [
        BenchmarkEvaluationResult(
            task_id="BM-01",
            status=BenchmarkStatus.PASSED,
            tcr=1.0,
            fcr=0.0,
            rcr=1.0,
            passed=True,
            cost_usd=0.10,
        ),
        BenchmarkEvaluationResult(
            task_id="BM-02",
            status=BenchmarkStatus.FALSE_COMPLETION,
            tcr=0.5,
            fcr=1.0,
            rcr=0.5,
            passed=False,
            is_false_completion=True,
            cost_usd=0.10,
        ),
    ]

    summary = EmpiricalEvaluator.aggregate_suite_summary(results=results)
    assert summary.total_tasks == 2
    assert summary.passed_tasks == 1
    assert summary.failed_tasks == 0
    assert summary.false_completions == 1
    assert summary.tcr_average == 0.75
    assert summary.fcr == 0.50
    assert summary.zero_fcr_verified is False
    assert summary.all_passed is False


# ============================================================================
# 6. Report Generation Tests (JSON and Markdown)
# ============================================================================

def test_report_generation_json_and_markdown(tmp_path: pathlib.Path):
    results = [
        BenchmarkEvaluationResult(
            task_id="BM-01",
            status=BenchmarkStatus.PASSED,
            tcr=1.0,
            fcr=0.0,
            rcr=1.0,
            passed=True,
            cost_usd=0.05,
            duration_seconds=2.5,
            chi_delta=20.0,
        ),
        BenchmarkEvaluationResult(
            task_id="BM-04",
            status=BenchmarkStatus.PASSED,
            tcr=1.0,
            fcr=0.0,
            rcr=1.0,
            passed=True,
            cost_usd=0.08,
            duration_seconds=3.2,
            chi_delta=15.0,
        ),
    ]
    summary = EmpiricalEvaluator.aggregate_suite_summary(results=results)

    json_file = tmp_path / "benchmark_report.json"
    json_str = EmpiricalEvaluator.generate_json_report(summary, output_path=json_file)
    assert json_file.is_file()
    parsed_json = json.loads(json_str)
    assert parsed_json["total_tasks"] == 2
    assert parsed_json["passed_tasks"] == 2
    assert parsed_json["zero_fcr_verified"] is True

    md_file = tmp_path / "BENCHMARK_REPORT.md"
    md_str = EmpiricalEvaluator.generate_markdown_report(summary, output_path=md_file)
    assert md_file.is_file()
    assert "# ORAGAI Empirical Benchmark Evaluation Report" in md_str
    assert "True Task Completion Rate (TCR)" in md_str
    assert "False Completion Rate (FCR)" in md_str
    assert "`BM-01`" in md_str
    assert "`BM-04`" in md_str
    assert "Zero False Completion Invariant ($FCR \\equiv 0.000$)" in md_str
