# PROJECT_STATE.md

## Executive Summary
- Project: Antigravity Multi-Agent Orchestrator (`Antigravity-Agent-API` / `orchestrator-ai-agent`)
- Purpose: Autonomous, multi-agent software engineering system using OpenHands SDK (v1.49.4) and `.agents/skills/` specification. Coordinates Architect, Developer, Tester, and Reviewer agents across dual pipelines (`dev-test`, `full`) with strict token budgeting, Git safety, zero-token static gatekeepers, and interactive TUI telemetry.
- End Goal: Production-grade autonomous software engineering framework with zero-token codebase orientation (via Graft), resilient OpenRouter free-tier failover, automated code audit pipeline (`--mode audit`), and self-healing execution loops.

## Completed Tasks
- [DONE] OpenHands SDK v1.49.4 ToolProtocol compliance: Subclassed `ToolDefinition[ActionT, ObservationT]` with concrete `create()` factory and custom `ToolExecutor` implementations (`WorkspaceFileTool`, `WorkspaceTerminalTool`).
- [DONE] Windows Subprocess UTF-8 & Observation Resilience: Enforced `encoding="utf-8", errors="replace"` on `subprocess.run` across `WorkspaceTerminalTool` and `GitOps`, resolving Windows `UnicodeDecodeError` (`charmap` codec).
- [DONE] Terminal UI & Live Event Streaming: `OrchestratorLiveVisualizer` suppressing LiteLLM debug noise, streaming active roles, elapsed time, and token metrics; real-time `InteractiveLogExplorer` supporting arrow-key step navigation.
- [DONE] Graft Codebase Intelligence Integration: Fresh Graft graph built (`411 nodes, 1060 edges, 61 cards`), zero-token codebase structure injection (`orchestrator/utils/graft_context.py`), and Architect/Developer skill integration (`.agents/skills/graft-architecture-intelligence/SKILL.md`).
- [DONE] Phase 1–6 Improvements (21 Items Verified & Implemented):
  - Skill isolation (`load_project_skills=False`) preventing prompt bloat.
  - Step-level token & cost telemetry tracking.
  - Conversation context reuse across fix iterations.
  - Pre-flight zero-token syntax validation (`<50ms`).
  - Compact pytest failure parser (~70% prompt reduction).
  - RBAC tool permissions per agent role.
  - Terminal environment credential sanitization.
  - Human intervention channel (`--interactive`, `--approval-gates`).
  - Git branch task isolation (`agent/<task-slug>-<timestamp>`).
  - Smart semantic circuit breaker (exact hashes + test names + Levenshtein ratio >=0.88).
  - Cross-run conversation memory persistence (`diagnostics/memory/`).
  - Checkpoint manager (`.orchestrator_state.json`) with CLI `--resume`.
- [DONE] Sandbox Demo Project (`sandbox_demo/`):
  - Sliding Window Rate Limiter Python library with clean hexagonal architecture.
  - Cleaned up build-backend in `pyproject.toml` to `setuptools.build_meta`.
  - Added runnable interactive demo [demo.py](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/sandbox_demo/demo.py) and documentation [README.md](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/sandbox_demo/README.md).
  - 81/81 tests passing in `sandbox_demo/tests/`.
- [DONE] Phase 7: Dead Code Wiring, Path Isolation & Runtime Safety:
  - `PipelineController` (DC-1): Wired into `DevTestLoop` and `FullPipeline` with graceful pause/stop/abort handling (`check_should_continue()`, `request_abort()`).
  - `PipelineStateMachine` (DC-2): Enforced 12-state FSM transitions (`INIT -> ARCHITECT -> DEVELOP -> PREFLIGHT -> TEST -> FIX -> REVIEW -> COMMIT -> COMPLETED`).
  - `BudgetGuard` (DC-3): Directly integrated inside `TelemetryRecorder`, exposing `remaining_budget` and safely casting costs to prevent mock/type mismatches.
  - `MilestoneParser` (DC-4): Activated in `FullPipeline` after Architect step to decompose `PLAN.md` into discrete implementation milestones for Developer.
  - Zero-Token Tester Skip (7.1): Tester LLM invocation disabled for `iteration > 1` in both pipelines; re-verifies developer fixes directly via `pytest` subprocess (saving 5k–15k tokens per loop).
  - Workspace Path Isolation (7.2): Defined `ORCHESTRATOR_ROOT` and `DEFAULT_DIAGNOSTICS_DIR` in `config.py`. Prevented CWD pollution for `SkillManager`, reports, and logs when running on external workspaces.
  - Pre-Flight Exclusions: Added `venv`, `node_modules`, `site-packages` to `PreFlightGuard.check_syntax`.
  - Conversation Error Recovery (7.3): Added `_run_conv()` helper with exponential backoff retry across both pipelines.
  - Checkpoint Phase Skipping (7.4): Enabled `--resume` to skip already completed phases (`architect`, `developer`) recorded in `checkpoint.completed_phases`.
  - Verified with 4 new unit tests in [tests/test_phase7_improvements.py](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/tests/test_phase7_improvements.py).
  - Test Suite Status: **43/43 PASSED** across all 11 test modules.

## System Architecture
- Stack: Python 3.12+, OpenHands SDK v1.49.4, LiteLLM, Pydantic v2, Rich, Graft CLI, Pytest.
- Structure:
  - `orchestrator/agents/`: Role agent factories (`architect.py`, `developer.py`, `tester.py`, `reviewer.py`).
  - `orchestrator/pipeline/`: Execution engines (`dev_test_loop.py`, `full_pipeline.py`, `state_machine.py`, `milestone_dag.py`, `checkpoint.py`).
  - `orchestrator/control/`: Centralized control plane (`pipeline_controller.py`, `budget_guard.py`, `human_channel.py`).
  - `orchestrator/guards/`: Zero-token syntax & safety gatekeepers (`preflight.py`, `budget_guard.py`).
  - `orchestrator/memory/`: Cross-run intelligence & persistence (`conversation_store.py`).
  - `orchestrator/tools/`: RBAC-secured SDK tools (`workspace_tools.py`).
  - `orchestrator/utils/`: Graft context (`graft_context.py`), Pytest parser (`pytest_parser.py`), Skill compressor (`skill_compressor.py`), Visualizer (`visualizer.py`), Git isolation (`git_ops.py`), Output helpers (`output.py`).
  - `orchestrator/telemetry/`: Incident, token cost & circuit breaker tracker (`recorder.py`, `schemas.py`).
  - `orchestrator/evolution/`: Self-audit & diagnostic engine (`auditor.py`).
  - `.agents/skills/`: 9 modular YAML+Markdown skills.
  - `graft/`: Local codebase wiring graph (411 nodes, 1060 edges, 61 cards).
  - `diagnostics/`: System-wide telemetry (`reports/`, `logs/`, `memory/`).
  - `sandbox_demo/`: Clean Python Sliding Window Rate Limiter sample project (81 passing tests).

## Technical Decisions
- Decision: Use `ORCHESTRATOR_ROOT` as the anchor for `SkillManager` and `DEFAULT_DIAGNOSTICS_DIR`.
  - Reason: When orchestrator runs against external projects via `--workspace`, logs and skills must not be read from or written to the target workspace or arbitrary launch CWD.
  - Status: Implemented & Verified in `config.py`, `recorder.py`, `visualizer.py`, `conversation_store.py`, `main.py`.
- Decision: Bypass Tester LLM in Fix Iterations (`iteration > 1`).
  - Reason: Once tests are written in iteration 1, developer fixes only need `pytest -v` validation. Invoking Tester LLM just to run pytest burned 5k–15k tokens per loop without added value.
  - Status: Implemented & Verified in `dev_test_loop.py` and `full_pipeline.py`.
- Decision: Decompose `PLAN.md` via `MilestoneParser` into Developer implementation guidance.
  - Reason: Prevents LLM context exhaustion on complex tasks by providing structured milestone breakdown.
  - Status: Implemented & Verified in `full_pipeline.py`.
- Decision: Architecture of `--mode audit` will be Hybrid (Static AST/Linter + LLM Agent).
  - Reason: User confirmed preference for hybrid approach to ensure 0-token fast vulnerability detection combined with architectural insight.
  - Status: Implemented & Verified in `orchestrator/pipeline/audit_pipeline.py`, `orchestrator/agents/auditor.py`, `tests/test_audit_pipeline.py`.
- Decision: Pre-execution Cost Estimation via `--estimate` CLI flag.
  - Reason: Enables zero-token cost and token burn projections before committing API spend.
  - Status: Implemented & Verified in `orchestrator/control/cost_estimator.py` and `tests/test_phase8_improvements.py`.
- Decision: Anchor default workspace for new projects strictly to `DEFAULT_WORKSPACE_DIR` (`ORCHESTRATOR_ROOT / "workspace"`).
  - Reason: Prevents project files from scattering relative to arbitrary execution CWD.
  - Status: Implemented in `config.py` and `workspace_tools.py`.
- Decision: Wall-clock timeout cap (300s) on `Conversation.run()` via `threading.Timer`.
  - Reason: Prevents runaway agent loops or infinite tool-call cycles.
  - Status: Implemented in `full_pipeline.py`, `dev_test_loop.py`, `audit_pipeline.py`.
- Decision: Throttled log persistence (5s debounce) in `SessionLogStore`.
  - Reason: Prevents file I/O storms when agents make high-frequency tool calls.
  - Status: Implemented in `visualizer.py`.
- Decision: Zero-token importability preflight check via `PreFlightGuard.check_importability`.
  - Reason: Catches missing `__init__.py` or top-level import crashes before running pytest.
  - Status: Implemented in `guards/preflight.py`.
- Decision: Diagnostics Log Rotation & Project-Partitioned Session Storage.
  - Reason: Prevents unbound disk proliferation of telemetry JSON reports (FIFO auto-pruning to `MAX_RETAINED_REPORTS=20`) and prevents multi-project collision in `latest_session.json` by namespacing sessions under `diagnostics/logs/<project_slug>/` while preserving global backward compatibility.
  - Status: Implemented & Verified in `telemetry/recorder.py`, `utils/visualizer.py`, `config.py`, `pipeline/base_pipeline.py`, `main.py`, `tests/test_log_rotation_and_partitioning.py`.

## Constraints
- OpenHands SDK v1.49.4 ToolProtocol requires strictly subclassing `ToolDefinition` and implementing `create()`.
- Windows PowerShell CP1252 terminal encoding requires UTF-8 subprocess enforcement and avoiding non-ASCII console chars in CLI logs.
- Python 3.12+ required.

## Current State
- Status: **Phase P13 (Systemic Deep Audit, Resilience Hardening & Cross-Layer Remediation) Complete**.
- Active Stopping Point: Production-ready with 100% verified test coverage across 224 unit & integration tests.
- Working Files:
  - `orchestrator/telemetry/recorder.py`
  - `orchestrator/pipeline/dev_test_loop.py`
  - `orchestrator/pipeline/full_pipeline.py`
  - `orchestrator/pipeline/audit_report_io.py`
  - `orchestrator/memory/conversation_store.py`
  - `orchestrator/sentinel/diagnostics_db.py`
  - `orchestrator/ui/session_store.py`
  - `orchestrator/tools/workspace_tools.py`
  - `orchestrator/control/token_governance.py`
  - `tests/test_systemic_resilience_audit.py`
- What Works:
  - Circuit Breaker dual-signature compatibility (`check_circuit_breaker(diff, error)` and `check_circuit_breaker(error)`).
  - Proper FSM terminal state transitions (`PipelinePhase.FAILED`) on unexpected pipeline exceptions.
  - Case-insensitive and normalized resolution of `docs/AUDIT_REPORT.md`.
  - SQLite WAL mode and busy timeout handling in Sentinel diagnostics database.
  - Thread-safe `SessionLogStore` preventing state corruption under concurrent events.
  - Symbol extraction token governance clamping to prevent context window blowup.
  - Re-exported clean utils modules without code duplication.
- Known Bugs / Blockers: None.

## Next Steps
1. [PRODUCTION] Continuous multi-agent task execution and autonomous self-healing monitoring.

## Context Required for Continuation
- The primary codebase path is: `D:\files\Contracted projects\IdeaProjects\Antigravity-Agent-API\orchestrator-ai-agent`.
- All commands should be run using `uv run pytest tests/ -v` or `uv run python -m orchestrator.main ...`.
- Graft graph is built and cached in `graft/`. Run `graft map` for an instant architectural sitemap.
- Test suite currently has 224 passing tests across 34 test modules. Do not break existing contracts.


