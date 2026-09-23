"""Structured session log store and step tracking for interactive analysis."""

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestrator.core.constants import DEFAULT_DIAGNOSTICS_DIR


@dataclass
class LogStep:
    index: int
    role: str
    phase: str
    timestamp: str
    summary: str
    action_type: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    thought: Optional[str] = None
    observation: Optional[str] = None
    is_error: bool = False
    duration_s: float = 0.0


class SessionLogStore:
    """Stores full structured execution logs for interactive exploration."""

    def __init__(
        self,
        workspace_path: Optional[Path] = None,
        max_retained_sessions: int = 10,
    ):
        self.steps: List[LogStep] = []
        self.workspace_path = workspace_path
        ws_name = workspace_path.name if workspace_path else "default"
        import re

        self.project_slug = (
            re.sub(r"[^a-zA-Z0-9_\-]+", "_", ws_name.lower()).strip("_") or "default"
        )
        self.max_retained_sessions = max_retained_sessions
        self.current_role: str = "System"
        self.current_phase: str = "Initializing"
        self.current_model: str = "Unknown"
        self.current_llm: Optional[Any] = None
        self.milestones: List[str] = []
        self.start_time: float = time.time()
        self.phase_start_time: float = time.time()
        self._session_ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime(self.start_time))
        self._session_file_name = f"session_{self._session_ts}.json"
        self._last_save_time = 0.0

    def set_agent_context(
        self,
        role: str,
        phase: str,
        model: str = "",
        llm: Optional[Any] = None,
    ) -> None:
        self.current_role = role
        self.current_phase = phase
        self.current_model = model or getattr(llm, "model", self.current_model)
        self.current_llm = llm
        self.phase_start_time = time.time()

    def add_step(
        self,
        summary: str,
        action_type: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        thought: Optional[str] = None,
        observation: Optional[str] = None,
        is_error: bool = False,
        duration_s: Optional[float] = None,
    ) -> LogStep:
        t_str = time.strftime("%H:%M:%S")
        calc_dur = round(time.time() - self.start_time, 2) if duration_s is None else duration_s
        step = LogStep(
            index=len(self.steps) + 1,
            role=self.current_role,
            phase=self.current_phase,
            timestamp=t_str,
            summary=summary,
            action_type=action_type,
            arguments=arguments,
            thought=thought,
            observation=observation,
            is_error=is_error,
            duration_s=calc_dur,
        )
        self.steps.append(step)
        short_msg = f"[{t_str}] [{self.current_role}] {summary}"
        self.milestones.append(short_msg)
        if len(self.milestones) > 6:
            self.milestones.pop(0)

        # Throttled write to disk to prevent I/O storms (at most once every 5s)
        now = time.time()
        if (now - getattr(self, "_last_save_time", 0.0)) >= 5.0:
            try:
                self.save_to_file()
                self._last_save_time = now
            except Exception:
                pass
        return step

    def get_latest_step(self) -> Optional[LogStep]:
        return self.steps[-1] if self.steps else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project_slug,
            "workspace": str(self.workspace_path) if self.workspace_path else "",
            "session_start": self.start_time,
            "total_steps": len(self.steps),
            "steps": [asdict(s) for s in self.steps],
        }

    def save_to_file(
        self,
        target_dir: Optional[Path] = None,
        diagnostics_dir: Optional[Path] = None,
        filepath: Optional[Path] = None,
    ) -> Path:
        out_dir = target_dir or diagnostics_dir or (DEFAULT_DIAGNOSTICS_DIR / "logs")
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Project-specific partitioned directory
        project_dir = out_dir / self.project_slug
        project_dir.mkdir(parents=True, exist_ok=True)
        session_file = filepath or (project_dir / self._session_file_name)

        data = self.to_dict()
        json_content = json.dumps(data, indent=2, ensure_ascii=False)

        # Write timestamped project session file
        session_file.write_text(json_content, encoding="utf-8")

        # Update project-level latest session pointer
        (project_dir / "latest_session.json").write_text(json_content, encoding="utf-8")

        # Update global latest session pointer (backwards compatible)
        (out_dir / "latest_session.json").write_text(json_content, encoding="utf-8")

        # Enforce session retention policy per project (FIFO pruning)
        self._prune_project_sessions(project_dir)

        return session_file

    def _prune_project_sessions(self, project_dir: Path) -> int:
        """Prune old session_*.json files in the project directory exceeding max_retained_sessions."""
        if self.max_retained_sessions <= 0:
            return 0
        try:
            files = sorted(
                project_dir.glob("session_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            pruned = 0
            if len(files) > self.max_retained_sessions:
                for old in files[self.max_retained_sessions :]:
                    try:
                        old.unlink()
                        pruned += 1
                    except OSError:
                        pass
            return pruned
        except Exception:
            return 0
