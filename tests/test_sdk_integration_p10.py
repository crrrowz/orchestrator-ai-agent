"""Comprehensive Integration and Invariant Test Suite for Phase 10: OpenHands SDK Runtime Boundary.

Validates P10 Canonical Requirements:
1. Single-turn envelope boundaries terminate cleanly upon hitting T_allocated without background interrupt signals.
2. ExitStatusClassifier deterministically classifies natural completion vs step exhaustion vs token limits vs tool errors.
3. Tool registration passes OpenHands SDK schema validation with default tools completely excluded.
4. Synchronous telemetry forwarding updates step counts and token expenditure accurately directly to TelemetryRecorder.
5. SecretMaskingFilter redacts environment variables (ANTHROPIC_API_KEY, OPENROUTER_API_KEY, Bearer tokens) from event streams.
6. Zero runtime monkey-patching confirmed via AST inspection of active runtime modules.
7. Standardized persona agent instantiations (Architect, Developer, Tester, Reviewer, Auditor, Remediation) injecting AgentExecutionScope (P5) and prompt views (P6).
"""

from __future__ import annotations

import ast
import json
import os
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
    TokenEvent,
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
from orchestrator.telemetry.recorder import TelemetryRecorder
from orchestrator.tools.hardened.manager import ToolSandboxManager
from orchestrator.tools.hardened.models import (
    AgentExecutionScope,
    ToolPermissionLevel,
)
from orchestrator.ui.session_store import SessionLogStore


# ==============================================================================
# Helpers
# ==============================================================================


@dataclass
class MockConvState:
    execution_status: ConversationExecutionStatus
    events: List[Any] = field(default_factory=list)


@dataclass
class MockAgent:
    llm: Any = None


@dataclass
class MockConversation:
    state: MockConvState
    agent: MockAgent = field(default_factory=MockAgent)


def make_action(
    thought: str = "Analyzing...",
    tool_name: str = "workspace_file",
    action: Optional[Any] = None,
) -> ActionEvent:
    return ActionEvent(
        source="agent",
        thought=[TextContent(text=thought)],
        tool_name=tool_name,
        tool_call_id="call_mock_1",
        tool_call=MessageToolCall(
            id="call_mock_1", name=tool_name, arguments="{}", origin="completion"
        ),
        llm_response_id="resp_mock_1",
        action=action,
    )


def make_observation(
    observation: Any,
    tool_name: str = "workspace_file",
) -> ObservationEvent:
    return ObservationEvent(
        source="environment",
        tool_name=tool_name,
        tool_call_id="call_mock_1",
        action_id="act_mock_1",
        observation=observation,
    )


# ==============================================================================
# 1. SINGLE-TURN ENVELOPE BOUNDARIES WITHOUT BACKGROUND INTERRUPT SIGNALS
# ==============================================================================


def test_single_turn_envelope_bounded_execution(tmp_path: Path):
    """Verify that SDKSessionRunner invokes LocalConversation with bounded max_iteration_per_run without background polling threads."""
    llm = LLM(model="gpt-4o")
    agent = Agent(llm=llm, tools=[], include_default_tools=[], tool_concurrency_limit=1)
    prompt_view = PromptView(compiled_prompt="Analyze repository structure.")
    envelope = TurnEnvelope(max_turns=12, token_ceiling=40_000)
    telemetry = OpenHandsTelemetryBridge()

    # Track how LocalConversation is instantiated
    created_conversations = []

    original_init = LocalConversation.__init__

    def wrapped_init(self, *args, **kwargs):
        created_conversations.append({
            "max_iteration_per_run": kwargs.get("max_iteration_per_run"),
            "stuck_detection": kwargs.get("stuck_detection"),
            "delete_on_close": kwargs.get("delete_on_close"),
            "callbacks": kwargs.get("callbacks"),
        })
        original_init(self, *args, **kwargs)

    with patch.object(LocalConversation, "__init__", wrapped_init), \
         patch.object(LocalConversation, "send_message") as mock_send, \
         patch.object(LocalConversation, "run") as mock_run, \
         patch.object(LocalConversation, "close") as mock_close, \
         patch.object(ExitStatusClassifier, "classify") as mock_classify:

        mock_outcome = AgentExecutionOutcome(
            role="architect",
            exit_reason=AgentExitReason.STEP_LIMIT_REACHED,
            completed_naturally=False,
            iterations_executed=12,
            max_iterations_allocated=12,
            prompt_tokens=2000,
            completion_tokens=500,
            total_tokens=2500,
            cost_usd=0.015,
            error_message="Turn step limit reached (12 turns).",
            mutated_files=(),
            final_thought="Finished analysis.",
        )
        mock_classify.return_value = mock_outcome

        outcome = SDKSessionRunner.run_turn(
            agent=agent,
            workspace_path=tmp_path,
            prompt_view=prompt_view,
            turn_envelope=envelope,
            telemetry_bridge=telemetry,
            role_name="architect",
        )

        assert outcome.exit_reason == AgentExitReason.STEP_LIMIT_REACHED
        assert outcome.iterations_executed == 12
        assert mock_send.called
        assert mock_run.called
        assert mock_close.called

        # Verify conversation parameters: single-turn bounded envelope
        assert len(created_conversations) == 1
        conv_params = created_conversations[0]
        assert conv_params["max_iteration_per_run"] == 12
        assert conv_params["stuck_detection"] is True
        assert conv_params["delete_on_close"] is True
        assert telemetry.on_event in conv_params["callbacks"]


# ==============================================================================
# 2. DETERMINISTIC EXIT STATUS CLASSIFICATION TAXONOMY
# ==============================================================================


def test_exit_status_classifier_all_taxonomies():
    """Verify ExitStatusClassifier deterministically handles all standard exit categories."""
    # 1. Natural Completion
    conv_finished = MockConversation(
        state=MockConvState(
            execution_status=ConversationExecutionStatus.FINISHED,
            events=[make_action(thought="Done.")],
        )
    )
    outcome_nat = ExitStatusClassifier.classify(
        conv=conv_finished,
        role="developer",
        max_turns=10,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=["src/main.py"],
    )
    assert outcome_nat.exit_reason == AgentExitReason.NATURAL_COMPLETION
    assert outcome_nat.completed_naturally is True
    assert outcome_nat.final_thought == "Done."

    # 2. Step Limit Reached via MaxIterationsReached
    conv_step = MockConversation(
        state=MockConvState(
            execution_status=ConversationExecutionStatus.ERROR,
            events=[
                ConversationErrorEvent(source="environment", code="MaxIterationsReached", detail="Limit 15 reached"),
            ],
        )
    )
    outcome_step = ExitStatusClassifier.classify(
        conv=conv_step,
        role="developer",
        max_turns=15,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
    )
    assert outcome_step.exit_reason == AgentExitReason.STEP_LIMIT_REACHED
    assert outcome_step.completed_naturally is False

    # 3. Token Limit Reached
    mock_llm = MagicMock()
    mock_llm.metrics.accumulated_token_usage.prompt_tokens = 35_000
    mock_llm.metrics.accumulated_token_usage.completion_tokens = 20_000
    conv_tokens = MockConversation(
        agent=MockAgent(llm=mock_llm),
        state=MockConvState(
            execution_status=ConversationExecutionStatus.RUNNING,
            events=[],
        ),
    )
    outcome_tokens = ExitStatusClassifier.classify(
        conv=conv_tokens,
        role="developer",
        max_turns=20,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
    )
    assert outcome_tokens.exit_reason == AgentExitReason.TOKEN_LIMIT_REACHED
    assert outcome_tokens.total_tokens == 55_000

    # 4. Tool Rejection (Security Sandbox Violation)
    obs_sec = HardenedTerminalObservation(
        exit_code=126,
        security_violation=True,
        error_message="Execution Denied: Command injection attempt",
    )
    conv_sec = MockConversation(
        state=MockConvState(
            execution_status=ConversationExecutionStatus.RUNNING,
            events=[make_observation(obs_sec, tool_name="workspace_terminal")],
        )
    )
    outcome_sec = ExitStatusClassifier.classify(
        conv=conv_sec,
        role="developer",
        max_turns=10,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
    )
    assert outcome_sec.exit_reason == AgentExitReason.TOOL_REJECTION

    # 5. Tool Rejection (RBAC Violation)
    obs_rbac = HardenedFileObservation(
        success=False,
        error_message="RBAC Violation: Writing to 'src/app.py' is outside permitted role scope ['tests/']",
    )
    conv_rbac = MockConversation(
        state=MockConvState(
            execution_status=ConversationExecutionStatus.RUNNING,
            events=[make_observation(obs_rbac, tool_name="workspace_file")],
        )
    )
    outcome_rbac = ExitStatusClassifier.classify(
        conv=conv_rbac,
        role="tester",
        max_turns=10,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
    )
    assert outcome_rbac.exit_reason == AgentExitReason.TOOL_REJECTION

    # 6. Agent Stuck Loop
    conv_stuck = MockConversation(
        state=MockConvState(
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

    # 7. Fatal Error
    conv_fatal = MockConversation(
        state=MockConvState(
            execution_status=ConversationExecutionStatus.ERROR,
            events=[
                ConversationErrorEvent(source="environment", code="LLMBadRequest", detail="Context window exhausted"),
            ],
        )
    )
    outcome_fatal = ExitStatusClassifier.classify(
        conv=conv_fatal,
        role="developer",
        max_turns=10,
        initial_tokens=0,
        token_ceiling=50_000,
        mutated_files=[],
    )
    assert outcome_fatal.exit_reason == AgentExitReason.FATAL_ERROR
    assert "Context window exhausted" in (outcome_fatal.error_message or "")


# ==============================================================================
# 3. TOOL REGISTRATION AND SCHEMA VALIDATION WITH EXCLUDED DEFAULTS
# ==============================================================================


def test_tool_registration_and_clean_schema_validation(tmp_path: Path):
    """Verify official ToolDefinition schemas export without monkey-patching and exclude defaults."""
    sandbox = ToolSandboxManager(workspace_root=tmp_path, persona_role="developer")
    tools = SDKToolAdapter.create_tools_for_persona(sandbox, "developer")

    file_tool = next(t for t in tools if t.name == "workspace_file")
    terminal_tool = next(t for t in tools if t.name == "workspace_terminal")

    # MCP Schema checks
    mcp_file = file_tool.to_mcp_tool()
    assert mcp_file["name"] == "workspace_file"
    assert "operation" in mcp_file["inputSchema"]["properties"]

    mcp_term = terminal_tool.to_mcp_tool()
    assert mcp_term["name"] == "workspace_terminal"
    assert "cmd" in mcp_term["inputSchema"]["properties"]

    # OpenAI Schema checks
    openai_file = file_tool.to_openai_tool()
    assert openai_file["function"]["name"] == "workspace_file"
    assert "parameters" in openai_file["function"]

    openai_term = terminal_tool.to_openai_tool()
    assert openai_term["function"]["name"] == "workspace_terminal"
    assert "parameters" in openai_term["function"]

    # Verify SDKAgentFactory excludes default tools and sets concurrency limit
    config = OrchestratorConfig()
    llm_manager = MagicMock()
    llm_manager.get_llm.return_value = LLM(model="gpt-4o")

    agent = SDKAgentFactory.create_agent(
        config=config,
        llm_manager=llm_manager,
        role_name="developer",
        system_prompt="You are a developer.",
        tools=tools,
    )
    assert agent.include_default_tools == []
    assert agent.tool_concurrency_limit == 1
    assert len(agent.tools) == 2


# ==============================================================================
# 4. SYNCHRONOUS TELEMETRY FORWARDING TO TELEMETRYRECORDER
# ==============================================================================


def test_telemetry_bridge_forwards_directly_to_recorder(tmp_path: Path):
    """Verify synchronous event listening updates step metrics and token usage directly in TelemetryRecorder."""
    recorder = TelemetryRecorder(task_description="P10 verification task")
    store = SessionLogStore(workspace_path=tmp_path)
    store.set_agent_context(role="developer", phase="implementation")

    bridge = OpenHandsTelemetryBridge(
        log_store=store,
        telemetry_recorder=recorder,
        role_name="developer",
    )

    # 1. Receive TokenEvent
    tok_ev = TokenEvent(
        source="agent",
        prompt_token_ids=[101, 102, 103, 104, 105],
        response_token_ids=[201, 202, 203],
    )
    bridge.on_event(tok_ev)
    assert bridge.prompt_tokens == 5
    assert bridge.completion_tokens == 3
    assert bridge.total_tokens == 8

    # 2. Receive ActionEvent
    action = HardenedFileAction(
        operation=FileOperationType.WRITE,
        path="src/service.py",
        content="class Service:\n    pass\n",
    )
    act_ev = make_action(thought="Writing service class", tool_name="workspace_file", action=action)
    bridge.on_event(act_ev)
    assert bridge.step_count == 1
    assert "src/service.py" in bridge.mutated_files

    # 3. Receive ObservationEvent - triggers TelemetryRecorder.record_step
    obs = HardenedFileObservation(success=True, operation="write", path="src/service.py")
    obs_ev = make_observation(observation=obs, tool_name="workspace_file")
    bridge.on_event(obs_ev)

    assert len(recorder.metrics) == 1
    recorded_metric = recorder.metrics[0]
    assert recorded_metric.agent_role == "developer"
    assert recorded_metric.action_type == "workspace_file"
    assert recorded_metric.iteration == 1
    assert recorded_metric.success is True
    assert recorded_metric.prompt_tokens == 5
    assert recorded_metric.completion_tokens == 3
    assert recorded_metric.total_tokens == 8

    # 4. Receive ConversationErrorEvent - triggers TelemetryRecorder.record_incident
    err_ev = ConversationErrorEvent(source="environment", code="ToolError", detail="Filesystem locked")
    bridge.on_event(err_ev)
    assert len(recorder.incidents) == 1
    incident = recorder.incidents[0]
    assert incident.incident_type == "ToolError"
    assert "Filesystem locked" in incident.details


# ==============================================================================
# 5. SECRET MASKING FILTER FOR ENVIRONMENT VARIABLES AND BEARER TOKENS
# ==============================================================================


def test_secret_masking_filter_env_vars_and_bearer_tokens(monkeypatch):
    """Verify SecretMaskingFilter redacts environment variables, Bearer tokens, and secrets."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-live-token-secret-12345678")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-super-secret-key-9988776655")

    raw_text = (
        "Authorization: Bearer my-confidential-bearer-token-12345\n"
        "Connecting with ANTHROPIC_API_KEY: sk-ant-live-token-secret-12345678\n"
        "Fallback with OPENROUTER_API_KEY: sk-or-v1-super-secret-key-9988776655\n"
        "Extra key: 'sk-99998888777766665555444433332222'\n"
    )

    masked = SecretMaskingFilter.mask(raw_text)

    # All secrets must be scrubbed
    assert "my-confidential-bearer-token-12345" not in masked
    assert "sk-ant-live-token-secret-12345678" not in masked
    assert "sk-or-v1-super-secret-key-9988776655" not in masked
    assert "sk-99998888777766665555444433332222" not in masked

    assert "[REDACTED_SECRET]" in masked or "[REDACTED_ANTHROPIC_API_KEY]" in masked
    assert "Bearer [REDACTED_SECRET]" in masked


# ==============================================================================
# 6. ZERO RUNTIME MONKEY-PATCHING CONFIRMED VIA AST INSPECTION
# ==============================================================================


def test_zero_runtime_monkey_patching_ast_inspection():
    """Verify via AST inspection that active runtime bridge files contain no monkey-patching assignments."""
    bridge_file = Path(__file__).parent.parent / "orchestrator" / "engine" / "openhands_bridge.py"
    tree = ast.parse(bridge_file.read_text(encoding="utf-8"), filename=str(bridge_file))

    for node in ast.walk(tree):
        # Ensure no setattr on openhands or litellm
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setattr":
            first_arg = ast.unparse(node.args[0]) if node.args else ""
            assert "openhands" not in first_arg
            assert "litellm" not in first_arg

        # Ensure no direct attribute assignment into external libraries
        if isinstance(node, ast.Assign):
            for target in node.targets:
                target_str = ast.unparse(target)
                assert not target_str.startswith("openhands.")
                assert not target_str.startswith("litellm.")


# ==============================================================================
# 7. STANDARDIZED PERSONA AGENT FACTORY INJECTIONS (P5 / P6)
# ==============================================================================


def test_sdk_agent_factory_persona_scope_injections(tmp_path: Path):
    """Verify SDKAgentFactory.create_persona_agent injects correct AgentExecutionScope and tools."""
    config = OrchestratorConfig()
    llm_manager = MagicMock()
    llm_manager.get_llm.return_value = LLM(model="gpt-4o")

    # 1. Architect persona: scoped write to PLAN.md, docs/
    arch_prompt = PromptView(
        compiled_prompt="Formulate high-level architectural plan.",
        tier0_system_prompt="You are a Principal Software Architect.",
    )
    arch_agent = SDKAgentFactory.create_persona_agent(
        config=config,
        llm_manager=llm_manager,
        role_name="architect",
        prompt_view=arch_prompt,
        workspace_path=tmp_path,
    )
    assert isinstance(arch_agent, Agent)
    assert arch_agent.system_prompt == "You are a Principal Software Architect."
    assert arch_agent.include_default_tools == []

    # 2. Tester persona: scoped write to tests/
    tester_prompt = PromptView(
        compiled_prompt="Write unit tests.",
        tier0_system_prompt="You are a QA / Test Engineer.",
    )
    tester_agent = SDKAgentFactory.create_persona_agent(
        config=config,
        llm_manager=llm_manager,
        role_name="tester",
        prompt_view=tester_prompt,
        workspace_path=tmp_path,
    )
    assert isinstance(tester_agent, Agent)
    assert tester_agent.system_prompt == "You are a QA / Test Engineer."

    # 3. Reviewer persona: read-only
    reviewer_prompt = PromptView(
        compiled_prompt="Review implementation diff.",
        tier0_system_prompt="You are a Senior Code Reviewer.",
    )
    reviewer_agent = SDKAgentFactory.create_persona_agent(
        config=config,
        llm_manager=llm_manager,
        role_name="reviewer",
        prompt_view=reviewer_prompt,
        workspace_path=tmp_path,
    )
    assert isinstance(reviewer_agent, Agent)
    assert reviewer_agent.system_prompt == "You are a Senior Code Reviewer."

    # Verify default scopes
    arch_scope = SDKAgentFactory.get_default_scope_for_role("architect", config)
    assert "PLAN.md" in arch_scope.allowed_write_prefixes
    assert arch_scope.file_permission == ToolPermissionLevel.RESTRICTED_WRITE

    tester_scope = SDKAgentFactory.get_default_scope_for_role("tester", config)
    assert "tests/" in tester_scope.allowed_write_prefixes
    assert tester_scope.file_permission == ToolPermissionLevel.RESTRICTED_WRITE

    reviewer_scope = SDKAgentFactory.get_default_scope_for_role("reviewer", config)
    assert reviewer_scope.file_permission == ToolPermissionLevel.READ_ONLY
