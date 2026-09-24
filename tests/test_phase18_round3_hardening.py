"""Round 3 Ultra-Deep Hardening & Robustness Test Suite.

Verifies:
1. ReviewerVerdict parser with relaxed JSON (trailing commas, single quotes, markdown markers).
2. MilestoneDAG dependency parsing, topological ordering, and cycle fallback.
3. WorkspaceFileTool fuzzy patch synthesis on whitespace drift.
4. CloudResilienceMesh exponential backoff with jitter and retry-after header parsing.
"""

from pathlib import Path

from orchestrator.pipeline.milestone_dag import MilestoneParser, SubtaskMilestone
from orchestrator.pipeline.reviewer_parser import ReviewerVerdict
from orchestrator.sentinel.cloud_mesh import CloudResilienceMesh
from orchestrator.tools.workspace_tools import (
    WorkspaceFileAction,
    execute_file_action,
)


class TestRound3ReviewerParserHardening:
    """Tests for ultra-resilient reviewer output parsing."""

    def test_parse_json_with_trailing_commas_and_single_quotes(self):
        malformed_json = """
        ```json
        {
            'verdict': 'APPROVED',
            'reasoning': [
                'Code adheres to clean architecture',
                'Zero regressions detected',
            ],
            'required_fixes': [],
        }
        ```
        """
        verdict = ReviewerVerdict.parse(malformed_json)
        assert verdict.approved is True
        assert verdict.verdict == "APPROVED"
        assert len(verdict.reasoning) == 2

    def test_parse_relaxed_verdict_keywords(self):
        text_passed = '{"verdict": "PASSED"}'
        verdict = ReviewerVerdict.parse(text_passed)
        assert verdict.approved is True
        # Fallback keyword or structured
        verdict_structured = ReviewerVerdict.parse('{"verdict": "LGTM"}')
        assert verdict_structured.approved is True

    def test_parse_markdown_verdict_headers(self):
        text = "### Verdict: APPROVED\nAll tests passed with 100% coverage."
        verdict = ReviewerVerdict.parse(text)
        assert verdict.approved is True
        assert verdict.verdict == "APPROVED"


class TestRound3MilestoneDAGHardening:
    """Tests for milestone dependency parsing and topological sorting."""

    def test_topological_sorting_with_dependencies(self):
        plan_text = """
## Milestone 1: Database Schemas
Target: models.py
Prerequisites: None

## Milestone 2: API Endpoints
Target: api.py
Depends on: Milestone 1

## Milestone 3: Background Worker
Target: worker.py
Depends on: Milestone 1, Milestone 2
"""
        milestones = MilestoneParser.parse_plan(plan_text)
        assert len(milestones) == 3
        assert [m.index for m in milestones] == [1, 2, 3]

    def test_cycle_detection_fallback_to_natural_order(self):
        # Create milestones with cyclic dependencies (1 -> 2 -> 1)
        m1 = SubtaskMilestone(index=1, title="M1", content="M1", dependencies=[2])
        m2 = SubtaskMilestone(index=2, title="M2", content="M2", dependencies=[1])

        ordered = MilestoneParser.resolve_execution_order([m1, m2])
        assert len(ordered) == 2
        assert [m.index for m in ordered] == [1, 2]


class TestRound3WorkspaceFileFuzzyPatching:
    """Tests for fuzzy whitespace and indentation tolerant editing."""

    def test_fuzzy_edit_fallback_on_indent_drift(self, tmp_path: Path):
        test_file = tmp_path / "service.py"
        test_file.write_text(
            "class UserService:\n    def authenticate(self, user, pwd):\n        validate(user)\n        check_hash(pwd)\n        return True\n",
            encoding="utf-8",
        )

        # Agent provides target without 8-space indent
        action = WorkspaceFileAction(
            operation="edit",
            path="service.py",
            target_text="validate(user)\ncheck_hash(pwd)",
            replacement_text="validate(user)\nrate_limit(user)\ncheck_hash(pwd)",
        )

        obs = execute_file_action(action, base_dir=tmp_path)
        assert obs.is_error is False
        assert obs.success is True
        content = test_file.read_text(encoding="utf-8")
        assert "rate_limit(user)" in content


class TestRound3CloudMeshBackoffHardening:
    """Tests for exponential backoff and retry-after header parsing."""

    def test_exponential_backoff_calculation(self):
        delay_0 = CloudResilienceMesh.calculate_backoff_delay(attempt=0, base_delay=1.0)
        delay_1 = CloudResilienceMesh.calculate_backoff_delay(attempt=1, base_delay=1.0)
        delay_2 = CloudResilienceMesh.calculate_backoff_delay(attempt=2, base_delay=1.0)

        assert 1.0 <= delay_0 <= 1.5
        assert 2.0 <= delay_1 <= 3.0
        assert 4.0 <= delay_2 <= 6.0

    def test_extract_retry_after(self):
        err1 = "Rate limit exceeded. Retry-After: 12.5 seconds."
        err2 = "Too many requests. resets in 30s"

        assert CloudResilienceMesh.extract_retry_after(err1) == 12.5
        assert CloudResilienceMesh.extract_retry_after(err2) == 30.0
