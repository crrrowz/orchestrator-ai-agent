"""Rigorous unit and integration test suite for P4 Adaptive Resource Governance.

Verifies complexity-scored turn budgeting, 100% investigation allocation,
AST-aware code folding, monetary circuit breaker tripping, stagnation penalties,
provider quota backoff, context headroom preservation, and GuardedFSMEngine integration.
"""

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from orchestrator.config import OrchestratorConfig
from orchestrator.control.adaptive import (
    AdaptiveBudgetAllocator,
    AdaptiveResourceGovernor,
    ASTAwareContextClamper,
    CircuitBreakerStatus,
    CircuitState,
    MonetaryCircuitBreaker,
    PhaseBudgetProfile,
    ProviderQuotaProtector,
    ResourceExhaustionReason,
    ResourceGovernorConfig,
    ResourcePhase,
    TurnBudgetResult,
)
from orchestrator.engine.openhands_bridge import (
    AgentExecutionOutcome as BridgeAgentOutcome,
    AgentExitReason,
    TurnEnvelope,
)
from orchestrator.pipeline.fsm.engine import GuardedFSMEngine
from orchestrator.pipeline.fsm.events import EventType
from orchestrator.pipeline.fsm.profiles import PipelineMode, get_profile
from orchestrator.pipeline.fsm.states import FSMState


# ============================================================================
# 1. Turn Budget Scaling & Complexity Scoring
# ============================================================================

def test_turn_budget_scales_with_ac_and_dag_complexity():
    """Verify turn budget scales dynamically with complexity and is never capped at legacy 5."""
    allocator = AdaptiveBudgetAllocator()

    # 1 AC, simple task
    res_simple = allocator.allocate_turn_budget(
        phase=ResourcePhase.IMPLEMENTATION,
        acceptance_criteria_count=1,
        dag_depth=1,
        target_files_count=1,
        symbol_count=5,
    )
    assert res_simple.allocated_turns >= 10, f"Expected at least 10 turns, got {res_simple.allocated_turns}"
    assert res_simple.allocated_turns > 5, "Must never be strangled at legacy 5 turns"
    assert 0.0 < res_simple.complexity_score < 0.3

    # High complexity: 8 ACs, deep DAG (5 levels), 6 files, 50 symbols
    res_complex = allocator.allocate_turn_budget(
        phase=ResourcePhase.IMPLEMENTATION,
        acceptance_criteria_count=8,
        dag_depth=5,
        target_files_count=6,
        symbol_count=50,
    )
    assert res_complex.complexity_score == 1.0
    # raw_turns = floor(10 * (1.0 + 0.8 * 1.0)) = 18
    assert res_complex.allocated_turns >= 18
    assert res_complex.allocated_turns <= 20
    assert res_complex.allocated_turns > res_simple.allocated_turns


def test_planning_and_audit_receive_100_percent_investigation():
    """Verify PLANNING and AUDIT receive full investigation allocation and 0-turn deterministic phases."""
    allocator = AdaptiveBudgetAllocator()

    # Planning phase
    plan_res = allocator.allocate_turn_budget(
        phase=ResourcePhase.PLANNING,
        acceptance_criteria_count=2,
    )
    profile_plan = allocator.PHASE_PROFILES[ResourcePhase.PLANNING]
    assert profile_plan.investigation_token_ratio == 1.0
    assert plan_res.allocated_turns >= 15
    assert plan_res.allocated_output_tokens == 8192

    # Audit phase
    audit_res = allocator.allocate_turn_budget(
        phase=ResourcePhase.AUDIT,
        acceptance_criteria_count=4,
    )
    profile_audit = allocator.PHASE_PROFILES[ResourcePhase.AUDIT]
    assert profile_audit.investigation_token_ratio == 1.0
    assert audit_res.allocated_turns >= 20
    assert audit_res.allocated_output_tokens == 8192

    # Deterministic zero-token phases
    preflight_res = allocator.allocate_turn_budget(phase=ResourcePhase.PREFLIGHT)
    assert preflight_res.allocated_turns == 0
    assert preflight_res.allocated_output_tokens == 0

    verif_res = allocator.allocate_turn_budget(phase=ResourcePhase.VERIFICATION)
    assert verif_res.allocated_turns == 0
    assert verif_res.allocated_output_tokens == 0


# ============================================================================
# 2. AST Code Folding Engine
# ============================================================================

def test_ast_code_folding_preserves_target_symbols_and_syntax():
    """Verify AST code folding compresses non-target functions while preserving targets and valid syntax."""
    source_code = '''
class OrderProcessor:
    """Manages order transactions."""

    def helper_function(self, a, b):
        """Docstring for helper."""
        line1 = a + 1
        line2 = b + 2
        line3 = line1 * line2
        line4 = line3 / 2
        line5 = line4 - 1
        line6 = line5 * 10
        return line6

    def target_method(self, order_id: str) -> bool:
        """Target to preserve intact."""
        verified = True
        return verified

async def non_target_async():
    """Async docstring."""
    step1 = 1
    step2 = 2
    step3 = 3
    step4 = 4
    step5 = 5
    step6 = 6
    return step6
'''
    # Fold non-target functions while keeping target_method intact
    folded_code, was_folded = ASTAwareContextClamper.fold_python_source(
        source_code=source_code,
        target_symbols={"target_method"},
        min_fold_lines=4,
    )

    assert was_folded is True
    # Verify valid Python syntax through ast.parse()
    parsed_tree = ast.parse(folded_code)
    assert parsed_tree is not None

    # Target implementation must be intact
    assert "verified = True" in folded_code
    assert "return verified" in folded_code

    # Non-target implementation body should be replaced with notice and pass
    assert "[Folded implementation:" in folded_code
    assert "[Folded async implementation:" in folded_code
    assert "line6 = line5 * 10" not in folded_code
    assert "step6 = 6" not in folded_code

    # Docstring must be preserved
    assert "Docstring for helper." in folded_code
    assert "Async docstring." in folded_code


def test_ast_folding_handles_syntax_errors_gracefully():
    """Verify malformed code is returned untouched without exceptions."""
    broken_code = "def invalid_syntax(:"
    out_code, was_folded = ASTAwareContextClamper.fold_python_source(broken_code)
    assert was_folded is False
    assert out_code == broken_code


# ============================================================================
# 3. Monetary Circuit Breaker & Provider Resilience
# ============================================================================

def test_monetary_circuit_breaker_tripping_and_warnings():
    """Verify multi-tier budget warnings and hard tripping at $5.00 ceiling."""
    cfg = ResourceGovernorConfig(max_budget_usd=5.00, warning_budget_usd=4.00)
    breaker = MonetaryCircuitBreaker(config=cfg)

    # 1. Normal spend: $3.00
    breaker.record_consumption(cost_usd=3.00, tokens=50_000, phase=ResourcePhase.IMPLEMENTATION)
    assert breaker.is_tripped is False
    assert breaker.warning_triggered is False
    assert breaker.remaining_budget_usd == 2.00
    assert breaker.state == CircuitState.CLOSED

    # 2. Warning spend: reaches $4.20
    breaker.record_consumption(cost_usd=1.20, tokens=20_000, phase=ResourcePhase.IMPLEMENTATION)
    assert breaker.is_tripped is False
    assert breaker.warning_triggered is True
    assert breaker.remaining_budget_usd == 0.80

    # 3. Trip spend: reaches $5.10
    breaker.record_consumption(cost_usd=0.90, tokens=10_000, phase=ResourcePhase.IMPLEMENTATION)
    assert breaker.is_tripped is True
    assert breaker.state == CircuitState.OPEN
    assert breaker.trip_reason == ResourceExhaustionReason.MONETARY_BUDGET_EXHAUSTED
    assert breaker.remaining_budget_usd == 0.0

    # Verify governor returns 0 turns once tripped
    gov = AdaptiveResourceGovernor(config=cfg)
    gov.circuit_breaker = breaker
    turn_res = gov.pre_dispatch_allocate(phase=ResourcePhase.IMPLEMENTATION)
    assert turn_res.allocated_turns == 0
    assert "Circuit breaker tripped" in turn_res.reasoning


def test_token_ceiling_circuit_breaker_tripping():
    """Verify token ceiling breach trips circuit breaker."""
    cfg = ResourceGovernorConfig(max_task_tokens=100_000)
    breaker = MonetaryCircuitBreaker(config=cfg)

    breaker.record_consumption(cost_usd=0.10, tokens=120_000, phase=ResourcePhase.IMPLEMENTATION)
    assert breaker.is_tripped is True
    assert breaker.trip_reason == ResourceExhaustionReason.TOKEN_CEILING_EXCEEDED


def test_provider_quota_protector_backoff_and_recovery():
    """Verify exponential backoff calculation and retry threshold tripping."""
    protector = ProviderQuotaProtector(max_retries=3, base_delay_seconds=2.0)

    # Exponential delay verification
    assert protector.compute_backoff_delay(0) == 2.0
    assert protector.compute_backoff_delay(1) == 4.0
    assert protector.compute_backoff_delay(2) == 8.0
    assert protector.compute_backoff_delay(3) == 16.0

    # Test rate limit events
    assert protector.record_rate_limit_event() is False  # 1 fail
    assert protector.record_rate_limit_event() is False  # 2 fails
    assert protector.record_rate_limit_event() is False  # 3 fails
    tripped = protector.record_rate_limit_event()        # 4 fails > max_retries(3)
    assert tripped is True
    assert protector.is_tripped is True

    # Recovery on success
    protector.record_success()
    assert protector.is_tripped is False
    assert protector.consecutive_rate_limits == 0


# ============================================================================
# 4. Stagnation Penalties & Loop Tightening
# ============================================================================

def test_stagnation_penalty_tightens_loop_turns():
    """Verify consecutive stagnant yields penalize turn allocation down to min_turns."""
    gov = AdaptiveResourceGovernor()

    # Initial turn allocation (no stagnation)
    t0 = gov.pre_dispatch_allocate(phase=ResourcePhase.IMPLEMENTATION)
    base_allocated = t0.allocated_turns

    # Stagnant yield 1 (no meaningful progress)
    gov.post_yield_record(
        phase=ResourcePhase.IMPLEMENTATION,
        cost_usd=0.01,
        tokens_consumed=1000,
        turns_used=2,
        made_meaningful_progress=False,
    )
    t1 = gov.pre_dispatch_allocate(phase=ResourcePhase.IMPLEMENTATION)
    assert t1.stagnation_penalty == 2
    assert t1.allocated_turns == base_allocated - 2

    # Stagnant yield 2
    gov.post_yield_record(
        phase=ResourcePhase.IMPLEMENTATION,
        cost_usd=0.01,
        tokens_consumed=1000,
        turns_used=2,
        made_meaningful_progress=False,
    )
    t2 = gov.pre_dispatch_allocate(phase=ResourcePhase.IMPLEMENTATION)
    assert t2.stagnation_penalty == 4
    assert t2.allocated_turns == base_allocated - 4

    # Meaningful progress resets stagnation counter
    gov.post_yield_record(
        phase=ResourcePhase.IMPLEMENTATION,
        cost_usd=0.01,
        tokens_consumed=1000,
        turns_used=2,
        made_meaningful_progress=True,
    )
    t_recovered = gov.pre_dispatch_allocate(phase=ResourcePhase.IMPLEMENTATION)
    assert t_recovered.stagnation_penalty == 0
    assert t_recovered.allocated_turns == base_allocated


# ============================================================================
# 5. Priority Tiered Context Assembly & Headroom
# ============================================================================

def test_context_assembly_guarantees_output_headroom():
    """Verify assembled context strictly respects headroom and tier priority."""
    clamper = ASTAwareContextClamper()

    tier0 = "Requirement: implement payments securely."
    tier1 = "FAILED tests/test_payment.py::test_checkout"
    tier2 = {
        "large_file.py": (
            "class Service:\n"
            + "".join(f"    def method_{i}(self):\n        return {i}\n" for i in range(50))
        )
    }
    tier3 = "Graft topology: Module A imports Module B"

    # Assemble context with strict 2,000 char max and 500 reserved headroom
    # Effective limit: 1,500 chars
    assembled = clamper.assemble_clamped_context(
        tier0_intent=tier0,
        tier1_diagnostics=tier1,
        tier2_files=tier2,
        tier3_architecture=tier3,
        max_context_chars=2000,
        reserved_headroom_chars=500,
    )

    assert len(assembled) <= 1500, f"Assembled context ({len(assembled)}) breached effective ceiling (1500)"
    assert "=== TASK INTENT & REQUIREMENTS ===" in assembled
    assert "=== FAILURE DIAGNOSTICS ===" in assembled
    assert "=== TARGET SOURCE FILES ===" in assembled


# ============================================================================
# 6. GuardedFSMEngine Integration
# ============================================================================

def test_guarded_fsm_engine_uses_adaptive_governor(tmp_path: Path):
    """Verify GuardedFSMEngine dynamically allocates turns and records spend via governor."""
    app_py = tmp_path / "app.py"
    app_py.write_text("def run(): return 0\n", encoding="utf-8")

    plan_md = tmp_path / "PLAN.md"
    plan_md.write_text("## Milestone 1: Core\nImplement core\n", encoding="utf-8")

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
    )

    assert engine.governor is not None
    assert isinstance(engine.governor, AdaptiveResourceGovernor)

    # Mock agent execution outcome
    mock_outcome = BridgeAgentOutcome(
        role="developer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=3,
        max_iterations_allocated=10,
        prompt_tokens=500,
        completion_tokens=200,
        total_tokens=700,
        cost_usd=0.05,
        error_message=None,
        mutated_files=("app.py",),
        final_thought="Completed milestone",
    )

    engine.runtime_bridge = MagicMock()
    engine.runtime_bridge.execute_bounded_turn.return_value = mock_outcome

    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, stdout="All tests passed")
    engine.context.adapter = mock_adapter

    result = engine.run("Implement core feature")
    assert result["success"] is True

    # Verify governor recorded consumption
    assert engine.governor.circuit_breaker.usage.total_cost_usd >= 0.05
    assert engine.governor.circuit_breaker.usage.total_tokens_consumed >= 700
    assert engine.governor.stagnation_counter == 0


def test_fsm_halts_cleanly_when_circuit_breaker_tripped(tmp_path: Path):
    """Verify GuardedFSMEngine halts execution to BLOCKED when circuit breaker trips."""
    app_py = tmp_path / "app.py"
    app_py.write_text("def run(): return 0\n", encoding="utf-8")

    plan_md = tmp_path / "PLAN.md"
    plan_md.write_text("## Milestone 1: Core\nImplement core\n", encoding="utf-8")

    gov_cfg = ResourceGovernorConfig(max_budget_usd=0.01)
    gov = AdaptiveResourceGovernor(config=gov_cfg)
    # Trip the circuit breaker in advance
    gov.circuit_breaker.record_consumption(
        cost_usd=0.05,
        tokens=10_000,
        phase=ResourcePhase.IMPLEMENTATION,
    )
    assert gov.is_tripped is True

    cfg = OrchestratorConfig(workspace_path=tmp_path)
    engine = GuardedFSMEngine(
        config=cfg,
        profile=get_profile(PipelineMode.DEV_TEST),
        workspace_path=tmp_path,
        governor=gov,
    )

    mock_adapter = MagicMock()
    mock_adapter.run_tests.return_value = MagicMock(passed=True, stdout="OK")
    engine.context.adapter = mock_adapter

    result = engine.run("Blocked due to budget")
    assert result["success"] is False
    assert result["status"] == FSMState.BLOCKED.value
