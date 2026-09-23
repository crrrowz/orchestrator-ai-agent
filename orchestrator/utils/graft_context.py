"""Programmatic Graft Context Engine for Zero-Token Codebase Orientation."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional


class GraftContextProvider:
    """Pre-computes codebase wiring maps and skeletons via Graft CLI for direct context injection."""

    @staticmethod
    def is_graft_available() -> bool:
        """Check if graft CLI binary exists in system PATH."""
        return shutil.which("graft") is not None

    @classmethod
    def build_index(cls, workspace: Path) -> bool:
        """Build or refresh local graft/ context graph in workspace."""
        if not cls.is_graft_available():
            return False
        try:
            res = subprocess.run(
                ["graft", "build"],
                cwd=str(workspace.resolve()),
                capture_output=True,
                text=True,
                timeout=15,
            )
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
            res = subprocess.run(
                ["graft", "map", "--format", "compact"],
                cwd=str(workspace.resolve()),
                capture_output=True,
                text=True,
                timeout=10,
            )
            out = res.stdout.strip()
            if res.returncode == 0 and out:
                return out[:max_chars]
        except Exception:
            pass
        return None

    @classmethod
    def get_skeleton(cls, workspace: Path, relative_file: str) -> Optional[str]:
        """Fetch API surface and function/class definitions without full implementation tokens."""
        if not cls.is_graft_available():
            return None
        try:
            res = subprocess.run(
                ["graft", "skeleton", relative_file],
                cwd=str(workspace.resolve()),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return None
