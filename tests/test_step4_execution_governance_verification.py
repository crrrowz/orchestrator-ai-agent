"""Tests for Step 4: Execution, Governance, and Verification Engines."""

import pytest
from orchestrator.engines.core import ServiceContainer
from orchestrator.engines.execution import ExecutionEngine
from orchestrator.engines.governance import GovernanceDecision, GovernanceEngine, GovernanceVerdict
from orchestrator.engines.verification import VerificationEngine, VerificationStatus


@pytest.mark.anyio
async def test_execution_governance_verification():
    container = ServiceContainer()
    exec_engine = ExecutionEngine()
    gov_engine = GovernanceEngine(max_token_ceiling=10_000, max_cost_usd=1.0)
    verif_engine = VerificationEngine()

    await exec_engine.initialize(container)
    await gov_engine.initialize(container)
    await verif_engine.initialize(container)

    await exec_engine.start()
    await gov_engine.start()
    await verif_engine.start()

    # 1. Test Execution Turn Loop
    loop_result = await exec_engine.run_agent_loop("developer", "Fix bug in auth", max_turns=3)
    assert loop_result["status"] == "completed"
    assert loop_result["total_turns"] == 2
    assert loop_result["total_tokens"] > 0

    # 2. Test Governance Nominal & Tripping
    decision_ok = await gov_engine.evaluate_turn("developer", current_tokens=500, current_cost=0.05, turn_count=1)
    assert decision_ok.verdict == GovernanceVerdict.CONTINUE

    decision_halt = await gov_engine.evaluate_turn("developer", current_tokens=15_000, current_cost=0.05, turn_count=1)
    assert decision_halt.verdict == GovernanceVerdict.HALT

    assert await gov_engine.check_command_safety("git status") is True
    assert await gov_engine.check_command_safety("rm -rf /") is False

    # 3. Test Verification Evidence Gates
    report_pass = await verif_engine.verify_evidence("task-123", test_passed=True, diff_present=True)
    assert report_pass.passed is True
    assert report_pass.status == VerificationStatus.PASSED

    report_fail = await verif_engine.verify_evidence("task-124", test_passed=False, diff_present=True)
    assert report_fail.passed is False
    assert report_fail.status == VerificationStatus.FAILED
    assert len(report_fail.defects) == 1
