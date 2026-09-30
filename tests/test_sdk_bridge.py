"""Comprehensive Test Suite for OpenHands SDK v1.49.4 Runtime Bridge and Clean Boundary.

Validates P10 Canonical Requirements:
- TEST-P10-01: Zero monkey-patching integrity (eradication of sdk_patch.py).
- TEST-P10-02: Hardened file tool SDK registration, schemas, and execution.
- TEST-P10-03: Hardened terminal tool SDK registration, schemas, and execution.
- TEST-P10-04: SDK tool adapter persona RBAC and tool constriction.
- TEST-P10-05: Exit status classifier for natural completion.
- TEST-P10-06: Exit status classifier for step limit ceiling.
- TEST-P10-07: Exit status classifier for token budget exhaustion.
- TEST-P10-08: Exit status classifier for tool rejection and security violations.
- TEST-P10-09: Exit status classifier for stuck agent loop and fatal errors.
- TEST-P10-10: Secret masking boundary in telemetry and live log streaming.
- TEST-P10-11: Synchronous EventStream demultiplexing to SessionLogStore.
- TEST-P10-12: SDK Agent factory configuration with concurrency limit.
- TEST-P10-13: OpenHandsRuntimeBridge master facade execution delegation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from openhands.sdk import Agent, LLM
from openhands.sdk.conversation import (
    ConversationExecutionStatus,
    LocalConversation,
)
from openhands.sdk.event import (
    ActionEvent,
    AgentErrorEvent,
    Event,
    ObservationEvent,
)
from openhands.sdk.event.conversation_error import ConversationErrorEvent
from openhands.sdk.llm.message import MessageToolCall, TextContent

from orchestrator.config import OrchestratorConfig
from orchestrator.engine.openhands_bridge import (
    AgentExecutionOutcome,
    AgentExitReason,
    ExitStatusClassifier,
    FileOperationType,
    HardenedFileAction,
    HardenedFileObservation,
    HardenedTerminalAction,
    HardenedTerminalObservation,
    HardenedWorkspaceFileTool,
    HardenedWorkspaceTerminalTool,
    OpenHandsRuntimeBridge,
    OpenHandsTelemetryBridge,
    PromptView,
    SDKAgentFactory,
    SDKSessionRunner,
    SDKToolAdapter,
    SecretMaskingFilter,
    TurnEnvelope,
)
from orchestrator.tools.hardened.manager import ToolSandboxManager
from orchestrator.ui.session_store import SessionLogStore


# ==============================================================================
# Helper Functions for Event Generation
# ==============================================================================


def make_action_event(
    thought: str = "Working...",
    action: Optional[Any] = None,
    tool_name: str = "workspace_file",
) -> ActionEvent:
    """Construct a valid OpenHands SDK ActionEvent."""
    return ActionEvent(
        source="agent",
        thought=[TextContent(text=thought)],
        tool_name=tool_name,
        tool_call_id="call_123",
        tool_call=MessageToolCall(
            id="call_123", name=tool_name, arguments="{}", origin="completion"
        ),
        llm_response_id="resp_123",
        action=action,
    )


def make_observation_event(
    observation: Any,
    tool_name: str = "workspace_file",
    action_id: Optional[str] = None,
) -> ObservationEvent:
    """Construct a valid OpenHands SDK ObservationEvent."""
    return ObservationEvent(
        source="environment",
        tool_name=tool_name,
        tool_call_id="call_123",
        action_id=action_id or "act_123",
        observation=observation,
    )


# ==============================================================================
# 1. ZERO MONKEY PATCHING INTEGRITY (TEST-P10-01)
# ==============================================================================


def test_zero_monkey_patching_integrity():
    """Verify that openhands.sdk and litellm contain zero runtime monkey-patches."""
    import openhands.sdk.agent.utils as agent_utils
    import orchestrator

    # Ensure parse_tool_call_arguments is the clean SDK original
    assert agent_utils.parse_tool_call_arguments.__module__ == "openhands.sdk.agent.utils"

    # Verify sdk_patch apply function emits deprecation warning and does not mutate
    with pytest.deprecated_call():
        from orchestrator.utils.sdk_patch import apply_sdk_patches
        apply_sdk_patches()

    assert agent_utils.parse_tool_call_arguments.__module__ == "openhands.sdk.agent.utils"


# ==============================================================================
# 2. HARDENED FILE TOOL SDK REGISTRATION & SCHEMAS (TEST-P10-02)
# ==============================================================================


def test_hardened_file_tool_sdk_registration_and_schemas(tmp_path: Path):
    """Verify HardenedWorkspaceFileTool conforms to ToolDefinition and exports clean schemas."""
    sandbox = ToolSandboxManager(workspace_root=tmp_path, persona_role="developer")
    tools = HardenedWorkspaceFileTool.create(sandbox_manager=sandbox)

    assert len(tools) == 1
    tool = tools[0]
    assert tool.name == "workspace_file"
    assert tool.action_type == HardenedFileAction
    assert tool.observation_type == HardenedFileObservation

    # Test MCP Schema export
    mcp_schema = tool.to_mcp_tool()
    assert mcp_schema["name"] == "workspace_file"
    assert "inputSchema" in mcp_schema
    assert "properties" in mcp_schema["inputSchema"]
    assert "file_path" in mcp_schema["inputSchema"]["properties"]

    # Test OpenAI Tool Schema export
    openai_tool = tool.to_openai_tool()
    assert openai_tool["type"] == "function"
    assert openai_tool["function"]["name"] == "workspace_file"
    assert "parameters" in openai_tool["function"]

    # Test execution: write
    action_write = HardenedFileAction(
        operation=FileOperationType.WRITE,
        path="src/app.py",
        content="def hello():\n    return 'world'\n",
    )
    obs_write = tool(action_write)
    assert obs_write.success is True
    assert (tmp_path / "src" / "app.py").exists()

    # Test execution: read
    action_read = HardenedFileAction(
        operation=FileOperationType.READ,
        path="src/app.py",
    )
    obs_read = tool(action_read)
    assert obs_read.success is True
    assert "def hello():" in (obs_read.content or "")

    # Test execution: alias resolution (file_path, text)
    action_alias = HardenedFileAction.model_validate({
        "operation": "write",
        "file_path": "src/config.py",
        "text": "DEBUG = True\n",
    })
    assert action_alias.path == "src/config.py"
    assert action_alias.content == "DEBUG = True\n"
    obs_alias = tool(action_alias)
    assert obs_alias.success is True
    assert (tmp_path / "src" / "config.py").exists()

    # Test execution: AST outline
    action_outline = HardenedFileAction(
        operation=FileOperationType.OUTLINE,
        path="src/app.py",
    )
    obs_outline = tool(action_outline)
    assert obs_outline.success is True
    assert "hello" in (obs_outline.outline_summary or obs_outline.content or "")


# ==============================================================================
# 3. HARDENED TERMINAL TOOL SDK REGISTRATION (TEST-P10-03)
# ==============================================================================


def test_hardened_terminal_tool_sdk_registration_and_security(tmp_path: Path):
    """Verify HardenedWorkspaceTerminalTool executes safe commands and blocks violations."""
    sandbox = ToolSandboxManager(workspace_root=tmp_path, persona_role="developer")
    tools = HardenedWorkspaceTerminalTool.create(sandbox_manager=sandbox)

    assert len(tools) == 1
    tool = tools[0]
    assert tool.name == "workspace_terminal"
    assert tool.action_type == HardenedTerminalAction
    assert tool.observation_type == HardenedTerminalObservation

    # MCP Schema
    mcp_schema = tool.to_mcp_tool()
    assert mcp_schema["name"] == "workspace_terminal"
    assert "cmd" in mcp_schema["inputSchema"]["properties"]

    # Safe Command Execution
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\n", encoding="utf-8")

    action_safe = HardenedTerminalAction(
        command="python -c \"print('terminal_success')\""
    )
    obs_safe = tool(action_safe)
    assert obs_safe.exit_code == 0
    assert "terminal_success" in obs_safe.stdout
    assert obs_safe.security_violation is False

    # Command Injection Violation
    action_injected = HardenedTerminalAction(command="pytest tests/ ; rm -rf /")
    obs_injected = tool(action_injected)
    assert obs_injected.exit_code == 126
    assert obs_injected.security_violation is True
    assert "Security policy violation" in obs_injected.stderr or "Execution Denied" in obs_injected.stderr


# ==============================================================================
# 4. SDK TOOL ADAPTER & PERSONA RBAC / CONSTRICTION (TEST-P10-04)
# ==============================================================================


def test_sdk_tool_adapter_persona_rbac_and_constriction(tmp_path: Path):
    """Verify SDKToolAdapter configures persona tools and handles dynamic constrictions."""
    # 1. Standard Developer: has file and terminal tools
    dev_sandbox = ToolSandboxManager(workspace_root=tmp_path, persona_role="developer")
    dev_tools = SDKToolAdapter.create_tools_for_persona(dev_sandbox, "developer")
    tool_names = [t.name for t in dev_tools]
    assert "workspace_file" in tool_names
    assert "workspace_terminal" in tool_names

    # 2. Constricted Role (Terminal Banned)
    constricted_sandbox = ToolSandboxManager(
        workspace_root=tmp_path,
        persona_role="developer",
        banned_tools={"workspace_terminal"},
    )
    c_tools = SDKToolAdapter.create_tools_for_persona(constricted_sandbox, "developer")
    c_tool_names = [t.name for t in c_tools]
    assert "workspace_file" in c_tool_names
    assert "workspace_terminal" not in c_tool_names

    # 3. Tester Role Write Scope RBAC
    tester_sandbox = ToolSandboxManager(
        workspace_root=tmp_path,
        persona_role="tester",
        allowed_write_prefixes=["tests/"],
    )
    tester_tools = SDKToolAdapter.create_tools_for_persona(tester_sandbox, "tester")
    file_tool = next(t for t in tester_tools if t.name == "workspace_file")

    # Tester cannot write to src/
    obs_denied = file_tool(HardenedFileAction(
        operation=FileOperationType.WRITE,
        path="src/malicious.py",
        content="print(1)\n",
    ))
    assert obs_denied.success is False
    assert "RBAC Violation" in (obs_denied.error_message or "")

    # Tester CAN write to tests/
    obs_allowed = file_tool(HardenedFileAction(
        operation=FileOperationType.WRITE,
        path="tests/test_something.py",
        content="def test_ok():\n    assert True\n",
    ))
    assert obs_allowed.success is True
    assert (tmp_path / "tests" / "test_something.py").exists()


# ==============================================================================
# 5. EXIT STATUS CLASSIFIER (TEST-P10-05 TO TEST-P10-09)
# ==============================================================================


@dataclass
class DummyConvState:
    execution_status: ConversationExecutionStatus
    events: List[Any]


@dataclass
class DummyAgent:
    llm: Any = None


@dataclass
class DummyConversation:
    state: DummyConvState
    agent: DummyAgent = field(default_factory=DummyAgent)


def test_exit_status_classifier_natural_completion():
    """Verify natural completion classification on FINISHED status."""
    conv = DummyConversation(
        state=DummyConvState(
            execution_status=ConversationExecutionStatus.FINISHED,
            events=[
                make_action_event(thought="Plan complete."),
            ],
        )
    )
    outcome = ExitStatusClassifier.classify(
        conv=conv,
        role="developer",
        max_turns=15,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=["src/app.py"],
    )
    assert outcome.completed_naturally is True
    assert outcome.exit_reason == AgentExitReason.NATURAL_COMPLETION
    assert outcome.final_thought == "Plan complete."
    assert outcome.mutated_files == ("src/app.py",)


def test_exit_status_classifier_step_limit_error_event():
    """Verify STEP_LIMIT_REACHED is classified when MaxIterationsReached is emitted."""
    conv = DummyConversation(
        state=DummyConvState(
            execution_status=ConversationExecutionStatus.ERROR,
            events=[
                make_action_event(thought="Still working..."),
                ConversationErrorEvent(
                    source="environment",
                    code="MaxIterationsReached",
                    detail="Limit 15 reached",
                ),
            ],
        )
    )
    outcome = ExitStatusClassifier.classify(
        conv=conv,
        role="developer",
        max_turns=15,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
    )
    assert outcome.completed_naturally is False
    assert outcome.exit_reason == AgentExitReason.STEP_LIMIT_REACHED
    assert outcome.iterations_executed == 15
    assert "step limit reached" in (outcome.error_message or "").lower()


def test_exit_status_classifier_token_budget_exhaustion():
    """Verify TOKEN_LIMIT_REACHED is classified when token usage exceeds ceiling."""
    llm_mock = MagicMock()
    llm_mock.metrics.accumulated_token_usage.prompt_tokens = 40_000
    llm_mock.metrics.accumulated_token_usage.completion_tokens = 25_000

    conv = DummyConversation(
        agent=DummyAgent(llm=llm_mock),
        state=DummyConvState(
            execution_status=ConversationExecutionStatus.RUNNING,
            events=[make_action_event(thought="Thinking...")],
        ),
    )
    outcome = ExitStatusClassifier.classify(
        conv=conv,
        role="developer",
        max_turns=20,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
    )
    assert outcome.completed_naturally is False
    assert outcome.exit_reason == AgentExitReason.TOKEN_LIMIT_REACHED
    assert outcome.total_tokens == 65_000


def test_exit_status_classifier_tool_rejection():
    """Verify TOOL_REJECTION is classified when an observation indicates a security violation."""
    obs = HardenedTerminalObservation(
        exit_code=126,
        security_violation=True,
        error_message="Security policy violation: Command injection detected",
    )
    conv = DummyConversation(
        state=DummyConvState(
            execution_status=ConversationExecutionStatus.RUNNING,
            events=[
                make_observation_event(observation=obs, tool_name="workspace_terminal"),
            ],
        )
    )
    outcome = ExitStatusClassifier.classify(
        conv=conv,
        role="developer",
        max_turns=10,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
    )
    assert outcome.completed_naturally is False
    assert outcome.exit_reason == AgentExitReason.TOOL_REJECTION
    assert "Security" in (outcome.error_message or "")


def test_exit_status_classifier_stuck_and_fatal_error():
    """Verify AGENT_STUCK and FATAL_ERROR classifications."""
    # 1. Stuck
    conv_stuck = DummyConversation(
        state=DummyConvState(
            execution_status=ConversationExecutionStatus.STUCK,
            events=[],
        )
    )
    outcome_stuck = ExitStatusClassifier.classify(
        conv=conv_stuck,
        role="developer",
        max_turns=10,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
    )
    assert outcome_stuck.exit_reason == AgentExitReason.AGENT_STUCK

    # 2. Fatal Error
    conv_err = DummyConversation(
        state=DummyConvState(
            execution_status=ConversationExecutionStatus.ERROR,
            events=[
                ConversationErrorEvent(
                    source="environment",
                    code="RateLimitError",
                    detail="OpenAI quota exceeded",
                ),
            ],
        )
    )
    outcome_err = ExitStatusClassifier.classify(
        conv=conv_err,
        role="developer",
        max_turns=10,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
    )
    assert outcome_err.exit_reason == AgentExitReason.FATAL_ERROR
    assert "quota exceeded" in (outcome_err.error_message or "")

    # 3. Direct Execution Exception
    conv_crashed = DummyConversation(
        state=DummyConvState(
            execution_status=None,
            events=[],
        )
    )
    outcome_crash = ExitStatusClassifier.classify(
        conv=conv_crashed,
        role="developer",
        max_turns=10,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
        execution_exception=RuntimeError("SDK Internal Connection Reset"),
    )
    assert outcome_crash.exit_reason == AgentExitReason.FATAL_ERROR
    assert outcome_crash.completed_naturally is False
    assert "SDK Internal Connection Reset" in (outcome_crash.error_message or "")


# ==============================================================================
# 6. SECRET MASKING & TELEMETRY BRIDGE (TEST-P10-10 & TEST-P10-11)
# ==============================================================================


def test_secret_masking_filter_comprehensive():
    """Verify SecretMaskingFilter redacts various credentials and sensitive keys."""
    raw_text = (
        "Using api_key: 'sk-1234567890abcdef1234567890abcdef' and token = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'\n"
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY-----\n"
        "and password: 'super_secret_password'"
    )
    masked = SecretMaskingFilter.mask(raw_text)

    assert "sk-1234567890abcdef1234567890abcdef" not in masked
    assert "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890" not in masked
    assert "MIIEowIBAAKCAQEA0" not in masked
    assert "super_secret_password" not in masked
    assert "[REDACTED_SECRET]" in masked or "[REDACTED_PRIVATE_KEY]" in masked


def test_openhands_telemetry_bridge_synchronous_forwarding(tmp_path: Path):
    """Verify OpenHandsTelemetryBridge synchronously forwards and masks events in SessionLogStore."""
    store = SessionLogStore(workspace_path=tmp_path)
    store.set_agent_context(role="developer", phase="implementation")

    bridge = OpenHandsTelemetryBridge(log_store=store)

    # 1. Action Event with secret and file mutation
    action = HardenedFileAction(
        operation=FileOperationType.WRITE,
        path="src/secret.py",
        content="API_KEY = 'sk-1234567890abcdef1234567890abcdef'\n",
    )
    action_event = make_action_event(
        thought="Writing key sk-1234567890abcdef1234567890abcdef to file",
        action=action,
        tool_name="workspace_file",
    )
    bridge.on_event(action_event)

    assert "src/secret.py" in bridge.mutated_files
    latest_step = store.get_latest_step()
    assert latest_step is not None
    assert latest_step.thought is not None
    assert "sk-1234567890abcdef" not in latest_step.thought
    assert "[REDACTED_SECRET]" in latest_step.thought

    # 2. Observation Event
    obs = HardenedFileObservation(
        success=True,
        operation="write",
        path="src/secret.py",
        content="OK",
    )
    obs_event = make_observation_event(observation=obs, tool_name="workspace_file")
    bridge.on_event(obs_event)

    latest_obs_step = store.get_latest_step()
    assert latest_obs_step is not None
    assert latest_obs_step.action_type == "workspace_file"
    assert latest_obs_step.is_error is False


# ==============================================================================
# 7. SDK AGENT FACTORY & RUNTIME BRIDGE FACADE (TEST-P10-12 & TEST-P10-13)
# ==============================================================================


def test_sdk_agent_factory_configuration(tmp_path: Path):
    """Verify SDKAgentFactory constructs Agent with include_default_tools=[] and tool_concurrency_limit=1."""
    config = OrchestratorConfig()
    llm_manager = MagicMock()
    llm_instance = LLM(model="gpt-4o")
    llm_manager.get_llm.return_value = llm_instance

    sandbox = ToolSandboxManager(workspace_root=tmp_path, persona_role="developer")
    tools = SDKToolAdapter.create_tools_for_persona(sandbox, "developer")

    agent = SDKAgentFactory.create_agent(
        config=config,
        llm_manager=llm_manager,
        role_name="developer",
        system_prompt="You are a developer.",
        tools=tools,
    )

    assert isinstance(agent, Agent)
    assert agent.include_default_tools == []
    assert agent.tool_concurrency_limit == 1
    assert len(agent.tools) == 2


def test_openhands_runtime_bridge_facade_execution(tmp_path: Path):
    """Verify OpenHandsRuntimeBridge facade coordinates tool creation, prompt ingestion, and runner."""
    config = OrchestratorConfig()
    llm_manager = MagicMock()
    llm_instance = LLM(model="gpt-4o")
    llm_manager.get_llm.return_value = llm_instance

    store = SessionLogStore(workspace_path=tmp_path)
    bridge = OpenHandsRuntimeBridge(
        config=config,
        llm_manager=llm_manager,
        log_store=store,
    )

    sandbox = ToolSandboxManager(workspace_root=tmp_path, persona_role="developer")
    prompt_view = PromptView(
        compiled_prompt="Implement calculator feature.",
        tier0_system_prompt="You are an expert developer.",
    )
    turn_envelope = TurnEnvelope(max_turns=10, token_ceiling=30_000)

    mock_outcome = AgentExecutionOutcome(
        role="developer",
        exit_reason=AgentExitReason.NATURAL_COMPLETION,
        completed_naturally=True,
        iterations_executed=3,
        max_iterations_allocated=10,
        prompt_tokens=1500,
        completion_tokens=400,
        total_tokens=1900,
        cost_usd=0.01,
        error_message=None,
        mutated_files=("src/calc.py",),
        final_thought="Feature complete.",
    )

    with patch.object(SDKSessionRunner, "run_turn", return_value=mock_outcome) as mock_run:
        outcome = bridge.execute_bounded_turn(
            role_name="developer",
            workspace_path=tmp_path,
            prompt_view=prompt_view,
            turn_envelope=turn_envelope,
            sandbox_manager=sandbox,
        )

        assert outcome == mock_outcome
        assert mock_run.called
        assert mock_run.call_args[1]["role_name"] == "developer"
        assert mock_run.call_args[1]["workspace_path"] == tmp_path
        assert store.current_model == "gpt-4o"
        assert store.current_llm == llm_instance


def test_migration_routing_flag_active():
    """Verify migration_routing.json has use_clean_sdk_bridge enabled."""
    routing_path = Path(__file__).parent.parent / "orchestrator" / "config" / "migration_routing.json"
    data = json.loads(routing_path.read_text(encoding="utf-8"))
    assert data.get("use_clean_sdk_bridge") is True
    assert data.get("use_hardened_sandbox") is True
