"""Comprehensive unit and integration tests for Cognitive Sentinel, Self-Healing, and Cloud Mesh."""

from pathlib import Path

from orchestrator.sentinel import (
    CognitiveSentinelSupervisor,
    SelfHealingEngine,
    CloudResilienceMesh,
    TerminalCommandTranslator,
    SentinelMode,
    IncidentSeverity,
    InterventionAction,
    ProviderHealthStatus,
)


class TestSelfHealingEngine:
    """Tests for zero-token AST code repairs, missing import injection, and fuzzy edits."""

    def test_heal_syntax_missing_colon(self, tmp_path: Path):
        engine = SelfHealingEngine()
        broken_code = "def calculate_total(a, b)\n    return a + b\n"
        test_file = tmp_path / "math_ops.py"

        healed, fixed_code, note = engine.heal_syntax_error(
            test_file, broken_code, "SyntaxError: expected ':'"
        )
        assert healed is True
        assert "def calculate_total(a, b):" in fixed_code
        assert "Auto-injected missing colon" in note

    def test_heal_syntax_empty_indented_block(self, tmp_path: Path):
        engine = SelfHealingEngine()
        broken_code = "class DataHandler:\n    def process(self):\n\ndef next_step():\n    return True\n"
        test_file = tmp_path / "handler.py"

        healed, fixed_code, note = engine.heal_syntax_error(
            test_file, broken_code, "IndentationError: expected an indented block"
        )
        assert healed is True
        assert "pass" in fixed_code

    def test_heal_syntax_mixed_tabs_spaces(self, tmp_path: Path):
        engine = SelfHealingEngine()
        broken_code = "def compute():\n\tx = 1\n    return x\n"
        test_file = tmp_path / "compute.py"

        healed, fixed_code, note = engine.heal_syntax_error(
            test_file, broken_code, "TabError: inconsistent use of tabs and spaces"
        )
        assert healed is True
        assert "\t" not in fixed_code

    def test_inject_missing_import(self, tmp_path: Path):
        engine = SelfHealingEngine()
        code_without_tuple = '"""Docstring."""\n\ndef get_coords() -> Tuple[int, int]:\n    return (1, 2)\n'
        test_file = tmp_path / "geo.py"

        injected, updated_code, note = engine.inject_missing_import(
            test_file, code_without_tuple, "Tuple"
        )
        assert injected is True
        assert "from typing import Tuple" in updated_code
        assert "Injected missing import" in note

    def test_fix_fuzzy_edit_indentation(self):
        engine = SelfHealingEngine()
        original = "class Service:\n    def run(self):\n        step1()\n        step2()\n        return True\n"
        target = "step1()\nstep2()"
        replacement = "step1()\nstep_intermediate()\nstep2()"

        applied, updated, note = engine.fix_fuzzy_edit(original, target, replacement)
        assert applied is True
        assert "step_intermediate()" in updated
        assert "Applied fuzzy whitespace match" in note


class TestTerminalCommandTranslator:
    """Tests for translating UNIX utilities to PowerShell on Windows."""

    def test_translate_grep(self):
        cmd = 'grep -rn "API_KEY" src/'
        allowed, rewritten, note = TerminalCommandTranslator.intercept_and_translate(
            cmd, os_name="nt"
        )
        assert allowed is True
        assert "Select-String" in rewritten

    def test_translate_cat_head(self):
        cmd = "cat data.log | head -n 25"
        allowed, rewritten, note = TerminalCommandTranslator.intercept_and_translate(
            cmd, os_name="nt"
        )
        assert allowed is True
        assert "Get-Content data.log" in rewritten
        assert "Select-Object -First 25" in rewritten

    def test_translate_ls(self):
        cmd = "ls -la src/"
        allowed, rewritten, note = TerminalCommandTranslator.intercept_and_translate(
            cmd, os_name="nt"
        )
        assert allowed is True
        assert "Get-ChildItem -Force src/" in rewritten

    def test_translate_dev_null_redirect(self):
        cmd = "pytest -q > /dev/null 2>&1"
        allowed, rewritten, note = TerminalCommandTranslator.intercept_and_translate(
            cmd, os_name="nt"
        )
        assert allowed is True
        assert "$null" in rewritten


class TestCloudResilienceMesh:
    """Tests for multi-tier LLM provider failover and quota circuit breakers."""

    def test_record_success(self):
        mesh = CloudResilienceMesh(["google/gemini-3.7-flash", "openrouter/qwen/qwen-2.5-72b-instruct"])
        mesh.record_call_success("google/gemini-3.7-flash", latency_ms=120.5)

        summary = mesh.get_dashboard_summary()
        assert summary["google/gemini-3.7-flash"]["status"] == ProviderHealthStatus.ONLINE.value
        assert summary["google/gemini-3.7-flash"]["latency_ms"] == 120.5
        assert summary["google/gemini-3.7-flash"]["calls"] == 1

    def test_failover_on_429_quota_exhausted(self):
        chain = ["google/gemini-3.7-flash", "openrouter/qwen/qwen-2.5-72b-instruct", "groq/llama-3.3-70b-versatile"]
        mesh = CloudResilienceMesh(chain)

        # Trigger 429 quota exhaustion
        should_failover, next_model = mesh.record_call_failure(
            "google/gemini-3.7-flash", "Error 429: RateLimitError - daily free quota exhausted"
        )
        assert should_failover is True
        assert next_model == "openrouter/qwen/qwen-2.5-72b-instruct"

        # Healthy candidate selection
        healthy = mesh.get_healthy_provider("google/gemini-3.7-flash")
        assert healthy == "openrouter/qwen/qwen-2.5-72b-instruct"


class TestCognitiveSentinelSupervisor:
    """Tests for supervisor interception, incident logging, and dashboard state."""

    def setup_method(self):
        CognitiveSentinelSupervisor.reset_instance()

    def test_intercept_valid_python_file(self, tmp_path: Path):
        supervisor = CognitiveSentinelSupervisor.get_instance(
            mode=SentinelMode.ENFORCING, workspace_path=tmp_path
        )
        valid_code = "def add(x: int, y: int) -> int:\n    return x + y\n"
        allowed, msg, healed = supervisor.intercept_file_write(tmp_path / "valid.py", valid_code)
        assert allowed is True
        assert "verified cleanly" in msg
        assert healed is None

    def test_intercept_and_auto_heal_broken_file(self, tmp_path: Path):
        supervisor = CognitiveSentinelSupervisor.get_instance(
            mode=SentinelMode.ENFORCING, workspace_path=tmp_path
        )
        broken_code = "def multiply(a, b)\n    return a * b\n"
        allowed, msg, healed = supervisor.intercept_file_write(tmp_path / "broken.py", broken_code)
        assert allowed is True
        assert healed is not None
        assert "def multiply(a, b):" in healed
        assert supervisor.total_auto_heals >= 1

    def test_diagnose_and_heal_quota_error(self, tmp_path: Path):
        supervisor = CognitiveSentinelSupervisor.get_instance(
            mode=SentinelMode.ENFORCING, workspace_path=tmp_path
        )
        error = Exception("HTTP 429: RateLimitError insufficient_quota for model")
        incident = supervisor.diagnose_and_heal(
            error, {"role": "developer", "model": "google/gemini-3.7-flash"}
        )
        assert incident.severity == IncidentSeverity.CRITICAL
        assert incident.suggested_action == InterventionAction.SWITCH_CLOUD_PROVIDER
        assert incident.auto_healed is True

    def test_dashboard_state_generation(self, tmp_path: Path):
        supervisor = CognitiveSentinelSupervisor.get_instance(
            mode=SentinelMode.ENFORCING, workspace_path=tmp_path
        )
        state = supervisor.get_dashboard_state()
        assert state.sentinel_mode == SentinelMode.ENFORCING
        assert state.is_healthy is True
        assert len(state.provider_health) > 0
