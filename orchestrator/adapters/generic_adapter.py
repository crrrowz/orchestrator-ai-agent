"""Generic fallback project adapter for unmanaged or polyglot environments."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.adapters.base import ProjectAdapter


class GenericAdapter(ProjectAdapter):
    """Fallback adapter for projects with no detected language manifest."""

    @property
    def language_name(self) -> str:
        return "generic"

    def detect(self, workspace: Path) -> bool:
        return True

    def check_syntax(self, workspace: Path) -> Tuple[bool, List[str]]:
        return (True, [])

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        return (True, "No auto-fixer applicable for generic workspace")

    def run_static_analysis(self, workspace: Path) -> Tuple[bool, List[str]]:
        return (True, [])

    def has_test_suite(self, workspace: Path) -> bool:
        return False

    def get_test_command(self, workspace: Path) -> Optional[str]:
        return None

    def parse_test_failures(self, stdout: str, stderr: str) -> str:
        combined = f"{stdout}\n{stderr}".strip()
        lines = [line.strip() for line in combined.splitlines() if line.strip()]
        return "\n".join(lines[-25:])

    def get_developer_prompt_guidance(self) -> str:
        return (
            "Software Engineering Standards:\n"
            "- Maintain clean modular architecture and single-responsibility principles.\n"
            "- Write robust error handling and defensive checks.\n"
            "- Ensure comprehensive test coverage where appropriate."
        )

    def collect_codebase_metrics(self, workspace: Path) -> Dict[str, Any]:
        ignored = {".git", ".venv", "node_modules", "dist", "build"}
        files: List[Path] = []
        for p in workspace.rglob("*"):
            if p.is_file() and not any(
                part in ignored or part.startswith(".") for part in p.parts
            ):
                files.append(p)

        total_lines = 0
        file_metrics = []
        for f in files:
            try:
                line_count = len(
                    f.read_text(encoding="utf-8", errors="replace").splitlines()
                )
                total_lines += line_count
                file_metrics.append((str(f.relative_to(workspace)), line_count))
            except Exception:
                pass

        file_metrics.sort(key=lambda x: x[1], reverse=True)
        total_files = len(files)
        avg_loc = (total_lines // total_files) if total_files > 0 else 0
        return {
            "total_files": total_files,
            "total_loc": total_lines,
            "total_lines": total_lines,
            "avg_loc": avg_loc,
            "top_files": file_metrics[:10],
            "language": "Generic",
        }
