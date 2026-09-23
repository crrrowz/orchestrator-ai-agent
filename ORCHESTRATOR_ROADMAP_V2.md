# 🗺️ Orchestrator-AI-Agent — Internal Development Roadmap V2

> **Scope**: تحليل داخلي عميق ثاني — بعد اكتمال جميع الـ 21 تطوير سابق. هذه الخارطة تبني على الكود الحالي فعلياً.
>
> **Generated**: 2026-09-23 | **Audit Source**: 24 Python source files, 10 test files (39/39 ✅), 9 skills, full pipeline flow analysis

---

## 📊 Current State After V1 Roadmap

| Metric | Value |
|---|---|
| Source Files | 24 Python modules (↑33% from 18) |
| Total LOC | ~4,200 lines |
| Unit Tests | **39/39 passing** (10 test files) |
| Modules | `agents/`, `pipeline/`, `tools/`, `telemetry/`, `control/`, `guards/`, `memory/`, `evolution/`, `utils/` |
| V1 Items Completed | **21/21** ✅ |

---

## ✅ V1 MATRIX VERIFICATION — Previous 17 Items Audit

> كل عنصر من العناصر الـ 17 السابقة تم التحقق منه عبر الكود المصدري + الاختبارات.

| # | Item | Status | Verification Evidence |
|---|---|---|---|
| 1 | Budget enforcement at runtime | ✅ **REAL** | [`recorder.py:110-123`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/telemetry/recorder.py#L110-L123) — `check_budget()` called at 5 checkpoints in both pipelines. [`budget_guard.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/control/budget_guard.py) exists as standalone class. |
| 2 | Reuse Conversation across fix loops | ✅ **REAL** | [`dev_test_loop.py:244`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L244) — `dev_conv.send_message()` reuses conversation. No `Conversation()` constructor in fix loop. |
| 3 | Graceful pipeline stop (keyboard signals) | ⚠️ **PARTIAL** | [`pipeline_controller.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/control/pipeline_controller.py) exists with pause/stop/abort states, but **is never instantiated or called** by either `dev_test_loop.py` or `full_pipeline.py`. Dead code. Pipelines still rely on bare `except KeyboardInterrupt`. |
| 4 | Per-step token tracking in telemetry | ✅ **REAL** | [`schemas.py:26-29`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/telemetry/schemas.py#L26-L29) — `StepMetric` has `prompt_tokens`, `completion_tokens`, `total_tokens`, `estimated_cost_usd`. All `record_step()` calls pass token data. |
| 5 | Graft context injection | ✅ **REAL** | [`dev_test_loop.py:84`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L84) — `GraftContextProvider.get_compact_map()` called and injected into prompt. Graceful `None` fallback if graft not installed. |
| 6 | Pytest output parser (compact errors) | ✅ **REAL** | [`pytest_parser.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/pytest_parser.py) — `PytestOutputParser.extract_compact_failures()` used at [`dev_test_loop.py:238`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L238). |
| 7 | Skill summarization / lazy loading | ✅ **REAL** | [`skill_compressor.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/skill_compressor.py) — `CompactSkillInjector.create_compact_skill()` called in [`config.py:107`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/config.py#L107). Max 800 chars/skill. |
| 8 | Human intervention channel | ✅ **REAL** | [`human_channel.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/control/human_channel.py) — Queue-based, `inject_into_prompt()` used in both pipelines. Enabled via `--interactive`. |
| 9 | Step-level approval gates | ✅ **REAL** | [`human_channel.py:63-97`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/control/human_channel.py#L63-L97) — `prompt_gate()` called at `after_architect`, `after_developer`, `before_commit` in both pipelines. |
| 10 | Verbose/quiet visualization modes | ✅ **REAL** | [`visualizer.py:123`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/visualizer.py#L123) — `self.verbosity` checked at lines 189-196. `--verbose`, `--quiet` CLI flags in [`main.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/main.py#L83-L91). |
| 11 | Fix `review_approved` default to False | ✅ **REAL** | [`full_pipeline.py:345`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L345) — `review_approved = False`. |
| 12 | Smart circuit breaker (semantic) | ✅ **REAL** | [`recorder.py:125-176`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/telemetry/recorder.py#L125-L176) — 3-way detection: exact hash, failing test names, and `SequenceMatcher` similarity ≥0.88. |
| 13 | Branch isolation per task | ✅ **REAL** | [`git_ops.py:79-101`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/git_ops.py#L79-L101) — `create_task_branch()` generates `agent/<slug>-<timestamp>`. Called at start of both pipelines. |
| 14 | File list depth limit + exclusions | ✅ **REAL** | [`workspace_tools.py:175-182`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/tools/workspace_tools.py#L175-L182) — `ignored_dirs` set + 100-file cap with truncation message. |
| 15 | `datetime.utcnow()` → `datetime.now(UTC)` | ✅ **REAL** | All files use `datetime.now(timezone.utc)`. Zero `utcnow()` calls remain. |
| 16 | Pipeline state machine refactor | ⚠️ **EXISTS BUT UNUSED** | [`state_machine.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/state_machine.py) — `PipelineStateMachine` class is defined and tested, but **never imported or used** by `full_pipeline.py` or `dev_test_loop.py`. |
| 17 | Conversation memory/persistence | ✅ **REAL** | [`conversation_store.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/memory/conversation_store.py) — `save_run_memory()` + `format_memory_context()` called in both pipelines. Relevance-ranked retrieval via word overlap + file overlap scoring. |

---

## 🔍 V1 DEAD CODE IDENTIFIED

> الكود التالي موجود ومختبر لكنه **غير مستخدم فعلياً** في التنفيذ:

### DC-1: `PipelineController` — Dead Module
- **File**: [`pipeline_controller.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/control/pipeline_controller.py)
- **Problem**: Has `request_pause()`, `resume()`, `request_stop_after_current()`, `request_abort()`, `check_should_continue()` — none called anywhere.
- **Fix**: Either wire it into the pipeline loop (`while iteration <= max and controller.check_should_continue():`) or delete it.

### DC-2: `PipelineStateMachine` — Dead Module  
- **File**: [`state_machine.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/state_machine.py)
- **Problem**: Has a full FSM with transitions graph. Never imported by any pipeline.
- **Fix**: Either refactor pipelines to use FSM transitions, or remove.

### DC-3: `BudgetGuard` — Redundant with `TelemetryRecorder.check_budget()`
- **File**: [`budget_guard.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/control/budget_guard.py)
- **Problem**: `TelemetryRecorder.check_budget()` does the same thing inline. `BudgetGuard` is never used.
- **Fix**: Consolidate into `TelemetryRecorder` or replace `check_budget()` with `BudgetGuard` usage.

### DC-4: `MilestoneParser` — Defined But Not Executed
- **File**: [`milestone_dag.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/milestone_dag.py)
- **Problem**: `MilestoneParser.parse_plan()` exists and is tested, but `full_pipeline.py` still sends `"Read PLAN.md and implement the complete solution"` — monolithic prompt. No milestone-by-milestone iteration.
- **Fix**: After architect phase, parse PLAN.md into milestones and loop Developer per milestone.

---

# 🔴 PHASE 7: CRITICAL — Architectural Integrity & Runtime Safety

---

## 7.1 🔴 CRITICAL: Tester LLM Over-Invocation Still Active

**Files**: [`dev_test_loop.py:169-183`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L169-L183), [`full_pipeline.py:235-245`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L235-L245)

**Problem**: In iteration 2+, the code calls `tester_conv.send_message(...)` + `tester_conv.run()` **before** running `pytest -v` via subprocess. This means the Tester LLM is invoked every iteration even when all we need is to execute existing tests.

```python
# Iteration 2+: This WASTES an entire LLM call
tester_conv.send_message(
    f"Iteration {iteration}: Developer updated the code to address previous failures. "
    "Run pytest -v to re-verify the test suite. If needed, update tests."
)
tester_conv.run()  # <-- 5K-15K tokens burned

# THEN we also run pytest directly:
test_run = execute_terminal_action(
    WorkspaceTerminalAction(command="pytest -v", timeout_seconds=60),
    base_dir=self.workspace_path,
)
```

**Impact**: 🔥 **Double-cost per iteration**. The Tester LLM runs `pytest` internally via its own tool AND then the orchestrator runs it again via subprocess. Iteration 2+ should skip the Tester LLM entirely.

**Fix**: 
```python
if iteration == 1:
    # Tester creates test suite
    tester_conv.send_message(...)
    tester_conv.run()
else:
    # Skip Tester LLM — just run pytest directly (0 tokens)
    pass

test_run = execute_terminal_action(...)
```

Only re-invoke Tester if Developer modifies interface signatures (detectable via diff analysis on `def `, `class `, imports).

**Savings**: ~10K-30K tokens per fix iteration.

---

## 7.2 🔴 CRITICAL: Workspace Path Constraint — External Projects Cannot Be Developed

> **سؤالك**: هل يستطيع النظام تطوير مشروع خارجي عبر مساره أم يحتاج أن يكون داخل فولدر `orchestrator-ai-agent`؟

**Answer**: النظام حالياً **يستطيع** العمل على أي مسار خارجي عبر `--workspace` argument:

```bash
uv run python -m orchestrator.main "Add JWT auth" --workspace "D:\MyProject"
```

**لكن هناك مشاكل حقيقية عند استخدام مسارات خارجية:**

### Problem A: `SkillManager` Always Reads from `Path.cwd()`
**File**: [`orchestrator.py:16`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/orchestrator.py#L16), [`main.py:201`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/main.py#L201)

```python
# orchestrator.py:16
self.skill_manager = SkillManager(Path.cwd())

# main.py:201
skill_manager = SkillManager(Path.cwd())
```

`SkillManager` scans `.agents/skills/` relative to `Path.cwd()`. If the user runs the orchestrator from a different directory, or if the external project has its own `.agents/skills/`, the skills won't load.

**Fix**: Pass `project_root` explicitly based on the package install location:
```python
ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent
self.skill_manager = SkillManager(ORCHESTRATOR_ROOT)
```

### Problem B: `diagnostics/` Written Relative to CWD
**Files**: [`recorder.py:48`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/telemetry/recorder.py#L48), [`visualizer.py:99`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/visualizer.py#L99), [`conversation_store.py:27`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/memory/conversation_store.py#L27)

```python
self.reports_dir = (reports_dir or Path("diagnostics/reports")).resolve()  # CWD-relative!
```

Reports, logs, and memory are saved to wherever the user launched the command. On external projects, these files land in the wrong directory.

**Fix**: All `diagnostics/` paths should resolve relative to the orchestrator package root, not CWD:
```python
ORCHESTRATOR_DATA = Path(__file__).resolve().parent.parent / "diagnostics"
```

### Problem C: `PreFlightGuard.check_syntax()` Scans Entire Workspace Recursively
**File**: [`preflight.py:16-17`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/guards/preflight.py#L16-L17)

On large external projects with hundreds of Python files, `rglob("*.py")` + `py_compile.compile()` could take seconds or crash on intentionally invalid files (e.g., template files).

**Fix**: Limit to files changed since last git commit:
```python
def check_syntax_changed_only(workspace: Path) -> Tuple[bool, str]:
    # Only compile files in `git diff --name-only`
    changed = subprocess.run(["git", "diff", "--name-only"], ...)
    py_files = [workspace / f for f in changed if f.endswith(".py")]
```

### Problem D: Missing `conftest.py` / `pyproject.toml` Detection for External Projects
The orchestrator runs `pytest -v` assuming it can find tests. External projects may have their own `pyproject.toml` with different `testpaths`, `pythonpath`, or `conftest.py` that conflicts.

**Fix**: Before running pytest, detect and use the project's own test configuration:
```python
if (workspace / "pyproject.toml").exists():
    pytest_cmd = "pytest -v"  # Use project's own config
elif (workspace / "tests").exists():
    pytest_cmd = "pytest tests/ -v"
else:
    pytest_cmd = "python -m pytest -v"
```

---

## 7.3 🔴 No Error Recovery When `Conversation.run()` Raises

**Files**: [`dev_test_loop.py:100`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L100), [`full_pipeline.py:113`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L113)

**Problem**: If `Conversation.run()` throws an API error (rate limit, timeout, model unavailable), the entire pipeline crashes via the generic `except Exception as e` block. No retry, no fallback, no checkpoint save.

The `create_llm_for_role()` has `num_retries=2` at the LLM level, but if the conversation runner itself has an unrecoverable error, there's no recovery.

**Fix**: Wrap each `conv.run()` with retry + checkpoint:
```python
MAX_CONV_RETRIES = 2
for attempt in range(MAX_CONV_RETRIES + 1):
    try:
        conv.run()
        break
    except Exception as e:
        if attempt < MAX_CONV_RETRIES:
            ConsoleOutput.warning(f"Conversation failed (attempt {attempt+1}): {e}. Retrying...")
            time.sleep(2 ** attempt)
        else:
            PipelineCheckpointManager.save(...)
            raise
```

---

## 7.4 🔴 `--resume` Loads Checkpoint But Doesn't Skip Completed Phases

**File**: [`main.py:220-236`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/main.py#L220-L236)

**Problem**: When `--resume` is used, the code loads the checkpoint to get `task` and `mode`, but then passes them to `orchestrator.run_task()` which starts **from scratch**. The `completed_phases` from the checkpoint are never checked.

```python
# main.py:226-228 — loads checkpoint...
task = cp.task
mode = cp.mode
workspace = target_ws
# ...then creates a FRESH pipeline that ignores completed_phases
orchestrator.run_task(task=task, mode=mode, workspace_override=workspace)
```

**Impact**: `--resume` re-runs the entire pipeline from Phase 1 (Architect), wasting all previously burned tokens.

**Fix**: Pass checkpoint to pipeline constructor and skip completed phases:
```python
pipeline = FullPipeline(config, skill_manager, ws, checkpoint=cp)
# Inside pipeline.run():
if "architect" in self.checkpoint.completed_phases:
    ConsoleOutput.success("Architect phase already completed. Skipping...")
```

---

# 🟠 PHASE 8: HIGH — Token Efficiency Deep Cuts

---

## 8.1 🟠 Memory Injection Bloats Every First Prompt

**Files**: [`dev_test_loop.py:88-90`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L88-L90), [`full_pipeline.py:100-102`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L100-L102)

**Problem**: `ConversationStore.format_memory_context()` is called on every pipeline start and injected into the very first prompt. After multiple runs, this adds up to 1,500 chars (~375 tokens) of "HISTORICAL EXECUTION MEMORY" that may have zero relevance to the current task.

**Current relevance scoring**: Word overlap using regex `\w{3,}` — extremely naive. Common words like "implement", "create", "class", "service", "python" will match every past task.

**Fix**:
1. Increase minimum word length to 5+ chars for matching
2. Require minimum 3 overlapping words (not just 1) 
3. Only inject if relevance score > threshold (e.g., 8.0)
4. Add a `--no-memory` CLI flag to disable entirely

---

## 8.2 🟠 Graft Index Rebuilt On Every Pipeline Start

**File**: [`graft_context.py:18-32`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/graft_context.py#L18-L32), [`graft_context.py:41`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/graft_context.py#L41)

**Problem**: `get_compact_map()` calls `build_index()` every time, which runs `graft build` — a potentially 5-15s process on large repositories. On the second pipeline run, the index already exists but gets rebuilt anyway.

**Fix**: Check for index freshness before rebuilding:
```python
@classmethod
def build_index(cls, workspace: Path, force: bool = False) -> bool:
    index_dir = workspace / "graft"
    if not force and index_dir.exists() and (time.time() - index_dir.stat().st_mtime < 300):
        return True  # Index is fresh (< 5 min)
    # ... run graft build
```

---

## 8.3 🟠 Diff Sent to Reviewer Can Be Massive

**File**: [`full_pipeline.py:333-339`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L333-L339)

**Problem**: The Reviewer receives the full `git diff` in its prompt. On a multi-file implementation, this can be thousands of lines. The Reviewer's LLM context fills with raw diff characters instead of reviewable code.

```python
git_diff = self.git.get_diff() or self.git.get_status()
reviewer_conv.send_message(
    f"Task: {task_description}\n\n"
    f"Git Changes:\n{git_diff}\n\n"  # <-- Could be 50K+ chars
    ...
)
```

**Fix**: Truncate diff to essential parts (stat summary + first N lines per file):
```python
def get_compact_diff(self, max_lines_per_file: int = 50) -> str:
    stat = self._run_git("diff", "--stat").stdout
    diff = self._run_git("diff", "--unified=3").stdout
    # Truncate each file diff to max_lines_per_file
    ...
    return f"Diff Summary:\n{stat}\n\nDetailed Changes:\n{truncated_diff}"
```

---

## 8.4 🟠 No Token Cost Estimation Before Execution

**Problem**: The user has no idea how many tokens a task will consume before starting. Free-tier models have 1000 requests/day limits. There's no pre-execution estimate.

**Fix**: Add a `--estimate` CLI flag:
```python
# main.py
parser.add_argument("--estimate", action="store_true",
    help="Estimate token usage without executing.")
```
Calculate based on: system prompt size × agent count × estimated iterations.

---

# 🟡 PHASE 9: MEDIUM — Robustness & Developer Experience

---

## 9.1 🟡 No Timeout on `Conversation.run()`

**Problem**: If the LLM enters an infinite tool-call loop (reading file → confused → reading same file → ...), `Conversation.run()` blocks forever. There's no wall-clock timeout.

**Fix**: Add a `max_runtime_seconds` parameter and use a threading timer:
```python
import signal
import threading

def run_with_timeout(conv, timeout_seconds=300):
    timer = threading.Timer(timeout_seconds, lambda: conv.cancel())
    timer.start()
    try:
        conv.run()
    finally:
        timer.cancel()
```

---

## 9.2 🟡 Session Log Saves On Every Step (I/O Storm)

**File**: [`visualizer.py:92-95`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/visualizer.py#L92-L95)

**Problem**: `add_step()` calls `self.save_to_file()` after every single step. On a 50-step pipeline, that's 50 JSON serialization + file write operations.

```python
try:
    self.save_to_file()  # Called on EVERY step
except Exception:
    pass
```

**Fix**: Save on milestones only, or use a debounced writer:
```python
def add_step(self, ...):
    # ... add step ...
    if len(self.steps) % 10 == 0:  # Save every 10 steps
        self.save_to_file()
```
Final save is always done in `dev_test_loop.py:326` / `full_pipeline.py:516`.

---

## 9.3 🟡 `shell=True` in Terminal Tool — Command Injection Still Possible

**File**: [`workspace_tools.py:339-349`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/tools/workspace_tools.py#L339-L349)

**Problem**: Environment variables are sanitized (good), but `shell=True` with an agent-controlled command string is still a security risk. The agent can run `curl`, `wget`, `powershell -c`, or any destructive command.

**Fix — Command Allowlist**:
```python
ALLOWED_COMMANDS = {"pytest", "python", "pip", "uv", "git", "ruff", "mypy", "graft", "ls", "dir", "cat", "type"}

def validate_command(command: str) -> bool:
    base_cmd = command.strip().split()[0].lower()
    return base_cmd in ALLOWED_COMMANDS
```

---

## 9.4 🟡 Architect `allowed_write_prefixes=["PLAN.md"]` Too Restrictive

**File**: [`architect.py:40`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/agents/architect.py#L40)

**Problem**: `allowed_write_prefixes=["PLAN.md"]` uses prefix matching via `rel_posix.startswith("PLAN.md")`. This only allows writing to exactly `PLAN.md` but also accidentally allows `PLAN.md.bak`, `PLAN.md2`, etc. More importantly, it blocks the Architect from writing to subdirectories like `docs/architecture.md` if the architect skill recommends it.

**Fix**: Use exact match for single-file restrictions:
```python
file_tool = create_workspace_file_tool(workspace, allowed_write_files=["PLAN.md"])
```

---

## 9.5 🟡 `InteractiveLogExplorer` Blocks Pipeline Completion

**Files**: [`dev_test_loop.py:302`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L302), [`full_pipeline.py:492`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L492)

**Problem**: After pipeline completion, `InteractiveLogExplorer(log_store).run()` is called, which enters a blocking `while True` keyboard loop. If the orchestrator is called programmatically (e.g., from another Python script or CI), it hangs forever waiting for keyboard input.

```python
InteractiveLogExplorer(log_store).run()  # <-- Blocks forever in non-interactive mode

return {  # <-- This return is never reached in CI
    "status": status_str,
    ...
}
```

**Fix**: Only launch explorer if stdin is interactive:
```python
if sys.stdin.isatty():
    InteractiveLogExplorer(log_store).run()
```

---

## 9.6 🟡 `sandbox_demo/` Contains Orphaned Test Files

**Problem**: `sandbox_demo/` has `test_domain.py` and `test_rate_limiter.py` at the root level (not in `tests/`), a `-p` directory (likely a pytest artifact from incorrect argument parsing), and `conftest.py` — all generated by a previous agent run. These files may interfere with the orchestrator's own `pytest` execution if run from the project root.

**Fix**: Clean up or `.gitignore` the `sandbox_demo/` directory.

---

# 🟢 PHASE 10: LOW — Code Quality & Polish

---

## 10.1 🟢 `connectivity.py` Uses `httpx` — Not in `pyproject.toml`

**File**: [`connectivity.py:4`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/connectivity.py#L4)

**Problem**: `import httpx` is used for connectivity checks, but `httpx` is not listed in `pyproject.toml` dependencies. It works because `openhands-sdk` pulls it transitively, but this is an implicit dependency.

**Fix**: Add `httpx>=0.27.0` to `[project.dependencies]`.

---

## 10.2 🟢 `ConsoleOutput.summary_table()` Missing Token/Cost Data

**File**: [`output.py:51-62`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/output.py#L51-L62)

**Problem**: The summary table shows Status, Iterations, and Git Commit but **not** total tokens consumed or total cost. This is the most important information for the user.

**Fix**: Add parameters and rows:
```python
def summary_table(iterations: int, status: str, commit_hash: str = "",
                  total_tokens: int = 0, total_cost: float = 0.0) -> None:
    ...
    table.add_row("Total Tokens", f"{total_tokens:,}")
    table.add_row("Total Cost", f"${total_cost:.4f}")
```

---

## 10.3 🟢 `PowerShellHistory.txt` Checked Into Git

**Problem**: `PowerShellHistory.txt` exists in the project root. This file contains shell command history and should be in `.gitignore`.

---

## 10.4 🟢 `__init__.py` Suppresses Logs at Module Import Time

**File**: [`__init__.py:1-9`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/__init__.py#L1-L9)

**Problem**: Log suppression runs at import time via side effects in `__init__.py`. This affects any code that imports `orchestrator` as a library, not just CLI usage.

**Fix**: Move log suppression to `main.py` only (where it already exists at lines 7-19).

---

## 10.5 🟢 No `.env.example` Includes `MAX_BUDGET_USD`

**File**: [`.env.example`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/.env.example)

**Problem**: `.env.example` doesn't document `MAX_BUDGET_USD`, `CIRCUIT_BREAKER_THRESHOLD`, `INTERACTIVE`, `APPROVAL_GATES`, or `VERBOSITY` — all config values that exist in `OrchestratorConfig`.

---

# 🔵 PHASE 11: ARCHITECTURAL — System-Level Redesign

---

## 11.1 🔵 Wire Dead Code Into Pipeline Execution

Consolidate and activate the 4 dead-code modules into a single control flow:

```python
# At pipeline init:
self.controller = PipelineController()
self.budget_guard = BudgetGuard(config.max_budget_usd)
self.state_machine = PipelineStateMachine()

# At each iteration:
if not self.controller.check_should_continue():
    break
self.state_machine.transition_to(PipelinePhase.TEST)
```

This replaces ad-hoc `if` checks scattered across 500+ lines with a unified control plane.

---

## 11.2 🔵 Milestone-Driven Execution (Activate `MilestoneParser`)

Replace the monolithic Developer prompt with milestone iteration:

```python
# After Architect phase
plan_text = (self.workspace_path / "PLAN.md").read_text()
milestones = MilestoneParser.parse_plan(plan_text)

for milestone in milestones:
    dev_conv.send_message(
        f"Implement Milestone {milestone.index}: {milestone.title}\n\n"
        f"{milestone.content}\n\n"
        f"Target files: {', '.join(milestone.target_files)}"
    )
    dev_conv.run()
    
    # Verify syntax after each milestone
    syntax_ok, err = PreFlightGuard.check_syntax(self.workspace_path)
    if not syntax_ok:
        dev_conv.send_message(f"Syntax error after milestone {milestone.index}:\n{err}")
        dev_conv.run()
```

**Impact**: Prevents context overflow on complex tasks. Each milestone uses a focused prompt instead of "implement everything".

---

## 11.3 🔵 Pipeline as Plugin Architecture

Current code duplication between `dev_test_loop.py` (328 lines) and `full_pipeline.py` (518 lines) is ~60% identical. Both share:
- Git init + branch creation
- Graft context injection
- Memory injection
- Budget checks
- Checkpoint saves
- Fix iteration loop
- Commit logic
- Log explorer

**Fix**: Extract a `BasePipeline` class:

```python
class BasePipeline(ABC):
    def __init__(self, config, skill_manager, workspace_path, human_channel):
        # Common init (currently duplicated)
        ...
    
    def _setup(self, task: str) -> tuple[TelemetryRecorder, SessionLogStore, ...]:
        # Git, Graft, Memory, Recorder, Visualizer setup
        ...
    
    def _run_dev_test_loop(self, dev_conv, tester_conv, ...) -> bool:
        # Shared iteration logic
        ...
    
    def _finalize(self, recorder, log_store, ...) -> dict:
        # Commit, summary, memory persist, explorer
        ...
    
    @abstractmethod
    def run(self, task: str) -> dict:
        ...
```

This eliminates ~300 lines of duplication and ensures bug fixes apply to both pipelines simultaneously.

---

## 11.4 🔵 Structured Output Enforcement for Agents

**Problem**: The system relies on string parsing (`"VERDICT: APPROVED" in text`) to extract agent decisions. If the model uses slightly different wording ("Verdict: Approved", "VERDICT — APPROVED"), the parsing fails silently.

**Fix**: Use structured output / JSON mode:
```python
REVIEWER_SYSTEM_PROMPT += """
You MUST end your review with a valid JSON block:
```json
{"verdict": "APPROVED" | "REJECTED", "issues": [...], "fixes_required": [...]}
```
"""

# In pipeline:
import json
review_json = json.loads(extract_json_block(text))
review_approved = review_json["verdict"] == "APPROVED"
```

---

# 📋 COMPLETE IMPLEMENTATION PRIORITY MATRIX V2

| # | Item | Phase | Severity | Token Impact | LOE |
|---|---|---|---|---|---|
| 1 | Skip Tester LLM in iteration 2+ (direct pytest only) | P7 | 🔴 CRITICAL | **-10K-30K tok/iteration** | 1h |
| 2 | Fix `--resume` to actually skip completed phases | P7 | 🔴 CRITICAL | **Prevents re-burning 100% cost** | 2h |
| 3 | Add retry + checkpoint on `Conversation.run()` errors | P7 | 🔴 CRITICAL | **Prevents total loss on API failure** | 1h |
| 4 | Fix `SkillManager` CWD → package root (external project support) | P7 | 🔴 CRITICAL | **Enables external project development** | 30min |
| 5 | Fix `diagnostics/` CWD → package root | P7 | 🔴 CRITICAL | **Enables external project development** | 30min |
| 6 | Preflight: scan only git-changed files | P7 | 🔴 CRITICAL | **Prevents crash on large projects** | 30min |
| 7 | Prevent `InteractiveLogExplorer` blocking in CI | P9 | 🟡 MEDIUM | UX fix | 5min |
| 8 | Improve memory relevance scoring (reduce false matches) | P8 | 🟠 HIGH | **-375 tokens/prompt** | 30min |
| 9 | Cache Graft index (skip rebuild if fresh) | P8 | 🟠 HIGH | **-5-15s startup** | 15min |
| 10 | Truncate diff sent to Reviewer | P8 | 🟠 HIGH | **-5K-50K tokens** | 30min |
| 11 | Add `--estimate` flag for pre-execution cost estimate | P8 | 🟠 HIGH | UX safety | 1h |
| 12 | Add Conversation wall-clock timeout | P9 | 🟡 MEDIUM | **Prevents infinite hang** | 30min |
| 13 | Debounce session log saves | P9 | 🟡 MEDIUM | **I/O performance** | 10min |
| 14 | Terminal tool command allowlist | P9 | 🟡 MEDIUM | Security | 30min |
| 15 | Fix Architect prefix match → exact match | P9 | 🟡 MEDIUM | RBAC correctness | 15min |
| 16 | Add tokens/cost to `summary_table()` | P10 | 🟢 LOW | UX | 10min |
| 17 | Add `httpx` to explicit dependencies | P10 | 🟢 LOW | Build correctness | 5min |
| 18 | Update `.env.example` with all config vars | P10 | 🟢 LOW | Documentation | 10min |
| 19 | Clean up `sandbox_demo/` orphans | P10 | 🟢 LOW | Hygiene | 5min |
| 20 | Move log suppression from `__init__.py` to `main.py` | P10 | 🟢 LOW | Library-safe imports | 5min |
| 21 | Add `PowerShellHistory.txt` to `.gitignore` | P10 | 🟢 LOW | Hygiene | 1min |
| 22 | Wire `PipelineController` into pipeline loop | P11 | 🔵 ARCH | **Enables pause/stop** | 2h |
| 23 | Wire `PipelineStateMachine` into pipeline loop | P11 | 🔵 ARCH | **Extensibility** | 3h |
| 24 | Activate `MilestoneParser` for subtask execution | P11 | 🔵 ARCH | **-60% context overflow** | 3h |
| 25 | Extract `BasePipeline` to deduplicate pipelines | P11 | 🔵 ARCH | **Maintainability** | 4h |
| 26 | Structured JSON output for Reviewer verdicts | P11 | 🔵 ARCH | **Parsing reliability** | 1h |

---

# 🎯 Token Savings Projection V2

| Optimization | Current Waste | After Fix | Savings |
|---|---|---|---|
| Skip Tester LLM in iteration 2+ | ~15K tok/iteration | 0 tok | **100%** |
| `--resume` skips completed phases | 100% re-burn | 0% re-burn | **100%** |
| Truncate Reviewer diff | ~10K-50K tok | ~2K tok | **80-96%** |
| Improve memory relevance filter | ~375 tok/prompt (often irrelevant) | 0-375 tok (relevant only) | **50-100%** |
| Cache Graft index | 5-15s rebuild delay | 0s | **100%** |
| Activate milestone DAG | ~30K tok (monolithic prompt) | ~5K tok/milestone | **83%** |
| **Total per full pipeline run** | **~100K+ tok** | **~15K tok** | **~85%** |

---

# 🗂️ Proposed V2 Directory Structure

```diff
 orchestrator/
 ├── __init__.py
 ├── config.py
-├── orchestrator.py                      # Thin coordinator
+├── orchestrator.py                      # Accepts checkpoint for resume
 ├── main.py
 ├── agents/
 │   ├── architect.py
 │   ├── developer.py
 │   ├── tester.py
 │   └── reviewer.py
 ├── control/
 │   ├── __init__.py
-│   ├── pipeline_controller.py           # EXISTS BUT DEAD
+│   ├── pipeline_controller.py           # WIRED INTO PIPELINE LOOP
-│   ├── budget_guard.py                  # EXISTS BUT DEAD
+│   ├── budget_guard.py                  # USED BY RECORDER OR REMOVED
 │   └── human_channel.py
 ├── guards/
 │   └── preflight.py                    # + git-changed-only scanning
 ├── memory/
 │   └── conversation_store.py           # + improved relevance scoring
 ├── pipeline/
+│   ├── base_pipeline.py                # NEW: shared logic
-│   ├── dev_test_loop.py
+│   ├── dev_test_loop.py                # EXTENDS BasePipeline
-│   ├── full_pipeline.py
+│   ├── full_pipeline.py                # EXTENDS BasePipeline + milestone DAG
 │   ├── checkpoint.py                   # + actual resume logic
-│   ├── milestone_dag.py                # EXISTS BUT DEAD
+│   ├── milestone_dag.py                # ACTIVATED
-│   └── state_machine.py                # EXISTS BUT DEAD
+│   └── state_machine.py                # WIRED IN
 ├── tools/
-│   └── workspace_tools.py              # + command allowlist
+│   └── workspace_tools.py
 ├── telemetry/
 │   ├── recorder.py
 │   └── schemas.py
 ├── evolution/
 │   └── auditor.py
 └── utils/
     ├── connectivity.py
     ├── git_ops.py                      # + compact diff
     ├── graft_context.py                # + index caching
     ├── output.py                       # + tokens/cost in summary
     ├── pytest_parser.py
     ├── skill_compressor.py
     └── visualizer.py                   # + conditional explorer
```

---

# ⚡ Quick Wins (< 15 Minutes Each)

1. **Block `InteractiveLogExplorer` in CI** → Add `if sys.stdin.isatty():` guard
2. **Add tokens to summary table** → 4 lines in `output.py`
3. **Add `httpx` to deps** → 1 line in `pyproject.toml`
4. **Update `.env.example`** → Add missing config vars
5. **`.gitignore` PowerShellHistory.txt** → 1 line
6. **Move `__init__.py` side effects** → Move to `main.py`
7. **Clean `sandbox_demo/`** → Delete orphans

---

> **Total Estimated LOE**: ~26 hours across 26 items
> **Priority**: Items 1-6 should be done FIRST (< 6 hours, biggest impact on 100x efficiency goal)
