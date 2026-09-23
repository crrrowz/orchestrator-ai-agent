# 📖 Orchestrator Configuration Reference Manual (Enterprise V3)

> **Document Classification**: Enterprise Architecture & Runtime Specification  
> **Target Version**: `1.0.0`  
> **Schema Definition**: [`orchestrator/config/config_schema.json`](file:///d:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/config/config_schema.json)  
> **Configuration Source**: [`orchestrator.config.json`](file:///d:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator.config.json)

---

## 🏛️ Configuration Architecture & Cascading Priority

The Multi-Agent Orchestrator adopts a strict **4-Tier Priority Cascade**. Settings defined higher in the cascade supersede those defined below them.

```
┌────────────────────────────────────────────────────────┐
│  Tier 1: Runtime Overrides (CLI Arguments / Kwargs)    │ (Highest Priority)
└──────────────────────────┬─────────────────────────────┘
                           │ (falls back to)
┌──────────────────────────▼─────────────────────────────┐
│  Tier 2: orchestrator.config.json (Central JSON File)   │
└──────────────────────────┬─────────────────────────────┘
                           │ (falls back to)
┌──────────────────────────▼─────────────────────────────┐
│  Tier 3: .env File & System Environment Variables      │
└──────────────────────────┬─────────────────────────────┘
                           │ (falls back to)
┌──────────────────────────▼─────────────────────────────┐
│  Tier 4: Hardcoded Framework Defaults (Pydantic)       │ (Lowest Priority)
└────────────────────────────────────────────────────────┘
```

### Discovery Order for `orchestrator.config.json`:
1. Path provided explicitly via `--config <path>`
2. Path provided via `ORCHESTRATOR_CONFIG_PATH` environment variable
3. Current working directory `./orchestrator.config.json`
4. Repository root `<ORCHESTRATOR_ROOT>/orchestrator.config.json`

---

## 📊 Comprehensive Parameter Matrix

| JSON Path | Env Var Equivalent | Type | Default | Code Location | Positive Impact | Negative Impact / Risk |
|---|---|---|---|---|---|---|
| `execution.max_iterations` | `MAX_ITERATIONS` | `int \| str` | `4` | `orchestrator/config/__init__.py:42` | Allows developer multiple attempts to fix failing tests or audit issues. Accepts `'auto'` for backlog-scaled iterations. | High values without Circuit Breaker trigger runaway token burn. |
| `execution.max_budget_usd` | `MAX_BUDGET_USD` | `float` | `0.50` | `orchestrator/config/__init__.py:59` | Hard dollar spending ceiling across all agents in a single execution. Prevents costly API runaway. | If set too low, complex tasks or large codebases are aborted prematurely. |
| `execution.max_tokens_budget` | `MAX_TOKENS_BUDGET` | `int` | `350000` | `orchestrator/config/__init__.py:62` | Token consumption ceiling per run. Protects against LLM output flooding. | Lower than 100K can cause multi-agent loops to trip budget guard. |
| `execution.max_agent_steps` | `MAX_AGENT_STEPS` | `int` | `12` | `orchestrator/config/__init__.py:65` | Limits the internal tool-calling turns for each agent invocation. | Overly small limits truncate agent file editing before test completion. |
| `execution.max_tokens_per_call` | `MAX_TOKENS_PER_CALL` | `int` | `8192` | `orchestrator/config/__init__.py:66` | Caps max output tokens per single LLM call. | Truncates code generation if set below 4096 on large module creation. |
| `execution.circuit_breaker_threshold` | `CIRCUIT_BREAKER_THRESHOLD` | `int` | `2` | `orchestrator/config/__init__.py:69` | Halts infinite loops when consecutive iterations produce identical test errors or unchanged diffs. | Setting to `1` may abort after a transient or easily fixed initial failure. |
| `execution.conversation_timeout_seconds` | `CONVERSATION_TIMEOUT_SECONDS` | `int` | `300` | `orchestrator/config/__init__.py:72` | Enforces max wall-clock duration per conversation step to prevent hung tasks. | Very complex builds or network latency can hit timeout. |
| `execution.auto_commit` | `AUTO_COMMIT` | `bool` | `true` | `orchestrator/config/__init__.py:56` | Automatically records a clean git commit on verified task completion. | Commits unfinished work if verification gates are disabled. |
| `execution.auto_chain_audit` | `AUTO_CHAIN_AUDIT` | `bool` | `true` | `orchestrator/config/__init__.py:88` | Automatically runs audit pass following dev-test completion. | Adds extra execution step and tokens to simple dev tasks. |
| `execution.workspace_path` | `WORKSPACE_PATH` | `str` | `./workspace` | `orchestrator/config/__init__.py:36` | Target working directory isolated from orchestrator codebase. | Misconfigured relative path may target unintended directory. |
| `agents.architect.model` | `ARCHITECT_MODEL` | `str` | `qwen3.8-27b:free` | `orchestrator/config/__init__.py:160` | Decomposes complex specs into milestone DAGs and `PLAN.md`. | Free-tier models may occasionally hallucinate file boundaries. |
| `agents.architect.temperature` | - | `float` | `0.3` | `orchestrator/config/__init__.py:165` | Balances architectural exploration with deterministic structure. | High values (>0.7) degrade Markdown milestone parsing accuracy. |
| `agents.architect.skills` | - | `list[str]` | `[decomposition, contract, graft]` | `orchestrator/config/__init__.py:166` | Injects architectural standards and codebase map. | Unnecessary skills consume token context. |
| `agents.developer.model` | `DEVELOPER_MODEL` | `str` | `qwen3.8-27b:free` | `orchestrator/config/__init__.py:115` | Core implementation engine generating idiomatic code. | Weaker models require more iterations to pass tests. |
| `agents.developer.temperature` | - | `float` | `0.2` | `orchestrator/config/__init__.py:121` | Deterministic, bug-free code generation. | Very low temperature may struggle to break out of syntax ruts. |
| `agents.developer.skills` | - | `list[str]` | `[clean-python, debugging, docker, graft]` | `orchestrator/config/__init__.py:122` | Enforces zero-stub standards, systematic debugging, containerization. | Extra skills increase prompt token baseline. |
| `agents.tester.model` | `TESTER_MODEL` | `str` | `qwen3.8-27b:free` | `orchestrator/config/__init__.py:133` | Rigorous pytest test case generation and execution. | Hallucinated mock fixtures if model is low quality. |
| `agents.tester.temperature` | - | `float` | `0.0` | `orchestrator/config/__init__.py:139` | Strictly deterministic test assertions without random variability. | None; test generation requires zero stochastic hallucination. |
| `agents.tester.skills` | - | `list[str]` | `[pytest-rigorous-testing]` | `orchestrator/config/__init__.py:140` | Enforces pytest isolation, edge cases, deterministic fixtures. | None. |
| `agents.reviewer.model` | `REVIEWER_MODEL` | `str` | `gemini-2.0-flash-exp:free` | `orchestrator/config/__init__.py:146` | Uncompromising security and code review with structured JSON output. | Overly strict models might reject valid minor style variations. |
| `agents.reviewer.temperature` | - | `float` | `0.1` | `orchestrator/config/__init__.py:152` | Deterministic JSON verdict (`APPROVED` / `REJECTED`). | High values risk malformed JSON output. |
| `agents.reviewer.skills` | - | `list[str]` | `[code-review, security-audit]` | `orchestrator/config/__init__.py:153` | Checks OWASP, secret leaks, boundary integrity, adherence to plan. | High token overhead if skills are uncompressed. |
| `memory.enabled` | `ENABLE_MEMORY` | `bool` | `true` | `orchestrator/config/__init__.py:85` | Injects historical lessons, past bug fixes, and project context across runs. | May inject irrelevant memory if similarity score threshold is too low. |
| `memory.relevance_min_score` | `MEMORY_RELEVANCE_MIN_SCORE` | `float` | `3.0` | `orchestrator/config/__init__.py:196` | Keyword TF-IDF matching filter ensuring only highly pertinent history is passed. | High score (>5.0) filters out useful context. |
| `memory.max_memory_results` | `MAX_MEMORY_RESULTS` | `int` | `3` | `orchestrator/config/__init__.py:199` | Caps number of past session summaries injected into prompt. | Higher count burns tokens. |
| `memory.max_memory_chars` | `MAX_MEMORY_CHARS` | `int` | `1500` | `orchestrator/config/__init__.py:202` | Hard character truncation ceiling for memory context block. | Prevents memory context from overwhelming model window. |
| `telemetry.max_retained_reports` | `MAX_RETAINED_REPORTS` | `int` | `20` | `orchestrator/config/__init__.py:91` | Manages diagnostics disk footprint by rotating out oldest JSON reports. | Low values discard historical longitudinal trend data. |
| `telemetry.max_retained_sessions_per_project` | `MAX_RETAINED_SESSIONS_PER_PROJECT` | `int` | `10` | `orchestrator/config/__init__.py:94` | Limits session logs stored per project. | Old debug replays are purged after ceiling. |
| `telemetry.log_save_debounce_seconds` | `LOG_SAVE_DEBOUNCE_SECONDS` | `int` | `5` | `orchestrator/config/__init__.py:97` | Debounces disk writes during intensive multi-agent action loops. | Abrupt process kill within 5s window might lose last actions. |
| `safety.terminal_command_allowlist` | - | `list[str]` | `[pytest, python, pip, uv, git, ...]` | `orchestrator/config/__init__.py:175` | Restricts agent command execution to safe, pre-approved developer tooling. | Blocks custom binaries unless explicitly added by administrator. |
| `safety.blocked_write_prefixes_developer` | - | `list[str]` | `["tests/"]` | `orchestrator/config/__init__.py:182` | Prevents developer agent from modifying test suites to artificially "pass" tests. | Blocks valid test refactoring unless done by tester agent. |
| `safety.allowed_write_prefixes_architect` | - | `list[str]` | `["PLAN.md"]` | `orchestrator/config/__init__.py:185` | Ensures architect only writes specification files and cannot mutate code. | Architect cannot create scaffold files. |
| `safety.allowed_write_prefixes_auditor` | - | `list[str]` | `["AUDIT_REPORT.md", ...]` | `orchestrator/config/__init__.py:188` | Enforces auditor immutability—auditors report findings without mutating source. | Auditor cannot auto-apply fixes directly without remediation pipeline. |
| `graft.enabled` | `GRAFT_ENABLED` | `bool` | `true` | `orchestrator/config/__init__.py:190` | Injects codebase call graph and API skeleton into architect and developer prompts. | Adds small disk cache generation time on first execution. |
| `graft.max_age_seconds` | `GRAFT_MAX_AGE_SECONDS` | `float` | `300.0` | `orchestrator/config/__init__.py:193` | Reuses cached graft graph within 5 minutes. | Modifying files outside the orchestrator might use stale graph. |
| `rendering.verbosity` | `VERBOSITY` | `str` | `normal` | `orchestrator/config/__init__.py:82` | Controls terminal detail: `quiet` (milestones only), `normal` (panels), `verbose` (full thoughts). | `verbose` can clutter terminal output. |
| `rendering.show_diff_preview` | `SHOW_DIFF_PREVIEW` | `bool` | `true` | `orchestrator/config/__init__.py:199` | Renders color-coded diff highlights for all file modifications. | Increases terminal scroll buffer usage. |
| `human_in_the_loop.interactive` | `INTERACTIVE` | `bool` | `false` | `orchestrator/config/__init__.py:79` | Activates interactive approval prompts at critical milestones. | Requires human operator presence; halts automated CI runs. |
| `human_in_the_loop.approval_gates` | `APPROVAL_GATES` | `list[str]` | `[]` | `orchestrator/config/__init__.py:72` | Granular check gates (e.g. `after_architect`, `after_developer`, `before_commit`). | Each gate pauses execution until confirmed by operator. |

---

## 🛠️ Environment Recipes

### 1. Zero-Cost Free-Tier Developer Recipe
Ideal for local experimentation and MVP development:
```json
{
  "execution": {
    "max_iterations": 3,
    "max_budget_usd": 0.10,
    "auto_commit": true
  },
  "agents": {
    "architect": { "model": "openrouter/qwen/qwen3.8-27b:free", "temperature": 0.3 },
    "developer": { "model": "openrouter/qwen/qwen3.8-27b:free", "temperature": 0.2 },
    "tester":    { "model": "openrouter/qwen/qwen3.8-27b:free", "temperature": 0.0 },
    "reviewer":  { "model": "openrouter/google/gemini-2.0-flash-exp:free", "temperature": 0.1 }
  },
  "rendering": { "verbosity": "normal" }
}
```

### 2. High-Assurance Enterprise Production Recipe
Recommended for mission-critical software refactoring and enterprise auditing:
```json
{
  "execution": {
    "max_iterations": 6,
    "max_budget_usd": 2.50,
    "circuit_breaker_threshold": 3,
    "auto_commit": true
  },
  "agents": {
    "architect": { "model": "anthropic/claude-sonnet-4-5-20250929", "temperature": 0.2 },
    "developer": { "model": "anthropic/claude-sonnet-4-5-20250929", "temperature": 0.1 },
    "tester":    { "model": "openai/gpt-4o", "temperature": 0.0 },
    "reviewer":  { "model": "anthropic/claude-sonnet-4-5-20250929", "temperature": 0.0 }
  },
  "safety": {
    "blocked_write_prefixes_developer": ["tests/", "PLAN.md"]
  },
  "human_in_the_loop": {
    "interactive": true,
    "approval_gates": ["after_architect", "before_commit"]
  }
}
```

### 3. Automated Headless CI/CD Pipeline Recipe
Designed for GitHub Actions, GitLab CI, or Jenkins background verification:
```json
{
  "execution": {
    "max_iterations": 4,
    "max_budget_usd": 0.75,
    "circuit_breaker_threshold": 2,
    "auto_commit": false,
    "auto_chain_audit": true
  },
  "rendering": {
    "verbosity": "quiet",
    "show_diff_preview": false
  },
  "human_in_the_loop": {
    "interactive": false,
    "approval_gates": []
  }
}
```
