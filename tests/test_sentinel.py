"""Unit tests for the Autonomous Cognitive Sentinel SRE Mesh."""

import time
from pathlib import Path
from tempfile import TemporaryDirectory

from orchestrator.core.config import OrchestratorConfig
from orchestrator.core.exceptions import ProviderQuotaExceededError
from orchestrator.core.protocols import (
    CognitiveIncident,
    IncidentSeverity,
    InterventionAction,
)
from orchestrator.sentinel.ast_guard import ASTGuard
from orchestrator.sentinel.cloud_governor import CloudMeshGovernor
from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB
from orchestrator.sentinel.heuristics import HeuristicsDriftDetector
from orchestrator.sentinel.supervisor import CognitiveSentinelSupervisor
from orchestrator.tools.workspace_tools import (
    WorkspaceFileAction,
    WorkspaceTerminalAction,
    execute_file_action,
    execute_terminal_action,
)


def test_ast_guard_syntax_error():
    guard = ASTGuard()
    broken_code = "def invalid_func(\n    return 42"
    is_safe, msg, healed = guard.intercept_ast(Path("broken.py"), broken_code)
    assert not is_safe
    assert "SyntaxError" in msg
    assert healed is None


def test_ast_guard_valid_python():
    guard = ASTGuard()
    valid_code = "def valid_func() -> int:\n    return 42\n"
    is_safe, msg, healed = guard.intercept_ast(Path("valid.py"), valid_code)
    assert is_safe
    assert msg == ""
    assert healed == valid_code


def test_ast_guard_auto_heal_missing_imports():
    guard = ASTGuard()
    unhealed_code = (
        '"""Module docstring."""\n'
        "\n"
        "@dataclass\n"
        "class Config:\n"
        "    path: Path\n"
        "    items: List[str]\n"
        "\n"
        "def parse():\n"
        "    return json.dumps({})\n"
    )
    is_safe, msg, healed = guard.intercept_ast(Path("test_mod.py"), unhealed_code)
    assert is_safe
    assert "Auto-healed missing imports" in msg
    assert "from dataclasses import dataclass" in healed
    assert "from pathlib import Path" in healed
    assert "from typing import List" in healed
    assert "import json" in healed


def test_ast_guard_disallowed_stubs():
    guard = ASTGuard(disallow_stubs=True)
    stub_code = "def empty_worker():\n    pass\n"
    is_safe, msg, healed = guard.intercept_ast(Path("worker.py"), stub_code)
    assert not is_safe
    assert "Prohibited empty stub" in msg


def test_cloud_governor_healthy():
    gov = CloudMeshGovernor(fallback_chain=["model-b", "model-c"])
    can_proceed, reason, fallback = gov.intercept_cloud_call(
        provider="openrouter", model="model-a", prompt_tokens=2000
    )
    assert can_proceed
    assert fallback is None


def test_cloud_governor_prompt_ceiling():
    gov = CloudMeshGovernor(max_prompt_ceiling=10_000, fallback_chain=["model-b"])
    can_proceed, reason, fallback = gov.intercept_cloud_call(
        provider="openrouter", model="model-a", prompt_tokens=15_000
    )
    assert not can_proceed
    assert "exceed safety ceiling" in reason
    assert fallback == "model-b"


def test_cloud_governor_circuit_breaker():
    gov = CloudMeshGovernor(circuit_threshold=2, fallback_chain=["model-b", "model-c"])
    # Record two failures
    gov.record_call_result("openrouter", "model-a", success=False, latency_ms=100.0)
    fallback = gov.record_call_result(
        "openrouter", "model-a", success=False, latency_ms=120.0, status_code=429
    )
    assert fallback == "model-b"

    # Subsequent intercept should fail and recommend fallback
    can_proceed, reason, rec_model = gov.intercept_cloud_call(
        provider="openrouter", model="model-a", prompt_tokens=1000
    )
    assert not can_proceed
    assert "circuit breaker is TRIPPED" in reason
    assert rec_model == "model-b"


def test_heuristics_drift_detector():
    detector = HeuristicsDriftDetector(
        max_steps_without_edit=3, token_burn_threshold=10_000
    )
    # Low tokens -> no drift
    drift, _ = detector.evaluate_investigation_drift(
        "developer", steps=2, tokens_burned=5000, edits_done=0
    )
    assert not drift

    # High tokens and steps with 0 edits -> drift detected
    drift, directive = detector.evaluate_investigation_drift(
        "developer", steps=4, tokens_burned=12_000, edits_done=0
    )
    assert drift
    assert "SENTINEL INTERVENTION" in directive

    # If edits were done -> no drift
    drift, _ = detector.evaluate_investigation_drift(
        "developer", steps=4, tokens_burned=12_000, edits_done=1
    )
    assert not drift


def test_heuristics_repeated_tool_calls():
    detector = HeuristicsDriftDetector()
    args = {"path": "orchestrator/pipeline/base_pipeline.py"}
    is_repeated, _ = detector.check_repeated_tool_call("WorkspaceFileAction", args)
    assert not is_repeated

    # Calling again with identical args
    is_repeated, msg = detector.check_repeated_tool_call("WorkspaceFileAction", args)
    assert is_repeated
    assert "Identical repeated call" in msg


def test_diagnostics_db_crud():
    with TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_sentinel.db"
        db = SentinelDiagnosticsDB(db_path=db_path)

        incident = CognitiveIncident(
            incident_id="INC-TEST-001",
            severity=IncidentSeverity.HIGH,
            origin_module="test_mod",
            target_role="tester",
            error_signature="assertion_error",
            raw_payload={"detail": "sample"},
            suggested_action=InterventionAction.AUTO_PATCH_CODE,
            auto_healed=True,
            remedy_description="Patched code fixture",
            timestamp_epoch=time.time(),
        )
        db.record_incident(incident)
        history = db.get_incident_history()
        assert len(history) == 1
        assert history[0]["incident_id"] == "INC-TEST-001"
        assert history[0]["auto_healed"] == 1

        stats = db.get_stats()
        assert stats["total_incidents"] == 1
        assert stats["auto_healed_count"] == 1
        assert stats["healing_rate"] == 1.0


def test_sentinel_supervisor_lifecycle():
    with TemporaryDirectory() as tmp_dir:
        cfg = OrchestratorConfig(
            workspace_path=Path(tmp_dir),
            cloud_fallback_chain=["model-fallback-1", "model-fallback-2"],
        )
        supervisor = CognitiveSentinelSupervisor(config=cfg, workspace=Path(tmp_dir))

        # 1. AST interception with auto-heal
        unhealed_code = "def worker():\n    return json.dumps({'status': True})\n"
        is_safe, msg, healed = supervisor.intercept_ast_mutation(
            Path("worker.py"), unhealed_code
        )
        assert is_safe
        assert "import json" in healed

        # 2. Runtime error handling
        exc = ProviderQuotaExceededError(provider="OpenRouter", message="Rate limited")
        incident = supervisor.handle_runtime_error(exc, {"role": "developer"})
        assert incident.suggested_action == InterventionAction.SWITCH_CLOUD_PROVIDER
        assert incident.severity == IncidentSeverity.CRITICAL

        # 3. Investigation drift check
        drift = supervisor.evaluate_investigation_drift("developer", 5, 45_000, 0)
        assert drift

        # 4. Mesh health status
        health = supervisor.get_health_status()
        assert health["sentinel_active"] is True
        assert health["incidents"]["total_incidents"] >= 2


def test_workspace_tools_ast_guard_integration():
    with TemporaryDirectory() as tmp_dir:
        base_dir = Path(tmp_dir)

        # 1. Attempt writing invalid python syntax -> should be blocked by ASTGuard
        broken_action = WorkspaceFileAction(
            operation="write",
            path="broken.py",
            content="def broken_syntax(\n    return 1",
        )
        obs = execute_file_action(broken_action, base_dir=base_dir)
        assert obs.is_error
        assert "AST Integrity Violation" in obs.message
        assert not (base_dir / "broken.py").exists()

        # 2. Writing python missing standard import -> should be auto-healed
        heal_action = WorkspaceFileAction(
            operation="write",
            path="healed.py",
            content="def get_file():\n    return Path('test.txt')\n",
        )
        obs = execute_file_action(heal_action, base_dir=base_dir)
        assert not obs.is_error
        saved_content = (base_dir / "healed.py").read_text(encoding="utf-8")
        assert "from pathlib import Path" in saved_content


def test_workspace_tools_fuzzy_edit_fallback():
    with TemporaryDirectory() as tmp_dir:
        base_dir = Path(tmp_dir)
        file_path = base_dir / "sample.py"
        file_path.write_text(
            "def calculate(a, b):\n    result = a + b    \n    return result\n",
            encoding="utf-8",
        )

        # Target has no trailing space on `result = a + b` -> fuzzy matcher handles it
        edit_action = WorkspaceFileAction(
            operation="edit",
            path="sample.py",
            target_text="    result = a + b\n    return result",
            replacement_text="    return a + b",
        )
        obs = execute_file_action(edit_action, base_dir=base_dir)
        assert not obs.is_error
        updated = file_path.read_text(encoding="utf-8")
        assert "return a + b" in updated


def test_workspace_tools_windows_command_translation():
    with TemporaryDirectory() as tmp_dir:
        action = WorkspaceTerminalAction(command="ls")
        obs = execute_terminal_action(action, base_dir=Path(tmp_dir))
        assert not obs.timed_out
        assert "Security policy violation" not in obs.stderr


def test_cloud_resilience_mesh_test_mesh():
    from orchestrator.config import OrchestratorConfig
    from orchestrator.llm.manager import CloudResilienceMesh

    cfg = OrchestratorConfig(
        cloud_fallback_chain=[
            "openrouter/google/gemini-2.0-flash-001",
            "gemini/gemini-2.0-flash",
            "groq/llama-3.3-70b-versatile",
        ]
    )
    mesh = CloudResilienceMesh(cfg)
    results = mesh.test_mesh()
    assert len(results) == 3
    assert results[0]["tier"] == 1
    assert results[0]["provider"] == "openrouter"
    assert "circuit_state" in results[0]


def test_git_ops_rollback_and_checkpoint():
    from orchestrator.vcs.git_ops import GitOps

    with TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir)
        git = GitOps(repo_dir)
        git.init_repo()

        file_path = repo_dir / "code.py"
        file_path.write_text("x = 1\n", encoding="utf-8")
        git.commit("initial commit")

        # Create checkpoint before modification
        cp = git.create_checkpoint("test_checkpoint")
        assert cp is not None

        # Corrupt file
        file_path.write_text("broken_syntax(\n", encoding="utf-8")
        assert git.has_uncommitted_changes()

        # Execute safe rollback
        reverted = git.rollback(hard=True)
        assert reverted
        assert file_path.read_text(encoding="utf-8") == "x = 1\n"
        assert not git.has_uncommitted_changes()


def test_rendering_sentinel_extensions():
    from orchestrator.rendering.diff_renderer import DiffRenderer
    from orchestrator.rendering.output import ConsoleOutput
    from orchestrator.rendering.report_generator import MarkdownReportGenerator

    # 1. DiffRenderer with self-healed tag
    panel = DiffRenderer.render_file_change(
        "app.py", "def foo(): pass", "import os\ndef foo(): pass", is_self_healed=True
    )
    assert "SELF-HEALED" in str(panel.title)

    # 2. MarkdownReportGenerator with sentinel stats
    stats = {
        "total_incidents": 5,
        "auto_healed_count": 4,
        "healing_rate": 0.8,
        "failed_cloud_calls": 1,
    }
    report = MarkdownReportGenerator.generate_pipeline_summary(
        task="Test task",
        mode="hybrid",
        status="SUCCESS",
        iterations=2,
        duration_seconds=5.2,
        total_tokens=1000,
        total_cost_usd=0.01,
        sentinel_stats=stats,
    )
    assert "Cognitive Sentinel & Digital Immunity" in report
    assert "Autonomous Self-Healed Count" in report

    # 3. ConsoleOutput methods
    ConsoleOutput.sentinel_step("AST Check", "Validated clean")
    ConsoleOutput.self_healing_alert("main.py", "Missing import", "Added import sys")
    ConsoleOutput.cloud_failover_banner("model-a", "model-b", "Rate limited")


def test_handle_sentinel_heal_directory():
    from orchestrator.cli.handlers import handle_sentinel_heal

    with TemporaryDirectory() as tmp_dir:
        base_dir = Path(tmp_dir)
        sub_dir = base_dir / "pkg"
        sub_dir.mkdir()

        # Clean file
        (base_dir / "clean.py").write_text("def ok(): return 1\n", encoding="utf-8")
        # Missing import file -> auto-heal
        (sub_dir / "needs_heal.py").write_text(
            "def worker(): return json.dumps({'a': 1})\n", encoding="utf-8"
        )
        # Broken syntax file
        (sub_dir / "broken.py").write_text("def broken(\n", encoding="utf-8")

        handle_sentinel_heal(base_dir)

        # Check healed file got auto-healed
        healed_content = (sub_dir / "needs_heal.py").read_text(encoding="utf-8")
        assert "import json" in healed_content

