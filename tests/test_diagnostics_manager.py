"""Unit tests verifying DiagnosticsManager, indexing, search, and cleanup."""

import json
from pathlib import Path

from orchestrator.diagnostics import DiagnosticsManager
from orchestrator.memory.conversation_store import ConversationStore
from orchestrator.telemetry.recorder import TelemetryRecorder


def test_diagnostics_manager_overview_and_indexing(tmp_path: Path):
    diag_dir = tmp_path / "diagnostics"
    diag_dir.mkdir()
    reports_dir = diag_dir / "reports"
    reports_dir.mkdir()
    memory_dir = diag_dir / "memory"
    memory_dir.mkdir()
    logs_dir = diag_dir / "logs"
    logs_dir.mkdir()

    # Create dummy report
    rec = TelemetryRecorder(
        task_description="Implement feature X",
        reports_dir=reports_dir,
        max_retained_reports=10,
    )
    rec.finalize(completed_successfully=True)

    # Save memory
    mem_store = ConversationStore(memory_dir=memory_dir)
    mem_store.save_run_memory(
        task="Implement feature X",
        summary="Done with JWT and tests",
        files_touched=["src/feature.py"],
        tests_passed=True,
        lessons="Always check token expiration",
    )

    manager = DiagnosticsManager(diagnostics_dir=diag_dir)
    overview = manager.get_overview()

    assert overview["reports"]["total"] >= 1
    assert overview["reports"]["successful"] >= 1
    assert overview["memory"]["total_memories"] >= 1

    # Check search
    matching_mems = manager.memory_store.search_memories("JWT")
    assert len(matching_mems) >= 1
    assert matching_mems[0].task == "Implement feature X"

    # Test clean and index generation
    clean_res = manager.clean()
    assert (diag_dir / "INDEX.md").exists()
    assert "Implement feature X" in (diag_dir / "INDEX.md").read_text(encoding="utf-8")
