"""Unit tests verifying Phase 5: State Machine & Cross-Run Memory Persistence."""

from pathlib import Path
import pytest

from orchestrator.memory import ConversationStore, MemoryEntry
from orchestrator.pipeline.state_machine import PipelineStateMachine, PipelinePhase
from orchestrator.control import PipelineController, BudgetGuard


def test_conversation_store_persistence_and_retrieval(tmp_path: Path):
    """ConversationStore should persist task memories and retrieve relevant context based on keyword overlap."""
    store = ConversationStore(memory_dir=tmp_path)
    assert len(store.load_all_memories()) == 0

    # 1. Save memories
    store.save_run_memory(
        task="Create user authentication with JWT and refresh tokens",
        summary="Implemented AuthHandler with PyJWT and token blacklist table.",
        files_touched=["src/auth/jwt.py", "tests/test_auth.py"],
        tests_passed=True,
        lessons="Always revoke refresh tokens on logout.",
    )
    store.save_run_memory(
        task="Build billing stripe integration",
        summary="Created Stripe webhook handler.",
        files_touched=["src/billing/stripe.py"],
        tests_passed=True,
    )

    all_memories = store.load_all_memories()
    assert len(all_memories) == 2

    # 2. Search relevant memory for related task
    relevant = store.find_relevant_memories("Implement OAuth2 and JWT token refresh", files=["src/auth/jwt.py"])
    assert len(relevant) >= 1
    assert "JWT" in relevant[0].task

    # 3. Format prompt context
    formatted = store.format_memory_context("JWT authentication service")
    assert formatted is not None
    assert "[HISTORICAL EXECUTION MEMORY]" in formatted
    assert "AuthHandler" in formatted
    assert "Always revoke refresh tokens on logout" in formatted


def test_pipeline_state_machine_transitions():
    """PipelineStateMachine should enforce valid phase progressions and reject illegal jumps."""
    fsm = PipelineStateMachine(initial_phase=PipelinePhase.INIT)
    assert fsm.current_phase == PipelinePhase.INIT
    assert not fsm.is_terminal()

    # Valid transitions
    fsm.transition_to(PipelinePhase.ARCHITECT)
    assert fsm.current_phase == PipelinePhase.ARCHITECT

    fsm.transition_to(PipelinePhase.DEVELOP)
    assert fsm.current_phase == PipelinePhase.DEVELOP

    fsm.transition_to(PipelinePhase.PREFLIGHT)
    assert fsm.current_phase == PipelinePhase.PREFLIGHT

    fsm.transition_to(PipelinePhase.TEST)
    assert fsm.current_phase == PipelinePhase.TEST

    fsm.transition_to(PipelinePhase.REVIEW)
    assert fsm.current_phase == PipelinePhase.REVIEW

    fsm.transition_to(PipelinePhase.COMMIT)
    assert fsm.current_phase == PipelinePhase.COMMIT

    fsm.transition_to(PipelinePhase.COMPLETED)
    assert fsm.current_phase == PipelinePhase.COMPLETED
    assert fsm.is_terminal()
    assert len(fsm.history) == 8

    # Illegal transition from terminal state
    with pytest.raises(ValueError, match="Illegal state transition"):
        fsm.transition_to(PipelinePhase.DEVELOP)


def test_pipeline_controller_and_budget_guard():
    """PipelineController and BudgetGuard should correctly track control state and spend."""
    # Controller tests
    controller = PipelineController()
    assert controller.state == "running"
    assert controller.check_should_continue() is True

    controller.request_stop_after_current()
    assert controller.state == "stopping"
    assert controller.check_should_continue() is False

    controller.request_abort()
    assert controller.state == "abort"

    # BudgetGuard tests
    guard = BudgetGuard(max_budget_usd=0.50)
    assert not guard.is_exhausted
    assert guard.remaining_budget == 0.50

    exceeded = guard.update_cost(0.40)
    assert not exceeded
    assert not guard.is_exhausted
    assert round(guard.remaining_budget, 2) == 0.10

    exceeded2 = guard.update_cost(0.55)
    assert exceeded2
    assert guard.is_exhausted
    assert guard.remaining_budget == 0.0
