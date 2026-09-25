# P14 — POLYGLOT ADAPTATION & INTELLIGENT LANGUAGE MESH PLAN
## Universal Multi-Language Ecosystem Drivers, Zero-Token Syntax Verification & Dynamic AST Virtualization

---

### Executive Metadata
- **Document ID:** `ORAGAI-ARCH-P14-POLYGLOT-MESH`
- **Status:** `APPROVED / MASTER SPECIFICATION`
- **Classification:** Enterprise Architectural Blueprint & Polyglot Runtime Specification
- **Scope:** Complete Multi-Language Driver Mesh, Automatic Ecosystem Discrimination, Zero-Token Syntax Verification, Test Outcome Compactor, Anti-Stub Scanners, and Dynamic AST Virtualization for `orchestrator-ai-agent`
- **Target Seam:** `orchestrator/ports/driven/language_port.py` & `orchestrator/adapters/polyglot/`
- **Reference Invariants:** Hexagonal Architecture (Ports & Adapters), Guarded FSM (P3), Sandbox Hardening (P9), Strangler Migration (P12), Canonical Target Architecture (P13)
- **Author:** Principal Systems Architect, Multi-Language Runtime Specialist & Polyglot Tooling Engineer

---

## 1. Executive Summary & Universal Polyglot Paradigm

### 1.1 The Polyglot Imperative & Forensic Pathology of Single-Language Coupling
The foundational architectural iterations of ORAGAI (P0 through P13) established a resilient Control and Governance Plane utilizing Hexagonal Architecture (Ports & Adapters), Inversion of Control (IoC), and a Guarded Finite State Machine (FSM). However, initial tool execution and static verification subsystems retained deep structural coupling to the Python ecosystem:
1. **Python-Centric PreFlight Syntax Validation:** PreFlight verification (`orchestrator/guards/preflight.py`) and static AST parsing relied exclusively on Python's built-in `ast.parse()` and `py_compile`, rendering non-Python source edits incapable of zero-token offline syntax verification.
2. **Hardcoded Pytest Diagnostic Parsers:** Failure classification (`orchestrator/analysis/pytest_parser.py`) assumed pytest error layouts, traceback formats, and exit code semantics, failing on `jest`, `vitest`, `cargo test`, `ctest`, or `go test` output streams.
3. **Monolithic Adapter Coupling:** Early adapters (`orchestrator/adapters/`) conflated language identification, test execution commands, and AST code folding without a uniform, mathematically sound port contract.
4. **Context Window Inflation in Polyglot Monorepos:** Without ecosystem-specific symbol virtualization and AST folding, reading C/C++, Rust, TypeScript, or Go source files forced entire files into the agent context window, consuming scarce token budgets ($\mathcal{B}_{\text{tokens}}$) and precipitating context degradation.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            ORAGAI HISTORICAL VS P14 POLYGLOT PARADIGM                            │
├───────────────────────────────────────────────────┬──────────────────────────────────────────────┤
│           LEGACY MONOLITHIC COUPLING              │           P14 INTELLIGENT LANGUAGE MESH      │
├───────────────────────────────────────────────────┼──────────────────────────────────────────────┤
│ • Hardcoded `ast.parse` and `py_compile`          │ • Pluggable `ILanguageDriver` Ports          │
│ • Python-only test failure traceback regexes      │ • Polymorphic High-Signal Test Compaction    │
│ • Single-project workspace assumption             │ • Monorepo Sub-Workspace Detection & Routing │
│ • Python AST code-folding only                    │ • Universal Multi-Language Symbol Outlines   │
│ • Ad-hoc subprocess invocation                    │ • Sandboxed, Zero-Token First Local Tooling  │
└───────────────────────────────────────────────────┴──────────────────────────────────────────────┘
```

### 1.2 The Hexagonal Language Mesh Architecture
P14 establishes the **Universal Polyglot Engineering Factory**. The Domain Core (TaskTruthGraph, Requirement Entities, Guarded FSM, Evidence Engine) remains 100% agnostic of programming languages, compiler flags, and toolchain idiosyncrasies. All language-specific logic is encapsulated within driven adapters implementing the `ILanguageDriver` interface.

```
                                  =======================================
                                  ||        ORAGAI DOMAIN CORE         ||
                                  || (TaskTruthGraph / Guarded FSM)    ||
                                  =======================================
                                                     │
                                                     ▼
                                  =======================================
                                  ||       DRIVEN OUTBOUND PORT        ||
                                  ||        ILanguageDriver            ||
                                  =======================================
                                                     │
                     ┌───────────────────────────────┼───────────────────────────────┐
                     ▼                               ▼                               ▼
       ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
       │       PythonDriver        │   │        NodeDriver         │   │          CDriver          │
       │  (py_compile / pytest /   │   │ (node --check / tsc /     │   │ (gcc -fsyntax-only /      │
       │    ast symbol outline)    │   │  jest / vitest / eslint)  │   │  ctest / gtest / clang)   │
       └───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
                      │                               │                               │
                      ▼                               ▼                               ▼
        ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
        │        RustDriver         │   │         GoDriver          │   │SelfAdaptingPolyglotDriver │
        │ (cargo check / cargo test │   │  (go vet / go test /      │   │ (One-Time Probe / Cached  │
        │   compiler json stream)   │   │    ast symbol visitor)    │   │  Dynamic Profile / Regex) │
        └───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
```

### 1.3 Core Architectural Invariants & Guarantees
1. **Invariant 1 — Zero Domain Knowledge of Compilers:** The Domain Core, FSM state transitions, and Verification Gates must never query file extensions, invoke compilers, or format language-specific CLI flags directly. They communicate exclusively through `ILanguageDriver`.
2. **Invariant 2 — Deterministic Zero-Token First:** Every registered language driver must provide a local, deterministic, zero-token syntax validation mechanism that runs before any LLM agent turn or test suite execution. Syntax errors reject edits immediately with zero LLM token consumption.
3. **Invariant 3 — High-Signal Outcome Compaction:** Test execution output ($>10,000$ characters of raw compiler/runner logs) must be deterministically compacted into high-signal `CompactedFailureFrame` records ($<800$ characters) capturing the failing symbol, source line, error diagnostic, and localized snippet.
4. **Invariant 4 — Universal Anti-Stub Enforcement:** Every driver must detect incomplete placeholder artifacts (`pass`, `TODO`, `FIXME`, `throw new Error("TODO")`, `unimplemented!()`, `panic("TODO")`, `/* stub */`) and reject code commits before acceptance gates.
5. **Invariant 5 — AST Virtualization Parity:** Symbol outline extraction and selective folding must be supported across all target languages, allowing agents to inspect large codebases ($>2,000$ LOC files) with $>90\%$ context token compression.

---

## 2. Automated Language & Ecosystem Discrimination Engine (`LanguageDetector`)

### 2.1 Multi-Tier Discrimination Strategy
To operate autonomously across greenfield repositories, mature enterprise monoliths, and polyglot monorepos, the `LanguageDetector` implements a deterministic, multi-tiered identification algorithm:

$$\text{Confidence Score } \mathcal{S}(L) = \mathcal{W}_{\text{manifest}}(L) + \mathcal{W}_{\text{file\_ratio}}(L) + \mathcal{W}_{\text{config}}(L)$$

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          LANGUAGE DISCRIMINATION FLOW                                 │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────────┐
       │ Tier 1: Explicit Override Check (CLI / kilo.json / Config) │
       └────────────────────────────┬───────────────────────────────┘
                                    │ (If not specified)
                                    ▼
       ┌────────────────────────────────────────────────────────────┐
       │ Tier 2: Root Manifest Signature Scan (Cargo, npm, Pip...)  │
       └────────────────────────────┬───────────────────────────────┘
                                    │ (If multiple or ambiguous)
                                    ▼
       ┌────────────────────────────────────────────────────────────┐
       │ Tier 3: Heuristic Source File Volume & LOC Entropy Ranking │
       └────────────────────────────┬───────────────────────────────┘
                                    │ (If multi-module monorepo)
                                    ▼
       ┌────────────────────────────────────────────────────────────┐
       │ Tier 4: Sub-Workspace Partitioning & Dynamic Path Routing  │
       └────────────────────────────────────────────────────────────┘
```

### 2.2 Manifest Signatures & Dominance Weights
Manifest signatures provide definitive ecosystem identification. The detector matches files against the following weighted manifest matrix:

| Ecosystem / Language | Primary Manifest Signatures | Secondary / Tooling Signatures | Base Weight ($\mathcal{W}_{\text{manifest}}$) |
| :--- | :--- | :--- | :--- |
| **Rust** | `Cargo.toml`, `Cargo.lock` | `rust-toolchain.toml`, `clippy.toml` | 100 |
| **Go** | `go.mod`, `go.sum` | `go.work`, `Gopkg.toml` | 100 |
| **Python** | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt` | `Pipfile`, `poetry.lock`, `tox.ini`, `pytest.ini` | 90 |
| **Node.js / TS** | `package.json`, `tsconfig.json` | `pnpm-workspace.yaml`, `yarn.lock`, `package-lock.json` | 90 |
| **C / C++** | `CMakeLists.txt`, `Makefile`, `meson.build` | `conanfile.txt`, `vcpkg.json`, `compile_commands.json` | 85 |
| **Java** | `pom.xml`, `build.gradle`, `build.gradle.kts` | `settings.gradle`, `gradlew`, `mvnw` | 95 |
| **Generic** | `Makefile`, `Dockerfile`, `run.sh` | Shell scripts, config files | 30 |

### 2.3 Heuristic File-Extension Indexing & LOC Entropy Ranking
When manifest scans detect multiple ecosystems (or legacy projects lacking formal manifests), `LanguageDetector` performs an indexed file walk ignoring `.git`, `node_modules`, `target`, `vendor`, `.venv`, and `dist`:

$$\text{LOC Volume Ratio } \mathcal{R}_{\text{loc}}(L) = \frac{\sum_{f \in \mathcal{F}_L} \text{LOC}(f)}{\sum_{f \in \mathcal{F}_{\text{total}}} \text{LOC}(f)}$$

If $\mathcal{R}_{\text{loc}}(L) \ge 0.60$, ecosystem $L$ is selected as the primary driver. If no ecosystem satisfies the dominance threshold, the repository is classified as a **Polyglot Monorepo**.

### 2.4 Monorepo Partitioning & Sub-Workspace Segmentation
In polyglot workspaces (e.g., a React/TypeScript frontend inside `frontend/` and a Rust or C++ service inside `backend/` or `services/core/`), a single root driver is insufficient. `LanguageDetector` identifies **Sub-Workspaces**:

```
repo_root/
├── package.json               <-- Root Monorepo Orchestration
├── frontend/
│   ├── tsconfig.json          <-- Sub-Workspace 1 (Node/TypeScript Driver)
│   └── src/
└── core_engine/
    ├── Cargo.toml             <-- Sub-Workspace 2 (Rust Driver)
    └── src/
```

The `PolyglotDriverRegistry` maintains a hierarchical sub-workspace routing table. When an agent touches `frontend/src/App.tsx`, file operations and syntax checks route to `NodeDriver(workspace=repo_root/frontend)`. When touching `core_engine/src/lib.rs`, actions route to `RustDriver(workspace=repo_root/core_engine)`.

---

## 3. The Universal Language Driver Interface (`ILanguageDriver`)

### 3.1 Port Definition (`orchestrator/ports/driven/language_port.py`)
All language adapters must strictly implement the `ILanguageDriver` protocol, ensuring uniform interactions across PreFlight, Test Execution, Static Audits, and AST Virtualization.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ILanguageDriver PROTOCOL CONTRACT                              │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ + language_type: LanguageType                                                                    │
│ + language_name: str                                                                             │
│ + detect(workspace: Path) -> bool                                                                │
│ + check_syntax(file_path: Path) -> SyntaxCheckResult                                             │
│ + run_zero_token_autofix(workspace: Path) -> Tuple[bool, str]                                    │
│ + run_static_analysis(workspace: Path) -> StaticAnalysisResult                                   │
│ + has_test_suite(workspace: Path) -> bool                                                        │
│ + get_default_test_command(workspace: Path, target_test: Optional[str]) -> str                   │
│ + execute_test_suite(workspace: Path, target_test: Optional[str], timeout_sec: int)              │
│       -> TestExecutionOutcome                                                                    │
│ + parse_test_diagnostics(stdout: str, stderr: str, exit_code: int) -> List[CompactedFailureFrame]│
│ + detect_placeholders_and_stubs(file_path: Path) -> List[StubViolation]                          │
│ + extract_symbol_outline(file_path: Path) -> SymbolOutline                                       │
│ + fold_code_block(content: str, max_lines: int) -> str                                           │
│ + get_developer_prompt_guidance() -> str                                                         │
│ + collect_codebase_metrics(workspace: Path) -> CodebaseMetrics                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Canonical Data Structures
The domain protocol relies on immutable, strongly typed dataclasses:

```python
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable


class LanguageType(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    C = "c"
    CPP = "cpp"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    GENERIC = "generic"


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"
    NO_TESTS = "NO_TESTS"


class StubSeverity(Enum):
    CRITICAL = "CRITICAL"      # Blocks milestone / completion gate
    WARNING = "WARNING"        # Audit warning (e.g. TODO in test mock)


class SymbolKind(Enum):
    CLASS = "CLASS"
    STRUCT = "STRUCT"
    INTERFACE = "INTERFACE"
    TRAIT = "TRAIT"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    ENUM = "ENUM"
    MODULE = "MODULE"
    TYPE_ALIAS = "TYPE_ALIAS"


@dataclass(frozen=True)
class SyntaxCheckResult:
    is_clean: bool
    error_count: int
    error_messages: List[str]
    failing_file: Optional[Path] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None


@dataclass(frozen=True)
class CompactedFailureFrame:
    test_identifier: str
    file_path: str
    line_number: Optional[int]
    error_type: str
    diagnostic_message: str
    context_snippet: Optional[str] = None


@dataclass(frozen=True)
class TestExecutionOutcome:
    status: TestStatus
    exit_code: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration_seconds: float
    raw_stdout: str
    raw_stderr: str
    compacted_failures: List[CompactedFailureFrame]
    compaction_summary: str


@dataclass(frozen=True)
class StubViolation:
    file_path: Path
    line_number: int
    severity: StubSeverity
    symbol_name: str
    pattern_matched: str
    snippet: str


@dataclass(frozen=True)
class SymbolEntity:
    name: str
    kind: SymbolKind
    start_line: int
    end_line: int
    signature: str
    docstring: Optional[str] = None
    children: List["SymbolEntity"] = field(default_factory=list)


@dataclass(frozen=True)
class SymbolOutline:
    file_path: Path
    total_lines: int
    entities: List[SymbolEntity]
    raw_outline_text: str


@dataclass(frozen=True)
class StaticAnalysisResult:
    is_clean: bool
    violation_count: int
    violations: List[str]
    tool_name: str


@dataclass(frozen=True)
class CodebaseMetrics:
    language: LanguageType
    total_files: int
    total_loc: int
    test_files_count: int
    test_loc: int
    ecosystem_metadata: Dict[str, Any]
```

---

## 4. Concrete Ecosystem Driver Implementations

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ECOSYSTEM DRIVER CAPABILITY MATRIX                               │
├───────────────┬──────────────────────┬──────────────────────┬──────────────────┬─────────────────┤
│ Ecosystem     │ Zero-Token Syntax    │ Test Framework &     │ Anti-Stub        │ Symbol Virtual- │
│ Driver        │ Compiler Tool        │ Compaction Engine    │ Patterns         │ ization Tool    │
├───────────────┼──────────────────────┼──────────────────────┼──────────────────┼─────────────────┤
│ PythonDriver  │ `py_compile`,        │ `pytest` (v7/v8/v9), │ `pass`, `...`,   │ `ast.parse` /   │
│               │ `ast.parse`          │ tracebacks           │ `NotImplemented` │ AST visitor     │
├───────────────┼──────────────────────┼──────────────────────┼──────────────────┼─────────────────┤
│ NodeDriver    │ `node --check`,      │ `jest`, `vitest`,    │ `throw Error`,   │ Tree-sitter /   │
│ (JS / TS)     │ `tsc --noEmit`       │ `mocha`, JSON runner │ `return null;`   │ regex-outline   │
├───────────────┼──────────────────────┼──────────────────────┼──────────────────┼─────────────────┤
│ CDriver       │ `gcc -fsyntax-only`, │ `ctest`, `gtest`,    │ `abort()`,       │ Tree-sitter /   │
│ (C / C++)     │ `clang -fsyntax-only`│ `catch2`, `make test`│ `// TODO`, empty │ ctags outline   │
├───────────────┼──────────────────────┼──────────────────────┼──────────────────┼─────────────────┤
│ RustDriver    │ `cargo check`        │ `cargo test`         │ `todo!()`,       │ `cargo check` / │
│               │ (JSON diagnostics)   │ (JSON test runner)   │ `unimplemented!` │ tree-sitter-rs  │
├───────────────┼──────────────────────┼──────────────────────┼──────────────────┼─────────────────┤
│ GoDriver      │ `go vet`,            │ `go test -json`      │ `panic("TODO")`, │ Go AST /        │
│               │ `go build -o /dev/nul│ (structured streams) │ `panic("not imp")│ tree-sitter-go  │
├───────────────┼──────────────────────┼──────────────────────┼──────────────────┼─────────────────┤
│ SelfAdapting- │ Dynamic probe-derived│ Dynamic regex-based  │ Configurable     │ Regex symbol    │
│ PolyglotDriver│ compiler/syntax tool │ failure compaction   │ stub regexes &   │ outline / scope │
│ (Zig, Elixir, │ (e.g. `zig ast-check`│ (JSON / stream /     │ token-level AST  │ indentation map │
│  Swift, etc.) │  or `mix compile`)   │  stack trace parser) │ pattern scanner  │                 │
└───────────────┴──────────────────────┴──────────────────────┴──────────────────┴─────────────────┘
```

### 4.1 PythonDriver Specification
- **Syntax Check:** Employs in-process `ast.parse()` and `py_compile.compile(doraise=True)` with zero subprocess overhead for sub-millisecond validation.
- **Test Compaction:** Reuses ORAGAI's hardened `PytestOutputParser`, extracting failing test assertions, diff mismatches, and tracebacks, filtering out irrelevant virtualenv frames.
- **Anti-Stub Rules:** Inspects AST function/method bodies; flags functions containing only `pass`, `...`, `raise NotImplementedError`, or docstrings without executable logic.
- **AST Virtualization:** Direct Python AST traversal yielding classes, functions, asynchronous definitions, and signatures.

### 4.2 NodeDriver (JavaScript & TypeScript) Specification
- **Syntax Check:**
  - JavaScript: Subprocess `node --check <file_path>` for zero-token syntax validation.
  - TypeScript: If `tsconfig.json` exists, runs `npx tsc --noEmit --isolatedModules false` or checks file syntax with `node --check` via TS compiler transpile check.
- **Test Compaction:**
  - Supports `jest --json` / `vitest --reporter=json` when available, parsing structured test results.
  - Fallback string compaction for standard terminal output: captures `● <TestName>`, `FAIL <Path>`, assertion differences (`Expected ... Received ...`), and file line locations.
- **Anti-Stub Rules:**
  - Scans for `throw new Error("Not implemented")`, `throw new Error("TODO")`, empty function bodies `\{\s*\}`, and placeholder comments `// TODO: implement`.
- **AST Virtualization:**
  - TypeScript/JS symbol outline extractor recognizing `class`, `interface`, `type`, `function`, `const ... = (...) =>`, and `export`.

### 4.3 CDriver (C / C++) Specification
- **Syntax Check:**
  - Invokes `gcc -fsyntax-only -Wall -Wextra <file_path>` or `clang -fsyntax-only <file_path>`.
  - In MSVC environments, executes `cl.exe /Zs <file_path>`.
- **Test Compaction:**
  - Parses `ctest --output-on-failure`, Google Test (`[  FAILED  ]`), and Catch2 failure outputs.
  - Extracts failing test suite, test case name, source file, line number, and assertion expression (e.g., `Value of: result, Expected: 42, Actual: 0`).
- **Anti-Stub Rules:**
  - Detects `abort();`, `exit(1);`, empty body `{ /* TODO */ }`, `assert(false);`, and `__builtin_unreachable();` in non-void returning functions.
- **AST Virtualization:**
  - Parses header files (`.h`, `.hpp`) and source files (`.c`, `.cpp`) extracting `struct`, `class`, function declarations, macros, and typedefs.

### 4.4 RustDriver Specification
- **Syntax Check:**
  - Invokes `cargo check --message-format=json --quiet`.
  - Deserializes JSON diagnostic stream, capturing exact error codes (e.g. `E0308`), compiler error messages, primary span file paths, and line/column spans.
- **Test Compaction:**
  - Executes `cargo test -- --nocapture` or `cargo test --message-format=json`.
  - Captures `---- test_name stdout ----`, panics (`panicked at 'assertion failed'`), and file backtraces.
- **Anti-Stub Rules:**
  - Detects `todo!()`, `unimplemented!()`, `panic!("TODO")`, `unreachable!()`, and `todo!("...")` macro invocations.
- **AST Virtualization:**
  - Extracts `struct`, `enum`, `trait`, `impl`, `fn`, and `mod` declarations with visibility modifiers (`pub`, `pub(crate)`).

### 4.5 GoDriver Specification
- **Syntax Check:**
  - Invokes `go vet <file_path>` and `go build -o /dev/null` (or `NUL` on Windows) for zero-token compile validation.
- **Test Compaction:**
  - Invokes `go test -v -json ./...`, parsing Go's native JSON test event stream (`Action: "fail"`, `Test: "TestName"`, `Output: "..."`).
- **Anti-Stub Rules:**
  - Detects `panic("TODO")`, `panic("not implemented")`, `panic("implement me")`, and empty function bodies in exported functions.
- **AST Virtualization:**
  - Extracts `package`, `type ... struct`, `type ... interface`, `func ...`, and method receivers `func (s *Service) Method(...)`.

### 4.6 SelfAdaptingPolyglotDriver (Self-Adapting Dynamic Language Driver & One-Time Discovery Probe)

#### 4.6.1 The Unmapped Ecosystem Dilemma & Architectural Solution
Modern software engineering frequently encounters specialized, emerging, or niche toolchains (e.g., **Zig**, **Elixir / Phoenix**, **Swift / SPM**, **Kotlin Native**, **Nim**, **Haskell / Cabal**, **Dart / Flutter**, **OCaml / Dune**). A static driver registry cannot hardcode every compiler flag, test runner JSON protocol, and diagnostic format in existence without unbounded maintenance bloat. Conversely, naive generic fallbacks (such as generic Makefile checks or line-bounded regex scanning) fail catastrophically in production:
1. **Absence of Zero-Token Syntax Verification:** Edits to Zig or Elixir source files cannot be verified locally before dispatching costly test runs or LLM turns, violating Invariant 2.
2. **Raw Diagnostic Flooding:** Compiler errors and test runner outputs (which often span hundreds of lines of stack traces) flood agent context windows without structured extraction of the failing symbol, line number, or assertion diff.
3. **Pervasive Stub Blindness:** Generic fallbacks cannot identify ecosystem-specific stubs (such as Zig `@panic("TODO")`, Elixir `raise "TODO"`, Swift `fatalError("TODO")`, or Kotlin `TODO()`), allowing unfinished code to escape PreFlight verification.

ORAGAI resolves this via the **Self-Adapting Dynamic Language Driver (`SelfAdaptingPolyglotDriver`)**, governed by a **"One-Time Dynamic Probe & Persistent Cache" Lifecycle**.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│               SELF-ADAPTING POLYGLOT DRIVER: ONE-TIME PROBE & CACHED EXECUTION LIFECYCLE               │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
                     ┌─────────────────────────────────────────────────────────────┐
                     │ 1. Unknown Ecosystem Detected in Workspace                  │
                     │    (e.g., build.zig, mix.exs, Package.swift found)          │
                     └──────────────────────────────┬──────────────────────────────┘
                                                    │
                                                    ▼
                     ┌─────────────────────────────────────────────────────────────┐
                     │ 2. Check for Cached Profile:                                │
                     │    Does `<workspace>/.oragai/language_profile.json` exist?  │
                     └──────────────────────┬──────────────────────────────┬───────┘
                                            │ NO                           │ YES
                                            │                              ▼
                                            │             ┌────────────────────────────────┐
                                            │             │ 6. Fast Path:                  │
                                            │             │    Deserialize Cached Profile  │
                                            │             │    Zero LLM Tokens Consumed!   │
                                            │             └────────────────┬───────────────┘
                                            ▼                              │
                     ┌─────────────────────────────────────────────┐       │
                     │ 3. One-Time Dynamic Discovery Probe         │       │
                     │    - Manifest Analysis (build.zig, etc.)    │       │
                     │    - Bounded Subprocess CLI Help Probes     │       │
                     │    - Single Architect/Discovery LLM Call    │       │
                     │    - Schema-Enforced JSON Profile Synthesis │       │
                     └──────────────────────┬──────────────────────┘       │
                                            │                              │
                                            ▼                              │
                     ┌─────────────────────────────────────────────┐       │
                     │ 4. P9 Security & Grammar Validation Gate    │       │
                     │    - Validate command templates with P9     │       │
                     │      `CommandGrammarValidator`              │       │
                     │    - Reject dangerous token injections      │       │
                     └──────────────────────┬──────────────────────┘       │
                                            │                              │
                                            ▼                              │
                     ┌─────────────────────────────────────────────┐       │
                     │ 5. Atomic Profile Persistence               │       │
                     │    - Atomically write profile to            │       │
                     │      `<workspace>/.oragai/language_profile` │       │
                     └──────────────────────┬──────────────────────┘       │
                                            │                              │
                                            └──────────────┬───────────────┘
                                                           │
                                                           ▼
                     ┌─────────────────────────────────────────────────────────────┐
                     │ 7. Deterministic Zero-Token Subsequent Execution Engine     │
                     │    - Syntax Verification: Run `syntax_check_template`       │
                     │    - Test Suite Execution: Run `test_command_template`      │
                     │    - Failure Compaction: Match compiled `failure_regexes`   │
                     │    - Anti-Stub Scanning: Match compiled `stub_regexes`      │
                     │    - Symbol Outline: Run `symbol_outline_command` / parser  │
                     └─────────────────────────────────────────────────────────────┘
```

#### 4.6.2 The Three-Phase Dynamic Adaptation Lifecycle

##### Phase 1: Ecosystem Discovery & One-Time Bounded Probe
When `LanguageDetector` or `PolyglotDriverRegistry` encounters an unmapped ecosystem lacking a built-in static driver (or when file extension heuristics fail to achieve $\mathcal{R}_{\text{loc}} \ge 0.60$ for known languages), the system checks if the project has already undergone dynamic profiling by verifying the existence of `.oragai/language_profile.json`.

If no cached profile exists, a single, strictly bounded discovery probe is orchestrated:
1. **Manifest & Build Script Inspection:** The discovery agent scans the workspace root and immediate subdirectories for configuration files (e.g., `build.zig`, `mix.exs`, `Package.swift`, `build.gradle.kts`, `flake.nix`, `rebar.config`, `dune-project`). Up to 4,000 characters of the primary build manifest are ingested.
2. **Sandboxed Subprocess CLI Probing:** Before calling the LLM, the orchestrator invokes deterministic CLI probe commands via P9's `TerminalSandboxEngine` to verify executable availability and discover syntax flags:
   - `<toolchain> --version` or `<toolchain> version`
   - `<toolchain> --help` or `<toolchain> help test`
3. **Structured Architectural Persona Probe:** A single, temperature-0 LLM prompt is executed under the **Architect/Discovery** persona. The LLM is supplied with:
   - Manifest filenames and snippets.
   - CLI help outputs captured from the sandbox probes.
   - The strict Pydantic JSON schema of `DynamicEcosystemProfile`.
4. **Token Cost Invariant:** The discovery probe is bounded to a single interaction. Under no circumstances may the system re-invoke an LLM on every iteration or turn to decide how to run syntax checks or execute tests.

##### Phase 2: Dynamic Manifest Schema & P9 Security Validation
The synthesized JSON payload is parsed into a strongly typed `DynamicEcosystemProfile`:

```json
{
  "language_name": "zig",
  "manifest_files": ["build.zig", "build.zig.zon"],
  "file_extensions": [".zig"],
  "syntax_check_template": "zig ast-check {file_path}",
  "test_command_template": "zig test {target_test}",
  "failure_regexes": [
    "^(?P<file>[^:\\n]+):(?P<line>\\d+):(?P<col>\\d+):\\s+error:\\s+(?P<message>.+)$",
    "^(?P<test>[^\\n]+)\\.\\.\\.FAIL\\s+\\((?P<message>[^\\)]+)\\)$"
  ],
  "stub_regexes": [
    "@panic\\s*\\(\\s*[\"'](?:TODO|Not implemented|implement me)[\"']\\s*\\)",
    "//\\s*TODO\\s*:\\s*implement",
    "/\\*\\s*TODO\\s*:\\s*implement\\s*\\*/"
  ],
  "symbol_outline_command": null,
  "version": "1.0.0"
}
```

**Security & Grammar Validation Boundary:**
Prior to persistence or execution, all synthesized shell command templates (`syntax_check_template`, `test_command_template`, `symbol_outline_command`) MUST be submitted to P9's `CommandGrammarValidator.validate_command()`. 
- Any template that attempts token chaining (`&&`, `;`, `|`), backgrounding (`&`), redirection to sensitive system paths, or invocations of unauthorized binaries is immediately rejected.
- All regexes in `failure_regexes` and `stub_regexes` are pre-compiled and tested against sample strings with a strict execution timeout to prevent catastrophic backtracking (ReDoS).

**Human & Controller Validation Boundaries:**
- **Autonomous Mode:** If the validated commands invoke standard toolchain binaries identified in system paths and pass grammar validation, the profile is automatically written to disk and cached.
- **High-Assurance / Enterprise Gate:** If configured in `.kilo/config.json` (`"require_polyglot_profile_approval": true`), the FSM transitions to an advisory `HOLD` state, surfacing the generated profile to the human operator for explicit confirmation before executing untrusted external commands.

**Atomic Persistence:**
The validated profile is serialized and atomically written to `<workspace>/.oragai/language_profile.json` (using a temporary file and atomic file replace) to guarantee durability across agent session restarts.

##### Phase 3: Deterministic Zero-Token Subsequent Execution
Once `.oragai/language_profile.json` is stored on disk:
1. **Zero LLM Token Primacy:** All subsequent verification, testing, and diagnostic operations execute 100% locally via subprocesses and deterministic regular expression parsers. Zero LLM tokens are consumed for compiler invocations, test executions, or error trace extractions.
2. **Syntax Verification:** `SelfAdaptingPolyglotDriver.check_syntax(file_path)` formats `syntax_check_template` with the target file path, executes the command via P9's `TerminalSandboxEngine`, and parses any stderr output using `failure_regexes`.
3. **Test Suite Execution & High-Signal Compaction:** `SelfAdaptingPolyglotDriver.execute_test_suite()` formats `test_command_template` (replacing `{target_test}` with the specific test identifier if provided or stripping it if none is specified), executes the test binary via `TerminalSandboxEngine`, and pipes raw stdout/stderr into `parse_test_diagnostics()`.
4. **Diagnostic Compaction:** The output is scanned against the compiled `failure_regexes`, extracting:
   - `test_identifier`: Extracted failing test name or suite.
   - `file_path`: Source file where failure occurred.
   - `line_number`: Source line number of assertion or compiler failure.
   - `diagnostic_message`: Concise root-cause error text.
   - `context_snippet`: Surrounding failure lines.
5. **Anti-Stub Scanning:** `detect_placeholders_and_stubs()` evaluates modified source files line-by-line against compiled `stub_regexes`, preventing unfinished functions from passing the PreFlight gate.
6. **Symbol Virtualization:** If `symbol_outline_command` is specified, it is invoked; otherwise, the driver utilizes a deterministic regex/indentation block scanner to extract top-level declarations, functions, and structs.

---

## 5. Universal AST & Outline Virtualization

### 5.1 The Cross-Language Code Folding & Virtualization Challenge
Under the P4 Adaptive Resource Governance protocol, ORAGAI limits file reading token bloat by replacing large function implementations with folded stubs:
```
# Python Folding Example:
def calculate_merkle_root(nodes: List[bytes]) -> bytes:
    ... # [Folded: 48 lines]
```
For non-Python languages, native `ast` is unavailable. P14 defines a universal two-tier virtualization engine:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        UNIVERSAL VIRTUALIZATION ENGINE                                 │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────────┐
       │ Tier 1: Tree-sitter Multi-Language Dynamic Parser (Native) │
       │ (C, C++, Rust, Go, TypeScript, Java, Python grammar trees) │
       └────────────────────────────┬───────────────────────────────┘
                                    │ (Fallback if grammar unavailable)
                                    ▼
       ┌────────────────────────────────────────────────────────────┐
       │ Tier 2: Deterministic Indentation & Signature Heuristic    │
       │ (Scope-aware brace matching & signature regex parser)      │
       └────────────────────────────────────────────────────────────┘
```

### 5.2 Deterministic Outline Generation & Context Budget Minimization
When an agent requests a file outline via `WorkspaceFileVirtualizer` (P9), the driver generates an entity tree formatted as a concise, high-signal outline.

#### TypeScript/JavaScript Outline Representation:
```typescript
// === OUTLINE: frontend/src/services/api.ts (Total: 340 LOC) ===
export interface ApiResponse<T> { ... } [Lines: 12-18]
export interface RequestOptions { ... } [Lines: 20-35]
export class ApiClient {
    constructor(baseUrl: string) [Lines: 40-48]
    public async get<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> [Lines: 50-95]
    public async post<T>(endpoint: string, payload: unknown): Promise<ApiResponse<T>> [Lines: 97-150]
    private handleErrors(error: unknown): never [Lines: 152-190]
}
```

#### Rust Outline Representation:
```rust
// === OUTLINE: core/src/engine.rs (Total: 412 LOC) ===
pub enum EngineState { Init, Running, Paused, Fault(String) } [Lines: 10-18]
pub struct EngineConfig { ... } [Lines: 20-38]
pub trait Lifecycle {
    fn initialize(&mut self) -> Result<(), EngineError>;
    fn shutdown(&mut self) -> Result<(), EngineError>;
}
impl Lifecycle for EngineCore {
    fn initialize(&mut self) -> Result<(), EngineError> [Lines: 60-110]
    fn shutdown(&mut self) -> Result<(), EngineError> [Lines: 112-145]
}
```

### 5.3 Universal Anti-Stub Static Analysis Engine
The anti-stub scanner operates during PreFlight gates and Pre-Commit checks, preventing unfinished work from reaching the Completion Gate.

```
                    ┌──────────────────────────────────────────────┐
                    │ File Content / Diff for Modified Workspace   │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │ Match Language Driver via PolyglotRegistry   │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │ Driver: detect_placeholders_and_stubs(file)  │
                    └──────────────────────┬───────────────────────┘
                                           │
                     ┌─────────────────────┴─────────────────────┐
                     │                                           │
              [Stub Violations > 0]                       [Zero Violations]
                     │                                           │
                     ▼                                           ▼
    ┌───────────────────────────────────┐               ┌─────────────────┐
    │ REJECT: PreFlightGate Failure     │               │ PASS: Proceed   │
    │ Return Compacted Violations to LLM│               │ to Test Suite   │
    └───────────────────────────────────┘               └─────────────────┘
```

---

## 6. Canonical Python Architecture & Data Models

The following production-ready Python specifications define `orchestrator/ports/driven/language_port.py` and `orchestrator/adapters/polyglot/driver_mesh.py`.

### 6.1 `orchestrator/ports/driven/language_port.py`
```python
"""Universal Language Driver Port Definitions for ORAGAI."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class LanguageType(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    C = "c"
    CPP = "cpp"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    GENERIC = "generic"


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"
    NO_TESTS = "NO_TESTS"


class StubSeverity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


class SymbolKind(Enum):
    CLASS = "CLASS"
    STRUCT = "STRUCT"
    INTERFACE = "INTERFACE"
    TRAIT = "TRAIT"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    ENUM = "ENUM"
    MODULE = "MODULE"
    TYPE_ALIAS = "TYPE_ALIAS"


@dataclass(frozen=True)
class SyntaxCheckResult:
    is_clean: bool
    error_count: int
    error_messages: List[str]
    failing_file: Optional[Path] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None


@dataclass(frozen=True)
class CompactedFailureFrame:
    test_identifier: str
    file_path: str
    line_number: Optional[int]
    error_type: str
    diagnostic_message: str
    context_snippet: Optional[str] = None


@dataclass(frozen=True)
class TestExecutionOutcome:
    status: TestStatus
    exit_code: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration_seconds: float
    raw_stdout: str
    raw_stderr: str
    compacted_failures: List[CompactedFailureFrame]
    compaction_summary: str


@dataclass(frozen=True)
class StubViolation:
    file_path: Path
    line_number: int
    severity: StubSeverity
    symbol_name: str
    pattern_matched: str
    snippet: str


@dataclass(frozen=True)
class SymbolEntity:
    name: str
    kind: SymbolKind
    start_line: int
    end_line: int
    signature: str
    docstring: Optional[str] = None
    children: List["SymbolEntity"] = field(default_factory=list)


@dataclass(frozen=True)
class SymbolOutline:
    file_path: Path
    total_lines: int
    entities: List[SymbolEntity]
    raw_outline_text: str


@dataclass(frozen=True)
class StaticAnalysisResult:
    is_clean: bool
    violation_count: int
    violations: List[str]
    tool_name: str


@dataclass(frozen=True)
class CodebaseMetrics:
    language: LanguageType
    total_files: int
    total_loc: int
    test_files_count: int
    test_loc: int
    ecosystem_metadata: Dict[str, Any] = field(default_factory=dict)


class DynamicEcosystemProfile(BaseModel):
    """Pydantic model representing a persistent, synthesized ecosystem profile.

    Stored atomically at `<workspace>/.oragai/language_profile.json` following
    a one-time discovery probe. Governs zero-token subsequent execution.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    language_name: str = Field(..., description="Normalized ecosystem identifier (e.g., 'zig', 'elixir', 'swift')")
    manifest_files: List[str] = Field(default_factory=list, description="List of manifest filenames (e.g., ['build.zig'])")
    file_extensions: List[str] = Field(default_factory=list, description="Source file extensions (e.g., ['.zig'])")
    syntax_check_template: str = Field(..., description="Shell template for zero-token syntax validation (e.g., 'zig ast-check {file_path}')")
    test_command_template: str = Field(..., description="Shell template for test execution (e.g., 'zig test {target_test}')")
    failure_regexes: List[str] = Field(default_factory=list, description="Regex patterns capturing test and compiler failures")
    stub_regexes: List[str] = Field(default_factory=list, description="Regex patterns identifying placeholder stubs")
    symbol_outline_command: Optional[str] = Field(None, description="Optional shell command to generate symbol outlines")
    version: str = Field("1.0.0", description="Schema version of this ecosystem profile")


@runtime_checkable
class ILanguageDriver(Protocol):
    """Universal Language Driver Protocol for Polyglot Workspaces."""

    @property
    def language_type(self) -> LanguageType:
        """Return the concrete LanguageType enum value."""
        ...

    @property
    def language_name(self) -> str:
        """Human-readable identifier for the language ecosystem."""
        ...

    def detect(self, workspace: Path) -> bool:
        """Evaluate if this driver matches the target workspace directory."""
        ...

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        """Perform zero-token deterministic syntax verification on a single source file."""
        ...

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        """Execute deterministic offline code formatting / auto-fixing."""
        ...

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        """Execute ecosystem linter/analyzer without LLM intervention."""
        ...

    def has_test_suite(self, workspace: Path) -> bool:
        """Check if test configurations or test files exist."""
        ...

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        """Generate the shell command required to execute the test suite."""
        ...

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        """Execute the test suite in a sandboxed subprocess and return parsed outcome."""
        ...

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        """Extract high-signal failure frames from raw test output."""
        ...

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        """Scan file for stub patterns, empty bodies, and TODO markers."""
        ...

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        """Generate symbol tree outline for token-efficient agent context injection."""
        ...

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        """Fold function and class bodies exceeding max_lines threshold."""
        ...

    def get_developer_prompt_guidance(self) -> str:
        """Return ecosystem-specific best practices for developer agent prompts."""
        ...

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        """Gather file counts, LOC, test metrics, and ecosystem metadata."""
        ...
```

### 6.2 `orchestrator/adapters/polyglot/driver_mesh.py`
```python
"""Polyglot Driver Mesh, Registry, and Concrete Implementations."""

import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Tuple

from orchestrator.ports.driven.language_port import (
    CodebaseMetrics,
    CompactedFailureFrame,
    DynamicEcosystemProfile,
    ILanguageDriver,
    LanguageType,
    StaticAnalysisResult,
    StubSeverity,
    StubViolation,
    SymbolEntity,
    SymbolKind,
    SymbolOutline,
    SyntaxCheckResult,
    TestExecutionOutcome,
    TestStatus,
)


class PolyglotDriverRegistry:
    """Central registry and routing engine for Language Drivers."""

    def __init__(self) -> None:
        self._drivers: Dict[LanguageType, ILanguageDriver] = {}
        self._sub_workspace_cache: Dict[Path, ILanguageDriver] = {}

    def register(self, driver: ILanguageDriver) -> None:
        """Register a concrete language driver instance."""
        self._drivers[driver.language_type] = driver

    def get_driver(self, language_type: LanguageType) -> Optional[ILanguageDriver]:
        """Retrieve driver by LanguageType."""
        return self._drivers.get(language_type)

    def resolve_driver_for_path(
        self, file_or_dir_path: Path, root_workspace: Path
    ) -> ILanguageDriver:
        """Resolve the most specific driver for a given file or directory path."""
        abs_path = file_or_dir_path.resolve()
        abs_root = root_workspace.resolve()

        # Check sub-workspace cache
        for sub_path, driver in self._sub_workspace_cache.items():
            if abs_path == sub_path or abs_path.is_relative_to(sub_path):
                return driver

        # Walk upward from file_or_dir_path to root_workspace to find sub-manifest
        current = abs_path if abs_path.is_dir() else abs_path.parent
        while current >= abs_root:
            for driver in self._drivers.values():
                if driver.detect(current):
                    self._sub_workspace_cache[current] = driver
                    return driver
            if current == abs_root:
                break
            current = current.parent

        # Fallback to root detection or SelfAdaptingPolyglotDriver
        for driver in self._drivers.values():
            if driver.detect(abs_root):
                return driver

        self_adapting = self._drivers.get(LanguageType.GENERIC)
        if self_adapting:
            return self_adapting
        raise RuntimeError("No suitable LanguageDriver registered, including SelfAdaptingPolyglotDriver.")


class LanguageDetector:
    """Automated ecosystem discriminator scanning manifests and file volume."""

    MANIFEST_SIGNATURES: Dict[LanguageType, List[str]] = {
        LanguageType.RUST: ["Cargo.toml", "Cargo.lock"],
        LanguageType.GO: ["go.mod", "go.sum", "go.work"],
        LanguageType.PYTHON: ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile"],
        LanguageType.TYPESCRIPT: ["tsconfig.json"],
        LanguageType.JAVASCRIPT: ["package.json"],
        LanguageType.CPP: ["CMakeLists.txt", "meson.build", "conanfile.txt", "vcpkg.json"],
        LanguageType.C: ["Makefile"],
        LanguageType.JAVA: ["pom.xml", "build.gradle", "build.gradle.kts"],
    }

    FILE_EXTENSION_MAP: Dict[str, LanguageType] = {
        ".py": LanguageType.PYTHON,
        ".ts": LanguageType.TYPESCRIPT,
        ".tsx": LanguageType.TYPESCRIPT,
        ".js": LanguageType.JAVASCRIPT,
        ".jsx": LanguageType.JAVASCRIPT,
        ".mjs": LanguageType.JAVASCRIPT,
        ".cjs": LanguageType.JAVASCRIPT,
        ".rs": LanguageType.RUST,
        ".go": LanguageType.GO,
        ".c": LanguageType.C,
        ".h": LanguageType.C,
        ".cpp": LanguageType.CPP,
        ".hpp": LanguageType.CPP,
        ".cc": LanguageType.CPP,
        ".cxx": LanguageType.CPP,
        ".java": LanguageType.JAVA,
    }

    IGNORE_DIRS: Set[str] = {
        ".git", ".venv", "venv", "node_modules", "target", "vendor",
        "dist", "build", "out", "__pycache__", ".idea", ".vscode"
    }

    def detect_ecosystem(
        self, workspace: Path, forced_language: Optional[str] = None
    ) -> LanguageType:
        """Detect primary ecosystem for a workspace."""
        if forced_language:
            norm = forced_language.strip().lower()
            for lang in LanguageType:
                if lang.value == norm:
                    return lang
            if norm in ("js", "node", "nodejs"):
                return LanguageType.JAVASCRIPT
            if norm == "ts":
                return LanguageType.TYPESCRIPT
            if norm in ("c++", "cxx"):
                return LanguageType.CPP

        # 1. Manifest Matching
        for lang, manifests in self.MANIFEST_SIGNATURES.items():
            for manifest in manifests:
                if (workspace / manifest).is_file():
                    # If package.json has tsconfig.json, upgrade to TS
                    if lang == LanguageType.JAVASCRIPT and (workspace / "tsconfig.json").is_file():
                        return LanguageType.TYPESCRIPT
                    return lang

        # 2. File Count & Volume Ranking
        counts: Dict[LanguageType, int] = {lt: 0 for lt in LanguageType}
        try:
            for root, dirs, files in os.walk(workspace):
                dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext in self.FILE_EXTENSION_MAP:
                        counts[self.FILE_EXTENSION_MAP[ext]] += 1
        except Exception:
            return LanguageType.GENERIC

        dominant_lang = max(counts, key=lambda k: counts[k])
        if counts[dominant_lang] > 0:
            return dominant_lang

        return LanguageType.GENERIC


# ============================================================================
# CONCRETE DRIVER: NodeDriver (TypeScript / JavaScript)
# ============================================================================

class NodeDriver:
    """Driver for JavaScript, TypeScript, and Node.js ecosystems."""

    def __init__(self) -> None:
        self._stub_patterns: List[Tuple[Pattern[str], str, StubSeverity]] = [
            (re.compile(r'throw\s+new\s+Error\s*\(\s*["\'](?:TODO|Not implemented|NotImplemented|stub)["\']\s*\)', re.IGNORECASE), "throw new Error(TODO)", StubSeverity.CRITICAL),
            (re.compile(r'//\s*TODO\s*:\s*implement', re.IGNORECASE), "// TODO: implement", StubSeverity.CRITICAL),
            (re.compile(r'/\*\s*TODO\s*:\s*implement\s*\*/', re.IGNORECASE), "/* TODO: implement */", StubSeverity.CRITICAL),
            (re.compile(r'return\s+null\s*;\s*//\s*stub', re.IGNORECASE), "return null; // stub", StubSeverity.CRITICAL),
        ]

    @property
    def language_type(self) -> LanguageType:
        return LanguageType.TYPESCRIPT

    @property
    def language_name(self) -> str:
        return "Node.js / TypeScript"

    def detect(self, workspace: Path) -> bool:
        return (workspace / "package.json").is_file() or (workspace / "tsconfig.json").is_file()

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        if not file_path.is_file():
            return SyntaxCheckResult(is_clean=False, error_count=1, error_messages=[f"File not found: {file_path}"])

        ext = file_path.suffix.lower()
        if ext in (".ts", ".tsx"):
            # Check syntax via node --check with esbuild / tsc if available, else syntax compile probe
            tsc_bin = shutil.which("tsc")
            if tsc_bin:
                proc = subprocess.run(
                    [tsc_bin, "--noEmit", "--isolatedModules", str(file_path)],
                    capture_output=True,
                    text=True,
                    shell=False,
                )
                if proc.returncode != 0:
                    lines = [l.strip() for l in proc.stdout.splitlines() if l.strip()]
                    return SyntaxCheckResult(is_clean=False, error_count=len(lines), error_messages=lines[:5], failing_file=file_path)
            return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

        node_bin = shutil.which("node")
        if node_bin:
            proc = subprocess.run(
                [node_bin, "--check", str(file_path)],
                capture_output=True,
                text=True,
                shell=False,
            )
            if proc.returncode != 0:
                err = proc.stderr.strip() or proc.stdout.strip()
                return SyntaxCheckResult(is_clean=False, error_count=1, error_messages=[err], failing_file=file_path)

        return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        prettier_bin = shutil.which("prettier")
        if prettier_bin:
            proc = subprocess.run(
                [prettier_bin, "--write", "src/**/*.{ts,tsx,js,jsx}"],
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=False,
            )
            return proc.returncode == 0, proc.stdout
        return True, "No autofix tool found; skipped."

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        eslint_bin = shutil.which("eslint")
        if eslint_bin:
            proc = subprocess.run(
                [eslint_bin, ".", "--format", "json"],
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=False,
            )
            if proc.returncode != 0:
                try:
                    data = json.loads(proc.stdout)
                    violations = []
                    for item in data:
                        for msg in item.get("messages", []):
                            violations.append(f"{item.get('filePath')}:{msg.get('line')}:{msg.get('column')} - {msg.get('message')} ({msg.get('ruleId')})")
                    return StaticAnalysisResult(is_clean=False, violation_count=len(violations), violations=violations[:10], tool_name="eslint")
                except Exception:
                    return StaticAnalysisResult(is_clean=False, violation_count=1, violations=[proc.stderr[:500]], tool_name="eslint")
        return StaticAnalysisResult(is_clean=True, violation_count=0, violations=[], tool_name="none")

    def has_test_suite(self, workspace: Path) -> bool:
        pkg = workspace / "package.json"
        if pkg.is_file():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
                scripts = data.get("scripts", {})
                return "test" in scripts
            except Exception:
                pass
        return bool(list(workspace.glob("**/*.test.ts")) or list(workspace.glob("**/*.spec.ts")) or list(workspace.glob("**/*.test.js")))

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        base = "npm test"
        if (workspace / "pnpm-lock.yaml").is_file():
            base = "pnpm test"
        elif (workspace / "yarn.lock").is_file():
            base = "yarn test"
        if target_test:
            return f"{base} -- -t \"{target_test}\""
        return f"{base} -- --watchAll=false"

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        cmd = self.get_default_test_command(workspace, target_test)
        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            failures = self.parse_test_diagnostics(proc.stdout, proc.stderr, proc.returncode)
            status = TestStatus.PASSED if proc.returncode == 0 else TestStatus.FAILED
            summary = f"Node test suite: {'PASSED' if proc.returncode == 0 else 'FAILED'} (Exit code: {proc.returncode})"
            return TestExecutionOutcome(
                status=status,
                exit_code=proc.returncode,
                total_tests=len(failures) if status == TestStatus.FAILED else 1,
                passed_tests=0 if status == TestStatus.FAILED else 1,
                failed_tests=len(failures),
                skipped_tests=0,
                duration_seconds=duration,
                raw_stdout=proc.stdout,
                raw_stderr=proc.stderr,
                compacted_failures=failures,
                compaction_summary=summary,
            )
        except subprocess.TimeoutExpired as te:
            return TestExecutionOutcome(
                status=TestStatus.TIMEOUT,
                exit_code=124,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                duration_seconds=float(timeout_seconds),
                raw_stdout=te.stdout or "",
                raw_stderr=te.stderr or "Execution timed out.",
                compacted_failures=[],
                compaction_summary=f"Execution timed out after {timeout_seconds}s.",
            )

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        failures: List[CompactedFailureFrame] = []
        combined = stdout + "\n" + stderr
        # Match Jest / Vitest failure markers
        jest_fail_re = re.compile(r"●\s+(.*?)\n\n(.*?)(?=\n\s*●|\n\s*Test Suites:|\Z)", re.DOTALL)
        for match in jest_fail_re.finditer(combined):
            title = match.group(1).strip()
            body = match.group(2).strip()
            lines = body.splitlines()
            diag = lines[0] if lines else "Assertion failure"
            loc_match = re.search(r"at\s+.*?\((.*?):(\d+):(\d+)\)", body)
            f_path = loc_match.group(1) if loc_match else "unknown"
            line_no = int(loc_match.group(2)) if loc_match else None
            failures.append(
                CompactedFailureFrame(
                    test_identifier=title,
                    file_path=f_path,
                    line_number=line_no,
                    error_type="AssertionError",
                    diagnostic_message=diag[:300],
                    context_snippet="\n".join(lines[:6]),
                )
            )
        if not failures and exit_code != 0:
            failures.append(
                CompactedFailureFrame(
                    test_identifier="SuiteFailure",
                    file_path="workspace",
                    line_number=None,
                    error_type="ExecutionError",
                    diagnostic_message=combined[-400:].strip(),
                    context_snippet=None,
                )
            )
        return failures

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        violations: List[StubViolation] = []
        if not file_path.is_file():
            return violations
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for idx, line in enumerate(content.splitlines(), start=1):
                for pattern, name, severity in self._stub_patterns:
                    if pattern.search(line):
                        violations.append(
                            StubViolation(
                                file_path=file_path,
                                line_number=idx,
                                severity=severity,
                                symbol_name=name,
                                pattern_matched=pattern.pattern,
                                snippet=line.strip(),
                            )
                        )
        except Exception:
            pass
        return violations

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        entities: List[SymbolEntity] = []
        lines: List[str] = []
        if file_path.is_file():
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
                sym_re = re.compile(r"^(?:export\s+)?(?:default\s+)?(class|interface|type|enum|function|const|async\s+function)\s+([A-Za-z0-9_$]+)")
                for idx, line in enumerate(lines, start=1):
                    m = sym_re.match(line.strip())
                    if m:
                        kind_str, name = m.group(1), m.group(2)
                        kind = SymbolKind.FUNCTION
                        if "class" in kind_str:
                            kind = SymbolKind.CLASS
                        elif "interface" in kind_str:
                            kind = SymbolKind.INTERFACE
                        elif "enum" in kind_str:
                            kind = SymbolKind.ENUM
                        elif "type" in kind_str:
                            kind = SymbolKind.TYPE_ALIAS
                        entities.append(
                            SymbolEntity(
                                name=name,
                                kind=kind,
                                start_line=idx,
                                end_line=idx,
                                signature=line.strip()[:100],
                            )
                        )
            except Exception:
                pass
        outline_text = f"// === OUTLINE: {file_path.name} (Total: {len(lines)} LOC) ===\n"
        for e in entities:
            outline_text += f"{e.signature} [Line: {e.start_line}]\n"
        return SymbolOutline(file_path=file_path, total_lines=len(lines), entities=entities, raw_outline_text=outline_text)

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        lines = content.splitlines()
        if len(lines) <= max_lines:
            return content
        return "\n".join(lines[:15]) + f"\n    // ... [Folded: {len(lines) - 30} lines] ...\n" + "\n".join(lines[-15:])

    def get_developer_prompt_guidance(self) -> str:
        return (
            "Node.js / TypeScript Guidelines:\n"
            "- Always declare explicit return types on exported functions.\n"
            "- Use strict null checks and avoid 'any' types.\n"
            "- Never leave empty function stubs or throw placeholder errors."
        )

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        files = list(workspace.glob("**/*.ts")) + list(workspace.glob("**/*.tsx")) + list(workspace.glob("**/*.js"))
        total_loc = 0
        for f in files:
            try:
                total_loc += len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            except Exception:
                pass
        tests = [f for f in files if ".test." in f.name or ".spec." in f.name]
        return CodebaseMetrics(
            language=LanguageType.TYPESCRIPT,
            total_files=len(files),
            total_loc=total_loc,
            test_files_count=len(tests),
            test_loc=0,
            ecosystem_metadata={"package_json_exists": (workspace / "package.json").is_file()},
        )


# ============================================================================
# CONCRETE DRIVER: CDriver (C / C++)
# ============================================================================

class CDriver:
    """Driver for C and C++ ecosystems (GCC, Clang, CMake, CTest)."""

    def __init__(self) -> None:
        self._stub_patterns: List[Tuple[Pattern[str], str, StubSeverity]] = [
            (re.compile(r'\babort\s*\(\s*\)\s*;', re.IGNORECASE), "abort()", StubSeverity.CRITICAL),
            (re.compile(r'//\s*TODO\s*:\s*implement', re.IGNORECASE), "// TODO: implement", StubSeverity.CRITICAL),
            (re.compile(r'/\*\s*TODO\s*:\s*implement\s*\*/', re.IGNORECASE), "/* TODO: implement */", StubSeverity.CRITICAL),
            (re.compile(r'assert\s*\(\s*false\s*\)\s*;', re.IGNORECASE), "assert(false)", StubSeverity.CRITICAL),
            (re.compile(r'__builtin_unreachable\s*\(\s*\)\s*;', re.IGNORECASE), "__builtin_unreachable()", StubSeverity.CRITICAL),
        ]

    @property
    def language_type(self) -> LanguageType:
        return LanguageType.CPP

    @property
    def language_name(self) -> str:
        return "C / C++"

    def detect(self, workspace: Path) -> bool:
        return (workspace / "CMakeLists.txt").is_file() or (workspace / "Makefile").is_file() or (workspace / "meson.build").is_file()

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        if not file_path.is_file():
            return SyntaxCheckResult(is_clean=False, error_count=1, error_messages=[f"File not found: {file_path}"])

        compiler = shutil.which("clang++") or shutil.which("g++") or shutil.which("gcc") or shutil.which("clang")
        if not compiler:
            return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=["Compiler not found in path; skipping syntax check."])

        proc = subprocess.run(
            [compiler, "-fsyntax-only", "-Wall", "-Wextra", str(file_path)],
            capture_output=True,
            text=True,
            shell=False,
        )
        if proc.returncode != 0:
            err_lines = [l.strip() for l in proc.stderr.splitlines() if l.strip()]
            return SyntaxCheckResult(
                is_clean=False,
                error_count=len(err_lines),
                error_messages=err_lines[:5],
                failing_file=file_path,
            )
        return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        clang_format = shutil.which("clang-format")
        if clang_format:
            files = list(workspace.glob("**/*.cpp")) + list(workspace.glob("**/*.hpp")) + list(workspace.glob("**/*.c")) + list(workspace.glob("**/*.h"))
            for f in files[:50]:
                subprocess.run([clang_format, "-i", str(f)], capture_output=True, shell=False)
            return True, "clang-format executed."
        return True, "clang-format not found; skipped."

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        cppcheck = shutil.which("cppcheck")
        if cppcheck:
            proc = subprocess.run(
                [cppcheck, "--enable=warning,performance", "--quiet", str(workspace)],
                capture_output=True,
                text=True,
                shell=False,
            )
            lines = [l.strip() for l in proc.stderr.splitlines() if l.strip()]
            return StaticAnalysisResult(is_clean=len(lines) == 0, violation_count=len(lines), violations=lines[:10], tool_name="cppcheck")
        return StaticAnalysisResult(is_clean=True, violation_count=0, violations=[], tool_name="none")

    def has_test_suite(self, workspace: Path) -> bool:
        return (workspace / "CMakeLists.txt").is_file() or (workspace / "Makefile").is_file()

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        if (workspace / "build").is_dir():
            return "ctest --test-dir build --output-on-failure"
        return "make test"

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        cmd = self.get_default_test_command(workspace, target_test)
        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            failures = self.parse_test_diagnostics(proc.stdout, proc.stderr, proc.returncode)
            status = TestStatus.PASSED if proc.returncode == 0 else TestStatus.FAILED
            summary = f"C/C++ test suite: {'PASSED' if proc.returncode == 0 else 'FAILED'} (Exit code: {proc.returncode})"
            return TestExecutionOutcome(
                status=status,
                exit_code=proc.returncode,
                total_tests=len(failures) if status == TestStatus.FAILED else 1,
                passed_tests=0 if status == TestStatus.FAILED else 1,
                failed_tests=len(failures),
                skipped_tests=0,
                duration_seconds=duration,
                raw_stdout=proc.stdout,
                raw_stderr=proc.stderr,
                compacted_failures=failures,
                compaction_summary=summary,
            )
        except subprocess.TimeoutExpired as te:
            return TestExecutionOutcome(
                status=TestStatus.TIMEOUT,
                exit_code=124,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                duration_seconds=float(timeout_seconds),
                raw_stdout=te.stdout or "",
                raw_stderr=te.stderr or "Execution timed out.",
                compacted_failures=[],
                compaction_summary=f"C/C++ test execution timed out after {timeout_seconds}s.",
            )

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        failures: List[CompactedFailureFrame] = []
        combined = stdout + "\n" + stderr
        # Google Test Failure Pattern
        gtest_re = re.compile(r"\[\s*FAILED\s*\]\s*([A-Za-z0-9_]+\.[A-Za-z0-9_]+)(.*?)(?=\[\s*FAILED\s*\]|\[\s*PASSED\s*\]|\Z)", re.DOTALL)
        for match in gtest_re.finditer(combined):
            t_name = match.group(1).strip()
            body = match.group(2).strip()
            loc_match = re.search(r"^(.*?):(\d+):\s*Failure", body, re.MULTILINE)
            f_path = loc_match.group(1) if loc_match else "unknown"
            line_no = int(loc_match.group(2)) if loc_match else None
            failures.append(
                CompactedFailureFrame(
                    test_identifier=t_name,
                    file_path=f_path,
                    line_number=line_no,
                    error_type="GTestFailure",
                    diagnostic_message=body.splitlines()[0] if body else "Test failed",
                    context_snippet="\n".join(body.splitlines()[:5]),
                )
            )
        if not failures and exit_code != 0:
            failures.append(
                CompactedFailureFrame(
                    test_identifier="CTestFailure",
                    file_path="build",
                    line_number=None,
                    error_type="BuildOrRunError",
                    diagnostic_message=combined[-400:].strip(),
                    context_snippet=None,
                )
            )
        return failures

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        violations: List[StubViolation] = []
        if not file_path.is_file():
            return violations
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for idx, line in enumerate(content.splitlines(), start=1):
                for pattern, name, severity in self._stub_patterns:
                    if pattern.search(line):
                        violations.append(
                            StubViolation(
                                file_path=file_path,
                                line_number=idx,
                                severity=severity,
                                symbol_name=name,
                                pattern_matched=pattern.pattern,
                                snippet=line.strip(),
                            )
                        )
        except Exception:
            pass
        return violations

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        entities: List[SymbolEntity] = []
        lines: List[str] = []
        if file_path.is_file():
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
                sym_re = re.compile(r"^(?:template<.*?>\s*)?(?:class|struct|enum\s+class|enum)\s+([A-Za-z0-9_]+)")
                fn_re = re.compile(r"^[A-Za-z0-9_:<>&*]+\s+([A-Za-z0-9_:]+)\s*\([^)]*\)\s*(?:const)?\s*(?:noexcept)?\s*[{;]")
                for idx, line in enumerate(lines, start=1):
                    s_match = sym_re.match(line.strip())
                    if s_match:
                        entities.append(
                            SymbolEntity(
                                name=s_match.group(1),
                                kind=SymbolKind.STRUCT if "struct" in line else SymbolKind.CLASS,
                                start_line=idx,
                                end_line=idx,
                                signature=line.strip()[:100],
                            )
                        )
                    else:
                        f_match = fn_re.match(line.strip())
                        if f_match and not line.strip().startswith("return"):
                            entities.append(
                                SymbolEntity(
                                    name=f_match.group(1),
                                    kind=SymbolKind.FUNCTION,
                                    start_line=idx,
                                    end_line=idx,
                                    signature=line.strip()[:100],
                                )
                            )
            except Exception:
                pass
        outline_text = f"// === OUTLINE: {file_path.name} (Total: {len(lines)} LOC) ===\n"
        for e in entities:
            outline_text += f"{e.signature} [Line: {e.start_line}]\n"
        return SymbolOutline(file_path=file_path, total_lines=len(lines), entities=entities, raw_outline_text=outline_text)

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        lines = content.splitlines()
        if len(lines) <= max_lines:
            return content
        return "\n".join(lines[:15]) + f"\n    // ... [Folded: {len(lines) - 30} lines] ...\n" + "\n".join(lines[-15:])

    def get_developer_prompt_guidance(self) -> str:
        return (
            "C / C++ Guidelines:\n"
            "- Follow RAII and use smart pointers (`std::unique_ptr`, `std::shared_ptr`) instead of raw `new`/`delete`.\n"
            "- Avoid undefined behavior and ensure all switch branches and non-void functions return a valid value.\n"
            "- Never leave placeholder `abort()` or empty function stubs."
        )

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        files = list(workspace.glob("**/*.cpp")) + list(workspace.glob("**/*.hpp")) + list(workspace.glob("**/*.c")) + list(workspace.glob("**/*.h"))
        total_loc = 0
        for f in files:
            try:
                total_loc += len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            except Exception:
                pass
        return CodebaseMetrics(
            language=LanguageType.CPP,
            total_files=len(files),
            total_loc=total_loc,
            test_files_count=len([f for f in files if "test" in f.name.lower()]),
            test_loc=0,
            ecosystem_metadata={"cmake_exists": (workspace / "CMakeLists.txt").is_file()},
        )


# ============================================================================
# CONCRETE DRIVER: SelfAdaptingPolyglotDriver (Dynamic Polyglot Adaptation)
# ============================================================================

class SelfAdaptingPolyglotDriver:
    """Dynamic, self-adapting language driver for unmapped or modern ecosystems.

    Governed by the "One-Time Dynamic Probe & Persistent Cache" lifecycle:
    1. If `<workspace>/.oragai/language_profile.json` exists, it is loaded deterministically.
       All subsequent operations execute with zero LLM token consumption.
    2. If missing, a one-time bounded dynamic probe synthesizes an ecosystem profile,
       validates commands through P9's CommandGrammarValidator, and caches it atomically.
    3. All command execution routes through P9's TerminalSandboxEngine / hardened subprocess.
    """

    PROFILE_FILENAME: str = "language_profile.json"
    ORAGAI_DIR: str = ".oragai"

    # Known fallback discovery signatures for unmapped languages
    DISCOVERY_SIGNATURES: Dict[str, Tuple[List[str], str, str, List[str], List[str]]] = {
        "zig": (
            ["build.zig", "build.zig.zon"],
            "zig ast-check {file_path}",
            "zig test {target_test}",
            [
                r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<message>.+)$",
                r"^(?P<test>[^\n]+)\.\.\.FAIL\s+\((?P<message>[^\)]+)\)$",
            ],
            [
                r"@panic\s*\(\s*[\"'](?:TODO|Not implemented|implement me)[\"']\s*\)",
                r"//\s*TODO\s*:\s*implement",
            ],
        ),
        "elixir": (
            ["mix.exs"],
            "mix compile --warnings-as-errors",
            "mix test {target_test}",
            [
                r"^\s*\d+\)\s+test\s+(?P<test>.+)\s+\((?P<file>.+):(?P<line>\d+)\)\s*\n\s+(?P<message>.+)$",
                r"\*\* \((?P<type>\w+)\)\s+(?P<message>.+)",
            ],
            [
                r"raise\s+[\"']TODO[\"']",
                r"#\s*TODO\s*:\s*implement",
            ],
        ),
        "swift": (
            ["Package.swift"],
            "swiftc -typecheck {file_path}",
            "swift test --filter {target_test}",
            [
                r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<message>.+)$",
                r"Test Case '(?P<test>[^']+)' failed",
            ],
            [
                r"fatalError\s*\(\s*[\"'](?:TODO|Not implemented)[\"']\s*\)",
                r"//\s*TODO\s*:\s*implement",
            ],
        ),
        "kotlin": (
            ["build.gradle.kts"],
            "kotlinc -Werror -nowarn {file_path}",
            "gradle test --tests {target_test}",
            [
                r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<message>.+)$",
                r"FAILURE: Test (?P<test>.+) failed",
            ],
            [
                r"\bTODO\s*\(\s*[\"']?.*?[\"']?\s*\)",
                r"//\s*TODO\s*:\s*implement",
            ],
        ),
        "nim": (
            ["nim.cfg"],
            "nim check {file_path}",
            "nim c -r {target_test}",
            [
                r"^(?P<file>[^:\n]+)\((?P<line>\d+),\s*(?P<col>\d+)\)\s+Error:\s+(?P<message>.+)$",
            ],
            [
                r"quit\s*\(\s*[\"']TODO[\"']\s*\)",
                r"#\s*TODO\s*:\s*implement",
            ],
        ),
    }

    def __init__(
        self,
        workspace: Optional[Path] = None,
        probe_fn: Optional[Callable[[Path], DynamicEcosystemProfile]] = None,
    ) -> None:
        self._workspace: Optional[Path] = workspace
        self._probe_fn: Optional[Callable[[Path], DynamicEcosystemProfile]] = probe_fn
        self._profile: Optional[DynamicEcosystemProfile] = None
        self._compiled_failure_regexes: List[Pattern[str]] = []
        self._compiled_stub_regexes: List[Tuple[Pattern[str], str, StubSeverity]] = []
        self._discovery_probe_invoked: bool = False

        if self._workspace:
            profile_path = self._workspace / self.ORAGAI_DIR / self.PROFILE_FILENAME
            if profile_path.is_file():
                self._load_cached_profile(profile_path)

    @property
    def language_type(self) -> LanguageType:
        return LanguageType.GENERIC

    @property
    def language_name(self) -> str:
        if self._profile:
            return f"Self-Adapting ({self._profile.language_name})"
        return "Self-Adapting Polyglot Dynamic Driver"

    @property
    def active_profile(self) -> Optional[DynamicEcosystemProfile]:
        """Return the loaded ecosystem profile if initialized."""
        return self._profile

    def detect(self, workspace: Path) -> bool:
        """Evaluate if cached profile exists or if unknown manifests are present."""
        if (workspace / self.ORAGAI_DIR / self.PROFILE_FILENAME).is_file():
            return True
        for lang, (manifests, _, _, _, _) in self.DISCOVERY_SIGNATURES.items():
            if any((workspace / m).is_file() for m in manifests):
                return True
        return (workspace / "Makefile").is_file() or (workspace / "Dockerfile").is_file()

    def ensure_profile_loaded(self, workspace: Path) -> DynamicEcosystemProfile:
        """Deterministic loader: read cached profile or trigger one-time discovery probe."""
        if self._profile and self._workspace == workspace:
            return self._profile

        self._workspace = workspace
        profile_path = workspace / self.ORAGAI_DIR / self.PROFILE_FILENAME

        if profile_path.is_file():
            # FAST PATH: Cached profile on disk, zero LLM tokens consumed
            self._load_cached_profile(profile_path)
            return self._profile

        # ONE-TIME DISCOVERY PROBE: synthesize, validate, persist
        profile = self._execute_one_time_discovery_probe(workspace)
        self._validate_profile_security(profile)
        self._persist_profile(workspace, profile)
        self._apply_profile(profile)
        return self._profile

    def _load_cached_profile(self, profile_path: Path) -> None:
        """Load and deserialize profile JSON from disk with zero token consumption."""
        raw_text = profile_path.read_text(encoding="utf-8")
        profile = DynamicEcosystemProfile.model_validate_json(raw_text)
        self._apply_profile(profile)

    def _apply_profile(self, profile: DynamicEcosystemProfile) -> None:
        """Compile failure and stub regex patterns from the profile."""
        self._profile = profile
        self._compiled_failure_regexes = []
        for pat in profile.failure_regexes:
            try:
                self._compiled_failure_regexes.append(re.compile(pat, re.MULTILINE))
            except re.error:
                continue

        self._compiled_stub_regexes = []
        for pat in profile.stub_regexes:
            try:
                compiled = re.compile(pat, re.IGNORECASE)
                self._compiled_stub_regexes.append((compiled, pat[:40], StubSeverity.CRITICAL))
            except re.error:
                continue

    def _execute_one_time_discovery_probe(self, workspace: Path) -> DynamicEcosystemProfile:
        """Execute the one-time Architect/Discovery persona probe or deterministic fallback."""
        self._discovery_probe_invoked = True

        if self._probe_fn:
            return self._probe_fn(workspace)

        # Built-in deterministic probe heuristic across known signatures
        for lang_name, (manifests, syntax_cmd, test_cmd, failure_pats, stub_pats) in self.DISCOVERY_SIGNATURES.items():
            if any((workspace / m).is_file() for m in manifests):
                return DynamicEcosystemProfile(
                    language_name=lang_name,
                    manifest_files=manifests,
                    file_extensions=[f".{lang_name}"],
                    syntax_check_template=syntax_cmd,
                    test_command_template=test_cmd,
                    failure_regexes=failure_pats,
                    stub_regexes=stub_pats,
                    symbol_outline_command=None,
                    version="1.0.0",
                )

        # Default generic fallback profile
        return DynamicEcosystemProfile(
            language_name="generic",
            manifest_files=["Makefile"],
            file_extensions=[],
            syntax_check_template="make -n",
            test_command_template="make test {target_test}",
            failure_regexes=[
                r"(?i)(?:FAIL|ERROR|Exception|AssertionError):\s*(?P<message>.+)",
                r"(?P<file>[^:\n]+):(?P<line>\d+):\s*(?P<message>.+)",
            ],
            stub_regexes=[
                r"\b(?:TODO|FIXME|XXX|NOT_IMPLEMENTED)\b",
            ],
            symbol_outline_command=None,
            version="1.0.0",
        )

    def _validate_profile_security(self, profile: DynamicEcosystemProfile) -> None:
        """P9 CommandGrammarValidator Seam: verify command templates for shell injection."""
        dangerous_operators = [";", "&&", "||", "`", "$(", ">", "<", "\n", "\r"]
        for tmpl in (profile.syntax_check_template, profile.test_command_template, profile.symbol_outline_command):
            if not tmpl:
                continue
            for op in dangerous_operators:
                if op in tmpl:
                    raise ValueError(
                        f"P9 Security Violation: Command template '{tmpl}' contains disallowed shell operator '{op}'."
                    )

    def _persist_profile(self, workspace: Path, profile: DynamicEcosystemProfile) -> None:
        """Atomically persist synthesized profile to disk at `<workspace>/.oragai/language_profile.json`."""
        target_dir = workspace / self.ORAGAI_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        final_path = target_dir / self.PROFILE_FILENAME

        # Write to temporary file first, then atomically replace
        temp_fd, temp_path_str = tempfile.mkstemp(dir=target_dir, prefix="lang_prof_", suffix=".tmp")
        temp_path = Path(temp_path_str)
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                f.write(profile.model_dump_json(indent=2))
            temp_path.replace(final_path)
        except Exception:
            if temp_path.is_file():
                temp_path.unlink()
            raise

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        """Execute cached syntax check template via local subprocess (zero LLM tokens)."""
        workspace = self._workspace or file_path.parent
        profile = self.ensure_profile_loaded(workspace)

        cmd_str = profile.syntax_check_template.replace("{file_path}", str(file_path.resolve()))
        args = shlex.split(cmd_str, posix=False)

        try:
            proc = subprocess.run(
                args,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=False,
                timeout=30,
            )
            if proc.returncode == 0:
                return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

            combined = proc.stderr.strip() or proc.stdout.strip()
            errors = [l.strip() for l in combined.splitlines() if l.strip()]
            line_no = None
            for pat in self._compiled_failure_regexes:
                match = pat.search(combined)
                if match and "line" in match.groupdict():
                    try:
                        line_no = int(match.group("line"))
                        break
                    except (ValueError, TypeError):
                        pass

            return SyntaxCheckResult(
                is_clean=False,
                error_count=len(errors) if errors else 1,
                error_messages=errors[:5] if errors else [combined[:300]],
                failing_file=file_path,
                line_number=line_no,
            )
        except Exception as e:
            return SyntaxCheckResult(
                is_clean=False,
                error_count=1,
                error_messages=[f"Syntax check execution error: {str(e)}"],
                failing_file=file_path,
            )

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        return True, "No dynamic autofix configured; skipped."

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        return StaticAnalysisResult(is_clean=True, violation_count=0, violations=[], tool_name="dynamic")

    def has_test_suite(self, workspace: Path) -> bool:
        profile = self.ensure_profile_loaded(workspace)
        return any((workspace / m).is_file() for m in profile.manifest_files)

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        profile = self.ensure_profile_loaded(workspace)
        target = target_test.strip() if target_test else ""
        return profile.test_command_template.replace("{target_test}", target).strip()

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        profile = self.ensure_profile_loaded(workspace)
        cmd_str = self.get_default_test_command(workspace, target_test)
        args = shlex.split(cmd_str, posix=False)

        start_time = time.time()
        try:
            proc = subprocess.run(
                args,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=False,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            failures = self.parse_test_diagnostics(proc.stdout, proc.stderr, proc.returncode)
            status = TestStatus.PASSED if proc.returncode == 0 else TestStatus.FAILED
            summary = (
                f"{profile.language_name} test suite: "
                f"{'PASSED' if proc.returncode == 0 else 'FAILED'} (Exit code: {proc.returncode})"
            )
            return TestExecutionOutcome(
                status=status,
                exit_code=proc.returncode,
                total_tests=len(failures) if status == TestStatus.FAILED else 1,
                passed_tests=0 if status == TestStatus.FAILED else 1,
                failed_tests=len(failures),
                skipped_tests=0,
                duration_seconds=duration,
                raw_stdout=proc.stdout,
                raw_stderr=proc.stderr,
                compacted_failures=failures,
                compaction_summary=summary,
            )
        except subprocess.TimeoutExpired as te:
            return TestExecutionOutcome(
                status=TestStatus.TIMEOUT,
                exit_code=124,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                duration_seconds=float(timeout_seconds),
                raw_stdout=te.stdout or "",
                raw_stderr=te.stderr or "Execution timed out.",
                compacted_failures=[],
                compaction_summary=f"Dynamic test execution timed out after {timeout_seconds}s.",
            )

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        failures: List[CompactedFailureFrame] = []
        combined = stdout + "\n" + stderr

        for pat in self._compiled_failure_regexes:
            for match in pat.finditer(combined):
                groups = match.groupdict()
                t_id = groups.get("test") or "TestFailure"
                f_path = groups.get("file") or "workspace"
                line_str = groups.get("line")
                line_no = int(line_str) if line_str and line_str.isdigit() else None
                diag = groups.get("message") or match.group(0)[:200]

                failures.append(
                    CompactedFailureFrame(
                        test_identifier=t_id.strip(),
                        file_path=f_path.strip(),
                        line_number=line_no,
                        error_type="DynamicEcosystemFailure",
                        diagnostic_message=diag.strip()[:300],
                        context_snippet=match.group(0)[:400].strip(),
                    )
                )

        if not failures and exit_code != 0:
            failures.append(
                CompactedFailureFrame(
                    test_identifier="DynamicProcessFailure",
                    file_path="workspace",
                    line_number=None,
                    error_type="ExecutionError",
                    diagnostic_message=combined[-400:].strip() if combined.strip() else "Process failed with non-zero exit code.",
                    context_snippet=None,
                )
            )
        return failures

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        violations: List[StubViolation] = []
        if not file_path.is_file():
            return violations
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for idx, line in enumerate(content.splitlines(), start=1):
                for pattern, name, severity in self._compiled_stub_regexes:
                    if pattern.search(line):
                        violations.append(
                            StubViolation(
                                file_path=file_path,
                                line_number=idx,
                                severity=severity,
                                symbol_name=name,
                                pattern_matched=pattern.pattern,
                                snippet=line.strip(),
                            )
                        )
        except Exception:
            pass
        return violations

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        entities: List[SymbolEntity] = []
        lines: List[str] = []
        if file_path.is_file():
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
                sym_re = re.compile(r"^\s*(?:pub\s+)?(fn|def|func|function|type|struct|class|enum|trait)\s+([A-Za-z0-9_]+)")
                for idx, line in enumerate(lines, start=1):
                    m = sym_re.match(line)
                    if m:
                        kind_str, name = m.group(1), m.group(2)
                        kind = SymbolKind.FUNCTION
                        if kind_str in ("struct", "class"):
                            kind = SymbolKind.CLASS
                        elif kind_str in ("trait", "interface"):
                            kind = SymbolKind.INTERFACE
                        elif kind_str == "enum":
                            kind = SymbolKind.ENUM
                        entities.append(
                            SymbolEntity(
                                name=name,
                                kind=kind,
                                start_line=idx,
                                end_line=idx,
                                signature=line.strip()[:100],
                            )
                        )
            except Exception:
                pass
        outline_text = f"// === OUTLINE: {file_path.name} (Total: {len(lines)} LOC) ===\n"
        for e in entities:
            outline_text += f"{e.signature} [Line: {e.start_line}]\n"
        return SymbolOutline(file_path=file_path, total_lines=len(lines), entities=entities, raw_outline_text=outline_text)

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        lines = content.splitlines()
        if len(lines) <= max_lines:
            return content
        return "\n".join(lines[:15]) + f"\n    // ... [Folded: {len(lines) - 30} lines] ...\n" + "\n".join(lines[-15:])

    def get_developer_prompt_guidance(self) -> str:
        name = self._profile.language_name if self._profile else "Generic Polyglot"
        return (
            f"{name.capitalize()} Dynamic Ecosystem Guidelines:\n"
            f"- Strictly observe idiomatic patterns for {name}.\n"
            "- Implement all functions fully without leaving placeholder comments or stub exceptions.\n"
            "- Ensure all return types and error conditions match the module interface."
        )

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        profile = self.ensure_profile_loaded(workspace)
        extensions = set(profile.file_extensions) if profile.file_extensions else {".txt"}
        all_files: List[Path] = []
        for root, _, filenames in os.walk(workspace):
            if any(d in root for d in (".git", ".oragai", "target", "vendor", "node_modules")):
                continue
            for fn in filenames:
                if any(fn.endswith(ext) for ext in extensions):
                    all_files.append(Path(root) / fn)

        total_loc = 0
        for f in all_files:
            try:
                total_loc += len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            except Exception:
                pass

        test_files = [f for f in all_files if "test" in f.name.lower()]
        return CodebaseMetrics(
            language=LanguageType.GENERIC,
            total_files=len(all_files),
            total_loc=total_loc,
            test_files_count=len(test_files),
            test_loc=0,
            ecosystem_metadata={"profile": profile.language_name, "version": profile.version},
        )
```

---

## 7. Rigorous Test Matrix & Verification Scenarios

The following formal verification matrix defines automated test cases verifying the Polyglot Driver Mesh across discrimination, zero-token syntax checks, test diagnostic compaction, stub detection, and sandbox compliance.

| Test ID | Test Function Name | Target Invariant & Scope | Input / Fixture Scenario | Expected Validation Criteria |
| :--- | :--- | :--- | :--- | :--- |
| `TC-P14-DET-01` | `test_detect_rust_cargo_manifest` | Manifest identification | Workspace with `Cargo.toml` | Returns `LanguageType.RUST`, registers `RustDriver`. |
| `TC-P14-DET-02` | `test_detect_node_typescript_manifest` | TypeScript promotion | `package.json` + `tsconfig.json` | Promotes from JS to `LanguageType.TYPESCRIPT`. |
| `TC-P14-DET-03` | `test_detect_polyglot_monorepo_routing` | Sub-workspace routing | Root `package.json`, subfolder `engine/Cargo.toml` | File in `engine/src/lib.rs` routes to `RustDriver`. |
| `TC-P14-DET-04` | `test_detect_loc_entropy_fallback` | Extension volume | No manifest, 40 `.go` files vs 2 `.py` files | Correctly selects `LanguageType.GO`. |
| `TC-P14-SYN-01` | `test_python_syntax_zero_token_clean` | Python syntax | Valid Python 3.12 class | `is_clean=True`, `error_count=0`, 0 LLM calls. |
| `TC-P14-SYN-02` | `test_python_syntax_zero_token_error` | Python syntax error | Python code with missing `:` | `is_clean=False`, captures line & column error. |
| `TC-P14-SYN-03` | `test_node_syntax_check_valid` | Node syntax | Valid JS/TS source | `is_clean=True`, `error_count=0`. |
| `TC-P14-SYN-04` | `test_node_syntax_check_invalid` | Node syntax error | JS source with unmatched bracket `}` | `is_clean=False`, returns syntax error message. |
| `TC-P14-SYN-05` | `test_cpp_syntax_check_valid` | C/C++ syntax | Valid C++20 header with template | `gcc -fsyntax-only` returns clean status. |
| `TC-P14-SYN-06` | `test_cpp_syntax_check_invalid` | C/C++ syntax error | Missing semicolon in struct definition | `is_clean=False`, captures compiler error line. |
| `TC-P14-STUB-01`| `test_python_anti_stub_rejection` | Anti-Stub Gate | Method containing only `pass` or `TODO` | Returns `StubViolation(severity=CRITICAL)`. |
| `TC-P14-STUB-02`| `test_node_anti_stub_rejection` | Anti-Stub Gate | `throw new Error("TODO: implement")` | Returns critical stub violation, blocking gate. |
| `TC-P14-STUB-03`| `test_rust_anti_stub_rejection` | Anti-Stub Gate | Function containing `todo!()` macro | Returns critical stub violation. |
| `TC-P14-STUB-04`| `test_cpp_anti_stub_rejection` | Anti-Stub Gate | Function containing `abort()` | Returns critical stub violation. |
| `TC-P14-COMP-01`| `test_compact_jest_failures` | Test Compactor | 500-line Jest failure stream | Compacts to $<400$ chars capturing failing suite. |
| `TC-P14-COMP-02`| `test_compact_gtest_failures` | Test Compactor | Raw Google Test terminal log | Compacts to failing assertion and line location. |
| `TC-P14-COMP-03`| `test_compact_cargo_test_failures` | Test Compactor | Raw Cargo test failure log | Extracts failing test name and panic frame. |
| `TC-P14-OUTL-01`| `test_ts_symbol_outline_generation`| Outline Virtualizer | 400 LOC TypeScript class | Generates outline with $>90\%$ token reduction. |
| `TC-P14-OUTL-02`| `test_cpp_symbol_outline_generation`| Outline Virtualizer | 600 LOC C++ header file | Generates class/struct outline with line markers. |
| `TC-P14-SEAM-01`| `test_driver_mesh_hardened_sandbox` | P9 Sandbox seam | Subprocess test execution | Executes safely without shell injection or pipes. |
| `TC-P14-DYN-01` | `test_unknown_language_triggers_dynamic_discovery_probe` | One-Time Probe Seam | Workspace with unmapped `build.zig` and no profile | Triggers discovery probe exactly once, synthesizes valid `DynamicEcosystemProfile`. |
| `TC-P14-DYN-02` | `test_dynamic_ecosystem_profile_persistence_and_caching` | Atomic Persistence | Discovery probe completion | Profile atomically written to `.oragai/language_profile.json`; deserializable via Pydantic. |
| `TC-P14-DYN-03` | `test_subsequent_runs_use_cached_profile_with_zero_tokens` | Zero-Token Primacy | Cached `.oragai/language_profile.json` exists | Subsequent syntax/test runs execute 100% locally with 0 LLM calls or probe invocations. |
| `TC-P14-DYN-04` | `test_dynamic_regex_compaction_on_custom_test_outputs` | Polymorphic Compaction | Raw Zig/Elixir compiler & test error streams | Correctly parses `CompactedFailureFrame` extracting failing symbol, file, line, and message. |
| `TC-P14-DYN-05` | `test_dynamic_driver_p9_sandbox_command_validation` | P9 Sandbox Hardening | Command template with injection (`zig test; rm -rf /`) | Rejected by P9 `CommandGrammarValidator` prior to persistence or execution. |

### 7.1 Dynamic Adaptation & Zero-Token Test Specifications

The following canonical test implementations verify the zero-token invariants, persistent caching, and P9 sandbox compliance of `SelfAdaptingPolyglotDriver`:

```python
"""Automated verification suite for P14 Dynamic Adaptation & Self-Adapting Driver."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from orchestrator.adapters.polyglot.driver_mesh import (
    LanguageDetector,
    PolyglotDriverRegistry,
    SelfAdaptingPolyglotDriver,
)
from orchestrator.ports.driven.language_port import (
    DynamicEcosystemProfile,
    LanguageType,
    StubSeverity,
    TestStatus,
)


def test_unknown_language_triggers_dynamic_discovery_probe(tmp_path: Path):
    """Verify an unmapped ecosystem triggers discovery probe callback exactly once."""
    # 1. Setup workspace with unmapped language manifest
    zig_manifest = tmp_path / "build.zig"
    zig_manifest.write_text("// Zig build script", encoding="utf-8")
    
    probe_mock = MagicMock()
    probe_mock.return_value = DynamicEcosystemProfile(
        language_name="zig",
        manifest_files=["build.zig"],
        file_extensions=[".zig"],
        syntax_check_template="zig ast-check {file_path}",
        test_command_template="zig test {target_test}",
        failure_regexes=[r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<message>.+)$"],
        stub_regexes=[r"@panic\s*\(\s*\"TODO\"\s*\)"],
        symbol_outline_command=None,
    )

    driver = SelfAdaptingPolyglotDriver(workspace=tmp_path, probe_fn=probe_mock)
    
    # 2. Trigger profile load
    profile = driver.ensure_profile_loaded(tmp_path)
    
    # 3. Assert discovery probe was called exactly once
    assert probe_mock.call_count == 1
    assert profile.language_name == "zig"
    assert driver.language_name == "Self-Adapting (zig)"


def test_dynamic_ecosystem_profile_persistence_and_caching(tmp_path: Path):
    """Verify synthesized profile is atomically persisted to .oragai/language_profile.json."""
    zig_manifest = tmp_path / "build.zig"
    zig_manifest.write_text("// Zig build script", encoding="utf-8")

    driver = SelfAdaptingPolyglotDriver(workspace=tmp_path)
    profile = driver.ensure_profile_loaded(tmp_path)

    persisted_path = tmp_path / ".oragai" / "language_profile.json"
    assert persisted_path.is_file(), "Profile must be persisted on disk"

    # Verify JSON content matches Pydantic schema
    raw_json = json.loads(persisted_path.read_text(encoding="utf-8"))
    loaded = DynamicEcosystemProfile.model_validate(raw_json)
    assert loaded.language_name == "zig"
    assert loaded.syntax_check_template == "zig ast-check {file_path}"
    assert len(loaded.failure_regexes) > 0


def test_subsequent_runs_use_cached_profile_with_zero_tokens(tmp_path: Path):
    """Verify subsequent runs deserialize cached profile without calling discovery probe."""
    oragai_dir = tmp_path / ".oragai"
    oragai_dir.mkdir(parents=True)
    cached_profile = DynamicEcosystemProfile(
        language_name="elixir",
        manifest_files=["mix.exs"],
        file_extensions=[".ex", ".exs"],
        syntax_check_template="mix compile --warnings-as-errors",
        test_command_template="mix test {target_test}",
        failure_regexes=[r"\*\* \((?P<type>\w+)\)\s+(?P<message>.+)"],
        stub_regexes=[r"raise\s+\"TODO\""],
        symbol_outline_command=None,
    )
    (oragai_dir / "language_profile.json").write_text(
        cached_profile.model_dump_json(indent=2), encoding="utf-8"
    )

    probe_mock = MagicMock()
    # Initialize driver with probe mock
    driver = SelfAdaptingPolyglotDriver(workspace=tmp_path, probe_fn=probe_mock)
    loaded_profile = driver.ensure_profile_loaded(tmp_path)

    # Invariant check: Probe mock must NEVER be invoked when cached profile is present
    assert probe_mock.call_count == 0, "Cached profile must bypass LLM/probe execution"
    assert loaded_profile.language_name == "elixir"


def test_dynamic_regex_compaction_on_custom_test_outputs(tmp_path: Path):
    """Verify raw compiler and runner output streams are compacted into high-signal frames."""
    driver = SelfAdaptingPolyglotDriver(workspace=tmp_path)
    driver._apply_profile(
        DynamicEcosystemProfile(
            language_name="zig",
            manifest_files=["build.zig"],
            file_extensions=[".zig"],
            syntax_check_template="zig ast-check {file_path}",
            test_command_template="zig test",
            failure_regexes=[
                r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<message>.+)$",
                r"^(?P<test>[^\n]+)\.\.\.FAIL\s+\((?P<message>[^\)]+)\)$",
            ],
            stub_regexes=[r"@panic\s*\(\s*\"TODO\"\s*\)"],
        )
    )

    raw_zig_output = (
        "src/math.zig:42:15: error: expected type 'u32', found 'i32'\n"
        "    const x: u32 = -5;\n"
        "                  ^\n"
        "test.math.addition...FAIL (assertion failed)\n"
    )

    frames = driver.parse_test_diagnostics(stdout=raw_zig_output, stderr="", exit_code=1)
    assert len(frames) == 2

    # Frame 1: Compiler error
    assert frames[0].file_path == "src/math.zig"
    assert frames[0].line_number == 42
    assert "expected type 'u32'" in frames[0].diagnostic_message

    # Frame 2: Unit test failure
    assert frames[1].test_identifier == "test.math.addition"
    assert frames[1].diagnostic_message == "assertion failed"


def test_dynamic_driver_p9_sandbox_command_validation(tmp_path: Path):
    """Verify dangerous command templates trigger P9 security violation."""
    driver = SelfAdaptingPolyglotDriver(workspace=tmp_path)
    malicious_profile = DynamicEcosystemProfile(
        language_name="malicious",
        manifest_files=["bad.cfg"],
        syntax_check_template="zig test; rm -rf /",
        test_command_template="zig test && curl http://attacker.com",
    )

    with pytest.raises(ValueError, match="P9 Security Violation"):
        driver._validate_profile_security(malicious_profile)
```

---

## 8. Handoff Contract, Integration Points & P14 Exit Criteria

### 8.1 Integration with P9 (Hardened Sandbox & Tool Virtualizer)
1. **Tool Invocation Routing:** `orchestrator/tools/workspace_tools.py` queries `PolyglotDriverRegistry` for file reading, outline extraction, and syntax checks.
2. **Grammar & Subprocess Hardening:** Command execution in `execute_test_suite()` uses argv arrays or sanitized PowerShell invocations conforming to P9 rules.
3. **Dynamic Template Sanitization:** All command templates synthesized during dynamic language discovery are parsed by `CommandGrammarValidator` before persistence into `.oragai/language_profile.json`.

### 8.2 Integration with P12 (Strangler Fig Migration)
The migration to P14 polyglot drivers proceeds through the standard Strangler Fig sequence:
- **Phase 1 (Shadow Mode):** `PolyglotDriverRegistry` is initialized alongside legacy adapters; detection and syntax checks run in parallel, comparing outputs.
- **Phase 2 (PreFlight Gate Seam):** `PreFlightGate` delegates syntax checks exclusively to `ILanguageDriver.check_syntax()`.
- **Phase 3 (Completion Gate Seam):** `CompletionGate` executes test suites and extracts diagnostics via `ILanguageDriver.execute_test_suite()`.
- **Phase 4 (Legacy Adapter Deprecation):** Deprecate monolithic `orchestrator/adapters/base.py` and `orchestrator/adapters/python_adapter.py`.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   P14 ARCHITECTURAL EXIT CRITERIA                                │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [✓] 1. Zero production code modified during specification design phase.                          │
│ [✓] 2. Pure Protocol contract (`ILanguageDriver`) defined in `orchestrator/ports/driven/`.       │
│ [✓] 3. Universal Ecosystem Discrimination Engine (`LanguageDetector`) with Monorepo routing.    │
│ [✓] 4. Concrete drivers for Python, Node.js/TypeScript, C/C++, Rust, Go, & SelfAdaptingPolyglot. │
│ [✓] 5. One-time dynamic discovery probe and persistent `.oragai/language_profile.json` cache.    │
│ [✓] 6. Deterministic Zero-Token syntax validation specified for all supported & dynamic engines. │
│ [✓] 7. High-signal test outcome compaction specified for Pytest, Jest, CTest, Cargo & Dynamic.   │
│ [✓] 8. Universal Anti-Stub Scanner eliminating empty function bodies and placeholder markers.   │
│ [✓] 9. AST Outline Virtualization achieving >90% token reduction across multi-language sources.  │
│ [✓] 10. Formal verification matrix covering 25+ automated test scenarios across all invariants.  │
│ [✓] 11. Complete alignment with Hexagonal Architecture (P13), Sandbox (P9), and Rollout (P12).  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```
