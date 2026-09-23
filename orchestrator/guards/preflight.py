"""Zero-Token Pre-Flight Syntax and Compilation Guard."""

import py_compile
import subprocess
from pathlib import Path
from typing import Tuple, List


class PreFlightGuard:
    """Performs offline static syntax validation in <50ms without invoking LLMs."""

    @staticmethod
    def check_syntax(workspace: Path) -> Tuple[bool, str]:
        """Compile all Python files in the workspace. Returns (is_valid, error_message)."""
        py_files: List[Path] = [
            p for p in workspace.rglob("*.py")
            if not any(part.startswith(".") or part in ("__pycache__", ".venv", "build", "dist") for part in p.parts)
        ]

        if not py_files:
            return True, ""

        errors = []
        for file_path in py_files:
            try:
                py_compile.compile(str(file_path), doraise=True)
            except py_compile.PyCompileError as e:
                # Extract clean syntax error
                rel_path = file_path.relative_to(workspace)
                errors.append(f"Syntax error in '{rel_path}':\n{e.msg}")
            except Exception as ex:
                rel_path = file_path.relative_to(workspace)
                errors.append(f"Compilation error in '{rel_path}': {str(ex)}")

        if errors:
            return False, "\n\n".join(errors)

        return True, ""
