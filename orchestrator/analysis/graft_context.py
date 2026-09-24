"""Programmatic Graft Context Engine for Zero-Token Codebase Orientation."""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


class GraftContextProvider:
    """Pre-computes codebase wiring maps and skeletons via Graft CLI for direct context injection."""

    @staticmethod
    def is_graft_available() -> bool:
        """Check if graft CLI binary or powershell script exists in system PATH."""
        return (
            shutil.which("graft") is not None
            or shutil.which("graft.ps1") is not None
        )

    @classmethod
    def _run_graft_cmd(cls, args: list[str], workspace: Path, timeout: int = 10) -> subprocess.CompletedProcess:
        """Run graft command with cross-platform handling for Windows powershell scripts."""
        is_windows = sys.platform == "win32" or os.name == "nt"
        if is_windows and not shutil.which("graft") and shutil.which("graft.ps1"):
            cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "graft", *args]
        else:
            cmd = ["graft", *args]

        return subprocess.run(
            cmd,
            cwd=str(workspace.resolve()),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def build_index(
        cls, workspace: Path, force: bool = False, max_age_seconds: float = 300.0
    ) -> bool:
        """Build or refresh local graft/ context graph in workspace if stale or forced."""
        if not cls.is_graft_available():
            return False

        index_dir = (workspace / "graft").resolve()
        if not force and index_dir.exists():
            try:
                mtime = index_dir.stat().st_mtime
                if (time.time() - mtime) < max_age_seconds:
                    return True
            except Exception:
                pass

        try:
            res = cls._run_graft_cmd(["build"], workspace, timeout=15)
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def get_compact_map(cls, workspace: Path, max_chars: int = 1500) -> Optional[str]:
        """Generate compact repository structure map with hubs and hotspots."""
        if not cls.is_graft_available():
            return None

        # Ensure index exists
        cls.build_index(workspace)

        try:
            res = cls._run_graft_cmd(["map", "--format", "compact"], workspace, timeout=10)
            out = res.stdout.strip()
            if res.returncode == 0 and out:
                return out[:max_chars]
        except Exception:
            pass
        return None

    get_condensed_map = get_compact_map

    @classmethod
    def get_skeleton(cls, workspace: Path, relative_file: str) -> Optional[str]:
        """Fetch API surface and function/class definitions without full implementation tokens."""
        if not cls.is_graft_available():
            return None
        try:
            res = cls._run_graft_cmd(["skeleton", relative_file], workspace, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return None
