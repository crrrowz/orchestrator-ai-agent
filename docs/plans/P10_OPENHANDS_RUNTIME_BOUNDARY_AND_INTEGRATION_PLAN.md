# P10 — OPENHANDS RUNTIME BOUNDARY & INTEGRATION PLAN

> **Document Type:** Canonical Systems Architecture, SDK Runtime Boundary & Execution Seam Specification  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Systems Architect, AI Agent Runtime Specialist & OpenHands SDK Integration Engineer  
> **Baseline References:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md` through `docs/plans/P9_TOOLING_CONTEXT_WINDOWS_AND_SANDBOX_HARDENING_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Tests)  
> **Design Phase:** P10 (Specification & SDK Runtime Seam — Zero Production Code Modified)

---

# 1. Executive Summary & Legacy SDK Integration Audit

This specification establishes the canonical **OpenHands Runtime Boundary & Integration Plan (P10)** for the **ORAGAI** multi-agent software engineering orchestrator.

### 1.1 The Strategic Position of P10 in the ORAGAI Stack
To date, the architectural redesign of ORAGAI has established:
1. **P0 (Forensic Baseline & Invariants):** Proved the foundational division: ORAGAI owns Governance, Quality Gates, and State, while OpenHands SDK owns the single-agent ReAct execution turn loop. Dissected the violent 28% `conv.interrupt()` thread kill, step ceiling masking (`ConvRunResult.completed = True`), and `sdk_patch.py` monkey-patching fragility.
2. **P1 (Task Truth & Requirement Model):** Formulated deterministic requirement states, entity graphs, and task completion preconditions.
3. **P2.1 (Evidence Engine & Completion Gates):** Enforced read-only `TaskTruthSemanticQueries`, cryptographic content hashing, and non-agent self-certification.
4. **P3 (Guarded FSM & Lifecycle Orchestration):** Established Inversion of Control (IoC): OpenHands sessions are bounded, ephemeral workers yielding control via `AGENT_YIELDED` events to the Guarded FSM.
5. **P4 (Adaptive Resource Governance):** Implemented dynamic turn envelopes ($T_{\text{allocated}}$), context folding, and monetary circuit breakers.
6. **P5 (Agent Work & Milestone Execution):** Established persona RBAC boundaries, Micro-TDD loops, and `CrossAgentHandoffPayload` schemas.
7. **P6 (Context & Evidence Handoff):** Formulated priority context tiers (Tier 0 to Tier 3), Merkle workspace digests, and cryptographic handoff envelopes.
8. **P7 (Audit, Deep Inspection & Self-Evolution):** Established zero-token pre-audit sweeps, finding DAGs, Codebase Health Index ($\text{CHI}$), and SQLite WAL logging.
9. **P8 (Progress, Stagnation & Recovery):** Implemented Tier 3 Tool Constriction mutations, sliding-window oscillation analysis, and 4-tier circuit breaking.
10. **P9 (Tooling, Context Windows & Sandbox Hardening):** Built `ToolSandboxManager`, AST file virtualization, and grammar-based terminal security.

### The Core Mission of P10:
$$\text{While P9 hardens the tools and P3 governs the lifecycle,}$$
$$\text{\textbf{P10 formalizes the exact architectural seam between ORAGAI and openhands-sdk v1.49.4,}}$$
$$\text{\textbf{eliminating brittle monkey-patches (sdk\_patch.py), mapping P9 tools cleanly into official SDK protocols,}}$$
$$\text{\textbf{and binding the SDK EventStream to ORAGAI telemetry and FSM yield signals without asynchronous thread collisions.}}$$

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         ORAGAI CONTROL PLANE & SDK BOUNDARY (P10)                                      │
│                                                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                            Guarded FSM Engine (P3)                                             │   │
│   │                     [DISCOVERY ──▶ ARCHITECTURE ──▶ IMPLEMENTATION ──▶ TESTING ──▶ REVIEW ──▶ AUDIT]           │   │
│   └───────────────────────────────────────────────────────┬────────────────────────────────────────────────────────┘   │
│                                                           │ Dispatches Bounded Turn Envelope (T_allocated)             │
│                                                           ▼                                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                       OpenHandsRuntimeBridge (P10 Facade)                                      │   │
│   │                                                                                                                │   │
│   │   ┌──────────────────────────────┐  ┌──────────────────────────────┐  ┌────────────────────────────────────┐   │   │
│   │   │       SDKAgentFactory        │  │        SDKToolAdapter        │  │          SDKSessionRunner          │   │   │
│   │   │  • Persona LLM & System Prom │  │  • HardenedFileTool (P9)     │  │  • Ephemeral LocalConversation │   │   │
│   │   │  • Tool Filtering & Binding  │  │  • HardenedTerminalTool (P9) │  │  • Synchronous conv.run()      │   │   │
│   │   │  • P6 Tiered Prompt Ingest   │  │  • P5/P8 Sandbox Injection   │  │  • ExitStatusClassifier        │   │   │
│   │   └──────────────────────────────┘  └──────────────────────────────┘  └────────────────────────────────────┘   │   │
│   └───────────────────────┬───────────────────────────────┬──────────────────────────────────┬─────────────────────┘   │
│                           │ Instantiates                  │ Registers                        │ Synchronous EventStream │
│                           ▼                               ▼                                  ▼ Callback                │
│   ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                        OpenHands SDK v1.49.4 Runtime                                           │   │
│   │                                                                                                                │   │
│   │   ┌──────────────────────────────┐  ┌──────────────────────────────┐  ┌────────────────────────────────────┐   │   │
│   │   │     openhands.sdk.Agent      │  │ openhands.sdk.ToolDefinition │  │ openhands.sdk.LocalConversation    │   │   │
│   │   │  • LLM ReAct Loop            │  │  • ToolExecutor Protocol     │  │  • Bounded max_iteration_per_run │   │   │
│   │   │  • Native Tool Call Parsing  │  │  • Strict Pydantic Schemas   │  │  • Action/Observation Lifecycle │   │   │
│   │   └──────────────────────────────┘  └──────────────────────────────┘  └────────────────────────────────────┘   │   │
│   └──────────────────────────────────────────────────────────────────────────────────────────┬─────────────────────┘   │
│                                                                                              │ Synchronous Events      │
│                                                                                              ▼                         │
│   ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                  EventStream Telemetry & UI Pipeline (P10)                                     │   │
│   │                                                                                                                │   │
│   │   • Secret Masking Filter (P9) ──▶ SessionLogStore ──▶ OrchestratorLiveVisualizer ──▶ SentinelDiagnosticsDB    │   │
│   └────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1.2 Forensic Dissection of Legacy SDK Integration Pathologies

The legacy implementation in `orchestrator/pipeline/base_pipeline.py` and `orchestrator/utils/sdk_patch.py` contains severe architectural antipatterns that undermine system stability, corrupt execution states, and mask failures.

### Pathology 1: The Asynchronous Polling Thread & Violent `conv.interrupt()` Race Hazard
In `orchestrator/pipeline/base_pipeline.py:L249-352`, legacy ORAGAI spawns a separate background daemon thread to enforce timeouts and token limits:

```python
# Legacy Antipattern in base_pipeline.py
stop_monitor = threading.Event()
def monitor():
    while not stop_monitor.is_set():
        # Polling token usage every 1.0 second
        if delta_tok >= governor.allocation.investigation_budget:
            conv.interrupt() # <--- VIOLENT THREAD INTERRUPT
            break
        stop_monitor.wait(1.0)

monitor_thread = threading.Thread(target=monitor, daemon=True)
monitor_thread.start()
try:
    conv.run() # Running on main thread
finally:
    stop_monitor.set()
```

#### Why This Is Fatal:
1. **Thread Race on Internal State Lock:** OpenHands SDK's `LocalConversation` manages an internal state lock (`with self._state:`). When a background thread calls `conv.interrupt()` while `self.agent.step()` is actively in progress, `conv.interrupt()` forcefully mutates `self._state.execution_status = ConversationExecutionStatus.PAUSED` or attempts cancellation while LiteLLM is streaming chunks.
2. **Corrupted Tool Execution & Orphaned Subprocesses:** If `conv.interrupt()` fires while a terminal subprocess or file write is executing, the subprocess becomes orphaned or a file write is sliced mid-stream, leaving zero-byte or corrupt files in the working directory.
3. **The 28% Exploration Starvation:** The monitor thread computed token delta and violently killed any agent reading files without immediately writing code after consuming 28% of tokens, aborting legitimate architecture audits and test explorations.

### Pathology 2: Step Ceiling Masking (`ConvRunResult.completed = True`)
In `orchestrator/pipeline/base_pipeline.py:L56, L209, L353-370`:
- `ConvRunResult.completed` was initialized to `True`.
- When `conv.run()` terminated because OpenHands reached `max_iteration_per_run`, the SDK set `ConversationExecutionStatus.ERROR` or emitted a `ConversationErrorEvent(code="MaxIterationsReached")`.
- However, legacy ORAGAI checked `state.execution_status` with loose string equality, and if no fatal unhandled Python exception was raised, the method returned `run_result` with `completed=True`.
- Downstream pipelines interpreted step exhaustion as successful completion, advancing to subsequent phases with unwritten code and failing tests.

### Pathology 3: Runtime Monkey-Patching Fragility (`sdk_patch.py`)
In `orchestrator/utils/sdk_patch.py:L1-172`, ORAGAI monkey-patched internal modules:
1. Replaced `openhands.sdk.agent.utils.parse_tool_call_arguments` with `resilient_parse_tool_call_arguments`.
2. Patched `openhands.sdk.llm.utils.telemetry.Telemetry._cache_buckets`.
3. Patched `litellm.types.utils.PromptTokensDetailsWrapper.__getattr__`.

#### Why Monkey-Patching Is Unacceptable:
- **Version Lock-in & Silent Breakage:** Any internal refactoring in `openhands.sdk` (e.g., migrating from `agent.utils` to Pydantic-based schema parsing) silently breaks or bypasses the monkey-patch.
- **Hidden Control Flow:** Monkey-patching mutates global Python module namespaces, causing subtle cross-test pollution and unpredictable debugging behavior.
- **Architectural Smuggling:** Instead of defining strict Pydantic models for tools that validate their own arguments cleanly, monkey-patching attempted to paper over malformed JSON using greedy regex heuristics.

---

## 1.3 Architectural Seam Formulation: Control Plane vs Execution Runtime

P10 establishes a strict, formal boundary between the ORAGAI Control Plane and the OpenHands Execution Runtime.

| Dimension | ORAGAI Control Plane (Master) | OpenHands SDK Runtime (Worker) |
| :--- | :--- | :--- |
| **Architectural Role** | Governance, Quality Gates, Lifecycle FSM, Task Truth, Security Invariants. | Single-Agent ReAct Turn Loop, LLM Client Interaction, Tool Invocation. |
| **State Ownership** | `TaskTruthGraph`, `GuardedFSMEngine`, `MilestoneDAG`, `SessionLogStore`. | Ephemeral `ConversationState`, in-memory message history for active turn. |
| **Turn Budgeting** | Computes dynamic $T_{\text{allocated}} \in [10, 30]$ via P4 `AdaptiveBudgetAllocator`. | Executes exactly up to `max_iteration_per_run = T_allocated`. |
| **Tool Execution** | Hardened sandboxing, AST virtualization, grammar security, RBAC scopes (P9). | Standard `ToolDefinition[ActionT, ObservationT]` dispatch. |
| **Completion Evaluation** | Evaluates 14-step Completion Gate (P2.1) & Micro-TDD verification (P5). | Emits `FinishAction` or reaches `max_iteration_per_run`. |
| **Telemetry Ingestion** | Secret masking, live Rich visualizer, SQLite WAL diagnostics. | Fires synchronous `callbacks(Event)` on event emission. |

$$\text{Boundary Rule: The OpenHands SDK is NEVER allowed to determine task completion or lifecycle transitions.}$$
$$\text{OpenHands only yields execution status; ORAGAI evaluates semantic truth.}$$

---

# 2. Clean OpenHands SDK v1.49.4 Extension Architecture

P10 eliminates all monkey-patches in `orchestrator/utils/sdk_patch.py` and establishes clean integration using only the official, public extension points of `openhands-sdk v1.49.4`.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        OFFICIAL OPENHANDS SDK v1.49.4 EXTENSION POINTS                 │
│                                                                                        │
│   1. Agent Specification:                                                              │
│      openhands.sdk.Agent(                                                              │
│          llm=llm_instance,                                                             │
│          tools=[HardenedWorkspaceFileTool, HardenedWorkspaceTerminalTool],             │
│          system_prompt=synthesized_tier0_prompt,                                       │
│          include_default_tools=False,  # Disables unhardened builtins                  │
│          tool_concurrency_limit=1,     # Enforces deterministic sequential execution   │
│      )                                                                                 │
│                                                                                        │
│   2. Conversation Lifecycle:                                                           │
│      openhands.sdk.conversation.Conversation(                                          │
│          agent=agent_instance,                                                         │
│          workspace=Path(workspace_dir),                                                │
│          max_iteration_per_run=T_allocated,  # Enforces P4 turn envelope natively          │
│          stuck_detection=True,               # SDK native loop detection               │
│          callbacks=[telemetry_bridge.on_event],  # Synchronous EventStream telemetry   │
│          delete_on_close=True,               # Clean ephemeral teardown                │
│          visualizer=None,                    # Disables default visualizer (uses P10)  │
│      )                                                                                 │
│                                                                                        │
│   3. Tool Definition & Execution:                                                      │
│      class HardenedWorkspaceFileTool(ToolDefinition[FileAction, FileObservation]):     │
│          @classmethod                                                                  │
│          def create(cls, conv_state=None, **params) -> Sequence[Self]:                 │
│              return [cls(..., executor=HardenedFileExecutor(sandbox_mgr))]             │
│                                                                                        │
│   4. Event Stream Interception:                                                        │
│      def on_event(event: openhands.sdk.event.Event) -> None:                           │
│          # Synchronous, non-blocking telemetry and secret masking                      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2.1 Official Protocol Bindings

### 1. `openhands.sdk.agent.Agent` Binding
The `openhands.sdk.Agent` class is configured per persona without monkey-patching:
- **`llm`**: Managed instance from `LLMManager` configured with role-specific model, temperature, and fallback strategies.
- **`tools`**: Explicit list of `ToolDefinition` instances (P9 hardened tools). `include_default_tools` is set to `False` to prevent unhardened SDK default tools from leaking into the runtime.
- **`system_prompt`**: Synthesized Tier 0/Tier 1 prompt injected from P6 `ContextSynthesizer`.
- **`tool_concurrency_limit`**: Set to `1` to guarantee deterministic, sequential tool execution on Windows NT without filesystem concurrency races.

### 2. `openhands.sdk.conversation.Conversation` Lifecycle Binding
The conversation is managed as an ephemeral, single-turn execution unit:
- **`max_iteration_per_run`**: Set directly to $T_{\text{allocated}}$ calculated by P4 `AdaptiveBudgetAllocator`. This replaces external polling threads with the SDK's native turn counter.
- **`stuck_detection`**: Enabled to utilize SDK cycle detection.
- **`callbacks`**: Registered with `OpenHandsTelemetryBridge.on_event` to receive every `ActionEvent`, `ObservationEvent`, `AgentErrorEvent`, and `ConversationErrorEvent` synchronously as it is emitted.
- **`delete_on_close`**: Set to `True` to ensure ephemeral session resources are reclaimed immediately upon turn yield.

### 2.2 Deprecation & Elimination Strategy for `sdk_patch.py`

`orchestrator/utils/sdk_patch.py` and its invocation in `orchestrator/__init__.py` are deprecated and replaced by P10's native architecture:

```
[ Legacy Antipattern ]                       [ P10 Native Replacement ]
apply_sdk_patches()                    ───▶  REMOVED (Zero monkey patching)
resilient_parse_tool_call_arguments    ───▶  Pydantic v2 Action Model validation in ToolDefinition
patch_openhands_telemetry()            ───▶  Native LLMUsageTracker in ORAGAI LLMManager
PromptTokensDetailsWrapper patch       ───▶  Standard getattr(..., None) guards in TokenGovernor
```

#### Native Argument Parsing Resilience:
In `openhands-sdk v1.49.4`, `ToolDefinition` automatically parses JSON tool call arguments using `action_from_arguments()`:
1. The SDK calls `self.action_type.model_validate(action_arguments)`.
2. P9's `HardenedWorkspaceFileAction` and `HardenedWorkspaceTerminalAction` use Pydantic v2 `model_config = ConfigDict(extra="ignore", populate_by_name=True)`.
3. Field aliases (e.g. `path` aliased to `file_path`, `cmd` aliased to `command`) and pre-validators handle unescaped control characters and alias resolution natively within the Pydantic schema lifecycle, eliminating the need to monkey-patch `openhands.sdk.agent.utils`.

---

# 3. Hardened Tool Integration (P9 $\to$ OpenHands SDK Bridge)

P10 wraps P9's `WorkspaceFileVirtualizer` and `TerminalSandboxEngine` into official `openhands.sdk.tool.ToolDefinition` and `ToolExecutor` subclasses.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        P9 TOOL TO OPENHANDS SDK ADAPTER BRIDGE                         │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                          openhands.sdk.ToolDefinition                          │   │
│   └───────────────────────┬────────────────────────────────┬───────────────────────┘   │
│                           │ Subclasses                     │ Subclasses                │
│                           ▼                                ▼                           │
│   ┌───────────────────────────────────┐  ┌─────────────────────────────────────────┐   │
│   │     HardenedWorkspaceFileTool     │  │     HardenedWorkspaceTerminalTool       │   │
│   │                                   │  │                                         │   │
│   │   • Action: HardenedFileAction    │  │   • Action: HardenedTerminalAction      │   │
│   │   • Obs: HardenedFileObservation  │  │   • Obs: HardenedTerminalObservation    │   │
│   │   • Executor: HardenedFileExecutor│  │   • Executor: HardenedTerminalExecutor  │   │
│   └─────────────────┬─────────────────┘  └────────────────────┬────────────────────┘   │
│                     │ Invokes                                 │ Invokes                │
│                     ▼                                         ▼                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                          ToolSandboxManager (P9 Core)                          │   │
│   │                                                                                │   │
│   │   • Persona RBAC Write Verification (allowed_write_prefixes)                   │   │
│   │   • Dynamic Tool Constriction Enforcement (P8 denylists)                       │   │
│   │   • WorkspaceFileVirtualizer (AST Outline, Symbol Read, Windowing, Safe Write) │   │
│   │   • TerminalSandboxEngine (Grammar Tokenizer, UTF-8 Streams, Windows Pipes)    │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3.1 Hardened Workspace File Tool Protocol

The `HardenedWorkspaceFileTool` implements `ToolDefinition[HardenedFileAction, HardenedFileObservation]` and binds to `WorkspaceFileVirtualizer`.

```python
class FileOperationType(str, Enum):
    READ = "read"
    WRITE = "write"
    PATCH = "patch"
    SYMBOL = "symbol"
    OUTLINE = "outline"
    LIST = "list"
    DELETE = "delete"

class HardenedFileAction(Action):
    """Pydantic v2 action schema with native alias resolution."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    
    operation: FileOperationType = Field(
        default=FileOperationType.READ,
        description="The file operation to execute: 'read', 'write', 'patch', 'symbol', 'outline', 'list', 'delete'."
    )
    path: str = Field(
        ...,
        alias="file_path",
        description="Workspace-relative path to the target file or directory."
    )
    content: Optional[str] = Field(
        default=None,
        alias="text",
        description="File content for 'write' operation."
    )
    patch_find: Optional[str] = Field(
        default=None,
        description="Target substring or lines to match for 'patch' operation."
    )
    patch_replace: Optional[str] = Field(
        default=None,
        description="Replacement content for 'patch' operation."
    )
    symbol_name: Optional[str] = Field(
        default=None,
        alias="symbol",
        description="Name of function, class, or method for 'symbol' extraction."
    )
    offset_line: int = Field(
        default=1,
        ge=1,
        description="1-based starting line number for bounded window 'read'."
    )
    limit_lines: int = Field(
        default=250,
        ge=1,
        le=1000,
        description="Maximum number of lines to return in 'read' window."
    )

class HardenedFileObservation(Observation):
    """Sanitized, structured observation for file operations."""
    success: bool = True
    operation: str = "read"
    path: str = ""
    content: Optional[str] = None
    total_lines: int = 0
    returned_lines: int = 0
    has_more: bool = False
    ast_valid: bool = True
    error_message: Optional[str] = None
```

---

## 3.2 Hardened Workspace Terminal Tool Protocol

The `HardenedWorkspaceTerminalTool` implements `ToolDefinition[HardenedTerminalAction, HardenedTerminalObservation]` and binds to `TerminalSandboxEngine`.

```python
class HardenedTerminalAction(Action):
    """Pydantic v2 action schema for terminal commands."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    
    command: str = Field(
        ...,
        alias="cmd",
        description="The CLI command to execute within the workspace sandbox."
    )
    timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=600,
        description="Execution timeout in seconds."
    )

class HardenedTerminalObservation(Observation):
    """Sanitized, secret-masked observation for terminal executions."""
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    security_violation: bool = False
    error_message: Optional[str] = None
```

---

## 3.3 Dynamic Executor Binding & Tool Constriction

When `OpenHandsRuntimeBridge` creates tools for an agent turn, it injects the active `ToolSandboxManager` pre-configured with:
1. **Persona RBAC Scopes (P5):** `allowed_write_prefixes` and `blocked_write_prefixes` matching the role (e.g. Tester restricted to `tests/`).
2. **Dynamic Tool Constrictions (P8):** Banned tools (e.g. terminal banned during code-only mutations) and forced tools.
3. **Sensitive File Protections (P9):** Hard protection against accessing `.env`, `.git/`, `.ssh/`, and private keys.

```python
class HardenedFileExecutor(ToolExecutor[HardenedFileAction, HardenedFileObservation]):
    """Thread-safe executor invoking P9 WorkspaceFileVirtualizer."""
    
    def __init__(self, sandbox_manager: "ToolSandboxManager") -> None:
        self.sandbox = sandbox_manager

    def __call__(
        self,
        action: HardenedFileAction,
        conversation: Optional["LocalConversation"] = None,
    ) -> HardenedFileObservation:
        return self.sandbox.execute_file_action(action)

    def close(self) -> None:
        pass

class HardenedTerminalExecutor(ToolExecutor[HardenedTerminalAction, HardenedTerminalObservation]):
    """Thread-safe executor invoking P9 TerminalSandboxEngine."""
    
    def __init__(self, sandbox_manager: "ToolSandboxManager") -> None:
        self.sandbox = sandbox_manager

    def __call__(
        self,
        action: HardenedTerminalAction,
        conversation: Optional["LocalConversation"] = None,
    ) -> HardenedTerminalObservation:
        return self.sandbox.execute_terminal_action(action)

    def close(self) -> None:
        self.sandbox.terminate_active_processes()
```

---

# 4. Ephemeral Session Lifecycle & Clean Yield Protocol

The lifecycle of an OpenHands agent turn in ORAGAI follows an **Inversion of Control (IoC)** protocol. The agent does not loop indefinitely; it runs for exactly one bounded turn envelope ($T_{\text{allocated}}$) and yields control back to the FSM.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 EPHEMERAL SESSION LIFECYCLE TRACE (IoC TURN DISPATCH)                                  │
│                                                                                                                        │
│   [Guard FSM Engine (P3)]                                                                                              │
│              │                                                                                                         │
│   1. PRE-DISPATCH PHASE                                                                                                │
│      ├─ Compute Turn Envelope (P4): T_allocated in [10, 30]                                                            │
│      ├─ Synthesize Context PromptView (P6): Tier 0 (Task Truth) + Tier 1 (Handoff) + Tier 2 (Digest)                   │
│      ├─ Configure ToolSandboxManager (P9): Persona RBAC (P5) + Tool Constrictions (P8)                                 │
│      └─ SDKAgentFactory: Construct Agent(tools, system_prompt, tool_concurrency_limit=1)                               │
│              │                                                                                                         │
│              ▼                                                                                                         │
│   2. SYNCHRONOUS BOUNDED EXECUTION PHASE                                                                               │
│      ├─ Instantiate LocalConversation(max_iteration_per_run=T_allocated, callbacks=[telemetry_bridge.on_event])        │
│      ├─ Send initial task prompt to conversation                                                                       │
│      ├─ conv.run()  <── Synchronous execution on main worker thread (NO background interrupt threads)                  │
│      │     ├─ Iteration 1: Agent Step ──▶ ActionEvent ──▶ TelemetryBridge ──▶ ToolExecutor ──▶ ObservationEvent        │
│      │     ├─ Iteration 2: Agent Step ──▶ ActionEvent ──▶ TelemetryBridge ──▶ ToolExecutor ──▶ ObservationEvent        │
│      │     └─ ... (Runs until Agent finishes or iteration == T_allocated)                                              │
│      └─ conv.run() exits cleanly                                                                                       │
│              │                                                                                                         │
│              ▼                                                                                                         │
│   3. POST-YIELD STATUS CLASSIFIER PHASE                                                                                │
│      ├─ Inspect ConversationState.execution_status and event stream history                                            │
│      ├─ Classify deterministic AgentExecutionOutcome (NATURAL_COMPLETION vs STEP_LIMIT_REACHED vs TOOL_REJECTION)      │
│      ├─ Extract token usage metrics and generated artifacts                                                            │
│      └─ Execute conv.close(delete_on_close=True)                                                                        │
│              │                                                                                                         │
│              ▼                                                                                                         │
│   4. EVIDENCE & HANDOFF EMISSION PHASE                                                                                 │
│      ├─ Package CrossAgentHandoffPayload (P5/P6) with Merkle digest and artifact diffs                                 │
│      └─ Emit AGENT_YIELDED event to GuardedFSMEngine (P3) with AgentExecutionOutcome                                   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4.1 Deterministic Exit Status Classifier

When `conv.run()` yields, the `ExitStatusClassifier` analyzes the `ConversationState` and event sequence to produce an unambiguous `AgentExecutionOutcome`.

### Exit Status Taxonomy:
1. **`NATURAL_COMPLETION`**: The agent explicitly called the finish tool or the SDK marked execution status as `FINISHED`.
2. **`STEP_LIMIT_REACHED`**: The turn loop reached `max_iteration_per_run` ($T_{\text{allocated}}$) or emitted `MaxIterationsReached`.
3. **`TOKEN_LIMIT_REACHED`**: The turn consumed tokens exceeding the P4 turn budget envelope.
4. **`TOOL_REJECTION`**: Execution failed due to security sandbox violations, RBAC permission rejections, or repeated tool execution errors.
5. **`AGENT_STUCK`**: OpenHands native stuck detector triggered (`ConversationExecutionStatus.STUCK`).
6. **`ABORTED`**: Halted cleanly by user interaction or `PipelineController.stop()`.
7. **`FATAL_ERROR`**: Unhandled exception, API network crash, or unrecoverable LLM rate limit.

```python
class AgentExitReason(str, Enum):
    NATURAL_COMPLETION = "natural_completion"
    STEP_LIMIT_REACHED = "step_limit_reached"
    TOKEN_LIMIT_REACHED = "token_limit_reached"
    TOOL_REJECTION = "tool_rejection"
    AGENT_STUCK = "agent_stuck"
    ABORTED = "aborted"
    FATAL_ERROR = "fatal_error"

@dataclass(frozen=True)
class AgentExecutionOutcome:
    """Deterministic result of a single ephemeral OpenHands turn."""
    role: str
    exit_reason: AgentExitReason
    completed_naturally: bool
    iterations_executed: int
    max_iterations_allocated: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    error_message: Optional[str]
    mutated_files: tuple[str, ...]
    final_thought: Optional[str]
    handoff_payload: Optional[CrossAgentHandoffPayload]
```

### Classification Algorithm:

```python
class ExitStatusClassifier:
    """Deterministically classifies ConversationState into AgentExecutionOutcome."""
    
    @staticmethod
    def classify(
        conv: "LocalConversation",
        role: str,
        max_turns: int,
        initial_tokens: int,
        token_ceiling: int,
        mutated_files: Sequence[str],
    ) -> AgentExecutionOutcome:
        state = conv.state
        status = state.execution_status
        events = list(state.events)
        
        # 1. Extract Token Usage
        tu = getattr(getattr(conv.agent, "llm", None), "metrics", None)
        pt, ct = 0, 0
        if tu and hasattr(tu, "accumulated_token_usage"):
            pt = getattr(tu.accumulated_token_usage, "prompt_tokens", 0) or 0
            ct = getattr(tu.accumulated_token_usage, "completion_tokens", 0) or 0
        total_tokens = max(0, (pt + ct) - initial_tokens)
        
        # 2. Extract Final Thought & Actions
        final_thought = None
        for ev in reversed(events):
            if type(ev).__name__ == "ActionEvent" and getattr(ev, "thought", None):
                final_thought = str(ev.thought).strip()
                break
        
        # 3. Check for Fatal ConversationErrorEvent
        latest_error_event = next(
            (ev for ev in reversed(events) if type(ev).__name__ == "ConversationErrorEvent"),
            None
        )
        
        # 4. Deterministic Classification
        if status == ConversationExecutionStatus.FINISHED:
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.NATURAL_COMPLETION,
                completed_naturally=True,
                iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message=None,
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )
            
        if latest_error_event and getattr(latest_error_event, "code", "") == "MaxIterationsReached":
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.STEP_LIMIT_REACHED,
                completed_naturally=False,
                iterations_executed=max_turns,
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message=f"Turn step limit reached ({max_turns} turns).",
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )
            
        if token_ceiling > 0 and total_tokens >= token_ceiling:
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.TOKEN_LIMIT_REACHED,
                completed_naturally=False,
                iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message=f"Turn token budget exhausted ({total_tokens:,} >= {token_ceiling:,}).",
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )
            
        if status == ConversationExecutionStatus.STUCK:
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.AGENT_STUCK,
                completed_naturally=False,
                iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message="Agent loop repetition detected by SDK stuck detector.",
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )
            
        if status == ConversationExecutionStatus.ERROR or latest_error_event:
            err_msg = getattr(latest_error_event, "detail", "Unknown SDK runtime error") if latest_error_event else "Execution error"
            return AgentExecutionOutcome(
                role=role,
                exit_reason=AgentExitReason.FATAL_ERROR,
                completed_naturally=False,
                iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
                max_iterations_allocated=max_turns,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=total_tokens,
                cost_usd=0.0,
                error_message=str(err_msg),
                mutated_files=tuple(mutated_files),
                final_thought=final_thought,
                handoff_payload=None,
            )
            
        return AgentExecutionOutcome(
            role=role,
            exit_reason=AgentExitReason.STEP_LIMIT_REACHED,
            completed_naturally=False,
            iterations_executed=len([e for e in events if type(e).__name__ == "ActionEvent"]),
            max_iterations_allocated=max_turns,
            prompt_tokens=pt,
            completion_tokens=ct,
            total_tokens=total_tokens,
            cost_usd=0.0,
            error_message="Turn completed without explicit FINISHED state.",
            mutated_files=tuple(mutated_files),
            final_thought=final_thought,
            handoff_payload=None,
        )
```

---

# 5. EventStream Telemetry & Live UI Synchronization

OpenHands SDK v1.49.4 provides a synchronous callback mechanism: `Conversation(callbacks=[telemetry_bridge.on_event])`.
Whenever an event is created in the conversation lifecycle, the SDK invokes the callback synchronously on the executing thread.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SYNCHRONOUS TELEMETRY STREAMING PIPELINE                        │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                         OpenHands SDK LocalConversation                        │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │ Fires on_event(Event)                      │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        OpenHandsTelemetryBridge (P10)                          │   │
│   │                                                                                │   │
│   │   1. Secret Masking Boundary:                                                  │   │
│   │      • Redact API keys, bearer tokens, passwords, private keys                 │   │
│   │      • Mask file paths matching sensitive patterns                             │   │
│   │                                                                                │   │
│   │   2. Synchronous Demultiplexer:                                                │   │
│   │      ├──▶ SessionLogStore (In-Memory Step Log & Metrics)                       │   │
│   │      ├──▶ OrchestratorLiveVisualizer (Rich Terminal Live Status Card)          │   │
│   │      └──▶ SentinelDiagnosticsDB (SQLite WAL Event Journal)                    │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.1 Secret Masking Boundary Enforcement

Before any event is recorded in the `SessionLogStore`, rendered on screen, or committed to the SQLite WAL database, it passes through the `SecretMaskingFilter`.

```python
class SecretMaskingFilter:
    """High-performance regex mask preventing secret leakage into logs and UI."""
    
    SECRET_PATTERNS = (
        re.compile(r"(?i)(api[_-]?key|secret|token|password|auth|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"sk-[a-zA-Z0-9]{32,}"),
        re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC )?PRIVATE KEY-----"),
    )

    @classmethod
    def mask_text(cls, text: str) -> str:
        if not text:
            return text
        sanitized = text
        for pattern in cls.SECRET_PATTERNS:
            sanitized = pattern.sub(r"\1: [REDACTED_SECRET]", sanitized)
        return sanitized
```

---

## 5.2 Thread-Safe Telemetry Demultiplexer

```python
class OpenHandsTelemetryBridge:
    """Synchronous, thread-safe demultiplexer for OpenHands EventStream events."""
    
    def __init__(
        self,
        log_store: "SessionLogStore",
        visualizer: Optional["OrchestratorLiveVisualizer"],
        diagnostics_db: Optional["SentinelDiagnosticsDB"],
    ) -> None:
        self.store = log_store
        self.visualizer = visualizer
        self.db = diagnostics_db
        self.mutated_files: set[str] = set()

    def on_event(self, event: Event) -> None:
        """Process incoming SDK event synchronously."""
        event_type = type(event).__name__
        
        # 1. Action Events (Tool Calls & Thoughts)
        if event_type == "ActionEvent":
            action = getattr(event, "action", None)
            thought = getattr(event, "thought", "") or getattr(action, "thought", "")
            masked_thought = SecretMaskingFilter.mask_text(str(thought)) if thought else None
            
            tool_name = getattr(event, "tool_name", "") or getattr(action, "__class__", type(action)).__name__
            args = {}
            if hasattr(action, "model_dump"):
                args = action.model_dump()
            elif hasattr(action, "__dict__"):
                args = dict(action.__dict__)
            
            # Track file mutations
            op = args.get("operation") or ""
            target_path = args.get("path") or args.get("file_path") or ""
            if op in ("write", "patch", "delete") and target_path:
                self.mutated_files.add(str(target_path))
                
            self.store.record_action(
                tool_name=tool_name,
                operation=op,
                target_path=target_path,
                thought=masked_thought,
            )
            
            if self.visualizer:
                self.visualizer.on_action(tool_name, op, target_path, masked_thought)

        # 2. Observation Events (Tool Outputs)
        elif event_type == "ObservationEvent":
            obs = getattr(event, "observation", None)
            tool_name = getattr(event, "tool_name", "")
            
            obs_data = {}
            if hasattr(obs, "model_dump"):
                obs_data = obs.model_dump()
            elif hasattr(obs, "__dict__"):
                obs_data = dict(obs.__dict__)
                
            stdout = SecretMaskingFilter.mask_text(str(obs_data.get("stdout", "")))
            stderr = SecretMaskingFilter.mask_text(str(obs_data.get("stderr", "")))
            error_msg = SecretMaskingFilter.mask_text(str(obs_data.get("error_message", "")))
            
            self.store.record_observation(
                tool_name=tool_name,
                success=obs_data.get("success", True),
                stdout=stdout,
                stderr=stderr,
                error_message=error_msg,
            )
            
            if self.visualizer:
                self.visualizer.on_observation(tool_name, obs_data.get("success", True), error_msg)

        # 3. Error Events
        elif event_type in ("AgentErrorEvent", "ConversationErrorEvent"):
            code = getattr(event, "code", "Error")
            detail = SecretMaskingFilter.mask_text(str(getattr(event, "detail", getattr(event, "error", ""))))
            self.store.record_error(code, detail)
            if self.visualizer:
                self.visualizer.on_error(code, detail)
                
        # 4. Commit to SQLite WAL Diagnostics Journal
        if self.db:
            try:
                self.db.log_event(
                    role=self.store.current_role or "unknown",
                    event_type=event_type,
                    payload=SecretMaskingFilter.mask_text(str(event)),
                )
            except Exception:
                pass
```

---

# 6. Canonical Python Architecture & Data Models

This section provides the complete, production-ready, fully typed Python 3.12+ architecture for `orchestrator/engine/openhands_bridge.py`.

```python
"""Canonical OpenHands SDK Runtime Bridge for ORAGAI (P10 Specification).

Governs the execution boundary between ORAGAI Guarded FSM and OpenHands SDK v1.49.4.
Enforces Inversion of Control (IoC), bounded turn envelopes, clean tool adapters,
and synchronous telemetry streaming with zero monkey-patching.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from pydantic import BaseModel, ConfigDict, Field

from openhands.sdk import Agent, LLM
from openhands.sdk.conversation import Conversation, ConversationExecutionStatus, LocalConversation
from openhands.sdk.event import ActionEvent, ConversationErrorEvent, Event, ObservationEvent
from openhands.sdk.tool import ToolDefinition, ToolExecutor

if TYPE_CHECKING:
    from orchestrator.config import AgentRoleConfig, OrchestratorConfig
    from orchestrator.control.token_governance import TurnEnvelope
    from orchestrator.llm.manager import LLMManager
    from orchestrator.pipeline.context_envelope import CrossAgentHandoffPayload, PromptView
    from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB
    from orchestrator.skills.manager import SkillManager
    from orchestrator.tools.sandbox_manager import ToolSandboxManager
    from orchestrator.ui.session_store import SessionLogStore
    from orchestrator.ui.visualizer import OrchestratorLiveVisualizer

logger = logging.getLogger(__name__)


# =====================================================================
# 1. Data Models & Exit Taxonomy
# =====================================================================

class AgentExitReason(str, Enum):
    """Explicit, non-ambiguous exit status classification for an agent turn."""
    NATURAL_COMPLETION = "natural_completion"
    STEP_LIMIT_REACHED = "step_limit_reached"
    TOKEN_LIMIT_REACHED = "token_limit_reached"
    TOOL_REJECTION = "tool_rejection"
    AGENT_STUCK = "agent_stuck"
    ABORTED = "aborted"
    FATAL_ERROR = "fatal_error"


@dataclass(frozen=True)
class AgentExecutionOutcome:
    """Immutable record of an ephemeral agent turn's execution."""
    role: str
    exit_reason: AgentExitReason
    completed_naturally: bool
    iterations_executed: int
    max_iterations_allocated: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    error_message: Optional[str]
    mutated_files: Tuple[str, ...]
    final_thought: Optional[str]
    handoff_payload: Optional[CrossAgentHandoffPayload] = None


# =====================================================================
# 2. Hardened Tool Definition Models (P9 Integration)
# =====================================================================

class FileOperationType(str, Enum):
    READ = "read"
    WRITE = "write"
    PATCH = "patch"
    SYMBOL = "symbol"
    OUTLINE = "outline"
    LIST = "list"
    DELETE = "delete"


class HardenedFileAction(BaseModel):
    """Strict action model for AST-virtualized file operations."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    operation: FileOperationType = Field(
        default=FileOperationType.READ,
        description="The file operation: 'read', 'write', 'patch', 'symbol', 'outline', 'list', 'delete'."
    )
    path: str = Field(
        ...,
        alias="file_path",
        description="Workspace-relative path to the target file."
    )
    content: Optional[str] = Field(
        default=None,
        alias="text",
        description="Content for 'write' operation."
    )
    patch_find: Optional[str] = Field(
        default=None,
        description="Exact substring to find for 'patch' operation."
    )
    patch_replace: Optional[str] = Field(
        default=None,
        description="Replacement substring for 'patch' operation."
    )
    symbol_name: Optional[str] = Field(
        default=None,
        alias="symbol",
        description="Target function, class, or method name for 'symbol' extraction."
    )
    offset_line: int = Field(
        default=1,
        ge=1,
        description="1-based starting line number for 'read' window."
    )
    limit_lines: int = Field(
        default=250,
        ge=1,
        le=1000,
        description="Maximum lines to return in 'read' window."
    )


class HardenedFileObservation(BaseModel):
    """Observation returned from file operations."""
    model_config = ConfigDict(extra="ignore")

    success: bool = True
    operation: str = "read"
    path: str = ""
    content: Optional[str] = None
    total_lines: int = 0
    returned_lines: int = 0
    has_more: bool = False
    ast_valid: bool = True
    error_message: Optional[str] = None


class HardenedTerminalAction(BaseModel):
    """Strict action model for grammar-validated terminal commands."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    command: str = Field(
        ...,
        alias="cmd",
        description="The CLI command to execute."
    )
    timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=600,
        description="Execution timeout in seconds."
    )


class HardenedTerminalObservation(BaseModel):
    """Observation returned from terminal command execution."""
    model_config = ConfigDict(extra="ignore")

    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    security_violation: bool = False
    error_message: Optional[str] = None


class HardenedFileExecutor(ToolExecutor[HardenedFileAction, HardenedFileObservation]):
    """ToolExecutor delegating file operations to P9 ToolSandboxManager."""

    def __init__(self, sandbox_manager: "ToolSandboxManager") -> None:
        self.sandbox = sandbox_manager

    def __call__(
        self,
        action: HardenedFileAction,
        conversation: Optional[LocalConversation] = None,
    ) -> HardenedFileObservation:
        return self.sandbox.execute_file_action(action)

    def close(self) -> None:
        pass


class HardenedTerminalExecutor(ToolExecutor[HardenedTerminalAction, HardenedTerminalObservation]):
    """ToolExecutor delegating terminal commands to P9 ToolSandboxManager."""

    def __init__(self, sandbox_manager: "ToolSandboxManager") -> None:
        self.sandbox = sandbox_manager

    def __call__(
        self,
        action: HardenedTerminalAction,
        conversation: Optional[LocalConversation] = None,
    ) -> HardenedTerminalObservation:
        return self.sandbox.execute_terminal_action(action)

    def close(self) -> None:
        self.sandbox.terminate_active_processes()


class HardenedWorkspaceFileTool(ToolDefinition[HardenedFileAction, HardenedFileObservation]):
    """Official OpenHands SDK ToolDefinition for AST-virtualized file operations."""

    @classmethod
    def create(
        cls,
        conv_state: Optional[Any] = None,
        sandbox_manager: Optional["ToolSandboxManager"] = None,
        **params: Any,
    ) -> Sequence["HardenedWorkspaceFileTool"]:
        if sandbox_manager is None:
            raise ValueError("HardenedWorkspaceFileTool requires an active ToolSandboxManager instance.")
        return [
            cls(
                description=(
                    "Read, write, patch, list, delete, or inspect AST symbols/outlines in workspace files. "
                    "Supports bounded line windowing and hierarchical outline extraction."
                ),
                action_type=HardenedFileAction,
                observation_type=HardenedFileObservation,
                executor=HardenedFileExecutor(sandbox_manager),
            )
        ]


class HardenedWorkspaceTerminalTool(ToolDefinition[HardenedTerminalAction, HardenedTerminalObservation]):
    """Official OpenHands SDK ToolDefinition for grammar-secured terminal commands."""

    @classmethod
    def create(
        cls,
        conv_state: Optional[Any] = None,
        sandbox_manager: Optional["ToolSandboxManager"] = None,
        **params: Any,
    ) -> Sequence["HardenedWorkspaceTerminalTool"]:
        if sandbox_manager is None:
            raise ValueError("HardenedWorkspaceTerminalTool requires an active ToolSandboxManager instance.")
        return [
            cls(
                description=(
                    "Execute secured CLI commands (pytest, ruff, python, git, etc.) in the workspace. "
                    "Validates commands with strict grammar security and handles Windows PowerShell pipelines."
                ),
                action_type=HardenedTerminalAction,
                observation_type=HardenedTerminalObservation,
                executor=HardenedTerminalExecutor(sandbox_manager),
            )
        ]


# =====================================================================
# 3. Secret Masking & Telemetry Bridge
# =====================================================================

class SecretMaskingFilter:
    """Masks credentials, API keys, and sensitive tokens from telemetry streams."""

    PATTERNS: Tuple[re.Pattern[str], ...] = (
        re.compile(r"(?i)(api[_-]?key|secret|token|password|auth|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"sk-[a-zA-Z0-9]{32,}"),
        re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC )?PRIVATE KEY-----"),
    )

    @classmethod
    def mask(cls, text: str) -> str:
        if not text:
            return text
        sanitized = text
        for pattern in cls.PATTERNS:
            sanitized = pattern.sub(r"\1: [REDACTED_SECRET]", sanitized)
        return sanitized


class OpenHandsTelemetryBridge:
    """Synchronous EventStream callback bridge mapping SDK events to ORAGAI telemetry."""

    def __init__(
        self,
        log_store: "SessionLogStore",
        visualizer: Optional["OrchestratorLiveVisualizer"] = None,
        diagnostics_db: Optional["SentinelDiagnosticsDB"] = None,
    ) -> None:
        self.store = log_store
        self.visualizer = visualizer
        self.db = diagnostics_db
        self.mutated_files: Set[str] = set()

    def on_event(self, event: Event) -> None:
        """Synchronously process SDK event on emission."""
        event_name = type(event).__name__

        if event_name == "ActionEvent":
            action = getattr(event, "action", None)
            thought = getattr(event, "thought", "") or getattr(action, "thought", "")
            masked_thought = SecretMaskingFilter.mask(str(thought)) if thought else None

            tool_name = getattr(event, "tool_name", "") or getattr(action, "__class__", type(action)).__name__
            args = {}
            if hasattr(action, "model_dump"):
                args = action.model_dump()
            elif hasattr(action, "__dict__"):
                args = dict(action.__dict__)

            op = str(args.get("operation") or "")
            target_path = str(args.get("path") or args.get("file_path") or "")
            if op in ("write", "patch", "delete") and target_path:
                self.mutated_files.add(target_path)

            self.store.record_action(
                tool_name=tool_name,
                operation=op,
                target_path=target_path,
                thought=masked_thought,
            )
            if self.visualizer:
                self.visualizer.on_action(tool_name, op, target_path, masked_thought)

        elif event_name == "ObservationEvent":
            obs = getattr(event, "observation", None)
            tool_name = getattr(event, "tool_name", "")
            obs_dict: Dict[str, Any] = {}
            if hasattr(obs, "model_dump"):
                obs_dict = obs.model_dump()
            elif hasattr(obs, "__dict__"):
                obs_dict = dict(obs.__dict__)

            success = bool(obs_dict.get("success", True))
            stdout = SecretMaskingFilter.mask(str(obs_dict.get("stdout", "")))
            stderr = SecretMaskingFilter.mask(str(obs_dict.get("stderr", "")))
            error_msg = SecretMaskingFilter.mask(str(obs_dict.get("error_message", "")))

            self.store.record_observation(
                tool_name=tool_name,
                success=success,
                stdout=stdout,
                stderr=stderr,
                error_message=error_msg,
            )
            if self.visualizer:
                self.visualizer.on_observation(tool_name, success, error_msg)

        elif event_name in ("AgentErrorEvent", "ConversationErrorEvent"):
            code = str(getattr(event, "code", "Error"))
            detail = SecretMaskingFilter.mask(str(getattr(event, "detail", getattr(event, "error", ""))))
            self.store.record_error(code, detail)
            if self.visualizer:
                self.visualizer.on_error(code, detail)

        if self.db:
            try:
                self.db.log_event(
                    role=self.store.current_role or "agent",
                    event_type=event_name,
                    payload=SecretMaskingFilter.mask(str(event)),
                )
            except Exception:
                pass


# =====================================================================
# 4. SDK Agent Factory & Tool Adapter
# =====================================================================

class SDKToolAdapter:
    """Binds hardened P9 tools to OpenHands SDK ToolDefinition sequences."""

    @staticmethod
    def create_tools_for_persona(
        sandbox_manager: "ToolSandboxManager",
        role_name: str,
    ) -> List[ToolDefinition[Any, Any]]:
        """Instantiate hardened tools configured with persona RBAC and constrictions."""
        tools: List[ToolDefinition[Any, Any]] = []

        # 1. Hardened Workspace File Tool (Always included with RBAC write boundaries)
        file_tools = HardenedWorkspaceFileTool.create(sandbox_manager=sandbox_manager)
        tools.extend(file_tools)

        # 2. Hardened Workspace Terminal Tool (Conditionally included based on role and constrictions)
        if sandbox_manager.is_tool_permitted("terminal"):
            terminal_tools = HardenedWorkspaceTerminalTool.create(sandbox_manager=sandbox_manager)
            tools.extend(terminal_tools)

        return tools


class SDKAgentFactory:
    """Creates configured OpenHands Agent instances per persona without monkey-patching."""

    @staticmethod
    def create_agent(
        config: "OrchestratorConfig",
        llm_manager: "LLMManager",
        role_name: str,
        system_prompt: str,
        tools: List[ToolDefinition[Any, Any]],
    ) -> Agent:
        """Construct Agent instance with clean SDK configuration."""
        llm = llm_manager.get_llm(role_name)

        return Agent(
            llm=llm,
            tools=tools,
            system_prompt=system_prompt,
            include_default_tools=False,
            tool_concurrency_limit=1,
        )


# =====================================================================
# 5. SDK Session Runner & Execution Seam
# =====================================================================

class SDKSessionRunner:
    """Executes single-turn bounded conversations with synchronous lifecycle control."""

    @staticmethod
    def run_turn(
        agent: Agent,
        workspace_path: Path,
        prompt_view: "PromptView",
        turn_envelope: "TurnEnvelope",
        telemetry_bridge: OpenHandsTelemetryBridge,
        role_name: str,
    ) -> AgentExecutionOutcome:
        """Execute a single bounded turn envelope without background polling threads."""
        max_turns = turn_envelope.max_turns
        token_ceiling = turn_envelope.token_ceiling

        # 1. Baseline Token Inspection
        initial_tokens = 0
        llm = getattr(agent, "llm", None)
        if llm and hasattr(llm, "metrics") and hasattr(llm.metrics, "accumulated_token_usage"):
            tu = llm.metrics.accumulated_token_usage
            if tu:
                initial_tokens = int((getattr(tu, "prompt_tokens", 0) or 0) + (getattr(tu, "completion_tokens", 0) or 0))

        # 2. Ephemeral LocalConversation Instantiation
        conv = LocalConversation(
            agent=agent,
            workspace=workspace_path,
            max_iteration_per_run=max_turns,
            stuck_detection=True,
            callbacks=[telemetry_bridge.on_event],
            delete_on_close=True,
            visualizer=None,
        )

        # 3. Ingest Initial Prompt
        conv.send_message(prompt_view.compiled_prompt)

        # 4. Synchronous Execution
        try:
            conv.run()
        except Exception as e:
            logger.error(f"Execution error in {role_name} turn: {e}", exc_info=True)

        # 5. Classify Exit Status
        outcome = ExitStatusClassifier.classify(
            conv=conv,
            role=role_name,
            max_turns=max_turns,
            initial_tokens=initial_tokens,
            token_ceiling=token_ceiling,
            mutated_files=list(telemetry_bridge.mutated_files),
        )

        # 6. Ephemeral Teardown
        try:
            conv.close()
        except Exception:
            pass

        return outcome


# =====================================================================
# 6. Master Orchestration Facade
# =====================================================================

class OpenHandsRuntimeBridge:
    """Master facade providing clean execution delegation from GuardedFSMEngine to OpenHands SDK."""

    def __init__(
        self,
        config: "OrchestratorConfig",
        llm_manager: "LLMManager",
        log_store: "SessionLogStore",
        visualizer: Optional["OrchestratorLiveVisualizer"] = None,
        diagnostics_db: Optional["SentinelDiagnosticsDB"] = None,
    ) -> None:
        self.config = config
        self.llm_manager = llm_manager
        self.log_store = log_store
        self.visualizer = visualizer
        self.diagnostics_db = diagnostics_db

    def execute_bounded_turn(
        self,
        role_name: str,
        workspace_path: Path,
        prompt_view: "PromptView",
        turn_envelope: "TurnEnvelope",
        sandbox_manager: "ToolSandboxManager",
    ) -> AgentExecutionOutcome:
        """Execute a single bounded turn for the specified persona."""
        self.log_store.set_phase(role_name)

        # 1. Create Telemetry Bridge
        telemetry_bridge = OpenHandsTelemetryBridge(
            log_store=self.log_store,
            visualizer=self.visualizer,
            diagnostics_db=self.diagnostics_db,
        )

        # 2. Build Hardened Tools
        tools = SDKToolAdapter.create_tools_for_persona(
            sandbox_manager=sandbox_manager,
            role_name=role_name,
        )

        # 3. Instantiate Agent
        agent = SDKAgentFactory.create_agent(
            config=self.config,
            llm_manager=self.llm_manager,
            role_name=role_name,
            system_prompt=prompt_view.tier0_system_prompt,
            tools=tools,
        )

        # 4. Run Ephemeral Bounded Session
        outcome = SDKSessionRunner.run_turn(
            agent=agent,
            workspace_path=workspace_path,
            prompt_view=prompt_view,
            turn_envelope=turn_envelope,
            telemetry_bridge=telemetry_bridge,
            role_name=role_name,
        )

        return outcome
```

---

# 7. Rigorous Test Matrix & Verification Scenarios

The following verification matrix specifies the exact automated test suite validating the OpenHands Runtime Boundary architecture.

| Test ID | Test Function Name | Architectural Invariant Tested | Verification & Pass Criteria |
| :--- | :--- | :--- | :--- |
| **TEST-P10-01** | `test_zero_monkey_patching_integrity` | **Elimination of `sdk_patch.py`** | Verify that importing `orchestrator` does NOT patch `openhands.sdk.agent.utils`, `Telemetry`, or `PromptTokensDetailsWrapper`. |
| **TEST-P10-02** | `test_hardened_file_tool_sdk_registration` | **Official `ToolDefinition` Protocol** | Verify `HardenedWorkspaceFileTool` conforms to `ToolDefinition[HardenedFileAction, HardenedFileObservation]` and exports clean MCP and OpenAI schemas without exceptions. |
| **TEST-P10-03** | `test_hardened_terminal_tool_sdk_registration` | **Terminal Tool Protocol & Grammar Validation** | Verify `HardenedWorkspaceTerminalTool` converts commands via `TerminalSandboxEngine` and executes within the SDK turn loop. |
| **TEST-P10-04** | `test_ephemeral_conversation_turn_envelope_limit` | **$T_{\text{allocated}}$ Native Turn Bounding** | Verify `LocalConversation` initialized with `max_iteration_per_run=5` halts cleanly after 5 iterations with `ExitReason.STEP_LIMIT_REACHED` without spawning background threads. |
| **TEST-P10-05** | `test_exit_status_classifier_natural_completion` | **Clean Natural Completion Classification** | Verify that when agent finishes turn with status `FINISHED`, `ExitStatusClassifier` returns `completed_naturally=True` and `exit_reason=NATURAL_COMPLETION`. |
| **TEST-P10-06** | `test_exit_status_classifier_step_limit` | **Step Ceiling False Success Elimination** | Verify that when SDK emits `MaxIterationsReached`, `ExitStatusClassifier` returns `completed_naturally=False` and `exit_reason=STEP_LIMIT_REACHED`. |
| **TEST-P10-07** | `test_exit_status_classifier_token_budget_exhaustion` | **Turn Token Budget Classification** | Verify that when turn tokens exceed `token_ceiling`, classifier marks `exit_reason=TOKEN_LIMIT_REACHED`. |
| **TEST-P10-08** | `test_secret_masking_boundary_in_telemetry` | **Zero Secret Leakage in Telemetry** | Send `ActionEvent` containing `api_key='sk-1234567890abcdef'` and private keys; verify output in `SessionLogStore`, visualizer, and SQLite WAL contains `[REDACTED_SECRET]`. |
| **TEST-P10-09** | `test_synchronous_event_stream_demux` | **Synchronous Non-Blocking Telemetry Demux** | Emit sequence of 10 `ActionEvent` and `ObservationEvent` objects; verify exact 1:1 synchronous ingestion in `SessionLogStore` without thread deadlocks or race conditions. |
| **TEST-P10-10** | `test_tool_concurrency_limit_sequential_execution` | **Windows NT Determinism** | Verify `Agent(tool_concurrency_limit=1)` executes tool actions strictly sequentially without overlapping filesystem writes. |

---

# 8. Handoff Contract for P11 (Autonomous Benchmark & Verification Plan)

This section establishes the formal interfaces, mock harnesses, and verification telemetry produced by P10 that are consumed by **P11 (Autonomous Benchmark & Verification Plan)**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              P10 ──▶ P11 HANDOFF ARCHITECTURE                          │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                    OpenHands Runtime Bridge (P10 Delivery)                     │   │
│   │                                                                                │   │
│   │   • OpenHandsRuntimeBridge.execute_bounded_turn() Facade                       │   │
│   │   • Deterministic AgentExecutionOutcome Data Model                             │   │
│   │   • Hardened File & Terminal SDK Tool Definitions                              │   │
│   │   • Synchronous Secret-Masked Telemetry Pipeline                               │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │ Telemetry & Execution Hooks                │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │            Autonomous Benchmark & Verification Harness (P11 Ingestion)         │   │
│   │                                                                                │   │
│   │   • Mock LLM ReAct Session Harness (Simulated Multi-Turn Execution)            │   │
│   │   • Real-World SWE-Bench / Autonomous Milestone Execution Benchmarking         │   │
│   │   • Turn Envelope Compliance & False Completion Verifier                       │   │
│   │   • Secret Leakage & Command Injection Fuzzing Suite                           │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8.1 P10 Exit Criteria

Before P10 is marked complete and implementation commences in P11, all the following architectural criteria must be fulfilled:
1. **Zero Production Code Modifications:** The repository remains in a clean state with all 244 existing unit tests passing.
2. **Elimination of `sdk_patch.py`:** Complete architectural plan to remove global monkey-patching and replace it with official Pydantic v2 schemas and SDK `ToolDefinition` protocols.
3. **Formalization of Ephemeral Turn Lifecycle:** Elimination of background monitor threads calling `conv.interrupt()`; replacement with native SDK `max_iteration_per_run = T_allocated`.
4. **Deterministic Exit Classification:** Formal specification of `ExitStatusClassifier` preventing step limit exhaustion from masquerading as successful completion.
5. **Synchronous Telemetry Bridge:** Formal specification of `OpenHandsTelemetryBridge` with secret masking filter and SQLite WAL logging.

---

## 8.2 Input Contract for P11 (Autonomous Benchmark & Verification Plan)

P11 consumes the following interfaces and structures from P10:
- **`OpenHandsRuntimeBridge`**: The master orchestration facade used to execute real and simulated agent sessions.
- **`AgentExecutionOutcome`**: The structured output schema consumed by P11 benchmark runners to measure turn efficiency, token usage, and completion correctness.
- **`MockConversationHarness`**: The mock execution environment simulating OpenHands SDK turn loops for fast, deterministic unit and regression testing.
- **`TelemetryValidationHooks`**: Hooks to inspect `SessionLogStore` and SQLite WAL event logs during benchmark evaluation.

$$\text{\textbf{P10 Plan Specification Complete. Ready for P11 Architectural Planning.}}$$
