"""Unit tests verifying Phase 6: Agent Governance, Milestone DAG & Pipeline Checkpointing."""

from pathlib import Path
import pytest

from orchestrator.pipeline.milestone_dag import MilestoneParser, SubtaskMilestone
from orchestrator.pipeline.checkpoint import PipelineCheckpointManager, PipelineCheckpoint
from orchestrator.main import parse_args


def test_milestone_parser_structured_plan():
    """MilestoneParser should extract discrete milestones and file targets from PLAN.md."""
    plan_markdown = """# Architecture Plan

## Milestone 1: Data Layer
Define the core schemas in `src/models/user.py` and `src/models/token.py`.
Must ensure Pydantic v2 compatibility.

## Milestone 2: Service Implementation
Implement the authentication service in `src/services/auth.py`.
Add password hashing and token generation.

## Milestone 3: Test Verification
Write unit tests in `tests/test_auth.py`.
"""
    milestones = MilestoneParser.parse_plan(plan_markdown)
    assert len(milestones) == 3

    assert milestones[0].index == 1
    assert "Milestone 1: Data Layer" in milestones[0].title
    assert "src/models/user.py" in milestones[0].target_files
    assert "src/models/token.py" in milestones[0].target_files

    assert milestones[1].index == 2
    assert "Milestone 2: Service Implementation" in milestones[1].title
    assert "src/services/auth.py" in milestones[1].target_files

    assert milestones[2].index == 3
    assert "tests/test_auth.py" in milestones[2].target_files


def test_milestone_parser_monolithic_fallback():
    """MilestoneParser should fallback cleanly to a single task if no milestones are found."""
    plain_plan = "Implement a simple calculator function in calc.py with tests in test_calc.py."
    milestones = MilestoneParser.parse_plan(plain_plan)
    assert len(milestones) == 1
    assert milestones[0].index == 1
    assert milestones[0].title == "Full Implementation"
    assert "calc.py" in milestones[0].target_files


def test_checkpoint_manager_lifecycle(tmp_path: Path):
    """PipelineCheckpointManager should save, read, and delete .orchestrator_state.json."""
    # 1. No checkpoint initially
    assert PipelineCheckpointManager.load(tmp_path) is None

    # 2. Save checkpoint
    saved_path = PipelineCheckpointManager.save(
        workspace=tmp_path,
        run_id="run_12345",
        task="Build payment gateway",
        mode="full",
        current_phase="after_developer",
        completed_phases=["architect", "developer"],
        iteration=2,
    )
    assert saved_path.exists()

    # 3. Load checkpoint
    cp = PipelineCheckpointManager.load(tmp_path)
    assert cp is not None
    assert cp.run_id == "run_12345"
    assert cp.current_phase == "after_developer"
    assert "architect" in cp.completed_phases
    assert "developer" in cp.completed_phases
    assert cp.iteration == 2

    # 4. Clear checkpoint
    cleared = PipelineCheckpointManager.clear(tmp_path)
    assert cleared is True
    assert PipelineCheckpointManager.load(tmp_path) is None


def test_main_cli_resume_flag(monkeypatch):
    """CLI argument parser should recognize --resume flag."""
    import sys
    monkeypatch.setattr(sys, "argv", ["main.py", "--resume"])
    args = parse_args()
    assert args.resume is True
