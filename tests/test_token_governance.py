"""Tests for Dynamic Token Governance and Phase Budget Allocation."""

from orchestrator.control.token_governance import (
    DynamicTokenGovernor,
    PhaseBudgetAllocation,
    TokenPhase,
)


def test_phase_budget_allocation_math():
    """Verify that phase allocations sum exactly to the total budget."""
    alloc = PhaseBudgetAllocation(
        total_budget=100_000,
        investigation_budget=28_000,
        implementation_budget=47_000,
        testing_budget=15_000,
        reserve_budget=10_000,
    )
    assert alloc.total_consumed == 0
    assert alloc.remaining_total == 100_000
    assert alloc.remaining_investigation == 28_000

    alloc.investigation_consumed = 10_000
    alloc.implementation_consumed = 20_000
    assert alloc.total_consumed == 30_000
    assert alloc.remaining_total == 70_000
    assert alloc.remaining_investigation == 18_000
    assert alloc.remaining_implementation == 27_000


def test_compute_iteration_budget_tiers():
    """Test dynamic budget scaling across task complexities."""
    # 1. Simple task (1 file, low severity)
    gov_simple = DynamicTokenGovernor.compute_iteration_budget(
        role="developer",
        severity="LOW",
        affected_files_count=1,
        task_text="Fix typo in config comment",
    )
    assert 35_000 <= gov_simple.allocation.total_budget <= 45_000
    assert gov_simple.suggested_max_steps <= 5
    assert (
        gov_simple.allocation.investigation_budget
        + gov_simple.allocation.implementation_budget
        + gov_simple.allocation.testing_budget
        + gov_simple.allocation.reserve_budget
    ) == gov_simple.allocation.total_budget

    # 2. Medium task (2 files, medium severity)
    gov_medium = DynamicTokenGovernor.compute_iteration_budget(
        role="developer",
        severity="MEDIUM",
        affected_files_count=2,
        task_text="Add validation helper and test coverage",
    )
    assert 70_000 <= gov_medium.allocation.total_budget <= 90_000
    assert gov_medium.suggested_max_steps <= 7

    # 3. Architectural task with refactoring keywords
    gov_arch = DynamicTokenGovernor.compute_iteration_budget(
        role="developer",
        severity="HIGH",
        affected_files_count=3,
        task_text="Refactor and collapse _execute_pytest alias pair across base_pipeline and dev_test_loop",
        hard_ceiling=180_000,
    )
    assert gov_arch.allocation.total_budget >= 140_000
    assert gov_arch.allocation.total_budget <= 180_000
    assert gov_arch.suggested_max_steps == 8


def test_classify_action_phases():
    """Verify tool action classification into operational phases."""
    # Reads are investigation
    assert (
        DynamicTokenGovernor.classify_action(
            "WorkspaceFileAction", {"operation": "read", "path": "file.py"}
        )
        == TokenPhase.INVESTIGATION
    )
    assert (
        DynamicTokenGovernor.classify_action(
            "WorkspaceFileAction", {"operation": "list", "path": "."}
        )
        == TokenPhase.INVESTIGATION
    )
    assert (
        DynamicTokenGovernor.classify_action(
            "WorkspaceTerminalAction", {"command": "git grep -n foo"}
        )
        == TokenPhase.INVESTIGATION
    )
    assert (
        DynamicTokenGovernor.classify_action("ThinkAction", {})
        == TokenPhase.INVESTIGATION
    )

    # Edits and writes are implementation
    assert (
        DynamicTokenGovernor.classify_action(
            "WorkspaceFileAction", {"operation": "edit", "path": "file.py"}
        )
        == TokenPhase.IMPLEMENTATION
    )
    assert (
        DynamicTokenGovernor.classify_action(
            "WorkspaceFileAction", {"operation": "write", "path": "file.py"}
        )
        == TokenPhase.IMPLEMENTATION
    )
    assert (
        DynamicTokenGovernor.classify_action(
            "WorkspaceFileAction", {"operation": "append", "path": "file.py"}
        )
        == TokenPhase.IMPLEMENTATION
    )

    # Tests are testing
    assert (
        DynamicTokenGovernor.classify_action(
            "WorkspaceTerminalAction", {"command": "uv run pytest tests/test_foo.py"}
        )
        == TokenPhase.TESTING
    )


def test_investigation_circuit_breaker():
    """Verify that governor detects investigation overrun without code edits."""
    alloc = PhaseBudgetAllocation(
        total_budget=100_000,
        investigation_budget=28_000,
        implementation_budget=47_000,
        testing_budget=15_000,
        reserve_budget=10_000,
    )
    governor = DynamicTokenGovernor(alloc)

    # Agent consumes 15K on reading
    governor.record_step_tokens(TokenPhase.INVESTIGATION, 15_000)
    assert not governor.is_investigation_exhausted()
    assert not governor.has_performed_edit

    # Agent consumes another 15K on reading (total 30K > 28K budget)
    governor.record_step_tokens(TokenPhase.INVESTIGATION, 15_000)
    assert governor.is_investigation_exhausted()

    # Now agent performs an edit
    governor.record_step_tokens(TokenPhase.IMPLEMENTATION, 10_000)
    assert governor.has_performed_edit
    # Circuit breaker is lifted once edit is applied
    assert not governor.is_investigation_exhausted()
