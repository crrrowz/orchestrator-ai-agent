# Antigravity Multi-Agent Orchestrator & Sentinel SRE Mesh

Autonomous, multi-agent software engineering framework powered by the **OpenHands Software Agent SDK** (`openhands-sdk v1.49.4`), `.agents/skills/` specification, and zero-token codebase intelligence (via Graft).

---

## 🌟 System Overview & Reality

```
                                  USER TASK / SPEC FILE
                                            │
                                            ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                        ORCHESTRATOR CONTROL PLANE (Python 3.12+)                 │
 │  FSM State Machine (12 Phases) │ ContextManager │ DynamicTokenGovernor           │
 └──────┬──────────────┬──────────────┬──────────────┬──────────────┬───────────────┘
        │              │              │              │              │
        ▼              ▼              ▼              ▼              ▼
  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
  │ ARCHITECT │  │ DEVELOPER │  │  TESTER   │  │ REVIEWER  │  │  AUDITOR  │
  │   Agent   │  │   Agent   │  │   Agent   │  │   Agent   │  │   Agent   │
  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
        │              │              │              │              │
        ▼              ▼              ▼              ▼              ▼
 ┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐
 │ SKILLS:     ││ SKILLS:     ││ SKILL:      ││ SKILLS:     ││ SKILLS:     │
 │architectural││clean-python-││pytest-      ││code-review- ││code-review- │
 │decomposition││architecture││rigorous-    ││standards    ││standards    │
 │api-design   ││systematic-  ││testing      ││security-    ││security-    │
 │contract     ││debugging    ││             ││audit        ││hardening    │
 │graft-arch   ││docker-devops││             ││             ││graft-arch   │
 └─────────────┘└─────────────┘└─────────────┘└─────────────┘└─────────────┘
                                      │
                                      ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                      COGNITIVE SENTINEL & SRE MESH                               │
 │ ASTGuard (<15ms), SelfHealingEngine, CloudResilienceMesh, SQLite WAL Diagnostics │
 └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```text
.
├── orchestrator-ai-agent/       # Core Multi-Agent Orchestration Package (Python 3.12+)
│   ├── orchestrator/
│   │   ├── adapters/            # Polyglot Project Adapters (Python, Node, Generic)
│   │   ├── agents/              # Role Agent Factories (Architect, Developer, Tester, Reviewer, Auditor, Documentation)
│   │   ├── analysis/            # Pytest parsing, Graft context, Finding validators
│   │   ├── cli/                 # CLI handlers, argparse routing, interactive wizard
│   │   ├── config/              # Pydantic schemas, cascading JSON/.env loaders
│   │   ├── context/             # ContextManager, prompt builder, modular injectors
│   │   ├── control/             # TokenGovernor, BudgetGuard, HumanInterventionChannel
│   │   ├── core/                # Config, constants, exceptions, typing protocols
│   │   ├── guards/              # Zero-token preflight syntax & importability guards
│   │   ├── llm/                 # LLMManager, factory, pricing, model normalization
│   │   ├── memory/              # Cross-run persistent conversation memory
│   │   ├── pipeline/            # 5 Pipelines (DevTestLoop, FullPipeline, AuditPipeline, AuditFixPipeline, DocumentationPipeline)
│   │   ├── rendering/           # Rich diff renderer, terminal styling, report generators
│   │   ├── sentinel/            # Cognitive Sentinel: ASTGuard, SelfHealing, CloudMesh, DiagnosticsDB
│   │   ├── skills/              # Skill manager, compressor, resolver, registry
│   │   ├── tools/               # RBAC workspace file and parameterized terminal tools
│   │   ├── ui/                  # SessionLogStore, OrchestratorLiveVisualizer, InteractiveLogExplorer
│   │   └── vcs/                 # GitOps isolation, branching, diffs, checkpointing
│   ├── tests/                   # 34 Test Modules (224 Passing Tests)
│   ├── docs/                    # Package-level operational documentation
│   └── pyproject.toml           # Hatchling build backend & project dependencies
└── .agents/skills/              # 9 Standard YAML+Markdown engineering skills
```

---

## 🚀 Quick Start

### 1. Requirements
- Python `3.12+`
- `uv` (recommended) or `pip`
- Git

### 2. Installation & Configuration

```bash
cd orchestrator-ai-agent

# Install dependencies with uv
uv sync

# Configure environment
cp .env.example .env
```

Provide your API key in `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-...
```

### 3. Verification & Execution

```bash
# Verify setup offline (0 API tokens consumed)
uv run python -m orchestrator.main --check-config

# Run test suite (224 unit & integration tests)
uv run pytest -q

# Execute a software engineering task
uv run python -m orchestrator.main "Build a rate limiter" --mode dev-test
```

---

## ⚡ Execution Modes (`--mode`)

1. **`--mode dev-test` (Default)**: Developer + Tester iterative TDD loop.
2. **`--mode full`**: 4-Agent Pipeline coordinating Architect (creates `PLAN.md`), Developer (Milestone DAG), Tester (Pytest), and Reviewer (Independent Verdict).
3. **`--mode audit`**: Zero-token AST/linter inspection + Auditor agent producing structured `docs/audit_findings.json` and `docs/AUDIT_REPORT.md`.
4. **`--mode audit-fix`**: Continuous scan-remediate-verify self-healing loop directly on workspace working tree without Git operations.
5. **`--mode docs`**: Documentation agent authoring and updating repository documentation.

---

## 🛡️ Cognitive Sentinel & SRE Mesh

- **`--sentinel-status`**: Displays live Sentinel diagnostics, auto-healed incident counts, and cloud circuit breaker statuses.
- **`--sentinel-heal [PATH]`**: Offline zero-token AST syntax audit and automated import repair.
- **`--sentinel-test-mesh`**: Probes cloud fallback chain readiness across OpenRouter, Gemini, Groq, Anthropic, and OpenAI.

---

## 🧪 Testing & Verification

The test suite contains **224 automated tests** across **34 test modules** covering:
- OpenHands SDK tool protocol compliance (`WorkspaceFileTool`, `WorkspaceTerminalTool`).
- Circuit breaker state machines and semantic failure deduplication.
- Dynamic token governance and phase allocation (`TokenPhase`).
- Cognitive Sentinel supervision, AST guarding, and self-healing.
- Project log rotation and multi-workspace partitioning.

```bash
cd orchestrator-ai-agent
uv run pytest -v
```

All 224 tests pass deterministically.
