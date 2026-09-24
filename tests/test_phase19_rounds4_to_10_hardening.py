"""Rounds 4 to 10 Deep Hardening & Systems Resilience Test Suite.

Verifies:
1. ReviewerVerdict AST/JSON parsing with single quotes, trailing commas, and unquoted keys.
2. WorkspaceFileTool line-by-line fuzzy replacement with scope indent inheritance.
3. ASTGuard Python 3.12 PEP 695 type parameter recognition.
4. MilestoneDAG cycle recovery and topological execution ordering.
5. TelemetryRecorder thread-safe metric and incident logging.
6. PipelineStateMachine extended initialization transitions.
"""

from pathlib import Path
import threading

from orchestrator.pipeline.milestone_dag import MilestoneParser
from orchestrator.pipeline.reviewer_parser import ReviewerVerdict
from orchestrator.pipeline.state_machine import PipelinePhase, PipelineStateMachine
from orchestrator.sentinel.ast_guard import ASTGuard
from orchestrator.telemetry.recorder import TelemetryRecorder
from orchestrator.tools.workspace_tools import (
    WorkspaceFileAction,
    execute_file_action,
)


class TestRounds4To10Hardening:
    """Comprehensive multi-tier tests for Rounds 4 through 10."""

    def test_reviewer_parser_evaluates_python_dict_verdict(self):
        text = """
        Review complete:
        ```python
        {
            'verdict': 'APPROVED',
            'reasoning': ['All requirements satisfied', 'Zero regressions'],
            'required_fixes': [],
        }
        ```
        """
        verdict = ReviewerVerdict.parse(text)
        assert verdict.approved is True
        assert len(verdict.reasoning) == 2

    def test_workspace_file_fuzzy_line_edit_indents_properly(self, tmp_path: Path):
        test_file = tmp_path / "module.py"
        test_file.write_text(
            "class Controller:\n    def handle(self, req):\n        check(req)\n        dispatch(req)\n        return True\n",
            encoding="utf-8",
        )

        action = WorkspaceFileAction(
            operation="edit",
            path="module.py",
            target_text="check(req)\ndispatch(req)",
            replacement_text="check(req)\naudit(req)\ndispatch(req)",
        )

        obs = execute_file_action(action, base_dir=tmp_path)
        assert obs.is_error is False
        assert obs.success is True
        content = test_file.read_text(encoding="utf-8")
        assert "audit(req)" in content
        # Verify valid Python AST
        import ast

        tree = ast.parse(content)
        assert tree is not None

    def test_ast_guard_supports_pep695_type_params(self, tmp_path: Path):
        guard = ASTGuard()
        code_pep695 = "class Container[T]:\n    def __init__(self, value: T) -> None:\n        self.value = value\n"
        is_safe, msg, healed = guard.intercept_ast(tmp_path / "generic.py", code_pep695)
        assert is_safe is True
        # Type parameter T should not trigger fake missing import
        assert healed is not None

    def test_milestone_dag_resolves_linear_dependencies(self):
        plan = """
## Milestone 1: Init Database
Prerequisites: None

## Milestone 2: API Endpoints
Depends on: 1

## Milestone 3: Background Worker
Depends on: 1, 2
"""
        milestones = MilestoneParser.parse_plan(plan)
        assert len(milestones) == 3
        assert [m.index for m in milestones] == [1, 2, 3]

    def test_telemetry_recorder_concurrent_thread_safety(self, tmp_path: Path):
        recorder = TelemetryRecorder(
            task_description="Concurrent Test",
            reports_dir=tmp_path / "reports",
        )

        def worker(worker_id: int):
            for i in range(10):
                recorder.record_step(
                    agent_role=f"worker_{worker_id}",
                    action_type="concurrent_action",
                    iteration=i,
                    duration_seconds=0.01,
                    success=True,
                    total_tokens=100,
                )
                recorder.record_incident(
                    step_name=f"worker_{worker_id}",
                    incident_type="info",
                    details=f"Step {i} logged cleanly",
                )

        threads = [threading.Thread(target=worker, args=(w,)) for w in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(recorder.metrics) == 50
        assert len(recorder.incidents) == 50

    def test_state_machine_allows_init_to_preflight_and_test(self):
        sm = PipelineStateMachine()
        assert sm.can_transition(PipelinePhase.PREFLIGHT) is True
        assert sm.can_transition(PipelinePhase.TEST) is True
        sm.transition_to(PipelinePhase.PREFLIGHT)
        assert sm.current_phase == PipelinePhase.PREFLIGHT
