"""Unit tests for Phase 16 Domain Profiles, CLI package, and Documentation Pipeline."""

import sys
from pathlib import Path
from unittest.mock import patch


from orchestrator.cli.app import parse_args
from orchestrator.cli.handlers import (
    handle_check_config,
    handle_list_skills,
    resolve_workspace_dir,
)
from orchestrator.core.config import DomainProfile, OrchestratorConfig
from orchestrator.orchestrator import Orchestrator
from orchestrator.pipeline.documentation_pipeline import DocumentationPipeline
from orchestrator.skills.manager import SkillManager


# ---------------------------------------------------------------------------
# 1. CLI Package Tests
# ---------------------------------------------------------------------------


def test_cli_parse_args_domain_and_diff():
    """CLI argument parser must support --domain and --diff flags."""
    with patch.object(sys, "argv", ["orchestrator", "--domain", "nodejs", "--diff"]):
        args = parse_args()
        assert args.domain == "nodejs"
        assert args.diff is True


def test_cli_resolve_workspace_dir(tmp_path: Path):
    """resolve_workspace_dir should resolve directory and fall back from file to parent."""
    # Target is a directory
    test_dir = tmp_path / "my_project"
    test_dir.mkdir()
    assert resolve_workspace_dir(test_dir, tmp_path) == test_dir.resolve()

    # Target is a file -> resolves to parent
    test_file = test_dir / "app.py"
    test_file.write_text("print(1)")
    assert resolve_workspace_dir(test_file, tmp_path) == test_dir.resolve()

    # Target is None -> resolves default
    assert resolve_workspace_dir(None, tmp_path) == tmp_path.resolve()


def test_cli_handlers_smoke(tmp_path: Path, capsys):
    """CLI handlers must execute cleanly without exceptions."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(tmp_path)

    # 1. list skills
    handle_list_skills(sm)

    # 2. check config
    with patch(
        "orchestrator.analysis.connectivity.ConnectivityChecker.run_zero_token_audit"
    ):
        handle_check_config(cfg)
        captured = capsys.readouterr()
        assert "Environment & Cost Safety Controls:" in captured.out
        assert "Active Domain:" in captured.out


# ---------------------------------------------------------------------------
# 2. Domain Profile System
# ---------------------------------------------------------------------------


def test_domain_profile_switching(tmp_path: Path):
    """OrchestratorConfig must support dynamic domain profile switching."""
    cfg = OrchestratorConfig(active_domain="nodejs")
    profile = cfg.get_current_domain_profile()
    assert profile.name == "nodejs"
    assert profile.test_command == "npm test"
    assert ".ts" in profile.preflight_extensions

    # Custom domain definition
    cfg.domain_profiles["rust"] = DomainProfile(
        name="rust",
        test_command="cargo test",
        lint_command="cargo clippy",
        preflight_extensions=[".rs"],
    )
    cfg.active_domain = "rust"
    rust_profile = cfg.get_current_domain_profile()
    assert rust_profile.name == "rust"
    assert rust_profile.test_command == "cargo test"


# ---------------------------------------------------------------------------
# 3. Documentation Pipeline & Orchestrator Dispatch
# ---------------------------------------------------------------------------


def test_documentation_pipeline_instantiation(tmp_path: Path):
    """DocumentationPipeline must initialize with DocumentationAgent."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    sm = SkillManager(tmp_path)
    pipeline = DocumentationPipeline(
        config=cfg, skill_manager=sm, workspace_path=tmp_path
    )
    assert pipeline.workspace_path == tmp_path


def test_orchestrator_routes_docs_mode(tmp_path: Path):
    """Orchestrator must route mode='docs' to DocumentationPipeline."""
    cfg = OrchestratorConfig(workspace_path=tmp_path)
    orc = Orchestrator(cfg)

    with patch.object(
        DocumentationPipeline, "run", return_value={"status": "SUCCESS"}
    ) as mock_run:
        res = orc.run_task(
            "Generate documentation", mode="docs", workspace_override=tmp_path
        )
        assert res == {"status": "SUCCESS"}
        mock_run.assert_called_once_with("Generate documentation")
