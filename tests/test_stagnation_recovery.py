"""Tests for Phase 8: Progress, Stagnation & Recovery Engine.

Verifies:
- P8-T01: Semantic tracker ignores comment/whitespace churn (V_code == 0.0, STAGNANT).
- P8-T02: Semantic tracker detects real AST changes (V_code > 0.0, MAKING_PROGRESS).
- P8-T03: Verification velocity advances on passing tests (V_verif == 3.0, THRIVING).
- P8-T04: Verification velocity detects severe regressions (V_verif < -2.0, REGRESSING).
- P8-T05: Oscillation detector identifies Direct Stagnation (period = 1).
- P8-T06: Oscillation detector identifies Flip-Flop cycles (period = 2).
- P8-T07: Oscillation detector identifies Periodic cycles (period = 3..5).
- P8-T08: Adaptive circuit breaker transitions CLOSED -> DEGRADED on 1 stagnant turn.
- P8-T09: Adaptive circuit breaker transitions to STRATEGY_MUTATING on 2 failures or cycle.
- P8-T10: Strategy mutator Tier 1 generates prompt steering injections.
- P8-T11: Strategy mutator Tier 2 decomposes milestones into sub-atomic tasks.
- P8-T12: Strategy mutator Tier 3 constricts tools (bans bash, forces file tools).
- P8-T13: Strategy mutator Tier 4 designates high-reasoning elevated model.
- P8-T14: Recovery orchestrator triggers atomic rollback on severe test regression.
- P8-T15: Recovery orchestrator quarantines milestone on tier 4 exhaustion.
- P8-T16: Sentinel SQLite WAL logs progress snapshots and recovery events.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import pytest

from orchestrator.control.recovery import (
    AdaptiveCircuitBreaker,
    BreakerState,
    CyclePattern,
    MutationStrategyType,
    OscillationDetector,
    ProgressHealth,
    RecoveryActionType,
    RecoveryOrchestrator,
    SemanticProgressTracker,
    StateFingerprint,
    StrategyMutator,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Fixture providing an isolated workspace."""
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


# ============================================================================
# P8-T01 & P8-T02: Semantic Progress Tracker (AST Normalization)
# ============================================================================

def test_semantic_tracker_ignores_comment_whitespace(temp_workspace: Path):
    """P8-T01: Adding whitespace/comments/docstrings produces zero AST delta (V_code == 0.0)."""
    module = temp_workspace / "core.py"
    module.write_text(
        "def compute(a, b):\n"
        "    return a + b\n",
        encoding="utf-8",
    )

    tracker = SemanticProgressTracker(temp_workspace)
    tracker.initialize_baseline()

    # Modify only whitespace, comments, and add a docstring
    module.write_text(
        "def compute(a, b):\n"
        '    """Calculates sum of two values."""\n'
        "    # A comment here\n"
        "\n"
        "    return a + b\n"
        "    # Another comment\n",
        encoding="utf-8",
    )

    metrics = tracker.record_turn_snapshot(
        turn_index=1,
        passed_test_nodes=set(),
        failed_test_nodes={},
        satisfied_ac_ids=set(),
        open_defect_ids=set(),
        tokens_consumed=500,
    )

    assert metrics.v_code == 0.0
    assert metrics.health == ProgressHealth.STAGNANT


def test_semantic_tracker_detects_real_ast_change(temp_workspace: Path):
    """P8-T02: Adding a new function modifies AST symbol table (V_code > 0.0, MAKING_PROGRESS)."""
    module = temp_workspace / "core.py"
    module.write_text(
        "def compute(a, b):\n"
        "    return a + b\n",
        encoding="utf-8",
    )

    tracker = SemanticProgressTracker(temp_workspace)
    tracker.initialize_baseline()

    # Add a new function
    module.write_text(
        "def compute(a, b):\n"
        "    return a + b\n\n"
        "def multiply(a, b):\n"
        "    return a * b\n",
        encoding="utf-8",
    )

    metrics = tracker.record_turn_snapshot(
        turn_index=1,
        passed_test_nodes=set(),
        failed_test_nodes={},
        satisfied_ac_ids=set(),
        open_defect_ids=set(),
        tokens_consumed=500,
    )

    assert metrics.v_code > 0.0
    assert metrics.health == ProgressHealth.MAKING_PROGRESS


# ============================================================================
# P8-T03 & P8-T04: Verification Delta Velocity (V_verif)
# ============================================================================

def test_verification_velocity_positive_advance(temp_workspace: Path):
    """P8-T03: Fixing 2 test nodes yields positive verification score (V_verif == 3.0, THRIVING)."""
    tracker = SemanticProgressTracker(temp_workspace)
    tracker.initialize_baseline(
        passed_test_nodes={"test_1"},
        failed_test_nodes={"test_2": "err2", "test_3": "err3"},
    )

    # Both failing tests fixed and now passing
    metrics = tracker.record_turn_snapshot(
        turn_index=1,
        passed_test_nodes={"test_1", "test_2", "test_3"},
        failed_test_nodes={},
        satisfied_ac_ids=set(),
        open_defect_ids=set(),
        tokens_consumed=1000,
    )

    # delta_pass = 2, delta_fail = 2 -> V_verif = 2 + 0.5 * 2 = 3.0
    assert metrics.v_verif == 3.0
    assert metrics.health == ProgressHealth.THRIVING


def test_verification_velocity_detects_severe_regression(temp_workspace: Path):
    """P8-T04: Breaking 2 previously passing test nodes triggers regression (V_verif < -2.0, REGRESSING)."""
    tracker = SemanticProgressTracker(temp_workspace)
    tracker.initialize_baseline(
        passed_test_nodes={"test_1", "test_2", "test_3"},
        failed_test_nodes={},
    )

    # Turn breaks test_2 and test_3
    metrics = tracker.record_turn_snapshot(
        turn_index=1,
        passed_test_nodes={"test_1"},
        failed_test_nodes={"test_2": "broken", "test_3": "broken"},
        satisfied_ac_ids=set(),
        open_defect_ids=set(),
        tokens_consumed=1000,
    )

    # delta_pass = -2, delta_fail = -2 -> V_verif = -2 + 0.5 * (-2) = -3.0
    assert metrics.v_verif == -3.0
    assert metrics.v_verif < -2.0
    assert metrics.health == ProgressHealth.REGRESSING


def test_evidence_and_defect_velocity(temp_workspace: Path):
    """Verifies AC satisfaction velocity and verified defect resolution velocity."""
    tracker = SemanticProgressTracker(temp_workspace)
    tracker.initialize_baseline(
        satisfied_ac_ids={"AC-1"},
        open_defect_ids={"DEF-1", "DEF-2"},
    )

    metrics = tracker.record_turn_snapshot(
        turn_index=1,
        passed_test_nodes=set(),
        failed_test_nodes={},
        satisfied_ac_ids={"AC-1", "AC-2"},  # 1 new AC (+2.0)
        open_defect_ids={"DEF-2"},            # 1 resolved defect (+1.0)
        tokens_consumed=1000,
    )

    assert metrics.v_evid == 2.0
    assert metrics.v_defect == 1.0
    assert metrics.per_score > 0.0


# ============================================================================
# P8-T05, P8-T06, P8-T07: Sliding-Window Oscillation Detection
# ============================================================================

def test_oscillation_detector_detects_direct_stagnation():
    """P8-T05: Identical state back-to-back detected with period = 1 (DIRECT_STAGNATION)."""
    detector = OscillationDetector(window_size=5)

    fp1 = StateFingerprint(turn_index=1, ast_composite_hash="ast_A", failing_tests_hash="fail_A", defect_state_hash="def_0")
    pattern, period = detector.register_state(fp1)
    assert pattern == CyclePattern.NONE

    fp2 = StateFingerprint(turn_index=2, ast_composite_hash="ast_A", failing_tests_hash="fail_A", defect_state_hash="def_0")
    pattern, period = detector.register_state(fp2)
    assert pattern == CyclePattern.DIRECT_STAGNATION
    assert period == 1


def test_oscillation_detector_detects_p2_flip_flop_cycle():
    """P8-T06: State flips A -> B -> A detected with period = 2 (FLIP_FLOP_P2)."""
    detector = OscillationDetector(window_size=5)

    fp_a1 = StateFingerprint(turn_index=1, ast_composite_hash="ast_A", failing_tests_hash="fail_A", defect_state_hash="def_0")
    fp_b = StateFingerprint(turn_index=2, ast_composite_hash="ast_B", failing_tests_hash="fail_B", defect_state_hash="def_0")
    fp_a2 = StateFingerprint(turn_index=3, ast_composite_hash="ast_A", failing_tests_hash="fail_A", defect_state_hash="def_0")

    detector.register_state(fp_a1)
    detector.register_state(fp_b)
    pattern, period = detector.register_state(fp_a2)

    assert pattern == CyclePattern.FLIP_FLOP_P2
    assert period == 2


def test_oscillation_detector_detects_p3_periodic_cycle():
    """P8-T07: Cycle A -> B -> C -> A detected with period = 3 (PERIODIC_PN)."""
    detector = OscillationDetector(window_size=5)

    fp_a = StateFingerprint(turn_index=1, ast_composite_hash="ast_A", failing_tests_hash="fail_A", defect_state_hash="def_0")
    fp_b = StateFingerprint(turn_index=2, ast_composite_hash="ast_B", failing_tests_hash="fail_B", defect_state_hash="def_0")
    fp_c = StateFingerprint(turn_index=3, ast_composite_hash="ast_C", failing_tests_hash="fail_C", defect_state_hash="def_0")
    fp_a2 = StateFingerprint(turn_index=4, ast_composite_hash="ast_A", failing_tests_hash="fail_A", defect_state_hash="def_0")

    detector.register_state(fp_a)
    detector.register_state(fp_b)
    detector.register_state(fp_c)
    pattern, period = detector.register_state(fp_a2)

    assert pattern == CyclePattern.PERIODIC_PN
    assert period == 3


# ============================================================================
# P8-T08 & P8-T09: Adaptive Circuit Breaker
# ============================================================================

def test_adaptive_breaker_transitions_closed_to_degraded():
    """P8-T08: 1 stagnant turn moves state from CLOSED to DEGRADED."""
    breaker = AdaptiveCircuitBreaker(max_mutation_tiers=4)
    assert breaker.state == BreakerState.CLOSED

    stagnant_metrics = tracker_metrics_stub(health=ProgressHealth.STAGNANT, v_verif=0.0)
    state = breaker.evaluate_state_transition(stagnant_metrics, CyclePattern.NONE)

    assert state == BreakerState.DEGRADED
    assert breaker.stagnation_counter == 1


def test_adaptive_breaker_transitions_to_mutating():
    """P8-T09: 2 stagnant turns or P2 cycle moves to STRATEGY_MUTATING."""
    breaker = AdaptiveCircuitBreaker(max_mutation_tiers=4)

    stagnant_metrics = tracker_metrics_stub(health=ProgressHealth.STAGNANT, v_verif=0.0)
    breaker.evaluate_state_transition(stagnant_metrics, CyclePattern.NONE)  # Turn 1 -> DEGRADED
    state = breaker.evaluate_state_transition(stagnant_metrics, CyclePattern.NONE)  # Turn 2 -> STRATEGY_MUTATING

    assert state == BreakerState.STRATEGY_MUTATING
    assert breaker.mutation_tier_level == 1

    # Immediate escalation to mutating on Flip-Flop cycle
    breaker.reset()
    state = breaker.evaluate_state_transition(stagnant_metrics, CyclePattern.FLIP_FLOP_P2)
    assert state == BreakerState.STRATEGY_MUTATING
    assert breaker.mutation_tier_level == 1


def test_adaptive_breaker_recovers_on_positive_progress():
    """Breaker relaxes and returns to CLOSED when genuine progress occurs."""
    breaker = AdaptiveCircuitBreaker(max_mutation_tiers=4)
    stagnant_metrics = tracker_metrics_stub(health=ProgressHealth.STAGNANT, v_verif=0.0)
    breaker.evaluate_state_transition(stagnant_metrics, CyclePattern.NONE)
    assert breaker.state == BreakerState.DEGRADED

    thriving_metrics = tracker_metrics_stub(health=ProgressHealth.THRIVING, v_verif=2.0)
    state = breaker.evaluate_state_transition(thriving_metrics, CyclePattern.NONE)
    assert state == BreakerState.CLOSED
    assert breaker.stagnation_counter == 0


# ============================================================================
# P8-T10 to P8-T13: Strategy Mutator Tiers 1-4
# ============================================================================

def test_strategy_mutator_tier1_prompt_steering_injection():
    """P8-T10: Level 1 generates anti-oscillation prompt steering directives."""
    mutator = StrategyMutator()
    directive = mutator.generate_mutation(
        current_tier=1,
        failing_tests={"tests/test_x.py::test_fail": "AssertionError: 5 != 10"},
        cycle_pattern=CyclePattern.FLIP_FLOP_P2,
        active_milestone_id="M-1",
    )

    assert directive.mutation_type == MutationStrategyType.PROMPT_STEERING
    assert directive.tier_level == 1
    assert any("OSCILLATION DETECTED" in h for h in directive.prompt_injections)
    assert any("tests/test_x.py::test_fail" in h for h in directive.prompt_injections)


def test_strategy_mutator_tier2_target_decomposition():
    """P8-T11: Level 2 decomposes milestone into sub-atomic tasks."""
    mutator = StrategyMutator()
    directive = mutator.generate_mutation(
        current_tier=2,
        failing_tests={"tests/test_y.py::test_bad": "ValueError: missing key"},
        cycle_pattern=CyclePattern.DIRECT_STAGNATION,
        active_milestone_id="M-2",
    )

    assert directive.mutation_type == MutationStrategyType.TARGET_DECOMPOSITION
    assert directive.tier_level == 2
    assert len(directive.decomposed_subtasks) >= 3
    assert any("SUBTASK-1" in s for s in directive.decomposed_subtasks)


def test_strategy_mutator_tier3_tool_constriction_active():
    """P8-T12: Level 3 disables bash/terminal and locks to file tool only."""
    mutator = StrategyMutator()
    directive = mutator.generate_mutation(
        current_tier=3,
        failing_tests={"tests/test_z.py::test_err": "TimeoutError"},
        cycle_pattern=CyclePattern.NONE,
        active_milestone_id="M-3",
    )

    assert directive.mutation_type == MutationStrategyType.TOOL_CONSTRICTION
    assert directive.tier_level == 3
    assert "bash" in directive.banned_tools or "execute_bash" in directive.banned_tools
    assert "read_file" in directive.forced_tools


def test_strategy_mutator_tier4_model_elevation_failover():
    """P8-T13: Level 4 routes milestone to high-reasoning model tier."""
    mutator = StrategyMutator()
    directive = mutator.generate_mutation(
        current_tier=4,
        failing_tests={},
        cycle_pattern=CyclePattern.NONE,
        active_milestone_id="M-4",
    )

    assert directive.mutation_type == MutationStrategyType.MODEL_ELEVATION
    assert directive.tier_level == 4
    assert directive.elevated_model is not None


# ============================================================================
# P8-T14, P8-T15, P8-T16: Recovery Orchestrator & Persistence
# ============================================================================

def test_recovery_orchestrator_triggers_atomic_rollback(temp_workspace: Path):
    """P8-T14: Severe test regression causes emission of rollback decision with tag ref."""
    db_path = temp_workspace / "sentinel.db"
    orchestrator = RecoveryOrchestrator(workspace_path=temp_workspace, db_path=db_path)
    orchestrator.tracker.initialize_baseline(
        passed_test_nodes={"test_a", "test_b", "test_c"},
        failed_test_nodes={},
    )

    checkpoint_ref = "refs/oragai/checkpoints/run_01_turn_01"
    # Severe regression: 2 passing tests fail
    decision = orchestrator.evaluate_turn_outcome(
        run_id="run-test",
        turn_index=1,
        passed_test_nodes={"test_a"},
        failed_test_nodes={"test_b": "err", "test_c": "err"},
        satisfied_ac_ids=set(),
        open_defect_ids=set(),
        tokens_consumed=800,
        active_milestone_id="M-1",
        checkpoint_ref=checkpoint_ref,
    )

    assert decision.action == RecoveryActionType.TRANSACTIONAL_ROLLBACK
    assert decision.rollback_checkpoint_ref == checkpoint_ref
    assert decision.health == ProgressHealth.REGRESSING


def test_recovery_orchestrator_quarantines_on_tier4_exhaust(temp_workspace: Path):
    """P8-T15: 4 failed mutations transition milestone to QUARANTINED action emitted."""
    db_path = temp_workspace / "sentinel.db"
    quarantine_path = temp_workspace / "quarantined_findings.json"
    orchestrator = RecoveryOrchestrator(
        workspace_path=temp_workspace,
        db_path=db_path,
        quarantine_path=quarantine_path,
    )
    orchestrator.tracker.initialize_baseline(
        passed_test_nodes=set(),
        failed_test_nodes={"test_fail": "PersistentError"},
    )

    # Simulate exhausting all 4 mutation tiers
    orchestrator.circuit_breaker.mutation_tier_level = 4
    orchestrator.circuit_breaker.stagnation_counter = 4

    decision = orchestrator.evaluate_turn_outcome(
        run_id="run-quarantine",
        turn_index=5,
        passed_test_nodes=set(),
        failed_test_nodes={"test_fail": "PersistentError"},
        satisfied_ac_ids=set(),
        open_defect_ids=set(),
        tokens_consumed=1200,
        active_milestone_id="M-BLOCKED",
    )

    assert decision.action == RecoveryActionType.QUARANTINE_MILESTONE
    assert decision.breaker_state == BreakerState.TRIPPED_ESCALATING
    assert quarantine_path.exists()
    records = json.loads(quarantine_path.read_text(encoding="utf-8"))
    assert len(records) == 1
    assert records[0]["milestone_id"] == "M-BLOCKED"


def test_sentinel_sqlite_wal_recovery_event_logging(temp_workspace: Path):
    """P8-T16: Progress snapshot & recovery events committed to SQLite DB, rows verified > 0."""
    db_path = temp_workspace / "sentinel.db"
    orchestrator = RecoveryOrchestrator(workspace_path=temp_workspace, db_path=db_path)
    orchestrator.tracker.initialize_baseline()

    # Trigger a stagnant turn that will log a snapshot
    orchestrator.evaluate_turn_outcome(
        run_id="run-telemetry",
        turn_index=1,
        passed_test_nodes=set(),
        failed_test_nodes={"test_1": "fail"},
        satisfied_ac_ids=set(),
        open_defect_ids=set(),
        tokens_consumed=500,
        active_milestone_id="M-1",
    )

    # Trigger a 2nd stagnant turn that causes mutation injection
    orchestrator.evaluate_turn_outcome(
        run_id="run-telemetry",
        turn_index=2,
        passed_test_nodes=set(),
        failed_test_nodes={"test_1": "fail"},
        satisfied_ac_ids=set(),
        open_defect_ids=set(),
        tokens_consumed=600,
        active_milestone_id="M-1",
    )

    with sqlite3.connect(str(db_path)) as conn:
        snapshot_count = conn.execute("SELECT COUNT(*) FROM sentinel_progress_snapshots").fetchone()[0]
        event_count = conn.execute("SELECT COUNT(*) FROM sentinel_recovery_events").fetchone()[0]

    assert snapshot_count == 2
    assert event_count >= 1


# ============================================================================
# Helper Stub
# ============================================================================

def tracker_metrics_stub(health: ProgressHealth, v_verif: float):
    from orchestrator.control.recovery.models import ProgressVelocityMetrics
    return ProgressVelocityMetrics(
        v_code=0.0,
        v_verif=v_verif,
        v_evid=0.0,
        v_defect=0.0,
        tokens_consumed=500,
        per_score=0.0,
        normalized_score=0.5,
        health=health,
    )
