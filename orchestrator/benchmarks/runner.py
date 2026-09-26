"""Isolated Sandbox Runner for ORAGAI Benchmark Engine (P11).

Provides ephemeral workspace provisioning, strict test isolation, zero repository pollution,
and execution dispatch for both zero-token mock scripts and live pipelines.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import pathlib
import shutil
import tempfile
import time
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from orchestrator.benchmarks.models import (
    AgentExitReason,
    BenchmarkEvaluationResult,
    BenchmarkStatus,
    BenchmarkTaskSpec,
    MockConversationScript,
    MockTurnStep,
)


class BenchmarkRunner:
    """Orchestrates ephemeral benchmark workspaces and manages task execution cycles."""

    def __init__(
        self,
        base_workdir: Optional[pathlib.Path] = None,
        retain_workspaces: bool = False,
    ) -> None:
        self.base_workdir = (
            base_workdir
            or pathlib.Path(tempfile.gettempdir()) / "oragai_benchmark_sandboxes"
        )
        self.retain_workspaces = retain_workspaces
        self.base_workdir.mkdir(parents=True, exist_ok=True)
        self._active_workspaces: List[pathlib.Path] = []

    def provision_workspace(self, task: BenchmarkTaskSpec) -> pathlib.Path:
        """Create an isolated, ephemeral workspace directory populated with initial task fixtures."""
        timestamp_ns = time.time_ns()
        task_slug = task.task_id.lower().replace("-", "_")
        unique_seed = hashlib.sha256(f"{task.task_id}_{timestamp_ns}".encode()).hexdigest()[:10]
        workspace_dir = self.base_workdir / f"bench_{task_slug}_{unique_seed}"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        self._active_workspaces.append(workspace_dir)

        # Seed initial source files
        for rel_path, content in task.initial_files.items():
            file_path = workspace_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        # Seed broken/baseline test files
        for rel_path, content in task.broken_test_files.items():
            file_path = workspace_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        return workspace_dir

    def cleanup_workspace(self, workspace: pathlib.Path) -> bool:
        """Safely destroy an ephemeral workspace directory to prevent disk leakage."""
        if not workspace.exists():
            return True
        if self.retain_workspaces:
            return True

        try:
            # Defensive check: ensure path is strictly inside base_workdir
            resolved_ws = workspace.resolve()
            resolved_base = self.base_workdir.resolve()
            if not str(resolved_ws).startswith(str(resolved_base)):
                raise ValueError(
                    f"Refusing to delete directory outside benchmark base: {resolved_ws}"
                )

            shutil.rmtree(resolved_ws, ignore_errors=True)
            if workspace in self._active_workspaces:
                self._active_workspaces.remove(workspace)
            return True
        except Exception:
            return False

    def cleanup_all(self) -> int:
        """Clean up all recorded active ephemeral workspaces."""
        count = 0
        for ws in list(self._active_workspaces):
            if self.cleanup_workspace(ws):
                count += 1
        return count

    @contextlib.contextmanager
    def isolated_sandbox(
        self,
        task: BenchmarkTaskSpec,
    ) -> Generator[pathlib.Path, None, None]:
        """Context manager provisioning an ephemeral workspace and guaranteeing post-run cleanup."""
        workspace = self.provision_workspace(task)
        try:
            yield workspace
        finally:
            self.cleanup_workspace(workspace)

    def compute_workspace_hash(self, workspace: pathlib.Path) -> str:
        """Compute deterministic composite SHA-256 digest across all files in workspace."""
        hasher = hashlib.sha256()
        ignored_dirs = {".git", ".pytest_cache", "__pycache__", ".venv"}
        ignored_extensions = {".pyc", ".pyo", ".pyd"}

        for root, dirs, files in sorted(os.walk(workspace)):
            # Prune ignored directory trees in-place
            dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith(".")]

            for filename in sorted(files):
                if any(filename.endswith(ext) for ext in ignored_extensions):
                    continue
                file_path = pathlib.Path(root) / filename
                try:
                    rel_path = file_path.relative_to(workspace).as_posix()
                    file_bytes = file_path.read_bytes()
                    hasher.update(f"{rel_path}:{len(file_bytes)}:".encode("utf-8"))
                    hasher.update(file_bytes)
                except (OSError, UnicodeDecodeError):
                    continue

        return hasher.hexdigest()

    def run_mock_script(
        self,
        workspace: pathlib.Path,
        script: MockConversationScript,
    ) -> Tuple[str, List[MockTurnStep], int]:
        """Execute a scripted mock turn sequence against an ephemeral workspace.

        Returns:
            Tuple of (exit_reason, executed_steps, steps_count).
        """
        executed: List[MockTurnStep] = []
        step_count = 0

        for step in script.steps:
            if step_count >= script.max_steps:
                return "STEP_LIMIT_EXHAUSTED", executed, step_count

            step_count += 1
            executed.append(step)

            if step.simulated_delay_ms > 0:
                time.sleep(step.simulated_delay_ms / 1000.0)

            if step.force_error:
                return "TOOL_ERROR_FATAL", executed, step_count

            if step.action_type == "file_write":
                file_rel = step.action_payload.get("path")
                content = step.action_payload.get("content", "")
                if file_rel:
                    target_path = (workspace / file_rel).resolve()
                    # Enforce strict workspace containment boundary
                    if not str(target_path).startswith(str(workspace.resolve())):
                        return "TOOL_ERROR_FATAL", executed, step_count
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.write_text(content, encoding="utf-8")

            elif step.action_type == "file_read":
                file_rel = step.action_payload.get("path")
                if file_rel:
                    target_path = (workspace / file_rel).resolve()
                    if not str(target_path).startswith(str(workspace.resolve())):
                        return "TOOL_ERROR_FATAL", executed, step_count
                    # File read simulation
                    _ = target_path.exists()

            elif step.action_type == "yield":
                return "AGENT_YIELDED", executed, step_count

            elif step.action_type == "stagnate":
                # Do nothing, simulate unproductive turn
                pass

        return script.target_exit_reason, executed, step_count

    def execute_task(
        self,
        task: BenchmarkTaskSpec,
        execution_handler: Callable[[pathlib.Path, BenchmarkTaskSpec], Dict[str, Any]],
    ) -> Tuple[pathlib.Path, Dict[str, Any], str, str]:
        """Run a task through an arbitrary execution handler with pre/post hashing.

        Returns:
            Tuple of (workspace_path, handler_results, pre_hash, post_hash).
        """
        workspace = self.provision_workspace(task)
        pre_hash = self.compute_workspace_hash(workspace)
        start_time = time.time()

        try:
            handler_result = execution_handler(workspace, task)
            post_hash = self.compute_workspace_hash(workspace)
            handler_result["duration_seconds"] = time.time() - start_time
            return workspace, handler_result, pre_hash, post_hash
        except Exception as exc:
            post_hash = self.compute_workspace_hash(workspace)
            return (
                workspace,
                {
                    "error": str(exc),
                    "exit_reason": "UNHANDLED_EXCEPTION",
                    "duration_seconds": time.time() - start_time,
                },
                pre_hash,
                post_hash,
            )
