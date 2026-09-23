"""Unit tests for ContextBudgetManager."""

from orchestrator.control.context_budget_manager import (
    CallDecision,
    ContextBudgetManager,
)


def test_get_dynamic_output_budget_by_role_and_complexity():
    # Reviewer / Tester defaults to 2048 on low/medium
    assert ContextBudgetManager.get_dynamic_output_budget("reviewer", "low") == 2048
    assert ContextBudgetManager.get_dynamic_output_budget("tester", "medium") == 4096

    # Developer defaults to 4096
    assert ContextBudgetManager.get_dynamic_output_budget("developer", "medium") == 4096
    assert ContextBudgetManager.get_dynamic_output_budget("developer", "high") == 8192

    # Auditor / Architect gets 8192
    assert ContextBudgetManager.get_dynamic_output_budget("auditor", "medium") == 8192
    assert ContextBudgetManager.get_dynamic_output_budget("architect", "high") == 8192

    # Clamping by hard ceiling
    assert (
        ContextBudgetManager.get_dynamic_output_budget(
            "architect", "high", hard_ceiling=4096
        )
        == 4096
    )


def test_evaluate_call_allow():
    res = ContextBudgetManager.evaluate_call(
        estimated_input_tokens=10_000,
        role="developer",
        complexity="medium",
        current_tokens_used=50_000,
        max_tokens_budget=350_000,
        current_cost_usd=0.05,
        max_budget_usd=0.50,
    )
    assert res.decision == CallDecision.ALLOW
    assert res.allocated_output_tokens == 4096


def test_evaluate_call_budget_rejections():
    # Monetary ceiling exceeded
    res_cost = ContextBudgetManager.evaluate_call(
        estimated_input_tokens=5000,
        role="developer",
        current_cost_usd=0.51,
        max_budget_usd=0.50,
    )
    assert res_cost.decision == CallDecision.REJECT
    assert "Monetary budget ceiling reached" in res_cost.reason

    # Token budget exceeded
    res_tok = ContextBudgetManager.evaluate_call(
        estimated_input_tokens=5000,
        role="developer",
        current_tokens_used=349_500,
        max_tokens_budget=350_000,
    )
    assert res_tok.decision == CallDecision.REJECT
    assert "Token budget ceiling reached" in res_tok.reason


def test_evaluate_call_shrink_near_limit():
    res_shrink = ContextBudgetManager.evaluate_call(
        estimated_input_tokens=2000,
        role="developer",
        current_tokens_used=346_000,
        max_tokens_budget=350_000,
    )
    assert res_shrink.decision == CallDecision.SHRINK
    assert res_shrink.allocated_output_tokens == 2000


def test_clamp_tool_payload():
    short_payload = "Short output\nLine 2"
    clamped, was_truncated = ContextBudgetManager.clamp_tool_payload(
        short_payload, max_chars=100
    )
    assert not was_truncated
    assert clamped == short_payload

    long_payload = "A" * 50 + "\n" + "B" * 50 + "\n" + "C" * 50
    clamped_long, was_truncated_long = ContextBudgetManager.clamp_tool_payload(
        long_payload, max_chars=70
    )
    assert was_truncated_long
    assert "[Governance Notice: Payload truncated" in clamped_long
    assert len(clamped_long.splitlines()[0]) <= 70
