# Codebase Architecture & Security Audit Report

**Project**: Antigravity Multi-Agent Orchestrator (`orchestrator-ai-agent`)
**Audit Date**: 2026-09-23
**Scope**: 72 Python files, ~10,867 LOC, `orchestrator/` package + `tests/` + `graft/` intelligence maps
**Method**: Static inspection of 8 hotspot files, module-boundary mapping, DRY analysis, security review against OWASP/subprocess-injection hardening rubric.

---

## 1. Executive Summary & Architecture Health Score

### 1.1 Health Score: **B- (7.4 / 10)**

| Dimension | Score | Rationale |
|---|---|---|
| Architecture & Modularity | 8/10 | Clean layering: `config → agents → control → pipeline → utils/tools/adapters`. FSM, checkpoints, and budget guard well-separated. |
| Security Hardening | 8/10 | Parameterized `subprocess` (no `shell=True`), command allowlist, path sandboxing, secret redaction in output, `.env` read-block. Notable gaps below. |
| DRY / Cohesion | 5/10 | Significant duplicated iteration/telemetry/report logic across pipelines; duplicated pytest command selection; duplicated branch-slug generation. |
| Error Handling | 6/10 | Good retry/backoff in `_run_conv`, but several silent `except: pass` blocks that swallow failures in critical telemetry and checkpoint paths. |
| Testability | 7/10 | Module-level `execute_terminal_action` seam for mocking; but global mutable state (`_APPEND_COUNTS`, `ALLOWED_COMMAND_BINARIES`, ContextVar channel) couples tests. |
| Observability | 8/10 | TelemetryRecorder, SessionLogStore, structured iteration state, compact diff guards. |

### 1.2 Top-5 Risks (by severity)
1. **[HIGH] Global mutable security config** — `ALLOWED_COMMAND_BINARIES` in `workspace_tools.py` is a *module-level alias* to `DEFAULT_ALLOWED_COMMANDS`; `get_allowed_command_binaries()` reads env but the alias constant is never refreshed and is dead/reused inconsistently (Section 4.1).
2. **[HIGH] `ruff check --fix --unsafe-fixes` runs unconditionally** in `PythonAdapter.run_zero_token_autofix` and every audit-fix iteration (`run_zero_token_autofix()` called per loop), mutating arbitrary user workspaces with *unsafe* lint fixes and rewriting all Python files in-place — a destructive auto-mutation with no dry-run/diff gate and no scope restriction (Section 4.2).
3. **[HIGH] Duplicate budget-tracking truth** — `BudgetGuard` (BasePipeline) and `TelemetryRecorder.check_budget` both enforce the USD cap with independent state; `AuditFixPipeline` only checks the single-iteration dev cost against `budget_guard`, so cross-iteration cumulative spend can exceed `max_budget_usd` (Section 3.3 / 5.2).
4. **[MEDIUM] DRY: four near-identical pipeline `run()` lifecycle shells** (`DevTestLoop`, `FullPipeline`, `AuditPipeline`, `AuditFixPipeline`) each re-implement telemetry construction, report-file migration/fallback, `git get_diff`/`get_status` patterns, and fallback report generation. `_run_conv` itself is correctly hoisted to `BasePipeline`, but the surrounding scaffolding is not (Section 3.1).
5. **[MEDIUM] `check_importability` spawns one subprocess per module** (`python -c "import {mod}"`, 5s timeout each) — O(n) process spawns with no concurrency limit; large monorepos will stall preflight for minutes (Section 5.3).

### 1.3 Structural Invariants That Hold (do NOT break in remediation)
- FSM lifecycle (`state_machine.py`) with explicit `ALLOWED_TRANSITIONS` graph — keep.
- `PipelineCheckpointManager` resume protocol — keep.
- `HumanChannel` ContextVar (`set_active_channel` / `get_active_channel`) — keep, but note its non-propagation into spawned threads (Section 5.4).
- `BudgetGuard` dual-cap contract (USD + tokens) — keep, and re-unify its usage (Section 3.3).
- Graft zero-token context injection — keep.
- Telemetry `diagnostics/reports/` partitioning — keep.

---

## 2. Structural Hotspots & Module Boundaries

### 2.1 Files > 300 LOC (coupling & cohesion analysis)

| File | LOC | Role | Coupling | Notes |
|---|---|---|---|---|
| `orchestrator/tools/workspace_tools.py` | 980 | File + terminal tools, secret sanitization, path sandbox, command allowlist | **Very high** | Single module owns 4 responsibilities: (a) file tool, (b) terminal tool, (c) secret redaction (`sanitize_output_secrets`), (d) command validation. Should be split: `file_tool.py`, `terminal_tool.py`, `secrets.py`, `command_guard.py`. |
| `orchestrator/pipeline/audit_fix_pipeline.py` | 629 | Audit-fix loop + prompt engineering + report generation + 2 module-level regex extractors | High | `extract_actionable_recommendations` / `extract_affected_files` / `DEFAULT_AUDIT_FIX_TASKS` are module-level and mixed with pipeline orchestration. The whole iteration loop (lines ~260–500) is one ~240-line method. |
| `orchestrator/pipeline/full_pipeline.py` | 684 | 4-agent lifecycle + approval gates + checkpointing | High | `run()` alone exceeds 500 lines with deeply nested gate logic; 4 duplicated agent-scaffolding blocks. |
| `orchestrator/pipeline/base_pipeline.py` | 405 | Lifecycle, `_run_conv`, preflight, tests, finalize | Medium | Good abstractions, but `_run_preflight` is Python-specific (assumes `developer_agent`) while class is language-agnostic. |
| `orchestrator/main.py` | 461 | CLI, wizard, config checks | Medium | `interactive_wizard` + `resolve_task_input` + flag parsing in one module; acceptable for a CLI, but `resolve_task_input` does unscoped filesystem reads of any path in the task text (see 4.4). |
| `orchestrator/adapters/node_adapter.py` | 299 | Node detection/lint/test | Low | Balanced. |
| `orchestrator/config.py` | 296 | Config + SkillManager + LLM factory | Medium | Three responsibilities (config schema, skill management, LLM failover factory). `create_llm_for_role` reaches into `FallbackStrategy._resolved` (private attr) — fragile SDK coupling (5.5). |
| `orchestrator/guards/preflight.py` | ~140 | AST + importability | Low | Solid; see 5.3. |

### 2.2 Dependency Cycles & Boundaries
- **No hard import cycles detected** in inspected modules. `audit_fix_pipeline.py` lazily imports `AuditPipeline` (line ~306) and `PipelineCheckpointManager` (line ~497) *inside* the loop body to avoid a top-level cycle with `audit_pipeline` — functional but smells: both pipelines depend on each other's behavior. A shared `audit_report_io` helper would dissolve the lazy import (Section 3.4).
- `orchestrator/pipeline/dev_test_loop.py` imports `PipelinePhase` **from** `base_pipeline` (re-export) instead of from `orchestrator.pipeline.state_machine` — inconsistent import path; a consumer using `base_pipeline.PipelinePhase` vs `state_machine.PipelinePhase` gets the same object only via re-export, which is fragile.
- `orchestrator/tools/workspace_tools.py` imports `orchestrator.config.DEFAULT_WORKSPACE_DIR` **and** `orchestrator.control.human_channel` — a tools→control dependency. Control layer importing tools would create a cycle; current direction is acceptable, but a `WorkspaceContext` dataclass injected into executors would remove the module-level `get_active_channel()` global lookup.
- **Boundary violation**: `PythonAdapter.check_syntax` delegates to `PreFlightGuard` (a guard) while `NodeAdapter` implements its own `check_syntax` — asymmetric responsibility placement across the adapter contract (`ProjectAdapter`).

### 2.3 Module-Level Global State Inventory
| Global | Location | Risk |
|---|---|---|
| `_APPEND_COUNTS: dict` + `reset_append_counts()` | `workspace_tools.py` | Process-wide mutable counter; reset is manual (called from `audit_fix_pipeline` only). DevTestLoop/FullPipeline never reset → append-limit state persists across pipeline runs in the same process. |
| `ALLOWED_COMMAND_BINARIES = DEFAULT_ALLOWED_COMMANDS` | `workspace_tools.py` | Stale alias of the mutable default set; `config.allowed_commands` (env `ALLOWED_COMMANDS`) is a **third** copy of the same allowlist (see 3.3, 4.1). |
| `_active_channel_var` (ContextVar) | `control/human_channel.py` | Not propagated into the `threading.Thread` monitor spawned in `_run_conv` and into OpenHands SDK worker threads — permission prompts issued from tool executors in other threads silently see `channel=None` and **fail-closed deny** (5.4). |

---

## 3. DRY Violations & Duplicate Logic

### 3.1 [HIGH] Duplicated pytest command selection (3 copies)
The "pick pytest command" logic is triplicated:
1. `base_pipeline.py::_execute_tests` (lines ~316–330):
```python
test_cmd = self.adapter.get_test_command(self.workspace_path)
if not test_cmd:
    if (self.workspace_path / "pyproject.toml").exists():
        test_cmd = "pytest -v"
    elif (self.workspace_path / "tests").exists():
        test_cmd = "pytest tests/ -v"
    else:
        test_cmd = "pytest -v"
```
2. `dev_test_loop.py::_execute_pytest` (lines ~58–71): *identical* pyproject/tests/else fall-through, ignoring the adapter entirely.
3. `python_adapter.py::get_test_command`: `uv run pytest -v` / `python -m pytest -v` — a **different** decision table (note `pytest tests/ -v` vs `python -m pytest -v`).

**Recipe**: Delete `DevTestLoop._execute_pytest` and the pyproject fall-through in `BasePipeline._execute_tests`; let `ProjectAdapter.get_test_command` be the single source of truth and add a default to `base.py::ProjectAdapter.get_test_command` returning `"pytest -v"`.

### 3.2 [MEDIUM] `_execute_pytest` alias pair
`base_pipeline._execute_pytest` (self-described "backward-compatible alias") and `dev_test_loop._execute_pytest` (override) both exist. The base one delegates to `_execute_tests`; the override does not. Grep callers and collapse to one method on `BasePipeline`.

### 3.3 [HIGH] Duplicate budget-enforcement truth
- `BasePipeline.__init__` creates `BudgetGuard(max_budget_usd=config.max_budget_usd)`.
- `TelemetryRecorder` *also* takes `max_budget_usd` and exposes `check_budget()` (used in `full_pipeline.py` / `dev_test_loop.py` via `recorder.check_budget(_get_total_cost())`).
- `config.allowed_commands` (env `ALLOWED_COMMANDS`) duplicates `workspace_tools.DEFAULT_ALLOWED_COMMANDS` and `get_allowed_command_binaries()`.

In `AuditFixPipeline.run`, per-iteration budget check uses `self.budget_guard.update_cost(u_dev["estimated_cost_usd"])` — which sees only the **single iteration's** dev-agent cost, not the cumulative run cost, so the total can blow past `max_budget_usd`. Meanwhile the other two pipelines check via the *recorder*. Two owners, two sources of truth.

**Recipe**: Make `BudgetGuard` the single owner:
```python
# base_pipeline.py
def _check_budget(self, total_cost_usd: float) -> bool:
    return self.budget_guard.update_cost(total_cost_usd)

# TelemetryRecorder: remove check_budget(max_budget_usd); keep pure recording.
# audit_fix_pipeline.py (per iteration, after recording):
total_cost = get_llm_usage(developer_agent.llm)["estimated_cost_usd"]  # cumulative LLM usage, not per-iter delta
if self._check_budget(total_cost):
    ...
```
`BudgetGuard.update_cost` already *sets* (not adds) `_current_cost_usd`, so feeding it cumulative `estimated_cost_usd` (which `get_llm_usage` returns as accumulated) is correct — document this contract.

### 3.4 [MEDIUM] Duplicated "audit report read/migrate" logic
`audit_pipeline.py::run` (lines ~155–170) and `audit_fix_pipeline.py::run` (lines ~227–240 and ~305–315) each implement: look for `docs/AUDIT_REPORT.md`, fall back to workspace root, `replace()` root→docs, `read_text(errors="replace")` in try/except-pass. Extract to `orchestrator/pipeline/audit_report_io.py`:
```python
def locate_and_normalize_report(ws: Path, name: str = "AUDIT_REPORT.md") -> Optional[Path]: ...
def read_report(ws: Path, name: str = "AUDIT_REPORT.md") -> str: ...
```

### 3.5 [MEDIUM] Duplicated branch-slug generation
`base_pipeline._setup_run` builds `agent/{slug}-{int(time.time())}` with `re.sub(r"[^a-zA-Z0-9_\-]+", "-")`; `git_ops.create_task_branch` builds the *same* `agent/{slug}-{ts}` with slightly different regex (`[^a-zA-Z0-9_-]+`, `[:25]` vs `[:30]`). One implementation → `GitOps.create_task_branch(task_description)` called from `_setup_run`; the duplicated regex and length caps (30 vs 25) should be a single constant.

### 3.6 [LOW] Duplicated "truncation + governance notice" scaffolding
`workspace_tools.execute_file_action` read path, `GitOps.get_compact_diff`, and terminal-output truncation all implement "clamp to N chars + append explanatory notice". Acceptable for now; a shared `truncator.clamp(text, max_chars, notice_fn)` utility would unify.

### 3.7 [MEDIUM] Telemetry `record_step` boilerplate
`recorder.record_step(role, action, iteration, dur, True, prompt_tokens=..., completion_tokens=..., total_tokens=..., estimated_cost_usd=...)` appears verbatim ~10 times across `full_pipeline`, `dev_test_loop`, `base_pipeline._run_preflight`, `audit_pipeline`, `audit_fix_pipeline`. Introduce a context manager:
```python
# telemetry/recorder.py
@contextmanager
def timed_step(self, role, action, iteration=1):
    t0 = time.perf_counter()
    try:
        yield
    finally:
        u = get_llm_usage(...)  # or explicit llm param
        self.record_step(role, action, iteration, time.perf_counter() - t0, True, **u)
```

---

## 4. Security, Secret Leak & Subprocess Vulnerability Audit

### 4.1 [HIGH] Three-way command-allowlist divergence
`workspace_tools.py` exposes:
- `DEFAULT_ALLOWED_COMMANDS` (mutable module set, includes `cd`, `echo`, `find`)
- `ALLOWED_COMMAND_BINARIES = DEFAULT_ALLOWED_COMMANDS` (alias, **never read** by the validator — dead constant that misleads maintainers)
- `get_allowed_command_binaries()` reading env `ALLOWED_COMMANDS`
- `orchestrator/config.py::allowed_commands` — a *fourth* copy seeded from the same env var, but **never used** by the terminal tool.

Result: an operator setting `config.allowed_commands` (or reading docs saying so) gets no effect; the env path is the only live one. **Recipe**: delete `ALLOWED_COMMAND_BINARIES` and `OrchestratorConfig.allowed_commands`; single owner = `get_allowed_command_binaries()`. Also note `cd` and `echo` are allowlisted as real binaries — `cd` fails meaningfully on POSIX when exec'd directly (no cwd persistence across calls), and `echo` re-introduces an argument-injection-free but confusing path. Consider removing `cd`/`echo`/`where` from the allowlist.

### 4.2 [HIGH] Unscoped destructive auto-fix
`PythonAdapter.run_zero_token_autofix` runs:
```python
["ruff", "check", "--fix", "--unsafe-fixes", "--output-format=concise", "."]
["ruff", "format", "."]
```
with no timeout guard on the first call having a `--no-cache` consideration, and **`AuditFixPipeline.run` invokes `self.run_zero_token_autofix()` on every iteration** (line ~269) *without* even checking the boolean result. Consequences:
- `--unsafe-fixes` may rewrite semantics (e.g., `logging` → `log` rewrites, `open(..., encoding)` insertions) across the *entire* target workspace — including files the pipeline did not touch.
- No diff capture / no revert capability / no file-scope restriction.
- Return value ignored on the per-iteration call → a failure is silent.

**Recipe**:
```python
# python_adapter.py
def run_zero_token_autofix(self, workspace: Path, scope: Optional[list[str]] = None, unsafe: bool = False) -> Tuple[bool, str]:
    ruff = shutil.which("ruff")