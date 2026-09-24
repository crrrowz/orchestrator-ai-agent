"""Integration tests verifying systemic root-cause fixes, thread safety, and resilience."""

import json
import sqlite3
import threading
from pathlib import Path

from orchestrator.analysis.graft_context import GraftContextProvider
from orchestrator.control.token_governance import DynamicTokenGovernor, TokenPhase
from orchestrator.memory.conversation_store import (
    ConversationMemoryStore,
    ConversationStore,
    SessionMemoryStore,
)
from orchestrator.pipeline.audit_report_io import locate_and_normalize_report
from orchestrator.pipeline.state_machine import PipelinePhase, PipelineStateMachine
from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB
from orchestrator.telemetry.recorder import TelemetryRecorder
from orchestrator.tools.workspace_tools import (
    WorkspaceFileAction,
    execute_file_action,
)
from orchestrator.ui.session_store import SessionLogStore


def test_circuit_breaker_dual_signature_compatibility(tmp_path: Path):
    """Verify TelemetryRecorder.check_circuit_breaker supports single and dual argument signatures."""
    rec = TelemetryRecorder(
        task_description="test circuit breaker signature",
        reports_dir=tmp_path / "reports",
        circuit_breaker_threshold=2,
    )

    # 1. Single argument call (diff empty, only error text provided)
    tripped_1 = rec.check_circuit_breaker("AssertionError: test_app failed")
    assert tripped_1 is False
    tripped_2 = rec.check_circuit_breaker("AssertionError: test_app failed")
    assert tripped_2 is True

    rec.reset()
    # 2. Dual argument call (diff_text, error_text)
    t_dual_1 = rec.check_circuit_breaker("diff --git a/app.py", "SyntaxError: invalid syntax")
    assert t_dual_1 is False
    t_dual_2 = rec.check_circuit_breaker("diff --git a/app.py", "SyntaxError: invalid syntax")
    assert t_dual_2 is True


def test_memory_store_aliases_and_workspace_resolution(tmp_path: Path):
    """Verify ConversationStore, SessionMemoryStore, and ConversationMemoryStore aliases work uniformly."""
    store1 = ConversationStore(workspace_path=tmp_path)
    store2 = SessionMemoryStore(workspace_path=tmp_path)
    store3 = ConversationMemoryStore(memory_dir=tmp_path / "diagnostics" / "memory")

    assert isinstance(store1, ConversationStore)
    assert isinstance(store2, ConversationStore)
    assert isinstance(store3, ConversationStore)

    # Save a run memory and format context
    store1.save_run_memory(
        task="refactor authentication service",
        summary="Swapped basic auth to OAuth2 JWT provider successfully",
        files_touched=["auth/service.py"],
        tests_passed=True,
    )

    ctx = store2.format_memory_context("refactor authentication service")
    assert ctx is not None
    assert "OAuth2 JWT" in ctx


def test_session_log_store_thread_safety(tmp_path: Path):
    """Verify SessionLogStore handles concurrent multi-threaded writes without race conditions."""
    store = SessionLogStore(workspace_path=tmp_path)

    def worker(worker_id: int):
        for i in range(20):
            store.add_step(
                summary=f"Worker {worker_id} action {i}",
                action_type="WorkspaceFileTool",
                arguments={"path": f"src/file_{worker_id}.py"},
            )

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(store.steps) == 100
    saved_file = store.save_to_file()
    assert saved_file.exists()
    data = json.loads(saved_file.read_text(encoding="utf-8"))
    assert len(data["steps"]) == 100


def test_sqlite_diagnostics_wal_and_busy_timeout(tmp_path: Path):
    """Verify SentinelDiagnosticsDB initializes with WAL mode and handles concurrent access."""
    db_file = tmp_path / "sentinel.db"
    db = SentinelDiagnosticsDB(db_path=db_file)

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    conn.close()

    assert str(mode).upper() == "WAL"

    # Concurrent cloud call recording
    def log_calls(worker_id: int):
        for i in range(10):
            db.record_cloud_call(
                provider="openrouter",
                model=f"qwen_{worker_id}",
                latency_ms=120.5,
                success=True,
            )

    threads = [threading.Thread(target=log_calls, args=(t,)) for t in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stats = db.get_stats()
    assert stats["total_cloud_calls"] == 40


def test_symbol_extraction_character_budget_clamping(tmp_path: Path):
    """Verify operation='symbol' clamps oversized symbol outputs to prevent LLM context exhaustion."""
    large_func_lines = ["def massive_function():\n"]
    for i in range(500):
        large_func_lines.append(f"    var_{i} = 'some long repetitive value to balloon output size {i}'\n")

    py_file = tmp_path / "large_module.py"
    py_file.write_text("".join(large_func_lines), encoding="utf-8")

    act = WorkspaceFileAction(operation="symbol", path="large_module.py", symbol="massive_function")
    obs = execute_file_action(act, base_dir=tmp_path)

    assert obs.success is True
    assert len(obs.file_content) <= 13_000
    assert "Governance Notice" in obs.file_content or len(obs.file_content) <= 12_000


def test_token_governor_action_classification():
    """Verify DynamicTokenGovernor classifies modern action names into appropriate token phases."""
    assert DynamicTokenGovernor.classify_action("WorkspaceFileTool", {"operation": "edit"}) == TokenPhase.IMPLEMENTATION
    assert DynamicTokenGovernor.classify_action("WorkspaceFileTool", {"operation": "read"}) == TokenPhase.INVESTIGATION
    assert DynamicTokenGovernor.classify_action("WorkspaceTerminalTool", {"command": "pytest -v"}) == TokenPhase.TESTING
    assert DynamicTokenGovernor.classify_action("WorkspaceTerminalTool", {"command": "git status"}) == TokenPhase.TESTING
    assert DynamicTokenGovernor.classify_action("WorkspaceTerminalTool", {"command": "python script.py"}) == TokenPhase.INVESTIGATION


def test_graft_condensed_map_alias_compatibility(tmp_path: Path):
    """Verify GraftContextProvider exposes get_condensed_map alias for get_compact_map."""
    assert hasattr(GraftContextProvider, "get_condensed_map")
    assert hasattr(GraftContextProvider, "get_compact_map")
    assert GraftContextProvider.get_condensed_map == GraftContextProvider.get_compact_map


def test_audit_report_io_case_insensitivity(tmp_path: Path):
    """Verify locate_and_normalize_report resolves report filenames case-insensitively."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    report_file = docs_dir / "audit_report.md"
    report_file.write_text("# Audit Report", encoding="utf-8")

    found = locate_and_normalize_report(tmp_path, "AUDIT_REPORT.md")
    assert found is not None
    assert found.name.lower() == "audit_report.md"
