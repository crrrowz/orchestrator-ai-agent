"""Unit tests verifying Phase 3: Human-in-the-Loop (HITL) & Approval Gates."""

from io import StringIO

from orchestrator.config import OrchestratorConfig
from orchestrator.control import HumanInterventionChannel
from orchestrator.utils.visualizer import OrchestratorLiveVisualizer, SessionLogStore
from rich.console import Console


def test_human_channel_message_queue_and_injection():
    """HumanInterventionChannel should queue operator messages and prepend them cleanly to prompts."""
    channel = HumanInterventionChannel(enabled=True)
    assert not channel.has_message()

    base_prompt = "Write a calculator module in Python."
    # With no messages, prompt remains untouched
    assert channel.inject_into_prompt(base_prompt) == base_prompt

    # Enqueue guidance
    channel.send_message("Use Decimal instead of float for monetary calculations.")
    channel.send_message("Ensure 100% test coverage.")
    assert channel.has_message()

    modified_prompt = channel.inject_into_prompt(base_prompt)
    assert "[HUMAN OPERATOR GUIDANCE]:" in modified_prompt
    assert "Use Decimal instead of float" in modified_prompt
    assert "Ensure 100% test coverage" in modified_prompt
    assert base_prompt in modified_prompt

    # Queue should be empty after injection
    assert not channel.has_message()


def test_human_channel_approval_gates_interactive_mock():
    """HumanInterventionChannel.prompt_gate should handle approved, rejected, and guidance responses."""
    channel = HumanInterventionChannel(enabled=True)

    # 1. Approval
    res_approve = channel.prompt_gate(
        "after_architect", "PLAN.md preview", input_fn=lambda _: "y"
    )
    assert res_approve == "approved"

    # 2. Rejection
    res_reject = channel.prompt_gate(
        "after_developer", "Diff preview", input_fn=lambda _: "n"
    )
    assert res_reject == "rejected"

    # 3. Modification / Guidance
    inputs = iter(["m", "Please rename class Foo to Bar."])
    res_mod = channel.prompt_gate(
        "after_developer", "Diff preview", input_fn=lambda _: next(inputs)
    )
    assert res_mod == "modified"
    assert channel.has_message()
    assert channel.get_message() == "Please rename class Foo to Bar."


def test_human_channel_disabled_bypass():
    """Disabled channel should automatically approve all gates without prompting."""
    channel = HumanInterventionChannel(enabled=False)

    # Should never call input_fn when disabled
    def fail_if_called(_):
        raise RuntimeError("Should not be called")

    assert channel.prompt_gate("before_commit", input_fn=fail_if_called) == "approved"


def test_visualizer_verbosity_modes():
    """Live visualizer should respect quiet, normal, and verbose modes."""
    output_io = StringIO()
    test_console = Console(file=output_io, force_terminal=True, width=120)
    store = SessionLogStore()

    # 1. Quiet mode: suppresses thought lines
    viz_quiet = OrchestratorLiveVisualizer(
        store, console=test_console, verbosity="quiet"
    )
    assert viz_quiet.verbosity == "quiet"

    # 2. Verbose mode: preserves full thoughts without truncation
    viz_verbose = OrchestratorLiveVisualizer(
        store, console=test_console, verbosity="verbose"
    )
    assert viz_verbose.verbosity == "verbose"

    long_thought = "Thinking about architecture: " + ("deep analysis " * 20)
    viz_verbose._last_thought = long_thought

    # Create dummy action event
    class DummyAction:
        operation = "read"
        path = "main.py"

    class ActionEvent:
        action = DummyAction()

    viz_verbose.on_event(ActionEvent())
    captured = output_io.getvalue()
    # In verbose mode, the entire thought should be printed (not truncated with '...')
    assert "deep analysis deep analysis" in captured


def test_config_approval_gates_parsing(monkeypatch):
    """OrchestratorConfig should properly parse comma-separated approval gates from env."""
    monkeypatch.setenv(
        "APPROVAL_GATES", "after_architect, after_developer, before_commit"
    )
    monkeypatch.setenv("INTERACTIVE", "true")
    monkeypatch.setenv("VERBOSITY", "verbose")

    cfg = OrchestratorConfig()
    assert cfg.approval_gates == ["after_architect", "after_developer", "before_commit"]
    assert cfg.interactive is True
    assert cfg.verbosity == "verbose"
