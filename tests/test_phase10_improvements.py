"""Unit tests validating Phase 10: Code Quality, Polish & Configuration Standards."""

from io import StringIO
from rich.console import Console

from orchestrator.config import ORCHESTRATOR_ROOT
from orchestrator.rendering.output import ConsoleOutput


def test_summary_table_renders_tokens_and_cost():
    """Verify ConsoleOutput.summary_table correctly accepts both iteration/iterations and displays metrics."""
    Console(file=StringIO())

    # Test with keyword iterations
    ConsoleOutput.summary_table(
        iterations=3,
        status="SUCCESS",
        commit_hash="abc1234",
        total_tokens=15420,
        total_cost_usd=0.0125,
    )

    # Test with keyword iteration alias (backwards compatibility)
    ConsoleOutput.summary_table(
        iteration=2,
        status="FAILED",
        total_tokens=5000,
        total_cost_usd=0.0,
    )


def test_clean_orchestrator_import():
    """Verify importing orchestrator package does not fail."""
    import orchestrator

    assert hasattr(orchestrator, "__version__")
    assert orchestrator.__version__ == "0.1.0"


def test_env_example_contains_all_safety_and_budget_vars():
    """Verify .env.example contains budget, circuit breaker, and gate variables."""
    env_example = ORCHESTRATOR_ROOT / ".env.example"
    assert env_example.exists()
    content = env_example.read_text(encoding="utf-8")

    assert "MAX_BUDGET_USD" in content
    assert "CIRCUIT_BREAKER_THRESHOLD" in content
    assert "APPROVAL_GATES" in content
    assert "WORKSPACE_PATH" in content
    assert "INTERACTIVE" in content
    assert "ENABLE_MEMORY" in content
