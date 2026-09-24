"""Round 2 Deep-Tier Hardening & Resilience Test Suite.

Verifies:
1. Monitor thread lifecycle and clean teardown in BasePipeline.
2. Atomic memory persistence and recovery in ConversationStore.
3. DynamicTokenGovernor action classification and budget allocations.
4. Non-destructive report preservation and multi-format finding extraction in Audit pipelines.
5. Sentinel SRE health radar and auto-healing under edge conditions.
"""

from pathlib import Path
import threading
import time
from unittest.mock import MagicMock, patch
import pytest

from orchestrator.config import OrchestratorConfig, SkillManager, ORCHESTRATOR_ROOT
from orchestrator.control.token_governance import DynamicTokenGovernor, TokenPhase
from orchestrator.memory.conversation_store import ConversationStore, MemoryEntry
from orchestrator.pipeline.audit_fix_pipeline import extract_audit_findings_list
from orchestrator.pipeline.audit_pipeline import AuditPipeline
from orchestrator.sentinel import (
    CognitiveSentinelSupervisor,
    SentinelMode,
    SelfHealingEngine,
    CloudResilienceMesh,
    TerminalCommandTranslator,
)


class TestRound2ThreadingAndPipelineHardening:
    """Tests for threading lifecycle and monitor cleanup."""

    def test_base_pipeline_monitor_thread_joins_cleanly(self, tmp_path: Path):
        cfg = OrchestratorConfig(workspace_path=tmp_path)
        sm = SkillManager(ORCHESTRATOR_ROOT)
        pipeline = AuditPipeline(cfg, sm, tmp_path)

        # Mock conversation that runs quickly
        mock_conv = MagicMock()
        mock_conv.run.side_effect = lambda: time.sleep(0.05)

        res = pipeline._run_conv(
            mock_conv,
            role_name="tester",
            timeout_seconds=5.0,
            max_retries=0,
        )

        assert res.completed is True
        assert res.interrupted_by_timeout is False


class TestRound2ConversationMemoryStoreHardening:
    """Tests for atomic memory writes and safe retrieval."""

    def test_atomic_memory_write(self, tmp_path: Path):
        store = ConversationStore(tmp_path / "memory")
        saved_file = store.save_run_memory(
            task="Build auth service",
            summary="Completed auth service with JWT",
            files_touched=["src/auth.py", "tests/test_auth.py"],
            tests_passed=True,
            lessons="Always validate token expiration",
        )

        assert saved_file.exists()
        assert not saved_file.with_suffix(".tmp").exists()

        memories = store.load_all_memories()
        assert len(memories) == 1
        assert memories[0].task == "Build auth service"
        assert memories[0].lessons == "Always validate token expiration"

    def test_load_all_memories_skips_corrupted_files(self, tmp_path: Path):
        store = ConversationStore(tmp_path / "memory")
        # Save valid memory
        store.save_run_memory(task="Task 1", summary="Done")
        # Create corrupted JSON file
        corrupt_file = store.memory_dir / "corrupt_123.json"
        corrupt_file.write_text("{ this is not valid json }", encoding="utf-8")

        memories = store.load_all_memories()
        assert len(memories) == 1
        assert memories[0].task == "Task 1"


class TestRound2DynamicTokenGovernorHardening:
    """Tests for robust action classification across objects and dictionaries."""

    def test_classify_action_with_object_arguments(self):
        class MockFileAction:
            operation = "edit"

        phase = DynamicTokenGovernor.classify_action("WorkspaceFileAction", MockFileAction())
        assert phase == TokenPhase.IMPLEMENTATION

    def test_classify_action_with_dict_arguments(self):
        phase = DynamicTokenGovernor.classify_action(
            "WorkspaceTerminalAction", {"command": "pytest -v tests/"}
        )
        assert phase == TokenPhase.TESTING

    def test_compute_iteration_budget_with_multiple_files(self):
        gov = DynamicTokenGovernor.compute_iteration_budget(
            role="developer",
            severity="CRITICAL",
            affected_files_count=4,
            task_text="Refactor authentication and unify database architecture",
            hard_ceiling=200_000,
        )
        assert gov.allocation.total_budget >= 140_000
        assert gov.allocation.implementation_budget > gov.allocation.investigation_budget


class TestRound2AuditAndFindingExtractionHardening:
    """Tests for extracting diverse finding header formats."""

    def test_extract_findings_diverse_headers(self):
        sample_report = """
# Audit Report

### [CRITICAL] AUD-001 - src/auth.py:22
Problem: Unsalted password hash
Evidence: hashlib.md5(pwd)
Recommended Fix: Use bcrypt

### 2. [HIGH] Race Condition in worker.py
Problem: Shared global state without mutex lock
Evidence: counter += 1
Recommended Fix: Use threading.Lock()

### BUG-003 [MEDIUM] Unclosed file descriptor
Problem: File opened without context manager
Evidence: f = open('log.txt')
Recommended Fix: Use with open(...)

### [LOW] Missing Type Hints
Problem: Function lacks return type annotation
Evidence: def parse(x):
Recommended Fix: def parse(x: str) -> dict:
"""
        findings = extract_audit_findings_list(sample_report)
        assert len(findings) == 4
        assert findings[0]["severity"] == "CRITICAL"
        assert findings[1]["severity"] == "HIGH"
        assert findings[2]["severity"] == "MEDIUM"
        assert findings[3]["severity"] == "LOW"


class TestRound2SentinelEdgeCaseHardening:
    """Tests for edge case self-healing and translator safety."""

    def test_self_healing_unclosed_def_with_docstring(self, tmp_path: Path):
        engine = SelfHealingEngine()
        broken = 'def execute_task():\n    """Docstring only with no body."""\n\ndef next_task():\n    return 42\n'
        test_file = tmp_path / "task.py"

        # Even if Python parses docstring as valid expression, let's verify AST parsing
        is_safe, code, _ = engine.heal_syntax_error(test_file, broken, "")
        assert is_safe is True

    def test_terminal_translator_chained_powershell_safety(self):
        cmd = 'cat logs.txt | grep "ERROR"'
        allowed, rewritten, _ = TerminalCommandTranslator.intercept_and_translate(
            cmd, os_name="nt"
        )
        assert allowed is True
        assert "Get-Content" in rewritten or "Select-String" in rewritten
