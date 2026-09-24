"""Tests for Polyglot Project Adapters (Python, Node.js, Generic)."""

import json
from pathlib import Path

from orchestrator.adapters import (
    GenericAdapter,
    NodeAdapter,
    PythonAdapter,
    detect_adapter,
)


def test_detect_adapter_python_workspace(tmp_path: Path):
    """Verify detect_adapter accurately identifies Python projects."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\n", encoding="utf-8"
    )
    adapter = detect_adapter(tmp_path)
    assert isinstance(adapter, PythonAdapter)
    assert adapter.language_name == "python"


def test_detect_adapter_nodejs_workspace(tmp_path: Path):
    """Verify detect_adapter accurately identifies Node.js / TypeScript projects."""
    pkg = {"name": "sample-node", "scripts": {"test": "vitest run"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    adapter = detect_adapter(tmp_path)
    assert isinstance(adapter, NodeAdapter)
    assert adapter.language_name == "nodejs"


def test_detect_adapter_generic_fallback(tmp_path: Path):
    """Verify fallback to GenericAdapter when no recognized manifest is present."""
    (tmp_path / "README.txt").write_text("Plain project", encoding="utf-8")
    adapter = detect_adapter(tmp_path)
    assert isinstance(adapter, GenericAdapter)
    assert adapter.language_name == "generic"


def test_detect_adapter_forced_language(tmp_path: Path):
    """Verify forced language override bypasses filesystem detection."""
    # Even in an empty dir, forced_language='nodejs' returns NodeAdapter
    adapter_node = detect_adapter(tmp_path, forced_language="nodejs")
    assert isinstance(adapter_node, NodeAdapter)

    adapter_py = detect_adapter(tmp_path, forced_language="python")
    assert isinstance(adapter_py, PythonAdapter)


def test_node_adapter_test_commands(tmp_path: Path):
    """Verify NodeAdapter resolves the correct package-manager-aware test runner."""
    adapter = NodeAdapter()

    # 1. Default npm test
    pkg = {"name": "app", "scripts": {"test": "jest"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    assert adapter.get_test_command(tmp_path) == "npm test"

    # 2. Yarn lockfile
    (tmp_path / "yarn.lock").write_text("", encoding="utf-8")
    # If yarn CLI mock/present
    assert adapter.has_test_suite(tmp_path) is True

    # 3. Direct runner fallback
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "app"}), encoding="utf-8"
    )
    (tmp_path / "vitest.config.ts").write_text("export default {}", encoding="utf-8")
    assert adapter.get_test_command(tmp_path) == "npx vitest run"


def test_node_adapter_failure_parser():
    """Verify NodeAdapter extracts compact error signals and filters npm noise."""
    adapter = NodeAdapter()
    sample_npm_output = """
npm ERR! code 1
npm ERR! path D:\\projects\\demo
FAIL src/calculator.test.ts
  ✕ should sum two numbers properly
    AssertionError: expected 4 to deeply equal 5
    Expected: 5
    Received: 4
      at src/calculator.test.ts:12:18
npm ERR! A complete log of this run can be found in:
"""
    compact = adapter.parse_test_failures(sample_npm_output, "")
    assert "npm ERR!" not in compact
    assert "FAIL src/calculator.test.ts" in compact
    assert "AssertionError" in compact


def test_node_adapter_metrics(tmp_path: Path):
    """Verify NodeAdapter counts TypeScript/JavaScript files and ignores node_modules."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "index.ts").write_text(
        "export const a = 1;\nexport const b = 2;\n", encoding="utf-8"
    )
    (src_dir / "util.js").write_text("console.log('hi');\n", encoding="utf-8")

    nm_dir = tmp_path / "node_modules" / "pkg"
    nm_dir.mkdir(parents=True)
    (nm_dir / "ignored.js").write_text("ignored", encoding="utf-8")

    adapter = NodeAdapter()
    metrics = adapter.collect_codebase_metrics(tmp_path)
    assert metrics["total_files"] == 2
    assert metrics["language"] == "Node.js / TypeScript"


def test_python_adapter_metrics_and_guidance(tmp_path: Path):
    """Verify PythonAdapter metrics and developer prompt guidance."""
    adapter = PythonAdapter()
    (tmp_path / "main.py").write_text("def hello():\n    pass\n", encoding="utf-8")
    metrics = adapter.collect_codebase_metrics(tmp_path)
    assert metrics["total_files"] == 1
    assert metrics["language"] == "Python"

    guidance = adapter.get_developer_prompt_guidance()
    assert "PEP 8" in guidance
    assert "pytest" in guidance
