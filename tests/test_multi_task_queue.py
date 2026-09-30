"""Comprehensive test suite for Sequential Task Queue and MultiTask Runner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.config import OrchestratorConfig
from orchestrator.orchestrator import Orchestrator
from orchestrator.pipeline.task_queue import (
    SequentialTaskItem,
    SequentialTaskQueue,
    TaskQueueItemStatus,
)


def test_task_queue_from_descriptions_and_persistence(tmp_path: Path):
    """Verify constructing, saving, and loading a SequentialTaskQueue."""
    descriptions = [
        "Implement login endpoint",
        "Add JWT authentication",
        "Write integration tests",
    ]
    queue = SequentialTaskQueue.from_descriptions(descriptions)
    assert len(queue.tasks) == 3
    assert queue.tasks[0].task_id == "TASK-001"
    assert queue.tasks[0].status == TaskQueueItemStatus.PENDING

    saved_path = queue.save(tmp_path)
    assert saved_path.exists()

    loaded = SequentialTaskQueue.load(tmp_path)
    assert loaded is not None
    assert len(loaded.tasks) == 3
    assert loaded.tasks[1].description == "Add JWT authentication"


def test_task_queue_from_markdown_file(tmp_path: Path):
    """Verify parsing markdown checklists and bulleted task lists."""
    md_file = tmp_path / "TASKS.md"
    md_file.write_text(
        "# Project Roadmap\n\n"
        "- [ ] Setup database connection\n"
        "- [ ] Create user schema\n"
        "1. Configure migrations\n"
        "2. Run test verification\n",
        encoding="utf-8",
    )

    queue = SequentialTaskQueue.from_file(md_file)
    assert len(queue.tasks) == 4
    assert queue.tasks[0].description == "Setup database connection"
    assert queue.tasks[1].description == "Create user schema"
    assert queue.tasks[2].description == "Configure migrations"
    assert queue.tasks[3].description == "Run test verification"


def test_orchestrator_run_tasks_sequential_success(tmp_path: Path):
    """Verify Orchestrator.run_tasks executes tasks in sequence and returns aggregate summary."""
    (tmp_path / "app.py").write_text("def run(): pass\n", encoding="utf-8")
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    orchestrator = Orchestrator(config=cfg)

    executed_tasks = []

    def mock_run_task(task, mode="dev-test", workspace_override=None, checkpoint=None):
        executed_tasks.append(task)
        return {
            "success": True,
            "status": "COMPLETED",
            "run_id": f"RUN-{len(executed_tasks)}",
            "tokens_consumed": 100,
            "cost_usd": 0.005,
        }

    orchestrator.run_task = mock_run_task

    tasks = [
        "Task 1: Setup models",
        "Task 2: Build services",
        "Task 3: Add routes",
    ]
    summary = orchestrator.run_tasks(tasks, workspace_override=tmp_path)

    assert summary["success"] is True
    assert summary["total_tasks"] == 3
    assert summary["completed_tasks"] == 3
    assert summary["failed_tasks"] == 0
    assert executed_tasks == tasks

    # Verify persisted queue file
    persisted = SequentialTaskQueue.load(tmp_path)
    assert persisted is not None
    assert persisted.is_all_completed is True


def test_orchestrator_run_tasks_halts_on_failure(tmp_path: Path):
    """Verify Orchestrator.run_tasks halts on failure when stop_on_failure=True."""
    (tmp_path / "app.py").write_text("def run(): pass\n", encoding="utf-8")
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    orchestrator = Orchestrator(config=cfg)

    def mock_run_task(task, mode="dev-test", workspace_override=None, checkpoint=None):
        if "Task 2" in task:
            return {
                "success": False,
                "status": "FAILED",
                "error_message": "Dependency conflict in task 2",
            }
        return {
            "success": True,
            "status": "COMPLETED",
        }

    orchestrator.run_task = mock_run_task

    tasks = [
        "Task 1: Init",
        "Task 2: Broken task",
        "Task 3: Unreachable task",
    ]
    summary = orchestrator.run_tasks(tasks, workspace_override=tmp_path, stop_on_failure=True)

    assert summary["success"] is False
    assert summary["completed_tasks"] == 1
    assert summary["failed_tasks"] == 1
    assert summary["tasks"][0]["status"] == "COMPLETED"
    assert summary["tasks"][1]["status"] == "FAILED"
    assert summary["tasks"][2]["status"] == "PENDING"
