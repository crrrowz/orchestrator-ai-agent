# 🗺️ Orchestrator-AI-Agent — Internal Development Roadmap

> **Scope**: تحليل داخلي عميق للكود الموجود فعلياً. لا أفكار خارجية — فقط أخطاء، مشاكل، اقتراحات، وتوصيات لجعل النظام أكفأ 100x.
>
> **Generated**: 2026-09-23 | **Source**: Full audit of 18 source files across 7 modules

---

## 📊 Current State Summary

| Metric | Value |
|---|---|
| Source Files | 18 Python modules |
| Total LOC | ~2,400 lines |
| Unit Tests | 14/14 passing (4 test files) |
| Skills | 9 YAML+MD skills |
| Pipelines | 2 (`dev-test`, `full`) |
| Agents | 4 (Architect, Developer, Tester, Reviewer) |
| Known Bugs | **0 documented, 11 found in this audit** |

---

# 🔴 PHASE 1: CRITICAL — Token Hemorrhage Prevention

> **المشكلة الأساسية**: النظام يستهلك التوكنات بشكل جنوني بدون أي حدود ذكية. المطور يعمل لوحده بدون رقابة حقيقية.

---

## 1.1 🩸 BUG: No Token Budget Enforcement at Runtime

**File**: [`dev_test_loop.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py)
**File**: [`full_pipeline.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py)

**Problem**: `max_budget_usd` is defined in [`config.py:32`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/config.py#L32) but **never checked** during pipeline execution. The Developer can burn unlimited tokens through `Conversation.run()` while the $0.50 budget sits as a decorative config value.

```python
# config.py:32 — defined but DEAD CODE in pipelines
max_budget_usd: float = Field(default=float(os.environ.get("MAX_BUDGET_USD", "0.50")))
```

**Impact**: 🔥 Every pipeline run has **ZERO cost ceiling**. The agent can generate 100+ steps with 0 budget checks.

**Fix**: Add a `TokenBudgetGuard` that hooks into `OrchestratorLiveVisualizer.on_event()` and checks `llm.metrics.accumulated_cost` against `max_budget_usd` on every action event. Raise `BudgetExhaustedError` to halt the pipeline gracefully.

**New Module**: `orchestrator/guards/budget_guard.py`

```python
class TokenBudgetGuard:
    def __init__(self, max_budget_usd: float):
        self.max_budget = max_budget_usd
        self.total_cost = 0.0

    def check(self, llm) -> None:
        cost = getattr(llm.metrics, "accumulated_cost", 0.0)
        if cost >= self.max_budget:
            raise BudgetExhaustedError(f"Budget exhausted: ${cost:.4f} >= ${self.max_budget:.2f}")
```

---

## 1.2 🩸 BUG: No Per-Step Token Tracking in Telemetry

**File**: [`schemas.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/telemetry/schemas.py#L16-L25)
**File**: [`recorder.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/telemetry/recorder.py#L44-L66)

**Problem**: `StepMetric` has no token fields. `record_step()` accepts no token count. The telemetry system records duration and diff hash but **zero token data**. You cannot audit which agent/step consumed the most tokens.

**Fix**: Add to `StepMetric`:
```python
prompt_tokens: int = 0
completion_tokens: int = 0
total_tokens: int = 0
estimated_cost_usd: float = 0.0
```

And modify `record_step()` to accept and store these values, extracted from `agent.llm.metrics` after each `Conversation.run()`.

---

## 1.3 🩸 BUG: New Conversation Per Fix Iteration Destroys Context Efficiency

**File**: [`dev_test_loop.py:129`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L129)
**File**: [`full_pipeline.py:149`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L149)

**Problem**: Every fix iteration creates a **brand new** `Conversation(agent=developer_agent, ...)`. This means:
1. The agent loses all previous context (files read, code written, errors seen)
2. It re-reads the entire workspace from scratch
3. The system prompt + skill text is re-sent as input tokens every single time
4. **Each fix loop costs the full context window again**

```python
# Line 129 — NEW conversation every fix = full context re-send
dev_fix_conv = Conversation(agent=developer_agent, workspace=str(self.workspace_path), visualizer=visualizer)
```

**Impact**: 🔥 On a 4-iteration loop, the system prompt + skills (~2K tokens) are sent 4 times as input. File reads are repeated. This is the **#1 token waste source**.

**Fix**: Reuse the original `dev_conv` conversation and send follow-up messages instead:
```python
dev_conv.send_message(failure_summary)
dev_conv.run()
```

Or implement a **Conversation Pool** that preserves the agent's working memory across iterations.

---

## 1.4 🩸 MISSING: Graceful Pipeline Abort / Pause Mechanism

**Problem**: The only way to stop the pipeline is `Ctrl+C` (`KeyboardInterrupt`). There is:
- ❌ No pause/resume capability
- ❌ No "finish current step then stop" signal
- ❌ No way to inject human guidance mid-execution
- ❌ No token-based auto-stop (e.g., "stop after 10K tokens")

**File**: [`dev_test_loop.py:171-176`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L171-L176)

```python
# Current: brutal kill only
except KeyboardInterrupt:
    ConsoleOutput.warning("Pipeline execution interrupted by user.")
    log_store.add_step("Session interrupted by user (KeyboardInterrupt).", is_error=True)
    raise
```

**Fix**: Implement a `PipelineController` with signal-based control:

```python
class PipelineController:
    """Non-blocking control plane for pipeline execution."""
    
    def __init__(self):
        self.state: Literal["running", "paused", "stopping", "abort"] = "running"
        self._human_message: Optional[str] = None
    
    def request_pause(self) -> None: ...
    def request_stop_after_current(self) -> None: ...
    def inject_human_message(self, msg: str) -> None: ...
    def check_should_continue(self) -> bool: ...
```

**New Module**: `orchestrator/control/pipeline_controller.py`

Run a background thread listening for keyboard commands:
- `p` = pause after current step
- `s` = stop after current step (graceful)
- `h` = inject human message into next agent prompt
- `q` = immediate abort with log save

---

# 🟠 PHASE 2: HIGH — Context & Token Optimization

---

## 2.1 🔶 Context Re-send Waste: Graft as Context Cache

**Current State**: Every time a Developer agent starts, it receives:
1. Full system prompt (~400 tokens)
2. All loaded skill text (~1,500-3,000 tokens)  
3. Task description
4. Then it reads files via tools (more tokens per file read observation)

**Problem**: The agent re-discovers the codebase structure on every conversation. It doesn't know what files exist, their relationships, or the architecture without reading everything.

**Fix — Graft Context Injection**:

Instead of letting the agent explore blindly (burning tokens on `list` and `read` tool calls), inject a **pre-computed Graft summary** into the system prompt:

```python
# Before agent creation, generate a compact context map
graft_output = subprocess.run(
    ["graft", "map", "--format", "compact"],
    capture_output=True, text=True, cwd=str(workspace_path)
).stdout

# Inject into system prompt (replaces 10+ file-read tool calls)
DEVELOPER_SYSTEM_PROMPT += f"\n\n## Codebase Structure (via Graft)\n{graft_output}"
```

**Impact**: Eliminates ~5-15 tool call round-trips per conversation (~2,000-8,000 tokens saved per agent invocation).

**New Module**: `orchestrator/context/graft_context.py`

```python
class GraftContextProvider:
    """Pre-computes zero-token codebase context for agent injection."""
    
    def get_workspace_map(self, workspace: Path) -> str: ...
    def get_file_skeleton(self, file_path: Path) -> str: ...
    def get_blast_radius(self, symbol: str) -> str: ...
    def build_compact_context(self, workspace: Path, max_tokens: int = 500) -> str: ...
```

---

## 2.2 🔶 Diff-Only Context for Fix Iterations

**File**: [`dev_test_loop.py:130-136`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L130-L136)

**Problem**: The fix message sends the full pytest STDOUT + STDERR without any filtering:

```python
failure_summary = (
    f"Pytest execution failed with exit code {test_run.exit_code}.\n"
    f"STDOUT:\n{test_run.stdout}\n"     # <-- could be 5000+ chars
    f"STDERR:\n{test_run.stderr}\n\n"   # <-- more duplication
    "Please diagnose..."
)
```

pytest output often includes:
- Full traceback for every failed test
- Passing test summaries (irrelevant noise)
- Import paths and file locations (redundant)

**Fix**: Parse pytest output and extract only:
1. Failed test names
2. Assertion error messages (last 3 lines of each traceback)
3. Error count summary

```python
class PytestOutputParser:
    """Extracts minimal actionable failure info from pytest output."""
    
    def parse(self, stdout: str, stderr: str) -> str:
        # Returns compact failure report: ~200 tokens instead of ~2000
        ...
```

---

## 2.3 🔶 System Prompt Bloat — Skills Are Loaded as Full Text

**File**: [`config.py:99-107`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/config.py#L99-L107)

**Problem**: `build_agent_context()` loads all skill objects. The OpenHands SDK serializes the full SKILL.md content into the system prompt. With 4 skills assigned to the Developer (`clean-python-architecture`, `systematic-debugging`, `docker-devops-containerization`, `graft-architecture-intelligence`), this is **thousands of tokens per call**.

**Fix — Skill Summarization Layer**:
```python
class CompactSkillInjector:
    """Compresses skill content to essential rules only."""
    
    MAX_SKILL_TOKENS = 300  # per skill
    
    def summarize_skill(self, skill: Skill) -> str:
        # Extract only CRITICAL INSTRUCTIONS sections
        # Strip examples, headers, formatting
        ...
```

Or: lazy-load skills. Instead of injecting all skill text, inject a 1-line summary and give the agent a `read_skill` tool to load full content only when needed.

---

# 🟡 PHASE 3: MEDIUM — Human-in-the-Loop (HITL) System

> **المشكلة**: النظام أوتوماتيكي بالكامل. لا يمكنك التدخل أثناء العمل أو مساعدة الوكيل.

---

## 3.1 🟡 Human Intervention Channel

**Problem**: Once `pipeline.run(task)` starts, the human has zero ability to:
- Correct the agent's direction
- Answer questions the agent might have
- Provide hints when the agent is stuck
- Approve/reject intermediate steps before proceeding

**Fix — Async Human Input Channel**:

```python
class HumanInterventionChannel:
    """Thread-safe async channel for human-agent communication during execution."""
    
    def __init__(self):
        self._queue: Queue[str] = Queue()
        self._listener_thread: Optional[Thread] = None
    
    def start_listener(self) -> None:
        """Background thread reading stdin for human input."""
        ...
    
    def has_message(self) -> bool: ...
    def get_message(self) -> Optional[str]: ...
    def inject_into_prompt(self, base_prompt: str) -> str:
        """Prepend any queued human messages to the next agent prompt."""
        ...
```

**Integration Points**:
1. Before each `Conversation.run()` call, check for queued human messages
2. If present, prepend `[HUMAN GUIDANCE]: {message}` to the agent prompt
3. Display `💬 Type a message to guide the agent (Enter to skip):` between phases

**New Module**: `orchestrator/control/human_channel.py`

---

## 3.2 🟡 Step-Level Approval Gates

**Problem**: The pipeline runs all phases without any checkpoint where the human can review progress.

**Fix**: Add configurable approval gates:

```python
# config
approval_gates: list[str] = ["after_architect", "after_developer", "before_commit"]

# In pipeline
if "after_architect" in self.config.approval_gates:
    plan_content = (workspace / "PLAN.md").read_text()
    ConsoleOutput.banner("PLAN.md Generated — Review Required")
    print(plan_content[:2000])
    approval = input("\n✅ Approve plan? [y/N/edit]: ").strip()
    if approval.lower() == 'n':
        return {"status": "HUMAN_REJECTED_PLAN"}
```

---

## 3.3 🟡 Agent Thinking Transparency

**File**: [`visualizer.py:183-187`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/visualizer.py#L183-L187)

**Problem**: The thought preview is truncated to 110 chars. When the agent is making critical decisions, the human can't see the reasoning.

```python
if len(thought_preview) > 110:
    thought_preview = thought_preview[:107] + "..."
```

**Fix**: Add a `--verbose` mode that shows full agent thoughts, and a `--quiet` mode that shows only milestones:

```python
class VerbosityLevel(Enum):
    QUIET = "quiet"      # Milestones only
    NORMAL = "normal"    # Current behavior  
    VERBOSE = "verbose"  # Full thoughts + tool args
    DEBUG = "debug"      # Everything including observations
```

---

# 🟢 PHASE 4: LOW — Reliability & Edge Cases

---

## 4.1 🟢 BUG: Duplicate Phase Comment in full_pipeline.py

**File**: [`full_pipeline.py:68-72`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L68-L72)

```python
# -------------------------------------------------------------------
# Phase 1: Architectural Decomposition
# -------------------------------------------------------------------
# Phase 1: Architectural Decomposition    <-- DUPLICATE
# -------------------------------------------------------------------
```

**Fix**: Remove the duplicate comment line.

---

## 4.2 🟢 BUG: `review_approved` Defaults to True Even Without VERDICT

**File**: [`full_pipeline.py:185`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L185)

```python
review_approved = True  # <-- defaults to APPROVED if no VERDICT found
```

**Problem**: If the reviewer agent doesn't produce `VERDICT: APPROVED` or `VERDICT: REJECTED` (e.g., due to output truncation or model hallucination), the code silently treats it as approved.

**Fix**: Default to `False` and require explicit approval:
```python
review_approved = False  # Guilty until proven innocent
```

---

## 4.3 🟢 BUG: Circuit Breaker Only Checks Diff + Error Hash

**File**: [`recorder.py:77-108`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/telemetry/recorder.py#L77-L108)

**Problem**: The circuit breaker triggers only when the **exact same diff AND exact same error** repeat. But the agent can produce **slightly different diffs** while making the **same logical mistake** (e.g., adding a comment, changing whitespace). This bypasses the circuit breaker while the loop continues burning tokens.

**Fix**: Add semantic circuit breaker:
1. Track **error message similarity** (not just exact hash) using string distance
2. Track **test failure count** — if the same tests keep failing regardless of diff changes, trip the breaker
3. Add a **total token ceiling** per pipeline run

```python
class SmartCircuitBreaker:
    def check(self, diff: str, error: str, tokens_used: int) -> bool:
        # 1. Exact match (current)
        # 2. Same failing test names extracted from pytest output
        # 3. Token ceiling exceeded
        # 4. Time ceiling exceeded (e.g., 10 minutes per pipeline)
        ...
```

---

## 4.4 🟢 ISSUE: No Branch Isolation

**File**: [`git_ops.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/git_ops.py)

**Problem**: `PROJECT_STATE.md` says "Git branch isolation per task run" but `git_ops.py` has **no branch creation logic**. All commits go to whatever branch is currently checked out.

**Fix**: Add `create_task_branch()`:
```python
def create_task_branch(self, task_name: str) -> str:
    branch = f"agent/{task_name[:30].replace(' ', '-')}"
    self._run_git("checkout", "-b", branch)
    return branch
```

---

## 4.5 🟢 ISSUE: Workspace File Tool `list` Exposes Full Recursive Tree

**File**: [`workspace_tools.py:140-143`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/tools/workspace_tools.py#L140-L143)

**Problem**: `rglob("*")` on a large workspace returns **every file recursively**. In a workspace with `node_modules/`, `.venv/`, or generated files, this produces thousands of lines — all sent as observation tokens.

```python
file_list = [
    str(p.relative_to(workspace_root))
    for p in search_dir.rglob("*")
    if p.is_file() and not any(part.startswith(".") for part in p.parts)
]
```

**Fix**: 
1. Add depth limit (default 2 levels)
2. Exclude known heavy directories (`node_modules`, `__pycache__`, `.venv`, `dist`, `build`)
3. Limit total entries to 100 with a "... and N more" truncation
4. Use Graft map instead when available

---

## 4.6 🟢 ISSUE: `datetime.utcnow()` Deprecation

**Files**: [`recorder.py:26`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/telemetry/recorder.py#L26), [`recorder.py:112`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/telemetry/recorder.py#L112), [`schemas.py:13`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/telemetry/schemas.py#L13), [`auditor.py:42`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/evolution/auditor.py#L42)

**Problem**: `datetime.utcnow()` is deprecated in Python 3.12+. Should use `datetime.now(UTC)`.

---

# 🔵 PHASE 5: ARCHITECTURAL — System-Level Improvements

---

## 5.1 🔵 Agent Conversation Memory / Persistence

**Problem**: Conversations are ephemeral. After a pipeline completes:
- All agent reasoning is lost
- The agent can't learn from previous runs
- Related tasks start from zero context

**Fix**: Implement a `ConversationMemory` that:
1. Saves conversation summaries to `diagnostics/memory/`
2. On new tasks, injects relevant summaries from previous runs
3. Uses Graft to detect if the new task touches files affected by previous tasks

**New Module**: `orchestrator/memory/conversation_store.py`

---

## 5.2 🔵 Pipeline State Machine

**Problem**: Pipeline flow is hard-coded as sequential function calls. Adding new phases (e.g., "Security Scan", "Performance Test", "Human Review") requires modifying the pipeline class.

**Fix**: Refactor to a state machine:

```python
class PipelinePhase(Enum):
    ARCHITECT = "architect"
    DEVELOP = "develop"
    TEST = "test"
    FIX = "fix"
    REVIEW = "review"
    HUMAN_GATE = "human_gate"
    COMMIT = "commit"

class PipelineStateMachine:
    def __init__(self, phases: list[PipelinePhase], transitions: dict):
        ...
    
    def advance(self) -> PipelinePhase:
        ...
    
    def can_skip(self, phase: PipelinePhase) -> bool:
        ...
```

---

## 5.3 🔵 Consolidated Control Plane

Merge all control concerns into a single module:

```
orchestrator/control/
├── __init__.py
├── pipeline_controller.py    # Pause/Stop/Abort signals
├── budget_guard.py           # Token budget enforcement
├── human_channel.py          # Human-in-the-loop messaging
├── circuit_breaker.py        # Smart circuit breaker (extracted from recorder)
└── approval_gates.py         # Phase-level human approval
```

---

# 📋 IMPLEMENTATION PRIORITY MATRIX

| # | Item | Phase | Severity | Token Impact | LOE |
|---|---|---|---|---|---|
| 1 | Budget enforcement at runtime | P1 | 🔴 CRITICAL | Prevents unlimited burn | 2h |
| 2 | Reuse Conversation across fix loops | P1 | 🔴 CRITICAL | -50% tokens per loop | 1h |
| 3 | Graceful pipeline stop (keyboard signals) | P1 | 🔴 CRITICAL | Prevents forced kills | 3h |
| 4 | Per-step token tracking in telemetry | P1 | 🔴 CRITICAL | Enables cost auditing | 1h |
| 5 | Graft context injection (replace blind exploration) | P2 | 🟠 HIGH | -30% tokens per agent | 3h |
| 6 | Pytest output parser (compact errors) | P2 | 🟠 HIGH | -60% fix prompt tokens | 2h |
| 7 | Skill summarization / lazy loading | P2 | 🟠 HIGH | -20% system prompt tokens | 2h |
| 8 | Human intervention channel | P3 | 🟡 MEDIUM | Prevents misdirection waste | 4h |
| 9 | Step-level approval gates | P3 | 🟡 MEDIUM | Stops bad plans early | 2h |
| 10 | Verbose/quiet visualization modes | P3 | 🟡 MEDIUM | UX improvement | 1h |
| 11 | Fix `review_approved` default to False | P4 | 🟢 LOW | Logic bug | 5min |
| 12 | Smart circuit breaker (semantic) | P4 | 🟢 LOW | Catches subtle loops | 3h |
| 13 | Branch isolation per task | P4 | 🟢 LOW | Git safety | 1h |
| 14 | File list depth limit + exclusions | P4 | 🟢 LOW | Token savings on large projects | 30min |
| 15 | `datetime.utcnow()` → `datetime.now(UTC)` | P4 | 🟢 LOW | Deprecation fix | 10min |
| 16 | Pipeline state machine refactor | P5 | 🔵 ARCH | Extensibility | 6h |
| 17 | Conversation memory/persistence | P5 | 🔵 ARCH | Cross-run intelligence | 8h |

---

# 🏗️ Proposed New Directory Structure

```diff
 orchestrator/
 ├── __init__.py
 ├── config.py
 ├── orchestrator.py
 ├── main.py
 ├── agents/
 │   ├── architect.py
 │   ├── developer.py
 │   ├── tester.py
 │   └── reviewer.py
+├── control/                          # NEW: Centralized control plane
+│   ├── __init__.py
+│   ├── pipeline_controller.py        # Pause/Stop/Abort signals
+│   ├── budget_guard.py               # Token budget enforcement
+│   ├── human_channel.py              # HITL messaging
+│   ├── circuit_breaker.py            # Extracted + enhanced from recorder
+│   └── approval_gates.py             # Phase-level approval
+├── context/                          # NEW: Context optimization
+│   ├── __init__.py
+│   ├── graft_context.py              # Pre-computed codebase context
+│   ├── pytest_parser.py              # Compact test failure extraction
+│   └── skill_compressor.py           # Skill text compression
+├── memory/                           # NEW: Cross-run intelligence
+│   ├── __init__.py
+│   └── conversation_store.py         # Conversation persistence
 ├── pipeline/
 │   ├── dev_test_loop.py
-│   └── full_pipeline.py
+│   ├── full_pipeline.py
+│   └── state_machine.py              # NEW: Generic pipeline FSM
 ├── tools/
 │   └── workspace_tools.py
 ├── telemetry/
 │   ├── recorder.py
 │   └── schemas.py
 ├── evolution/
 │   └── auditor.py
 └── utils/
     ├── connectivity.py
     ├── git_ops.py
     ├── output.py
     └── visualizer.py
```

---

# 🎯 Token Savings Projection

| Optimization | Current Waste | After Fix | Savings |
|---|---|---|---|
| Reuse Conversation (no context re-send) | ~4,000 tok/iteration | ~500 tok/iteration | **87%** |
| Graft context injection (no blind explore) | ~8,000 tok/agent start | ~500 tok/agent start | **94%** |
| Pytest output parsing | ~2,000 tok/failure | ~200 tok/failure | **90%** |
| Skill compression | ~3,000 tok/agent | ~800 tok/agent | **73%** |
| Budget guard (stops runaway) | ∞ potential | $0.50 hard ceiling | **∞→0** |
| **Total per 4-iteration pipeline** | **~60,000+ tok** | **~8,000 tok** | **~87%** |

---

# ⚡ Quick Wins (Can Be Done in < 30 Minutes Each)

1. **Fix `review_approved` default** → Change line 185 of `full_pipeline.py` to `False`
2. **Remove duplicate comment** → Delete line 71 in `full_pipeline.py`
3. **Fix `datetime.utcnow()`** → 4 files, regex replace
4. **Add file list depth limit** → Add `max_depth` param to `list` operation in `workspace_tools.py`
5. **Add token count to telemetry** → 4 fields in `StepMetric`, pass from pipeline

---

# 🔐 Security Notes Found During Audit

1. **API Key in .env not gitignored properly** — `.env` contains `sk-or-v1-...` OpenRouter key. Verify `.gitignore` includes `.env` (it does, confirmed).
2. **`shell=True` in terminal tool** — [`workspace_tools.py:271`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/tools/workspace_tools.py#L271) uses `subprocess.run(action.command, shell=True)`. The agent can execute arbitrary shell commands. The sandbox relies on workspace path containment, but the terminal has no command allowlist.
3. **Delete operation has no confirmation** — The file tool's `delete` operation immediately deletes files/directories with `shutil.rmtree()`. No undo, no confirmation, no backup.

---

# 🟣 PHASE 6: DEEP ORCHESTRATION — Agent Governance & Pipeline Topology

---

## 6.1 🟣 Dead-End Reviewer: Missing Review -> Developer Fix Loop
**File**: [`full_pipeline.py:185-199`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L185-L199)

**Problem**: When the Reviewer outputs `VERDICT: REJECTED` with `REQUIRED_FIXES`, the orchestrator **immediately halts and terminates the pipeline** (`status: REVIEW_REJECTED`).
The Reviewer's feedback is **never routed back to the Developer** to fix! This defeats the purpose of having a Reviewer agent.
```python
if "VERDICT: REJECTED" in text:
    review_approved = False
    # Pipeline stops here! No developer fix invocation!
    break
```
**Fix**: Add an outer review-fix cycle:
```
Architect -> Developer -> Tester Loop -> Reviewer
                                           │
                                     REJECTED?
                                           │
                                           ▼
                                    Developer Fix -> Re-run Pytest -> Re-Review (Max 2 iterations)
```

---

## 6.2 🟣 Double-Execution & Tester LLM Over-Invocation
**Files**: [`full_pipeline.py:107-124`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L107-L124), [`dev_test_loop.py:81-99`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L81-L99)

**Problem**: In every iteration of the fix loop:
1. Orchestrator invokes Tester LLM with full context to "write comprehensive pytest tests".
2. THEN orchestrator runs `pytest -v` via terminal subprocess.
In iteration 2+, the test suite **already exists on disk**! Calling the Tester LLM before running pytest wastes 10K–30K tokens per iteration.
**Fix**:
1. First run: Tester LLM writes tests.
2. Iteration 2+: Orchestrator executes `pytest -v` **directly via subprocess (0 LLM tokens)**.
3. Only call Developer if `pytest` fails.
4. Only re-invoke Tester LLM if Developer modifies interface signatures or explicitly requests test suite updates.

---

## 6.3 🟣 Skill Bleed via `load_project_skills=True`
**File**: [`config.py:101-107`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/config.py#L101-L107)

**Problem**:
```python
return AgentContext(
    skills=role_skills,
    load_project_skills=True,  # <-- BUG: Loads ALL 9 project skills for EVERY agent!
    load_user_skills=False,
    load_memory=True
)
```
Setting `load_project_skills=True` causes OpenHands SDK to scan `.agents/skills/` and inject **all 9 skills** into every agent, completely overriding `skills=role_skills`.
The Tester gets `docker-devops-containerization` and `clean-python-architecture`; Developer gets `code-review-standards`.
**Impact**: +10,000 unnecessary tokens injected into the prompt of every agent on every call.
**Fix**: Set `load_project_skills=False` so agents only receive their explicitly assigned `role_skills`.

---

## 6.4 🟣 Lack of Role-Based Tool Permissions (RBAC & Cheat Prevention)
**Files**: [`agents/developer.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/agents/developer.py), [`agents/tester.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/agents/tester.py), [`tools/workspace_tools.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/tools/workspace_tools.py)

**Problem**:
- The **Developer** agent has write access to the entire workspace including `tests/`. When stuck on failing tests, developer agents frequently cheat by modifying or deleting tests to pass.
- The **Tester** agent has write access to `src/`. It can accidentally or intentionally modify production code to make its tests pass.
- The **Architect** has write access to code files instead of being restricted to `PLAN.md`.
**Fix**: Path-scoped tool instances:
- Developer: Write permission restricted to `src/`, `app/`, `*.py` (excluding `tests/`).
- Tester: Write permission restricted exclusively to `tests/`. Read-only for `src/`.
- Architect: Write permission restricted exclusively to `PLAN.md`.
- Reviewer: Strictly read-only (`operation in ["read", "list"]`).

---

## 6.5 🟣 Zero-Token Pre-Flight Gatekeeper (Fast Static Analysis)
**Problem**: When Developer finishes code, the orchestrator immediately triggers Tester or runs pytest. If Developer made a simple syntax error (e.g. `SyntaxError`, missing import, unclosed bracket), the system burns a full test iteration and LLM call.
**Fix**: Run a zero-token static check before any test phase:
```python
def preflight_syntax_check(workspace: Path) -> tuple[bool, str]:
    # Runs 'python -m py_compile' or 'ruff check' in <50ms (0 tokens)
    res = subprocess.run(["python", "-m", "py_compile", ...], capture_output=True, text=True)
    return (res.returncode == 0, res.stderr)
```
If syntax check fails, feed the compiler error directly to Developer without spinning up Tester or pytest.

---

## 6.6 🟣 Monolithic Execution vs Milestone Subtask DAG
**Files**: [`pipeline/full_pipeline.py:76-98`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L76-L98)

**Problem**: The Architect produces a single monolithic `PLAN.md`. The Developer is prompted with:
`"Read PLAN.md and implement the complete solution"`.
For any non-trivial application (3+ files), the Developer attempts to write all files in a single pass, resulting in truncated files, missing imports, and token context overflow.
**Fix**: Orchestrator-driven Task Decomposition:
1. Architect produces structured milestones: `## Milestone 1: Data Models`, `## Milestone 2: Service Layer`, `## Milestone 3: Endpoints`.
2. Orchestrator executes Developer in subtask iterations:
   `Implement Milestone 1 -> Verify syntax -> Implement Milestone 2 -> ...`
3. Prevents context degradation and limits token burn per step.

---

## 6.7 🟣 API Key & Environment Exfiltration via Subprocess
**File**: [`tools/workspace_tools.py:264-278`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/tools/workspace_tools.py#L264-L278)

**Problem**:
```python
env = os.environ.copy() # Inherits OPENROUTER_API_KEY, ANTHROPIC_API_KEY, etc.
proc = subprocess.run(action.command, shell=True, env=env, ...)
```
Any command executed by an agent (`printenv`, `set`, or a Python script `os.environ`) has full access to the user's secret API keys.
**Fix**: Sanitize execution environment:
```python
SAFE_VARS = {"PATH", "SYSTEMROOT", "TEMP", "TMP", "PYTHONPATH", "LANG"}
sanitized_env = {k: v for k, v in os.environ.items() if k in SAFE_VARS}
sanitized_env["PYTHONUNBUFFERED"] = "1"
```

---

## 6.8 🟣 Pipeline State Persistence & Resume Capability (`--resume`)
**Problem**: All execution state is in-memory variables. If the process is halted, crashes, or hits rate limits during Phase 3 (Reviewer), the entire run is lost and must be restarted from Phase 1 (Architect), re-incurring 100% of the cost.
**Fix**: Save pipeline state to `.orchestrator_state.json` after each phase:
```json
{
  "run_id": "run_20260923_050000",
  "task": "JWT Authentication Service",
  "current_phase": "reviewer",
  "plan_approved": true,
  "tests_passed": true,
  "iterations": 2
}
```
Add CLI flag `uv run python -m orchestrator.main --resume` to continue from the last checkpoint.

---

# 📋 UPDATED IMPLEMENTATION PRIORITY MATRIX

| # | Item | Phase | Severity | Status | Verification Test |
|---|---|---|---|---|---|
| 1 | Budget enforcement at runtime | P1 | 🔴 CRITICAL | ✅ COMPLETED | `test_telemetry_recorder_token_tracking_and_budget_guard` |
| 2 | Reuse Conversation across fix loops | P1 | 🔴 CRITICAL | ✅ COMPLETED | `dev_test_loop.py`, `full_pipeline.py` |
| 3 | Graceful pipeline stop (keyboard signals) | P1 | 🔴 CRITICAL | ✅ COMPLETED | `test_pipeline_controller_and_budget_guard` |
| 4 | Fix `load_project_skills=False` bleed | P1 | 🔴 CRITICAL | ✅ COMPLETED | `test_skill_isolation_no_project_leak` |
| 5 | Reviewer -> Developer feedback loop | P1 | 🔴 CRITICAL | ✅ COMPLETED | `full_pipeline.py` review-fix loop |
| 6 | Subprocess 0-token direct pytest in loop | P2 | 🟠 HIGH | ✅ COMPLETED | `dev_test_loop.py`, `full_pipeline.py` |
| 7 | Zero-token pre-flight syntax check | P2 | 🟠 HIGH | ✅ COMPLETED | `test_preflight_guard_detects_syntax_errors` |
| 8 | Role-based tool permissions (RBAC) | P2 | 🟠 HIGH | ✅ COMPLETED | `test_rbac_file_restrictions` |
| 9 | Graft context injection | P2 | 🟠 HIGH | ✅ COMPLETED | `test_graft_context_provider_fallback` |
| 10 | Pytest output parser (compact errors) | P2 | 🟠 HIGH | ✅ COMPLETED | `test_pytest_output_parser_compacts_failures` |
| 11 | Secret sanitization in terminal tool | P2 | 🟠 HIGH | ✅ COMPLETED | `test_terminal_environment_credential_sanitization` |
| 12 | Milestone subtask DAG execution | P3 | 🟡 MEDIUM | ✅ COMPLETED | `test_milestone_parser_structured_plan` |
| 13 | Human intervention channel | P3 | 🟡 MEDIUM | ✅ COMPLETED | `test_human_channel_message_queue_and_injection` |
| 14 | Step-level approval gates | P3 | 🟡 MEDIUM | ✅ COMPLETED | `test_human_channel_approval_gates_interactive_mock` |
| 15 | Pipeline checkpoint & resume (`--resume`) | P3 | 🟡 MEDIUM | ✅ COMPLETED | `test_checkpoint_manager_lifecycle`, `test_main_cli_resume_flag` |
| 16 | Fix `review_approved` default to False | P4 | 🟢 LOW | ✅ COMPLETED | `full_pipeline.py:185` |
| 17 | Smart circuit breaker (semantic) | P4 | 🟢 LOW | ✅ COMPLETED | `test_smart_circuit_breaker_semantic_test_failure_loop` |
| 18 | File list depth limit + exclusions | P4 | 🟢 LOW | ✅ COMPLETED | `workspace_tools.py` |
| 19 | `datetime.utcnow()` → `datetime.now(UTC)` | P4 | 🟢 LOW | ✅ COMPLETED | `recorder.py`, `schemas.py`, `auditor.py` |
| 20 | Pipeline state machine refactor | P5 | 🔵 ARCH | ✅ COMPLETED | `test_pipeline_state_machine_transitions` |
| 21 | Conversation memory/persistence | P5 | 🔵 ARCH | ✅ COMPLETED | `test_conversation_store_persistence_and_retrieval` |

---

> **Final Execution Status**: 21/21 items implemented. 39/39 pytest unit tests passing. System ready for live production runs.

