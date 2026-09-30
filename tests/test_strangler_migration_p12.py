"""Test suite for Phase 12: Strangler Fig Migration & Final Pipeline Consolidation.

Module: tests.test_strangler_migration_p12
Specification: docs/plans/P12_STRANGLER_FIG_MIGRATION_AND_SAFE_ROLLOUT_PLAN.md
"""

from __future__ import annotations

import json
import time
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.guards.preflight import PreFlightGuard
from orchestrator.orchestrator import Orchestrator
from orchestrator.pipeline import (
    AuditFixPipeline,
    AuditPipeline,
    CircuitBreakerStatus,
    DevTestLoop,
    DocumentationPipeline,
    ExecutionPlane,
    FullPipeline,
    GuardedFSMEngine,
    LifecycleProfile,
    MigrationGuard,
    MigrationRoutingConfig,
    OrchestratorDispatcher,
    PipelineMode,
    StranglerPipelineDispatcher,
    get_profile,
)


@pytest.fixture
def mock_ws(tmp_path: Path) -> Path:
    """Create a minimal valid workspace for pipeline execution tests."""
    (tmp_path / "app.py").write_text("def hello() -> str:\n    return 'world'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text(
        "from app import hello\ndef test_hello():\n    assert hello() == 'world'\n",
        encoding="utf-8",
    )
    return tmp_path


# ============================================================================
# 1. Pipeline Modes Routing to GuardedFSMEngine
# ============================================================================


@pytest.mark.parametrize(
    "mode,expected_pipeline_mode",
    [
        ("dev-test", PipelineMode.DEV_TEST),
        ("full", PipelineMode.FULL),
        ("audit", PipelineMode.AUDIT),
        ("audit-fix", PipelineMode.AUDIT_FIX),
        ("docs", PipelineMode.DOCS),
    ],
)
def test_all_5_pipeline_modes_route_to_guarded_fsm(
    mock_ws: Path, mode: str, expected_pipeline_mode: PipelineMode
):
    """Verify all 5 modes construct the appropriate LifecycleProfile and route through GuardedFSMEngine."""
    guard = MigrationGuard()
    guard.config.use_guarded_fsm = True
    guard.config.strangler_active = True
    guard.config.canary_percentage = 100

    dispatcher = OrchestratorDispatcher(migration_guard=guard)
    cfg = OrchestratorConfig(workspace_path=mock_ws)
    sm = SkillManager()

    mock_fsm_return = {
        "success": True,
        "status": "COMPLETED",
        "run_id": f"run_{mode}_123",
        "iterations": 1,
        "state_history": ["INIT", "PREFLIGHT", "COMPLETED"],
        "tokens_consumed": 250,
        "cost_usd": 0.002,
        "mutated_files": ["app.py"],
    }

    with patch.object(GuardedFSMEngine, "run", return_value=mock_fsm_return) as mock_engine_run:
        result = dispatcher.dispatch(
            task=f"Test execution for {mode}",
            mode=mode,
            config=cfg,
            skill_manager=sm,
            workspace=mock_ws,
        )

        assert mock_engine_run.call_count == 1
        assert result["plane"] == ExecutionPlane.MODERN_GUARDED_FSM.value
        assert result["mode"] == mode
        assert result["success"] is True
        assert result["status"] == "COMPLETED"
        assert result["run_id"] == f"run_{mode}_123"
        assert result["tokens_consumed"] == 250

        # Verify correct profile retrieval
        profile = get_profile(mode)
        assert profile.mode == expected_pipeline_mode


def test_orchestrator_entry_routes_through_dispatcher(mock_ws: Path):
    """Verify Orchestrator.run_task delegates through OrchestratorDispatcher to GuardedFSMEngine."""
    guard = MigrationGuard()
    guard.config.use_guarded_fsm = True
    guard.config.strangler_active = True
    guard.config.canary_percentage = 100

    dispatcher = OrchestratorDispatcher(migration_guard=guard)
    cfg = OrchestratorConfig(workspace_path=mock_ws)
    orch = Orchestrator(config=cfg, dispatcher=dispatcher)

    with patch.object(
        dispatcher,
        "dispatch",
        return_value={
            "success": True,
            "status": "COMPLETED",
            "plane": "MODERN_GUARDED_FSM",
            "mode": "dev-test",
            "run_id": "orch_test_001",
        },
    ) as mock_disp:
        res = orch.run_task("Build feature", mode="dev-test", workspace_override=mock_ws)
        assert res["success"] is True
        assert res["plane"] == "MODERN_GUARDED_FSM"
        mock_disp.assert_called_once()


# ============================================================================
# 2. Legacy Shims Parameter Passing & Conforming Results
# ============================================================================


def test_legacy_shims_delegation_to_fsm(mock_ws: Path):
    """Verify legacy pipeline classes pass parameters and return conforming result dictionaries."""
    cfg = OrchestratorConfig(workspace_path=mock_ws)
    sm = SkillManager()

    mock_res = {
        "success": True,
        "status": "COMPLETED",
        "run_id": "shim_run_456",
        "iterations": 1,
        "tokens_consumed": 150,
        "cost_usd": 0.001,
        "mutated_files": [],
    }

    # 1. DevTestLoop shim
    dev_shim = DevTestLoop(cfg, sm, mock_ws)
    with patch.object(GuardedFSMEngine, "run", return_value=mock_res):
        res1 = dev_shim.run("Dev test task", use_strangler=True)
        assert res1["success"] is True
        assert res1["plane"] == ExecutionPlane.MODERN_GUARDED_FSM.value
        assert res1["mode"] == "dev-test"

    # 2. FullPipeline shim
    full_shim = FullPipeline(cfg, sm, mock_ws)
    with patch.object(GuardedFSMEngine, "run", return_value=mock_res):
        res2 = full_shim.run("Full architecture task", use_strangler=True)
        assert res2["success"] is True
        assert res2["plane"] == ExecutionPlane.MODERN_GUARDED_FSM.value
        assert res2["mode"] == "full"

    # 3. AuditPipeline shim
    audit_shim = AuditPipeline(cfg, sm, mock_ws)
    with patch.object(GuardedFSMEngine, "run", return_value=mock_res):
        res3 = audit_shim.run("Audit task", use_strangler=True)
        assert res3["success"] is True
        assert res3["plane"] == ExecutionPlane.MODERN_GUARDED_FSM.value
        assert res3["mode"] == "audit"

    # 4. AuditFixPipeline shim
    audit_fix_shim = AuditFixPipeline(cfg, sm, mock_ws, auto_chain_audit=False)
    with patch.object(GuardedFSMEngine, "run", return_value=mock_res):
        res4 = audit_fix_shim.run("Audit fix task", use_strangler=True)
        assert res4["success"] is True
        assert res4["plane"] == ExecutionPlane.MODERN_GUARDED_FSM.value
        assert res4["mode"] == "audit-fix"

    # 5. DocumentationPipeline shim
    docs_shim = DocumentationPipeline(cfg, sm, mock_ws)
    with patch.object(GuardedFSMEngine, "run", return_value=mock_res):
        res5 = docs_shim.run("Docs task", use_strangler=True)
        assert res5["success"] is True
        assert res5["plane"] == ExecutionPlane.MODERN_GUARDED_FSM.value
        assert res5["mode"] == "docs"


def test_legacy_shims_fallback_conforming_results(mock_ws: Path):
    """Verify legacy fallback execution returns conforming dictionaries with plane='LEGACY_FALLBACK'."""
    cfg = OrchestratorConfig(workspace_path=mock_ws)
    sm = SkillManager()
    guard = MigrationGuard()
    guard.config.use_guarded_fsm = False  # Disable modern FSM
    dispatcher = OrchestratorDispatcher(migration_guard=guard)

    pipe = DevTestLoop(cfg, sm, mock_ws)
    with patch.object(pipe, "_run_legacy", return_value={"status": "LEGACY_OK", "report_id": "rep_999"}):
        res = dispatcher.dispatch(
            task="Fallback task",
            mode="dev-test",
            config=cfg,
            skill_manager=sm,
            workspace=mock_ws,
            legacy_pipeline=pipe,
        )

        assert res["plane"] == ExecutionPlane.LEGACY_FALLBACK.value
        assert res["status"] == "LEGACY_OK"
        assert res["report_id"] == "rep_999"
        assert res["run_id"] == "rep_999"
        assert "tokens_consumed" in res
        assert "cost_usd" in res


# ============================================================================
# 3. Flag Toggling in Migration Routing Config
# ============================================================================


def test_flag_toggling_alternates_execution_paths(mock_ws: Path):
    """Verify toggling migration flags safely alternates execution paths without crashing."""
    guard = MigrationGuard()

    # Case 1: All active -> routes to Modern
    guard.update_config({"use_guarded_fsm": True, "strangler_active": True, "canary_percentage": 100})
    assert guard.should_route_to_modern("dev-test", workspace=mock_ws) is True
    assert guard.get_active_plane("dev-test", workspace=mock_ws) == ExecutionPlane.MODERN_GUARDED_FSM

    # Case 2: use_guarded_fsm = False -> routes to Legacy
    guard.update_config({"use_guarded_fsm": False})
    assert guard.should_route_to_modern("dev-test", workspace=mock_ws) is False
    assert guard.get_active_plane("dev-test", workspace=mock_ws) == ExecutionPlane.LEGACY_FALLBACK

    # Case 3: strangler_active = False -> routes to Legacy
    guard.update_config({"use_guarded_fsm": True, "strangler_active": False})
    assert guard.should_route_to_modern("dev-test", workspace=mock_ws) is False
    assert guard.get_active_plane("dev-test", workspace=mock_ws) == ExecutionPlane.LEGACY_FALLBACK

    # Case 4: canary_percentage = 0 -> routes to Legacy
    guard.update_config({"strangler_active": True, "canary_percentage": 0})
    assert guard.should_route_to_modern("dev-test", workspace=mock_ws) is False
    assert guard.get_active_plane("dev-test", workspace=mock_ws) == ExecutionPlane.LEGACY_FALLBACK

    # Case 5: canary_percentage = 100 -> routes to Modern
    guard.update_config({"canary_percentage": 100})
    assert guard.should_route_to_modern("dev-test", workspace=mock_ws) is True
    assert guard.get_active_plane("dev-test", workspace=mock_ws) == ExecutionPlane.MODERN_GUARDED_FSM


def test_canary_deterministic_hashing(mock_ws: Path):
    """Verify deterministic 50% canary traffic split."""
    guard = MigrationGuard()
    guard.update_config({"use_guarded_fsm": True, "strangler_active": True, "canary_percentage": 50})

    results = [
        guard.should_route_to_modern(mode="dev-test", task=f"Task number {i}", workspace=mock_ws)
        for i in range(200)
    ]
    modern_count = sum(1 for r in results if r)
    # Statistical split should be roughly balanced (between 35% and 65%)
    assert 70 <= modern_count <= 130


# ============================================================================
# 4. Rollback & Health Verification Harness (Trip-Wires)
# ============================================================================


def test_runtime_exception_triggers_fallback(mock_ws: Path):
    """TW-01: Verify unhandled exception in GuardedFSMEngine triggers safe fallback to Legacy."""
    guard = MigrationGuard()
    guard.update_config(
        {"use_guarded_fsm": True, "canary_percentage": 100, "fallback_to_legacy_on_error": True}
    )
    dispatcher = OrchestratorDispatcher(migration_guard=guard)
    cfg = OrchestratorConfig(workspace_path=mock_ws)
    sm = SkillManager()

    pipe = DevTestLoop(cfg, sm, mock_ws)

    with (
        patch.object(GuardedFSMEngine, "run", side_effect=RuntimeError("Simulated FSM crash")),
        patch.object(pipe, "_run_legacy", return_value={"status": "FALLBACK_SUCCESS", "run_id": "fb_1"}),
    ):
        res = dispatcher.dispatch(
            task="Crash test",
            mode="dev-test",
            config=cfg,
            skill_manager=sm,
            workspace=mock_ws,
            legacy_pipeline=pipe,
        )

        assert res["status"] == "FALLBACK_SUCCESS"
        assert res["plane"] == ExecutionPlane.LEGACY_FALLBACK.value

        # Check telemetry recorded the failure and fallback
        summary = guard.get_telemetry_summary()
        assert summary["modern_failures"] == 1
        assert summary["fallbacks_triggered"] == 1


def test_consecutive_errors_trip_circuit_breaker(mock_ws: Path):
    """TW-02: Verify 3 consecutive target failures trip circuit breaker to OPEN."""
    guard = MigrationGuard()
    guard.update_config(
        {
            "use_guarded_fsm": True,
            "canary_percentage": 100,
            "circuit_breaker_error_threshold": 3,
            "fallback_to_legacy_on_error": True,
        }
    )
    dispatcher = OrchestratorDispatcher(migration_guard=guard)
    cfg = OrchestratorConfig(workspace_path=mock_ws)
    sm = SkillManager()
    pipe = DevTestLoop(cfg, sm, mock_ws)

    with (
        patch.object(GuardedFSMEngine, "run", side_effect=RuntimeError("Persistent failure")),
        patch.object(pipe, "_run_legacy", return_value={"status": "FALLBACK_OK"}),
    ):
        for i in range(3):
            dispatcher.dispatch("Fail task", "dev-test", cfg, sm, mock_ws, legacy_pipeline=pipe)

        # After 3 failures, circuit breaker must be OPEN
        assert guard.circuit_status == CircuitBreakerStatus.OPEN
        assert guard.should_route_to_modern("dev-test", workspace=mock_ws) is False

        # Next run routes directly to legacy without calling modern
        with patch.object(GuardedFSMEngine, "run") as mock_engine:
            res = dispatcher.dispatch("After trip", "dev-test", cfg, sm, mock_ws, legacy_pipeline=pipe)
            assert res["plane"] == ExecutionPlane.LEGACY_FALLBACK.value
            mock_engine.assert_not_called()


def test_instant_rollback_and_reset(mock_ws: Path):
    """Verify execute_instant_rollback() diverts traffic immediately and reset restores operation."""
    guard = MigrationGuard()
    guard.update_config({"use_guarded_fsm": True, "canary_percentage": 100})
    assert guard.should_route_to_modern("dev-test", workspace=mock_ws) is True

    # Execute rollback
    guard.execute_instant_rollback(reason="Test incident rollback", persist=False)
    assert guard.circuit_status == CircuitBreakerStatus.OPEN
    assert guard.config.use_guarded_fsm is False
    assert guard.config.canary_percentage == 0
    assert guard.should_route_to_modern("dev-test", workspace=mock_ws) is False

    # Reset circuit breaker & restore
    guard.reset_circuit_breaker()
    guard.update_config({"use_guarded_fsm": True, "canary_percentage": 100})
    assert guard.circuit_status == CircuitBreakerStatus.CLOSED
    assert guard.should_route_to_modern("dev-test", workspace=mock_ws) is True


def test_verify_runtime_health(mock_ws: Path):
    """Verify runtime health check reports health metrics and clean syntax."""
    guard = MigrationGuard()
    health = guard.verify_runtime_health(mock_ws)
    assert health["healthy"] is True
    assert health["circuit_status"] == "CLOSED"
    assert health["syntax_clean"] is True
    assert health["consecutive_errors"] == 0


# ============================================================================
# 5. Legacy Facade Deprecation & Direct Import Verification
# ============================================================================


def test_legacy_utils_facades_emit_deprecation_warnings():
    """Verify all re-export wrappers in orchestrator.utils emit DeprecationWarning."""
    import importlib
    import sys

    for mod_name in [
        "orchestrator.utils.git_ops",
        "orchestrator.utils.visualizer",
        "orchestrator.utils.pytest_parser",
        "orchestrator.utils.output",
        "orchestrator.utils.graft_context",
        "orchestrator.utils.skill_compressor",
        "orchestrator.utils.sdk_patch",
    ]:
        sys.modules.pop(mod_name, None)
        with pytest.deprecated_call():
            importlib.import_module(mod_name)


def test_direct_domain_package_imports():
    """Verify direct domain package imports without deprecation warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        from orchestrator.analysis.graft_context import GraftContextProvider
        from orchestrator.analysis.pytest_parser import PytestOutputParser
        from orchestrator.rendering.output import ConsoleOutput
        from orchestrator.skills.compressor import CompactSkillInjector
        from orchestrator.ui.visualizer import OrchestratorLiveVisualizer
        from orchestrator.vcs.git_ops import GitOps

        assert GraftContextProvider is not None
        assert PytestOutputParser is not None
        assert ConsoleOutput is not None
        assert CompactSkillInjector is not None
        assert OrchestratorLiveVisualizer is not None
        assert GitOps is not None


# ============================================================================
# 6. Tarjan's SCC Zero Circular Dependency Invariant
# ============================================================================


def test_tarjan_scc_zero_circular_dependencies():
    """Verify zero circular import dependency cycles across the entire repository."""
    from orchestrator.analysis.audit.scanner import StaticAnalysisScanner

    scanner = StaticAnalysisScanner(Path("."))
    cycles = scanner._scan_circular_dependencies()
    assert (
        len(cycles) == 0
    ), f"Circular dependencies detected: {[c.problem_statement for c in cycles]}"


# ============================================================================
# 7. PreFlight Syntax Gate Clean Invariant
# ============================================================================


def test_preflight_syntax_clean_workspace():
    """PreFlight syntax check must remain 100% clean across all repository files."""
    is_clean, err_msg = PreFlightGuard.check_syntax(Path("."), auto_heal=False)
    assert is_clean is True, f"PreFlight syntax check failed: {err_msg}"


def test_migration_guard_singleton_reset_and_cooldown():
    """TASK-008: Verify reset_instance, reset, and circuit breaker cooldown recovery."""
    guard = MigrationGuard.get_instance()
    guard.trip_circuit_breaker("Test trip")
    assert guard.circuit_status == CircuitBreakerStatus.OPEN
    assert guard.should_route_to_modern("dev-test") is False

    # Verify reset clears in-memory state
    guard.reset()
    assert guard.circuit_status == CircuitBreakerStatus.CLOSED
    assert len(guard.telemetry_records) == 0

    # Trip again and simulate cooldown expiry
    guard.trip_circuit_breaker("Cooldown test trip")
    guard._circuit_tripped_at = time.time() - 120.0  # 2 minutes ago
    guard.config.circuit_breaker_cooldown_seconds = 60.0

    # Should transition to HALF_OPEN and allow routing
    assert guard.should_route_to_modern("dev-test") is True
    assert guard.circuit_status == CircuitBreakerStatus.HALF_OPEN

    # Reset instance
    MigrationGuard.reset_instance()
    fresh_guard = MigrationGuard.get_instance()
    assert fresh_guard is not guard

