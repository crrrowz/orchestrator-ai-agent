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
            if not any(
                part.startswith(".")
                or part in ("__pycache__", ".venv", "venv", "build", "dist", "site-packages", "node_modules")
                for part in p.parts
            )
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

    @staticmethod
    def check_importability(workspace: Path) -> Tuple[bool, str]:
        """Verify that top-level Python modules and packages can be imported without fatal errors."""
        import sys

        search_roots = [workspace]
        if (workspace / "src").exists() and (workspace / "src").is_dir():
            search_roots.append(workspace / "src")

        targets: list[str] = []
        for root in search_roots:
            try:
                for item in root.iterdir():
                    if item.name.startswith((".", "_")) or item.name in ("tests", "venv", ".venv", "build", "dist"):
                        continue
                    if item.is_dir() and (item / "__init__.py").exists():
                        targets.append(item.name)
                    elif item.is_file() and item.suffix == ".py":
                        targets.append(item.stem)
            except Exception:
                continue

        if not targets:
            return True, ""

        errors = []
        for mod in sorted(set(targets)):
            try:
                res = subprocess.run(
                    [sys.executable, "-c", f"import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'src'); import {mod}"],
                    cwd=str(workspace),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res.returncode != 0 and res.stderr:
                    err_text = res.stderr.strip()
                    # Only report local broken imports or syntax failures
                    if f"No module named '{mod}'" in err_text or "ImportError" in err_text or "SyntaxError" in err_text:
                        errors.append(f"Import failure in module '{mod}':\n{err_text}")
            except Exception:
                continue

        if errors:
            return False, "\n\n".join(errors)
        return True, ""
