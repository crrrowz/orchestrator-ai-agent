# PROJECT_STATE.md

## Executive Summary
- Project: Antigravity Multi-Agent Orchestrator (`Antigravity-Agent-API` / `orchestrator-ai-agent`)
- Purpose: Autonomous, multi-agent software engineering system using OpenHands SDK (v1.49.4) and standard `.agents/skills/` specification. Coordinates Architect, Developer, Tester, and Reviewer agents across dual pipelines with strict token budgeting, Git safety, and interactive telemetry.
- End Goal: Self-healing, production-grade autonomous software engineering framework with zero-token-waste codebase orientation (via Graft), transparent OpenRouter model failover, and interactive TUI inspection.

## Completed Tasks
- [DONE] OpenHands SDK v1.49.4 ToolProtocol compliance: Subclassed `ToolDefinition[ActionT, ObservationT]` with concrete `create()` factory and custom `ToolExecutor` implementations (`WorkspaceFileTool`, `WorkspaceTerminalTool`).
- [DONE] Fixed `TypeError: 'NoneType' object is not iterable` in `Observation.to_llm_content`: `WorkspaceFileObservation` refactored to populate `content=[TextContent(text=...)]`.
- [DONE] Token & Cost Control: Configured per-role limits (`max_tokens_per_call: 4096`, `max_iterations: 4-6`), call-budget circuit breakers, and cost/incident telemetry recorder in `orchestrator/telemetry/`.
- [DONE] OpenRouter Failover & Normalization:
  - Model slug normalization (`normalize_model_slug`) auto-routes `:free` suffixes and maps `openrouter/free` to `openrouter/openrouter/free`.
  - LiteLLM extra body failover array: `litellm_extra_body={"models": [slug, "openrouter/free"]}`.
  - Native OpenHands SDK `FallbackStrategy` attached with lazy-resolved `openrouter/openrouter/free` fallback LLM on transient exceptions (RateLimitError 429).
- [DONE] Terminal UI Overhaul:
  - Custom `OrchestratorLiveVisualizer` inheriting from `ConversationVisualizerBase`, suppressing raw prompt dumps and LiteLLM stack traces.
  - `OPENHANDS_SUPPRESS_BANNER=1` configured.
  - `InteractiveLogExplorer` supporting arrow-key step navigation, accordion expand/collapse (`Enter`/`Right`/`Left`/`A`), and `--logs` CLI review.
- [DONE] Graft Codebase Intelligence Integration:
  - Graft context graph built via `graft build` (137 nodes, 404 edges indexed across 28 files in 3s).
  - Added `.agents/skills/graft-architecture-intelligence/SKILL.md` (zero-token `graft map`, `graft skeleton`, `graft callers`, `graft blast`).
  - Equipped Architect agent with `WorkspaceTerminalTool` and updated system prompt for Graft-first orientation.
  - Integrated `graft-architecture-intelligence` into Architect and Developer skill profiles.
- [DONE] Unit Test Verification: 12/12 unit tests passing (`uv run pytest`) across git ops, skills discovery, tool executors, and visualizer.

## System Architecture
- Stack: Python 3.12+, OpenHands SDK v1.49.4, LiteLLM, Pydantic v2, Rich, msvcrt (Windows keyboard nav), Graft CLI.
- Structure:
  - `orchestrator/agents/`: Agent factories (`architect.py`, `developer.py`, `tester.py`, `reviewer.py`).
  - `orchestrator/pipeline/`: Execution engines (`dev_test_loop.py`, `full_pipeline.py`).
  - `orchestrator/tools/`: SDK tools (`workspace_tools.py` with `WorkspaceFileTool`, `WorkspaceTerminalTool`).
  - `orchestrator/utils/`: TUI visualizer (`visualizer.py`), Git isolation (`git_ops.py`), connectivity check (`connectivity.py`).
  - `orchestrator/telemetry/`: Incident & cost tracker (`recorder.py`, `schemas.py`).
  - `orchestrator/evolution/`: Self-audit & diagnostic engine (`auditor.py`).
  - `.agents/skills/`: 9 modular YAML+Markdown skills.
  - `graft/`: Local codebase wiring graph (gitignored).
- Data Flow:
  - User Task -> (Optional Architect `PLAN.md`) -> Developer Code Generation -> Tester (pytest execution loop) -> (Optional Reviewer Pass) -> Git Commit on task branch -> Interactive Log Explorer.
- Integrations:
  - OpenRouter API (primary & free-tier fallback routing).
  - Graft context engine (local wiring graph, call graphs, hubs, and hotspots).
  - Git CLI (branch isolation per task run).

## Technical Decisions
- Decision: Use native OpenHands SDK `FallbackStrategy` with lazy-resolved `openrouter/openrouter/free`.
  - Reason: OpenRouter upstream free-tier models frequently encounter transient 429 concurrency throttles. Secondary fallback LLM prevents pipeline termination.
  - Status: Implemented and verified.
- Decision: Use `ConversationVisualizerBase` subclass instead of default visualizer.
  - Reason: Default visualizer prints raw internal SDK prompts, LiteLLM tracebacks, and large JSON payloads directly to terminal stdout.
  - Status: Implemented via `OrchestratorLiveVisualizer`.
- Decision: Graft CLI via `WorkspaceTerminalTool` rather than ad-hoc custom python AST parsers.
  - Reason: Graft already provides sub-second indexing, call graphs, hubs, hotspots, and blast radius calculations at zero token cost.
  - Status: Implemented with `graft-architecture-intelligence` skill.

## Constraints
- Root `docs/` in `Antigravity-Agent-API` contains authoritative architecture blueprints (`00` to `07`) and must not be deleted or modified without explicit instruction.
- OpenRouter free-tier models must always have failover routing to `openrouter/free` to avoid pipeline halts.
- Terminal output must remain concise and clean; raw system prompts must never flood stdout.

## Current State
- Status: Green / Ready.
- Active Task: Completed OpenRouter `openrouter/free` fallback integration, Graft codebase intelligence wiring, and canonical project state persistence.
- Working Files:
  - `orchestrator/config.py`
  - `orchestrator/agents/architect.py`
  - `.agents/skills/graft-architecture-intelligence/SKILL.md`
  - `tests/test_skills.py`
- Implemented:
  - Full multi-agent orchestration pipelines (Dev-Test loop, 4-agent full pipeline).
  - Resilient OpenRouter API routing with dual fallback (litellm body + SDK FallbackStrategy).
  - Graft codebase intelligence skill and Architect terminal integration.
  - Interactive collapsible TUI logs.
- Known Bugs: None.
- Blockers: None.

## Next Steps
1. [HIGH] Execute end-to-end task run using `uv run python -m orchestrator.main` to verify live agent generation against free-tier OpenRouter.
2. [MEDIUM] Expose Graft MCP tools (`graft mcp`) directly as OpenHands native tools if stdio streaming is needed without subshell execution.
3. [LOW] Add automated periodic `graft build` hook upon Git commit in `orchestrator/utils/git_ops.py`.

## Context Required for Continuation
- Workspaces:
  - `Antigravity-Agent-API/` (Repository root with architecture `docs/`).
  - `orchestrator-ai-agent/` (Active Python package with `pyproject.toml`, `orchestrator/`, `tests/`).
- Package Manager: `uv` is the primary runner (`uv run pytest`, `uv run python -m orchestrator.main`).
- Skills location: `orchestrator-ai-agent/.agents/skills/`.
