"""Comprehensive Test Suite for Audit, Deep Inspection & Self-Evolution Engine (P7)."""

import sqlite3
import textwrap
from pathlib import Path
import pytest

from orchestrator.analysis.audit.cluster import ClusterPartitionEngine
from orchestrator.analysis.audit.db import SentinelDiagnosticsDB
from orchestrator.analysis.audit.engine import DeepInspectionEngine
from orchestrator.analysis.audit.fixer import AuditFixOrchestrator
from orchestrator.analysis.audit.models import (
    CodebaseHealthMetrics,
    FindingCategory,
    FindingSeverity,
    FindingSource,
    RemediationStatus,
    VerifiedAuditFinding,
)
from orchestrator.analysis.audit.scanner import StaticAnalysisScanner
from orchestrator.analysis.audit.validator import FindingValidator


# =====================================================================
# P7-T01: Static Analysis Scanner detects Python Syntax Errors
# =====================================================================
def test_static_scanner_detects_python_syntax_errors(tmp_path: Path):
    broken_file = tmp_path / "broken.py"
    broken_file.write_text("def malformed_syntax(:\n    pass\n", encoding="utf-8")

    scanner = StaticAnalysisScanner(tmp_path)
    findings = scanner.scan_workspace()

    syntax_findings = [f for f in findings if f.category == FindingCategory.RELIABILITY and "SYNTAX" in f.finding_id]
    assert len(syntax_findings) >= 1
    finding = syntax_findings[0]
    assert finding.severity == FindingSeverity.CRITICAL
    assert finding.source == FindingSource.STATIC_AST
    assert "broken.py" in finding.file_path


# =====================================================================
# P7-T02: Static Analysis Scanner detects Unimplemented Public Stubs
# =====================================================================
def test_static_scanner_detects_unimplemented_stubs(tmp_path: Path):
    stub_file = tmp_path / "service.py"
    code = textwrap.dedent("""
        def public_pass_stub(x, y):
            pass

        def public_raise_stub(query: str):
            \"\"\"Fetch query results.\"\"\"
            raise NotImplementedError("To be done later")

        def public_ellipsis_stub():
            ...

        def _private_helper():
            pass  # Allowed for private helpers
    """)
    stub_file.write_text(code, encoding="utf-8")

    scanner = StaticAnalysisScanner(tmp_path)
    findings = scanner.scan_workspace()

    stub_findings = [f for f in findings if "STUB" in f.finding_id]
    symbols = {f.ast_symbol for f in stub_findings}

    assert "public_pass_stub" in symbols
    assert "public_raise_stub" in symbols
    assert "public_ellipsis_stub" in symbols
    assert "_private_helper" not in symbols

    for f in stub_findings:
        assert f.severity == FindingSeverity.HIGH
        assert f.category == FindingCategory.ARCHITECTURE


# =====================================================================
# P7-T03: Static Analysis Scanner detects High Cyclomatic Complexity
# =====================================================================
def test_static_scanner_detects_high_cyclomatic_complexity(tmp_path: Path):
    complex_file = tmp_path / "complex_logic.py"
    # Construct a function with 16 branch points
    branches = "\n    ".join([f"if x == {i}:\n        y += {i}" for i in range(16)])
    code = f"def monster_function(x):\n    y = 0\n    {branches}\n    return y\n"
    complex_file.write_text(code, encoding="utf-8")

    scanner = StaticAnalysisScanner(tmp_path)
    findings = scanner.scan_workspace()

    complex_findings = [f for f in findings if "COMPLEX" in f.finding_id]
    assert len(complex_findings) >= 1
    finding = complex_findings[0]
    assert finding.severity == FindingSeverity.MEDIUM
    assert finding.category == FindingCategory.MAINTAINABILITY
    assert finding.ast_symbol == "monster_function"


# =====================================================================
# P7-T04: Static Analysis Scanner detects Secret Leaks & shell=True
# =====================================================================
def test_static_scanner_detects_secret_leaks_and_shell_true(tmp_path: Path):
    sec_file = tmp_path / "sec_test.py"
    code = textwrap.dedent("""
        import subprocess
        import pickle

        OPENAI_KEY = "sk-abcdef12345678901234567890123456"
        res = subprocess.run("ls", shell=True)
        data = pickle.loads(b"cos\\nsystem\\n(S'id'\\ntR.")
    """)
    sec_file.write_text(code, encoding="utf-8")

    scanner = StaticAnalysisScanner(tmp_path)
    findings = scanner.scan_workspace()

    sec_findings = [f for f in findings if f.category == FindingCategory.SECURITY]
    assert len(sec_findings) >= 3
    for f in sec_findings:
        assert f.severity == FindingSeverity.CRITICAL
        assert f.source == FindingSource.SECRET_SCAN


# =====================================================================
# P7-T05: Tarjan's SCC identifies Circular Dependencies across modules
# =====================================================================
def test_circular_dependency_detection_across_modules(tmp_path: Path):
    mod_a = tmp_path / "module_a.py"
    mod_b = tmp_path / "module_b.py"

    mod_a.write_text("import module_b\ndef fn_a(): return module_b.fn_b()\n", encoding="utf-8")
    mod_b.write_text("import module_a\ndef fn_b(): return module_a.fn_a()\n", encoding="utf-8")

    scanner = StaticAnalysisScanner(tmp_path)
    findings = scanner.scan_workspace()

    cycle_findings = [f for f in findings if "ARCH-CYCLE" in f.finding_id]
    assert len(cycle_findings) >= 1
    f = cycle_findings[0]
    assert f.severity == FindingSeverity.HIGH
    assert f.category == FindingCategory.ARCHITECTURE
    assert "module_a" in f.problem_statement and "module_b" in f.problem_statement


# =====================================================================
# P7-T06: Cluster Partition Engine bounds Files and LOC
# =====================================================================
def test_cluster_partition_bounds_files_and_loc(tmp_path: Path):
    core_dir = tmp_path / "orchestrator" / "core"
    core_dir.mkdir(parents=True, exist_ok=True)

    # Create 25 small python files
    for i in range(25):
        (core_dir / f"mod_{i:02d}.py").write_text(f"# Module {i}\nx = {i}\n", encoding="utf-8")

    engine = ClusterPartitionEngine(tmp_path, max_files_per_cluster=10, max_loc_per_cluster=1000)
    clusters = engine.partition_workspace()

    assert len(clusters) >= 3
    for c in clusters:
        assert len(c.files) <= 10
        assert c.total_loc <= 1000
        assert "orchestrator/core" in c.dominant_layer


# =====================================================================
# P7-T07: Finding Validator rejects Non-Existent Files
# =====================================================================
def test_finding_validator_rejects_nonexistent_files(tmp_path: Path):
    finding = VerifiedAuditFinding(
        finding_id="SEC-999",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.HIGH,
        source=FindingSource.AUDITOR_LLM,
        file_path="nonexistent_folder/missing.py",
        line_start=1,
        line_end=1,
        code_snippet="def foo(): pass",
        problem_statement="Security issue in ghost file.",
        remediation_proposal="Delete this non-existent file.",
    )
    is_valid, reason = FindingValidator.validate(finding, tmp_path)
    assert not is_valid
    assert "does not exist on disk" in (reason or "")


# =====================================================================
# P7-T08: Finding Validator rejects Out-of-Bounds Lines
# =====================================================================
def test_finding_validator_rejects_out_of_bounds_lines(tmp_path: Path):
    target = tmp_path / "short.py"
    target.write_text("x = 1\ny = 2\n", encoding="utf-8")

    finding = VerifiedAuditFinding(
        finding_id="BUG-100",
        category=FindingCategory.RELIABILITY,
        severity=FindingSeverity.MEDIUM,
        source=FindingSource.AUDITOR_LLM,
        file_path="short.py",
        line_start=500,
        line_end=500,
        code_snippet="x = 1",
        problem_statement="Out of bounds bug description here.",
        remediation_proposal="Fix the out of bounds logic.",
    )
    is_valid, reason = FindingValidator.validate(finding, tmp_path)
    assert not is_valid
    assert "out of bounds" in (reason or "")


# =====================================================================
# P7-T09: Finding Validator rejects Generic Flattery Fluff
# =====================================================================
def test_finding_validator_rejects_generic_flattery(tmp_path: Path):
    target = tmp_path / "sample.py"
    target.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

    flattery_finding = VerifiedAuditFinding(
        finding_id="FLAT-001",
        category=FindingCategory.ARCHITECTURE,
        severity=FindingSeverity.LOW,
        source=FindingSource.AUDITOR_LLM,
        file_path="sample.py",
        line_start=1,
        line_end=2,
        code_snippet="pass",  # Short code snippet without concrete evidence
        problem_statement="The architecture is well structured and code looks clean 98/100.",
        remediation_proposal="Ensure good practices and consider decomposing.",
    )
    is_valid, reason = FindingValidator.validate(flattery_finding, tmp_path)
    assert not is_valid
    assert "banned generic flattery" in (reason or "")


# =====================================================================
# P7-T10: Deterministic SHA-256 Finding Fingerprinting & Deduplication
# =====================================================================
def test_finding_fingerprint_deduplication():
    f1 = VerifiedAuditFinding(
        finding_id="F-1",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.HIGH,
        source=FindingSource.STATIC_AST,
        file_path="auth/login.py",
        line_start=10,
        line_end=12,
        ast_symbol="login",
        code_snippet="  subprocess.run(cmd,   shell=True)  \n",
        problem_statement="Shell injection hazard in authentication route.",
        remediation_proposal="Replace shell=True with shlex array.",
    )
    f2 = VerifiedAuditFinding(
        finding_id="F-2",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.HIGH,
        source=FindingSource.AUDITOR_LLM,
        file_path="auth/login.py",
        line_start=10,
        line_end=12,
        ast_symbol="login",
        code_snippet="subprocess.run(cmd, shell=True)",
        problem_statement="Shell injection risk detected by LLM.",
        remediation_proposal="Use parameterized subprocess call.",
    )

    fp1 = f1.compute_fingerprint()
    fp2 = f2.compute_fingerprint()
    assert fp1 == fp2
    assert len(fp1) == 16


# =====================================================================
# P7-T11: Remediation DAG Sort prioritizes Root Causes
# =====================================================================
def test_remediation_dag_sort_prioritizes_root_causes(tmp_path: Path):
    f_conv = VerifiedAuditFinding(
        finding_id="CONV-1",
        category=FindingCategory.CONVENTION,
        severity=FindingSeverity.LOW,
        source=FindingSource.STATIC_LINTER,
        file_path="a.py",
        line_start=1,
        line_end=1,
        code_snippet="import os",
        problem_statement="Unused import of module os.",
        remediation_proposal="Remove unused import statement.",
    )
    f_sec = VerifiedAuditFinding(
        finding_id="SEC-1",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.CRITICAL,
        source=FindingSource.SECRET_SCAN,
        file_path="b.py",
        line_start=5,
        line_end=5,
        code_snippet="sk-12345678901234567890123456789012",
        problem_statement="Hardcoded OpenAI API secret key.",
        remediation_proposal="Load secret from environment variable.",
    )
    f_arch = VerifiedAuditFinding(
        finding_id="ARCH-1",
        category=FindingCategory.ARCHITECTURE,
        severity=FindingSeverity.HIGH,
        source=FindingSource.COUPLING_ANALYZER,
        file_path="c.py",
        line_start=1,
        line_end=1,
        code_snippet="import c -> import d -> import c",
        problem_statement="Circular dependency between c and d.",
        remediation_proposal="Break cycle via dependency inversion.",
    )

    orchestrator = AuditFixOrchestrator(tmp_path)
    sorted_findings = orchestrator.sort_findings_dag([f_conv, f_sec, f_arch])

    assert sorted_findings[0].finding_id == "ARCH-1"
    assert sorted_findings[1].finding_id == "SEC-1"
    assert sorted_findings[2].finding_id == "CONV-1"


# =====================================================================
# P7-T12: PreFlight Syntax Guard triggers Atomic Rollback on error
# =====================================================================
def test_preflight_syntax_guard_triggers_atomic_rollback(tmp_path: Path):
    file_path = tmp_path / "valid.py"
    initial_content = "def calculate():\n    return 42\n"
    file_path.write_text(initial_content, encoding="utf-8")

    orchestrator = AuditFixOrchestrator(tmp_path)
    finding = VerifiedAuditFinding(
        finding_id="BUG-FIX-1",
        category=FindingCategory.RELIABILITY,
        severity=FindingSeverity.MEDIUM,
        source=FindingSource.STATIC_AST,
        file_path="valid.py",
        line_start=1,
        line_end=2,
        code_snippet="return 42",
        problem_statement="Return value needs validation.",
        remediation_proposal="Add return validation logic.",
    )

    def broken_patch():
        # Intentionally write broken syntax
        file_path.write_text("def calculate():\n    return (\n", encoding="utf-8")
        return True

    success = orchestrator.apply_fix_with_guard(finding, broken_patch)
    assert not success
    # Check that file was rolled back to initial_content
    restored_content = file_path.read_text(encoding="utf-8")
    assert restored_content == initial_content
    assert finding.remediation_attempts == 1
    assert finding.remediation_status == RemediationStatus.OPEN


# =====================================================================
# P7-T13: Quarantine Circuit Breaker isolates finding after 2 failures
# =====================================================================
def test_quarantine_circuit_breaker_isolates_finding(tmp_path: Path):
    target = tmp_path / "target.py"
    target.write_text("x = 10\n", encoding="utf-8")

    orchestrator = AuditFixOrchestrator(tmp_path, max_attempts_per_finding=2)
    finding = VerifiedAuditFinding(
        finding_id="HARD-BUG-1",
        category=FindingCategory.PERFORMANCE,
        severity=FindingSeverity.HIGH,
        source=FindingSource.AUDITOR_LLM,
        file_path="target.py",
        line_start=1,
        line_end=1,
        code_snippet="x = 10",
        problem_statement="Inefficient constant allocation.",
        remediation_proposal="Optimize allocation mechanism.",
    )

    def failing_patch():
        target.write_text("def broken_syntax(:\n", encoding="utf-8")
        return True

    # Attempt 1
    orchestrator.apply_fix_with_guard(finding, failing_patch)
    assert finding.remediation_attempts == 1
    assert finding.remediation_status == RemediationStatus.OPEN

    # Attempt 2: Trips circuit breaker
    orchestrator.apply_fix_with_guard(finding, failing_patch)
    assert finding.remediation_attempts == 2
    assert finding.remediation_status == RemediationStatus.QUARANTINED_BLOCKED


# =====================================================================
# P7-T14: Codebase Health Index (CHI) Mathematical Penalty Computation
# =====================================================================
def test_chi_formula_monotonic_penalty_computation():
    findings = []
    chi_clean, rating_clean = DeepInspectionEngine.compute_chi(findings, circular_cycles=0)
    assert chi_clean == 100.0
    assert rating_clean == "EXEMPLARY"

    # Add 1 CRITICAL finding (-30 points)
    crit_finding = VerifiedAuditFinding(
        finding_id="CRIT-1",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.CRITICAL,
        source=FindingSource.SECRET_SCAN,
        file_path="sec.py",
        line_start=1,
        line_end=1,
        code_snippet="secret",
        problem_statement="Critical secret leakage problem statement.",
        remediation_proposal="Sanitize critical secret from codebase.",
    )
    chi_crit, rating_crit = DeepInspectionEngine.compute_chi([crit_finding], circular_cycles=0)
    assert chi_crit == 70.0
    assert rating_crit == "DEGRADED"

    # Add 1 circular cycle (-20 points)
    chi_cycle, rating_cycle = DeepInspectionEngine.compute_chi([crit_finding], circular_cycles=1)
    assert chi_cycle == 50.0
    assert rating_cycle == "DEGRADED"


# =====================================================================
# P7-T15: Sentinel SQLite WAL Telemetry Persistence and Retrieval
# =====================================================================
def test_sentinel_sqlite_wal_persistence_and_query(tmp_path: Path):
    db_path = tmp_path / ".oragai" / "sentinel_diagnostics.db"
    db = SentinelDiagnosticsDB(db_path)

    metrics = CodebaseHealthMetrics(
        total_files=50,
        total_loc=4500,
        clean_static=False,
        chi_score=85.0,
        health_rating="HEALTHY",
        critical_findings_count=0,
        high_findings_count=1,
        medium_findings_count=0,
        low_findings_count=0,
        circular_dependency_cycles=0,
        mean_distance_main_sequence=0.1,
        line_coverage_ratio=0.88,
    )

    finding = VerifiedAuditFinding(
        finding_id="HIGH-001",
        category=FindingCategory.ARCHITECTURE,
        severity=FindingSeverity.HIGH,
        source=FindingSource.STATIC_AST,
        file_path="orchestrator/engine.py",
        line_start=15,
        line_end=20,
        ast_symbol="Engine.run",
        code_snippet="def run(): pass",
        problem_statement="Public function stub requires implementation.",
        remediation_proposal="Provide complete production implementation.",
        sha256_fingerprint="abc123def4567890",
    )

    db.record_run("RUN-TEST-01", "AUDIT", metrics, [finding], duration_sec=1.25)

    run_record = db.get_run("RUN-TEST-01")
    assert run_record is not None
    assert run_record["total_files"] == 50
    assert run_record["chi_score"] == 85.0
    assert run_record["health_rating"] == "HEALTHY"

    findings_records = db.get_findings_for_run("RUN-TEST-01")
    assert len(findings_records) == 1
    assert findings_records[0]["finding_id"] == "HIGH-001"
    assert findings_records[0]["severity"] == "HIGH"

    # Test WAL mode is active
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        assert mode.lower() == "wal"


# =====================================================================
# P7-T16: DeepInspectionEngine End-to-End Execution and Report Generation
# =====================================================================
def test_deep_inspection_engine_end_to_end(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    sample_file = src_dir / "app.py"
    sample_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

    db_path = tmp_path / "sentinel.db"
    engine = DeepInspectionEngine(tmp_path, db_path=db_path)

    findings, metrics = engine.execute_static_sweep(record_db=True, generate_report_files=True)
    assert metrics.total_files >= 1
    assert metrics.total_loc >= 2
    assert metrics.chi_score == 100.0
    assert metrics.clean_static is True

    # Verify generated report files
    json_path = tmp_path / "docs" / "audit_findings.json"
    md_path = tmp_path / "docs" / "AUDIT_REPORT.md"
    assert json_path.exists()
    assert md_path.exists()

    md_content = md_path.read_text(encoding="utf-8")
    assert "**Codebase Health Index (CHI):** 100.0 / 100.0" in md_content
    assert "No active defects detected" in md_content
