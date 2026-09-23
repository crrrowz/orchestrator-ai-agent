"""Registry and factory for Polyglot Project Adapters."""

from pathlib import Path
from typing import List, Optional

from orchestrator.adapters.base import ProjectAdapter
from orchestrator.adapters.generic_adapter import GenericAdapter
from orchestrator.adapters.node_adapter import NodeAdapter
from orchestrator.adapters.python_adapter import PythonAdapter


def get_available_adapters() -> List[ProjectAdapter]:
    """Return all registered language adapters."""
    return [NodeAdapter(), PythonAdapter(), GenericAdapter()]


def detect_adapter(
    workspace: Path, forced_language: Optional[str] = None
) -> ProjectAdapter:
    """Detect and return the appropriate ProjectAdapter for a workspace."""
    workspace = Path(workspace)

    # 1. Handle explicit language override
    if forced_language:
        lang = forced_language.strip().lower()
        if lang in ("python", "py"):
            return PythonAdapter()
        if lang in ("node", "nodejs", "javascript", "typescript", "js", "ts"):
            return NodeAdapter()
        if lang in ("generic", "other"):
            return GenericAdapter()

    node_adapter = NodeAdapter()
    python_adapter = PythonAdapter()

    node_detected = node_adapter.detect(workspace)
    python_detected = python_adapter.detect(workspace)

    # 2. Unambiguous detection
    if node_detected and not python_detected:
        return node_adapter
    if python_detected and not node_detected:
        return python_adapter

    # 3. Ambiguous (both package.json and pyproject/requirements exist, e.g. full-stack monorepo)
    if node_detected and python_detected:
        # Determine dominant language by file count
        try:
            py_count = len(list(workspace.glob("*.py"))) + len(
                list((workspace / "src").glob("**/*.py"))
            )
        except Exception:
            py_count = 0
        try:
            ts_js_count = (
                len(list(workspace.glob("*.ts")))
                + len(list(workspace.glob("*.js")))
                + len(list((workspace / "src").glob("**/*.ts")))
                + len(list((workspace / "src").glob("**/*.js")))
            )
        except Exception:
            ts_js_count = 0

        if ts_js_count > py_count:
            return node_adapter
        return python_adapter

    # 4. Fallback
    return GenericAdapter()
