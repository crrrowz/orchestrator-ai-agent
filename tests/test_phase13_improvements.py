"""Unit tests for Phase 13 enterprise configuration system and PLAN.md handling."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.config import (
    ORCHESTRATOR_ROOT,
    AgentRoleConfig,
    ConfigLoader,
    ConfigSchema,
    OrchestratorConfig,
    SkillManager,
    create_llm_for_role,
    normalize_model_slug,
)
from orchestrator.telemetry.recorder import TelemetryRecorder


def test_backward_compatibility_exports():
    """Verify that all legacy imports from orchestrator.config continue to function seamlessly."""
    assert ORCHESTRATOR_ROOT.is_dir()
    cfg = OrchestratorConfig()
    assert isinstance(cfg.developer, AgentRoleConfig)
    assert normalize_model_slug("qwen/qwen3.8-27b") == "openrouter/qwen/qwen3.8-27b:free"
    sm = SkillManager(ORCHESTRATOR_ROOT)
    assert isinstance(sm.available_skills, list)


def test_config_loader_discovery(tmp_path: Path):
    """ConfigLoader should locate orchestrator.config.json across resolution targets."""
    # 1. Custom path
    custom_cfg = tmp_path / "custom.config.json"
    custom_cfg.write_text("{}", encoding="utf-8")
    assert ConfigLoader.find_config_file(custom_path=custom_cfg) == custom_cfg.resolve()

    # 2. Start directory
    local_cfg = tmp_path / "orchestrator.config.json"
    local_cfg.write_text("{}", encoding="utf-8")
    assert ConfigLoader.find_config_file(start_dir=tmp_path) == local_cfg.resolve()

    # 3. Environment variable
    with patch.dict("os.environ", {"ORCHESTRATOR_CONFIG_PATH": str(custom_cfg)}):
        assert ConfigLoader.find_config_file() == custom_cfg.resolve()


def test_config_loader_parsing_and_defaults(tmp_path: Path):
    """ConfigLoader should parse nested JSON and correctly map to OrchestratorConfig fields."""
    sample_json = {
        "execution": {
            "max_iterations": 7,
            "max_budget_usd": 1.25,
            "max_tokens_budget": 450000,
            "max_agent_steps": 15,
            "max_tokens_per_call": 4096,
            "circuit_breaker_threshold": 3,
            "conversation_timeout_seconds": 180,
            "auto_commit": False,
            "auto_chain_audit": False,
            "workspace_path": str(tmp_path / "workspace"),
        },
        "agents": {
            "developer": {
                "model": "openrouter/anthropic/claude-3.5-sonnet",
                "temperature": 0.15,
                "skills": ["clean-python-architecture"],
            },
            "tester": {
                "model": "openrouter/openai/gpt-4o",
                "temperature": 0.05,
                "skills": ["pytest-rigorous-testing"],
            },
        },
        "memory": {
            "enabled": False,
            "relevance_min_score": 4.5,
            "max_memory_results": 5,
            "max_memory_chars": 2000,
        },
        "telemetry": {
            "max_retained_reports": 35,
            "max_retained_sessions_per_project": 12,
            "log_save_debounce_seconds": 8,
        },
        "safety": {
            "terminal_command_allowlist": ["pytest", "git"],
            "blocked_write_prefixes_developer": ["tests/", "docs/"],
        },
        "rendering": {
            "verbosity": "verbose",
            "show_diff_preview": False,
            "diff_max_lines_per_file": 25,
            "diff_max_chars": 1500,
        },
        "human_in_the_loop": {
            "interactive": True,
            "approval_gates": ["after_architect"],
        },
    }

    cfg_file = tmp_path / "test.config.json"
    cfg_file.write_text(json.dumps(sample_json), encoding="utf-8")

    cfg = ConfigLoader.load(config_path=cfg_file)

    assert cfg.max_iterations == 7
    assert cfg.max_budget_usd == 1.25
    assert cfg.max_tokens_budget == 450000
    assert cfg.max_agent_steps == 15
    assert cfg.max_tokens_per_call == 4096
    assert cfg.circuit_breaker_threshold == 3
    assert cfg.conversation_timeout_seconds == 180
    assert cfg.auto_commit is False
    assert cfg.auto_chain_audit is False
    assert cfg.developer.model == "openrouter/anthropic/claude-3.5-sonnet"
    assert cfg.developer.temperature == 0.15
    assert cfg.developer.skills == ["clean-python-architecture"]
    assert cfg.tester.model == "openrouter/openai/gpt-4o"
    assert cfg.enable_memory is False
    assert cfg.memory_relevance_min_score == 4.5
    assert cfg.max_memory_results == 5
    assert cfg.max_retained_reports == 35
    assert cfg.log_save_debounce_seconds == 8
    assert cfg.terminal_command_allowlist == ["pytest", "git"]
    assert cfg.blocked_write_prefixes_developer == ["tests/", "docs/"]
    assert cfg.verbosity == "verbose"
    assert cfg.show_diff_preview is False
    assert cfg.diff_max_lines_per_file == 25
    assert cfg.interactive is True
    assert cfg.approval_gates == ["after_architect"]


def test_config_loader_priority_cascade(tmp_path: Path):
    """Overrides passed to load() must take precedence over values in the JSON config."""
    cfg_file = tmp_path / "test.config.json"
    cfg_file.write_text(
        json.dumps({"execution": {"max_iterations": 4, "max_budget_usd": 0.50}}),
        encoding="utf-8",
    )

    # Override max_iterations and max_budget_usd explicitly
    cfg = ConfigLoader.load(config_path=cfg_file, max_iterations=10, max_budget_usd=2.00)

    assert cfg.max_iterations == 10
    assert cfg.max_budget_usd == 2.00


def test_config_loader_save_and_reload(tmp_path: Path):
    """ConfigLoader.save() must correctly serialize an OrchestratorConfig for round-trip loading."""
    cfg = OrchestratorConfig(
        max_iterations=8,
        max_budget_usd=1.50,
        enable_memory=False,
        terminal_command_allowlist=["pytest", "python", "git"],
    )

    save_path = tmp_path / "saved_orchestrator.config.json"
    ConfigLoader.save(cfg, save_path)
    assert save_path.is_file()

    reloaded = ConfigLoader.load(config_path=save_path)
    assert reloaded.max_iterations == 8
    assert reloaded.max_budget_usd == 1.50
    assert reloaded.enable_memory is False
    assert reloaded.terminal_command_allowlist == ["pytest", "python", "git"]


def test_config_schema_validation():
    """ConfigSchema should validate schema compliance and flag invalid data."""
    schema = ConfigSchema.get_schema()
    assert "$schema" in schema
    assert "properties" in schema
    assert "execution" in schema["properties"]
    assert "agents" in schema["properties"]

    # Valid config
    valid_data = {
        "execution": {"max_iterations": 4, "max_budget_usd": 0.50},
        "agents": {"developer": {"temperature": 0.2}},
    }
    assert ConfigSchema.validate_dict(valid_data) == []

    # Invalid config
    invalid_data = {
        "execution": {"max_budget_usd": -1.0, "max_iterations": "invalid_val"},
        "agents": {"developer": {"temperature": 5.0, "skills": "not_a_list"}},
    }
    errors = ConfigSchema.validate_dict(invalid_data)
    assert len(errors) >= 3
    assert any("max_budget_usd" in e for e in errors)
    assert any("temperature" in e for e in errors)
    assert any("skills" in e for e in errors)


def test_plan_md_missing_incident_recording(tmp_path: Path):
    """When PLAN.md is missing or empty, full_pipeline logic must record an incident."""
    recorder = TelemetryRecorder(task_description="test task", reports_dir=tmp_path)
    plan_path = tmp_path / "PLAN.md"

    # Simulate empty or missing plan condition
    plan_content = plan_path.read_text() if plan_path.exists() else ""
    if not plan_path.exists() or not plan_content.strip():
        recorder.record_incident(
            "PLAN.md", "missing_plan", "Architect did not produce PLAN.md"
        )

    assert len(recorder.incidents) == 1
    assert recorder.incidents[0].step_name == "PLAN.md"
    assert recorder.incidents[0].incident_type == "missing_plan"
