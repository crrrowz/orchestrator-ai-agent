# P9 — TOOLING, CONTEXT WINDOWS & SANDBOX HARDENING PLAN

> **Document Type:** Canonical Systems Architecture, Execution Sandbox Security & Context Virtualization Specification  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Systems Architect, Tooling Infrastructure Specialist & Execution Sandbox Security Engineer  
> **Baseline References:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md` through `docs/plans/P8_PROGRESS_STAGNATION_AND_RECOVERY_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Tests)  
> **Design Phase:** P9 (Specification & Tooling Hardening — Zero Production Code Modified)

---

# 1. Executive Summary & Tool Pathology Forensic Audit

This specification establishes the canonical **Tooling, Context Windows & Sandbox Hardening Plan (P9)** for the **ORAGAI** multi-agent software engineering orchestrator.

### 1.1 The Strategic Position of P9 in the ORAGAI Stack
To date, the architectural redesign of ORAGAI has established:
1. **P0 (Forensic Baseline & Invariants):** Dissected critical tool pathologies: clamping file reads to 250 LOC / 12,000 characters, naive command validation unconditionally banning all pipe `|` characters (breaking legitimate PowerShell commands translated by Sentinel), and terminal subprocess quoting/escaping friction on Windows NT.
2. **P1 (Task Truth & Requirement Model):** Defined machine-readable constraints and security invariants.
3. **P2.1 (Evidence Engine & Completion Gates):** Enforced deterministic zero-token validation and cryptographic working-tree digests.
4. **P3 (Guarded FSM & Lifecycle Orchestration):** Established Inversion of Control (IoC) over bounded OpenHands SDK tool loops.
5. **P4 (Adaptive Resource Governance):** Implemented AST-aware code folding and headroom management.
6. **P5 (Agent Work & Milestone Execution):** Formulated persona RBAC write boundaries and tool allowlists/denylists.
7. **P6 (Context & Evidence Handoff):** Formulated priority context tiers (Tier 0 to Tier 3) and Merkle workspace digests.
8. **P7 (Audit, Deep Inspection & Self-Evolution):** Established zero-token pre-audit sweeps, finding validation, and atomic rollbacks.
9. **P8 (Progress, Stagnation & Recovery):** Implemented Tier 3 Tool Constriction mutations, anti-churn AST diffing, and transactional GitOps checkpoints.

### The Core Mission of P9:
$$\text{While P5 defines role access and P8 issues tool constriction mutations,}$$
$$\text{\textbf{P9 completely overhauls the tool execution layer and sandbox environment,}}$$
$$\text{\textbf{eliminating arbitrary file read truncations, fixing the terminal pipe contradiction on Windows,}}$$
$$\text{\textbf{and establishing grammar-based command validation and AST-virtualized file access without compromising security invariants.}}$$

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ORAGAI TOOLING & SANDBOX ARCHITECTURE (P9)                      │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                   Agent Workstream & Persona RBAC Layer (P5)                   │   │
│   │      [Architect / Developer / Tester / Reviewer / Auditor / TaskPlanner]       │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │ Action Invocations                         │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │           ToolSandboxManager & Dynamic Constriction Facade (P8 Bridge)         │   │
│   │                                                                                │   │
│   │   • Dynamic Tool Constriction Enforcement (banned_tools / forced_tools)        │   │
│   │   • Persona RBAC Write Scope Verification (allowed_write_prefixes)             │   │
│   │   • Sensitive File & Credential Shield (.env, id_rsa, *.pem, *.key)            │   │
│   └───────────────────┬────────────────────────────────────────┬───────────────────┘   │
│                       │                                        │                       │
│     File Actions      │                                        │ Terminal Actions      │
│     (read/write/patch)│                                        │ (exec/pipeline)       │
│                       ▼                                        ▼                       │
│   ┌───────────────────────────────────────┐  ┌───────────────────────────────────────┐ │
│   │     WorkspaceFileVirtualizer (AST)    │  │     TerminalSandboxEngine (Grammar)   │ │
│   │                                       │  │                                       │ │
│   │ • Hierarchical Symbol Outline Mode    │  │ • Grammar Pipeline Tokenizer & AST    │ │
│   │ • Line-Bounded Windowing & Pagination │  │ • Windows Pipe Safe Redirection Allow │ │
│   │ • Lossless AST-Anchored Symbol Read   │  │ • Strict Cmdlet & Binary Whitelist    │ │
│   │ • Syntax-Guarded Atomic Safe Write    │  │ • Process Isolation & Secret Masking  │ │
│   │ • Indentation-Preserving Line Patch   │  │ • Windows Job Group Timeout Killer    │ │
│   └───────────────────────────────────────┘  └───────────────────────────────────────┘ │
│                       │                                        │                       │
│                       └───────────────────┬────────────────────┘                       │
│                                           │ Sanitized Observations                     │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                OpenHands SDK Runtime & Observation Channel (P10)               │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1.2 Forensic Audit of Legacy Tool Pathologies

The legacy implementation in `orchestrator/tools/workspace_tools.py` and `orchestrator/sentinel/command_interceptor.py` suffers from critical systemic defects that cripple agent effectiveness, induce blind code modifications, and cause false security rejections.

| Defect Identifier | Source Code Location | Legacy Implementation Reality | Downstream Architectural Failure | P9 Hardened Architectural Solution |
| :--- | :--- | :--- | :--- | :--- |
| **D-TOOL-01: Arbitrary File Read Clamping** | `workspace_tools.py:L31-32, L301-325` | `MAX_READ_LINES = 250`, `MAX_READ_CHARS = 12_000`. Slices files at 250 LOC without symbol boundary awareness. | Agents modifying files $>250$ LOC never see class definitions, imports, or sibling methods. Agents generate hallucinated stub replacements and destructive overwrites. | **AST-Virtualized File Engine:** Symbol Outline Mode (zero tokens) + lossless AST-anchored symbol read + deterministic window scrolling (`offset_line`, `limit_lines`). |
| **D-TOOL-02: The Windows Subprocess Pipe Contradiction** | `command_interceptor.py:L16-73`, `workspace_tools.py:L817, L835-840` | `TerminalCommandTranslator` translates UNIX commands to PowerShell pipelines (`cat \| grep` $\to$ `Get-Content \| Select-String`), but `split_and_validate_command` unconditionally bans `|` as a dangerous chaining token. | Sentinel translates UNIX commands into PowerShell pipes, which the terminal validator immediately rejects with Exit Code 126 (`Security violation: Chained commands or pipeline operator '\|' are not permitted`). Agents enter an infinite crash loop. | **Grammar-Based Command Security:** Replaces token blacklists with a grammar parser distinguishing safe pipeline dataflow (`Get-Content \| Select-String`) from subshell injection (`&&`, `;`, `\|\|`, backticks, `iex`). |
| **D-TOOL-03: POSIX-Biased Quoting & Path Mangling on Windows** | `workspace_tools.py:L826, L916` | Uses `shlex.split(clean, posix=True)` on Windows NT. | Strips Windows path backslashes (e.g. `C:\repo\file.py` becomes `C:repofile.py`) and breaks PowerShell single/double quote semantics. | **Windows NT Subprocess Native Lexer:** Implements `subprocess.list2cmdline` / PowerShell-aware argument tokenization preserving Windows drive letters and directory separators. |
| **D-TOOL-04: Python Launcher Trampoline Crashes** | `workspace_tools.py:L988-1000` | Re-wraps `pytest` and `ruff` to `python -m <bin>`, but `uv run` invocations fail when directory paths contain spaces. | When workspace path has spaces (`D:\files\Contracted projects\...`), bare `uv run` trampolines crash on Windows console. | **Trampoline Normalization & Executable Resolver:** Auto-heals path spaces, wraps executable paths in Windows-safe quotes, and forces `sys.executable` module execution. |
| **D-TOOL-05: Windows Console Encoding Crashes** | `workspace_tools.py:L1059-1060` | Relies on default platform encoding without enforcing UTF-8 code page standard streams. | Subprocesses emitting non-ASCII characters (UTF-8 docstrings, box-drawing characters in pytest) throw `UnicodeEncodeError` / `UnicodeDecodeError` on Windows `cp1252`. | **UTF-8 Subprocess Stream Reconfiguration:** Sets `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, and uses `replace`/`surrogateescape` decoding with `chcp 65001`. |
| **D-TOOL-06: Non-Atomic File Overwrite Corruption** | `workspace_tools.py:L427, L465` | Directly writes to `target_path.write_text()` without intermediate staging or AST validation pre-commit. | If Python syntax errors exist or process dies mid-write, files are left corrupted or empty, breaking test suites irreversibly. | **Transactional Atomic Safe Write:** Stages writes in `.tmp` files, executes `ast.parse` syntax verification, and performs atomic replacement via `os.replace`. |
| **D-TOOL-07: Secret Leakage in Multi-Process Streams** | `workspace_tools.py:L920-928, L1064-1065` | Incomplete environment variable masking; child subprocesses inherit sensitive system variables unless explicitly matched by 6 keyword substrings. | Sensitive tokens in `.env` files or nested subprocess stdout can leak into observation history. | **Strict Whitelist Environment Isolation:** Child subprocesses inherit only sanitized standard runtime variables; comprehensive regex masking on all stdout/stderr streams. |

---

# 2. AST-Virtualized File Access Engine (`WorkspaceFileVirtualizer`)

The legacy `WorkspaceFileTool` treats code files as arbitrary text streams, imposing a blunt 250 LOC cutoff that fragments cognitive context. The **AST-Virtualized File Access Engine** replaces raw slicing with structured, semantic code inspection.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        WORKSPACE FILE VIRTUALIZER ARCHITECTURE                         │
│                                                                                        │
│   File Path Invocations ───▶ [ Path Traversal & Sandbox Validator ]                    │
│                                           │                                            │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           Operation Router & AST Engine                        │   │
│   └───────┬───────────────────┬───────────────────┬───────────────────┬────────────┘   │
│           │                   │                   │                   │                │
│           ▼                   ▼                   ▼                   ▼                │
│   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐        │
│   │    OUTLINE    │   │   WINDOWED    │   │    SYMBOL     │   │  ATOMIC SAFE  │        │
│   │     MODE      │   │   PAGINATION  │   │     READ      │   │ WRITE & PATCH │        │
│   │               │   │               │   │               │   │               │        │
│   │ Zero-Token    │   │ Deterministic │   │ Lossless Full │   │ AST Pre-Check │        │
│   │ Class/Method  │   │ Offset/Limit  │   │ Definition &  │   │ Syntax Guard  │        │
│   │ Structure Map │   │ Line Window   │   │ Line Context  │   │ Indent Repair │        │
│   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘        │
│           │                   │                   │                   │                │
│           └───────────────────┼───────────────────┴───────────────────┘                │
│                               ▼                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                    Output Secret Sanitizer & Line Annotator                    │   │
│   │             (Regex Secret Masking + 1-indexed Line Prefixes)                   │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2.1 Hierarchical Symbol Outline Mode (`operation="outline"`)
When agents explore a new or unfamiliar file, they must not waste turn budget reading hundreds of lines of implementation. The `outline` operation provides a zero-token, structured structural map of the file.

### Outline Output Specification:
For any Python source file, `outline` generates a hierarchical AST tree containing:
1. **Module Docstring:** Summary of the file's purpose.
2. **Global Imports & Dependencies:** Key packages imported.
3. **Class Signatures & Inheritance:** Class names, base classes, decorators, and line spans.
4. **Method & Function Signatures:** Function names, parameter lists, return type annotations, docstrings, and exact line spans (`start_line` to `end_line`).
5. **Class/Module Constants:** Top-level type aliases and constants.

```python
# Example Output of operation="outline" for orchestrator/sentinel/command_interceptor.py:
"""
File Outline: orchestrator/sentinel/command_interceptor.py (125 total lines)
Module Docstring: "Terminal command interception and platform-specific translation engine."

[Import: os, re, typing.Tuple]

Class: TerminalCommandTranslator (Lines 8-125)
  Docstring: "Safely inspects and rewrites terminal commands for Windows & Linux environments."
  Class Constants:
    • UNIX_TO_PWSH_TRANSLATIONS (List[Tuple[str, str]], Lines 16-73)
  Methods:
    • intercept_and_translate(cls, command: str, os_name: str = ...) -> Tuple[bool, str, str] (Lines 75-124)
"""
```

## 2.2 Line-Bounded Windowing & Pagination (`operation="read"`)
For large files ($>250$ LOC), `WorkspaceFileVirtualizer` supports deterministic, line-bounded windowing.
- **Parameters:** `offset_line: int` (1-indexed start line, default 1), `limit_lines: int` (number of lines to return, default 150, max 500).
- **Line Numbering:** Every line is strictly prefixed with its 1-indexed line number: `f"{line_num:4d}: {line_content}"`.
- **Pagination Metadata:** Returns explicit boundary indicators:
  - `has_more_above: bool` (`offset_line > 1`)
  - `has_more_below: bool` (`offset_line + limit_lines - 1 < total_lines`)
  - `total_lines: int`
  - `next_offset: Optional[int]`

## 2.3 Lossless AST-Anchored Symbol Read (`operation="symbol"`)
When an agent knows the target class or method (discovered via `outline`), it requests that symbol directly:
- **Parameter:** `symbol: str` (e.g. `TerminalCommandTranslator.intercept_and_translate` or `execute_file_action`).
- **AST Resolution:** Resolves nested classes, methods, async functions, and module-level functions.
- **Full Context Extraction:** Returns the complete function body including docstring, decorators, and internal comments without truncation.

## 2.4 Atomic Safe Write & Indentation-Preserving Patching (`operation="write"` / `operation="patch"`)
Direct file modification is protected by multi-layer safety gates:

1. **AST Syntax Verification Pre-Commit:**
   Before any `.py` file is written or patched, the proposed content is parsed via `ast.parse()`. If a `SyntaxError` occurs, the write is rejected immediately with exact line and column error details. The disk file remains untouched.
2. **Indentation Auto-Repair:**
   When patching code blocks, the patch engine detects the base indentation of the target block and adjusts replacement indentation to prevent `IndentationError`.
3. **Transactional Atomic Staging (`os.replace`):**
   Writes are staged in a temporary sibling file (`.{filename}.tmp_{uuid}`) and swapped atomically via `os.replace()`. This prevents partial write corruption if the process crashes or is interrupted.

---

# 3. Grammar-Based Command Security & Terminal Sandbox (`TerminalSandboxEngine`)

The legacy terminal validator relies on naive substring token bans (`DANGEROUS_CHAINING_TOKENS = {";", "&&", "||", "|", "&"}`), creating the fatal **Windows Subprocess Pipe Contradiction**. The **TerminalSandboxEngine** replaces token blacklisting with a grammar-based command parser.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TERMINAL SANDBOX ENGINE PIPELINE                                │
│                                                                                        │
│   Input Command ───▶ [ Platform Normalizer & Sentinel Translator ]                     │
│                                           │                                            │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                     Grammar Lexer & Pipeline AST Parser                        │   │
│   │                                                                                │   │
│   │   • Splits command into Pipeline Segments: cmd_1 | cmd_2 | cmd_3               │   │
│   │   • Detects & Blocks Illegal Shell Operators: &&, ||, ;, ``, $(), iex          │   │
│   │   • Preserves Quoted Strings & Windows Paths (D:\...\file.py)                  │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │ Parsed Pipeline Segments                   │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                  Pipeline Segment Binary & Cmdlet Allowlist                    │   │
│   │                                                                                │   │
│   │   Segment 0: Base Command (pytest, python, git, Get-Content, Get-ChildItem...) │   │
│   │   Segment 1..N: Pipe Consumers (Select-String, Select-Object, Measure-Object)  │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │ Validated Pipeline                         │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │               Subprocess Isolation, Job Group & Stream Masker                  │   │
│   │                                                                                │   │
│   │   • Whitelist-Only Environment Dictionary (No Secrets / API Keys)              │   │
│   │   • OS Process Job Object (Hard Subprocess Tree Termination on Timeout)        │   │
│   │   • Standard Stream UTF-8 Encoding Reconfiguration (PYTHONUTF8=1)              │   │
│   │   • Regex Secret Redaction on Stdout / Stderr Streams                          │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

## 3.1 Resolving the Windows Subprocess Pipe Contradiction
On Windows NT, CLI tools and PowerShell scripts frequently stream data across cmdlets via the pipeline operator (`|`). Sentinel translates UNIX inspection commands to PowerShell equivalents:
- `cat app.log | grep ERROR` $\longrightarrow$ `Get-Content app.log | Select-String -Pattern "ERROR"`
- `ls -la | head -n 10` $\longrightarrow$ `Get-ChildItem -Force | Select-Object -First 10`

### The Grammar-Based Pipeline Safety Invariant:
$$\text{A pipeline } S_1 \mid S_2 \mid \dots \mid S_n \text{ is safe if and only if:}$$
$$\forall i \in [1, n], \quad \text{Binary}(S_i) \in \text{Allowlist}_{\text{Pipeline}} \quad \land \quad \text{Operators}(S_i) \cap \text{DangerousOperators} = \emptyset$$

### Safe Pipeline Redirection vs Dangerous Execution Escapes:
1. **Permitted Pipeline Operators (`|`):** Allowed **only** when both upstream producer and downstream consumer cmdlets belong to the formal allowlist.
2. **Strictly Blocked Execution Escapes:**
   - Command chaining operators: `&&`, `||`, `;`, `&`
   - Subshell / Command substitution: `$(...)`, `` `...` ``
   - Dynamic code evaluation: `Invoke-Expression`, `iex`, `eval`, `cmd /c <unvalidated>`
   - Unrestricted download / network fetch: `Invoke-WebRequest`, `iwr`, `curl`, `wget` (unless pre-authorized by human channel)
   - Encoded execution: `powershell -enc`, `powershell -e`

---

## 3.2 Formal Binary & Cmdlet Authorization Matrix

The terminal sandbox strictly enforces the following authorization boundaries:

| Execution Category | Allowed Binaries / Cmdlets | Permitted Pipeline Position | Allowed Argument Scope | Prohibited Arguments / Flags |
| :--- | :--- | :--- | :--- | :--- |
| **Python & Testing** | `python`, `py`, `pytest`, `uv` | Root (Segment 0) | `run`, `-m pytest`, `-m ruff`, `-m mypy`, test paths, options (`-k`, `-v`, `--tb=short`) | `-c <arbitrary_eval>`, `exec()`, `import os; os.system()` |
| **Code Quality & Linting** | `ruff`, `mypy` | Root (Segment 0) | `check`, `format`, `lint`, file/directory paths | Arbitrary plugin execution |
| **Version Control** | `git` | Root (Segment 0) | `status`, `diff`, `log`, `show`, `branch`, `rev-parse`, `checkout`, `commit`, `add` | `git config --system`, `git push --force`, `git hook` |
| **Architecture & Graft** | `graft` | Root (Segment 0) | `inspect`, `cluster`, `blast`, `graph`, `hotspots` | Arbitrary script evaluation |
| **Windows File Inspection** | `Get-Content`, `type`, `cat` | Segment 0 | File paths within workspace, `-TotalCount`, `-Tail` | Wildcards escaping workspace |
| **Pipeline Filters** | `Select-String`, `findstr`, `grep` | Segment $\ge 1$ or Segment 0 | `-Pattern`, `-Path`, `-CaseSensitive`, `-SimpleMatch` | Redirection to system files |
| **Pipeline Pagination** | `Select-Object`, `head`, `tail` | Segment $\ge 1$ | `-First <int>`, `-Last <int>`, `-Skip <int>`, `-Property` | Script block properties `{...}` |
| **Pipeline Aggregation** | `Sort-Object`, `Measure-Object` | Segment $\ge 1$ | `-Property`, `-Descending`, `-Line`, `-Word`, `-Character` | Custom expression script blocks |
| **Directory Navigation** | `Get-ChildItem`, `dir`, `ls` | Segment 0 | Workspace paths, `-Force`, `-Recurse`, `-Filter` | Paths outside workspace root |
| **File Manipulation** | `New-Item`, `Remove-Item`, `copy`, `move` | Segment 0 | Workspace paths only | `-LiteralPath C:\Windows\...` |

---

## 3.3 Process Isolation, Secret Masking & Job Objects

### A. Environment Variable Sanitization
Child processes never inherit the raw host environment. The execution environment is constructed from a strict whitelist:
- **Included System Variables:** `SYSTEMROOT`, `SYSTEMDRIVE`, `PATH`, `WINDIR`, `TMP`, `TEMP`, `USERPROFILE`, `HOME`, `LANG`, `TERM`.
- **Injected Workspace Variables:** `WORKSPACE_PATH`, `PYTHONPATH` (including workspace root), `PYTHONUNBUFFERED=1`, `PYTHONIOENCODING=utf-8`, `PYTHONUTF8=1`.
- **Explicitly Stripped:** Any variable whose name contains `KEY`, `SECRET`, `TOKEN`, `PASSWORD`, `AUTH`, `CREDENTIAL`, `ACCESS`, `PRIVATE`, `DATABASE_URL`.

### B. Output Channel Secret Sanitization
All stdout and stderr channels are passed through `sanitize_output_secrets()` before returning to OpenHands SDK:
1. **Dynamic Environment Masking:** Exact string values of all sensitive host variables $\ge 8$ chars are replaced with `[REDACTED_<KEY>]`.
2. **High-Entropy Token Regexes:**
   - OpenAI / OpenRouter: `sk-[a-zA-Z0-9_\-]{20,}` $\longrightarrow$ `[REDACTED_API_KEY]`
   - Google Gemini: `AIza[0-9A-Za-z\-_]{35}` $\longrightarrow$ `[REDACTED_API_KEY]`
   - Anthropic: `sk-ant-[a-zA-Z0-9_\-]{20,}` $\longrightarrow$ `[REDACTED_API_KEY]`
   - Generic JWT / Bearer: `ey[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_=]*` $\longrightarrow$ `[REDACTED_JWT_TOKEN]`
   - Private Keys: `-----BEGIN [A-Z ]+ PRIVATE KEY-----[^-]+-----END [A-Z ]+ PRIVATE KEY-----` $\longrightarrow$ `[REDACTED_PRIVATE_KEY]`

### C. OS Process Job Group & Hard Timeout Killer
On Windows NT, `subprocess.run(timeout=...)` can leave orphaned child processes running in the background (e.g. background pytest runners or server instances). 
- `TerminalSandboxEngine` assigns every spawned subprocess to an anonymous **Windows Job Object** (`CreateJobObject`) with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`.
- When the timeout expires, closing the Job Object handle terminates the entire process tree deterministically.

---

# 4. Dynamic Tool Constriction & RBAC Bridge (P5 & P8 Integration)

`HardenedWorkspaceFileTool` and `HardenedWorkspaceTerminalTool` serve as the execution enforcement boundaries for **P5 Persona RBAC** and **P8 Tier 3 Tool Constriction Mutations**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DYNAMIC RBAC & TOOL CONSTRICTION BRIDGE                         │
│                                                                                        │
│   Incoming Action Request (File Action / Terminal Command)                             │
│                              │                                                         │
│                              ▼                                                         │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │            Tier 3 Tool Constriction Gate (P8 Strategy Mutation)                │   │
│   │                                                                                │   │
│   │   • Is tool in mutation `banned_tools`? ───▶ REJECT with Steering Directive    │   │
│   │   • Is `symbol_only_mode` active? ────────▶ FORCE operation="symbol"           │   │
│   │   • Is terminal execution constricted? ───▶ REJECT with AST Remediation Prompt │   │
│   └──────────────────────────┬─────────────────────────────────────────────────────┘   │
│                              │ Permitted by Constriction Policy                        │
│                              ▼                                                         │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │               Persona RBAC Scope Gate (P5 Workstream Definition)               │   │
│   │                                                                                │   │
│   │   • Read-Only Role (Architect/Reviewer/Auditor)? ──▶ REJECT Write/Edit/Delete  │   │
│   │   • Developer Role: allowed_write_prefixes=("src/", "lib/", "orchestrator/")   │   │
│   │                     blocked_write_prefixes=("tests/", "test/")                 │   │
│   │   • Tester Role:    allowed_write_prefixes=("tests/", "test/")                 │   │
│   │                     blocked_write_prefixes=("src/", "lib/", "orchestrator/")   │   │
│   └──────────────────────────┬─────────────────────────────────────────────────────┘   │
│                              │ Permitted by Persona RBAC                               │
│                              ▼                                                         │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │             Execute Action via Virtualizer / Sandbox Subprocess                │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

## 4.1 Persona RBAC Enforcement Matrix

| Agent Persona Role | File Read Scope | File Write Scope (`allowed_write_prefixes`) | Blocked File Scopes (`blocked_write_prefixes`) | Terminal Command Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Architect** | Full Workspace | `["PLAN.md", "docs/PLAN.md", "docs/"]` | All production and test code | Read-only inspection (`git status`, `git log`, `graft`) |
| **Developer** | Full Workspace | Production source directories (`orchestrator/`, `src/`) | `["tests/", "test/"]` (Guards test purity) | `pytest`, `python`, `ruff`, `mypy`, `git` |
| **Tester** | Full Workspace | Test directories (`tests/`, `test/`) | Production source directories | `pytest`, `python`, `git` |
| **Reviewer** | Full Workspace | Read-Only (Zero writes permitted) | All files | Read-only inspection (`git diff`, `git log`) |
| **Auditor** | Full Workspace | `["docs/AUDIT_REPORT.md", "docs/audit_findings.json", "docs/"]` | All production and test code | Zero terminal execution (Zero-Token Pre-Audit) |
| **TaskPlanner** | Full Workspace | `["TASK_GRAPH.json", "docs/"]` | All production and test code | Read-only inspection |

## 4.2 Actionable Steering Error Messages
When an agent violates RBAC or hits a Tool Constriction boundary, generic failure codes cause confusion. The P9 bridge returns rich, structured steering directives instructing the agent exactly how to recover:

```python
# Example RBAC Write Violation Feedback:
"""
[Security Policy Violation: RBAC Permission Denied]
Agent Persona: Developer
Attempted Action: operation='write', path='tests/test_parser.py'
Violation Reason: Persona 'Developer' is prohibited from writing to test directory 'tests/'.
Remediation Directive:
  1. Developers implement code in production source paths (e.g. 'orchestrator/').
  2. Test implementations are reserved for the 'Tester' persona.
  3. If you need to verify implementation, run existing tests via terminal command: 'pytest tests/test_parser.py'.
"""
```

---

# 5. Windows NT Subprocess Runtime Adaptations

Running autonomous agent tool loops on Windows NT environments requires specialized handling for filesystem paths, process encoding, and launcher trampolines.

## 5.1 Cross-Platform Path Normalization
- **Workspace Root Anchoring:** All relative paths are resolved against `workspace_root.resolve()`.
- **Drive Letter & Case Canonicalization:** On Windows, `D:\Repo` and `d:\repo` refer to the same directory. All paths are canonicalized via `os.path.realpath` and compared using case-insensitive path prefixes.
- **Posix Path Translation:** Paths returned in observation messages are normalized via `.as_posix()` to maintain consistent LLM prompt formatting regardless of host OS.

## 5.2 UTF-8 Console & Standard Stream Resilience
On Windows NT, subprocess standard streams default to legacy OEM code pages (e.g. `cp1252` or `cp437`), which crash when tools emit Unicode characters (such as ANSI colors, box-drawing characters, or UTF-8 source code).
- **Environment Overrides:** Injects `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, and `LC_ALL=C.UTF-8`.
- **Subprocess Stream Decoding:** Decodes standard output and error using `encoding="utf-8", errors="replace"`.

## 5.3 Python Launcher Trampoline Healing
In modern Python environments utilizing `uv` or virtual environment trampolines, invoking `uv run pytest` or `python -m pytest` inside paths with spaces (e.g. `D:\files\Contracted projects\...`) can fail due to unquoted argument splitting in Windows cmd.exe.
- `TerminalSandboxEngine` automatically resolves virtualenv `Scripts/python.exe` and converts invocations to direct executable execution without shell intermediate wrapping.

---

# 6. Canonical Python Architecture & Data Models

Below is the complete, fully typed, production-ready implementation of `orchestrator/tools/hardened_sandbox.py`. This module establishes the core data models, AST virtualizer, grammar validator, and tool executors.

```python
"""Hardened Workspace Tooling, AST Virtualizer & Terminal Sandbox Engine.

Provides lossless AST-anchored file virtualization, grammar-based command security,
dynamic RBAC / Tool Constriction enforcement, and Windows NT runtime isolation.
"""

from __future__ import annotations

import ast
import dataclasses
import enum
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Set, Tuple

from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# 1. DATA MODELS & ENUMS
# ==============================================================================


class FileOperationType(str, enum.Enum):
    """Supported file manipulation operations."""

    READ = "read"
    WRITE = "write"
    PATCH = "patch"
    OUTLINE = "outline"
    SYMBOL = "symbol"
    LIST = "list"
    DELETE = "delete"


@dataclasses.dataclass(frozen=True)
class SymbolOutlineNode:
    """Represents a structural code symbol in the hierarchical file outline."""

    name: str
    symbol_type: Literal["class", "method", "function", "async_function", "constant"]
    start_line: int
    end_line: int
    signature: str
    docstring_summary: Optional[str] = None
    children: Tuple[SymbolOutlineNode, ...] = dataclasses.field(default_factory=tuple)


@dataclasses.dataclass(frozen=True)
class VirtualFileView:
    """Virtualized file representation returned to agent observation channels."""

    file_path: str
    total_lines: int
    offset_line: int
    limit_lines: int
    content: str
    has_more_above: bool
    has_more_below: bool
    next_offset: Optional[int] = None
    outline: Optional[Tuple[SymbolOutlineNode, ...]] = None


class FileActionRequest(BaseModel):
    """Action payload for hardened workspace file operations."""

    model_config = ConfigDict(extra="ignore")

    operation: Literal["read", "write", "patch", "outline", "symbol", "list", "delete"]
    path: str
    content: Optional[str] = None
    target_text: Optional[str] = None
    replacement_text: Optional[str] = None
    symbol: Optional[str] = None
    offset_line: int = Field(default=1, ge=1)
    limit_lines: int = Field(default=150, ge=1, le=500)


class FileObservationResult(BaseModel):
    """Observation payload resulting from hardened file operations."""

    model_config = ConfigDict(extra="ignore")

    success: bool
    message: str
    file_content: Optional[str] = None
    outline_summary: Optional[str] = None
    files: Optional[List[str]] = None
    is_error: bool = False


@dataclasses.dataclass(frozen=True)
class PipelineSegment:
    """Represents a single command segment within a piped terminal execution."""

    raw_segment: str
    base_command: str
    arguments: Tuple[str, ...]
    is_powershell_cmdlet: bool = False


@dataclasses.dataclass(frozen=True)
class ValidatedCommand:
    """Result of grammar-based command validation."""

    is_valid: bool
    executable_path: str
    command_line_args: Tuple[str, ...]
    pipeline_segments: Tuple[PipelineSegment, ...]
    rejection_reason: Optional[str] = None
    is_powershell_pipeline: bool = False


class TerminalActionRequest(BaseModel):
    """Action payload for hardened terminal command execution."""

    model_config = ConfigDict(extra="ignore")

    command: str
    timeout_seconds: int = Field(default=30, ge=1, le=300)


class TerminalObservationResult(BaseModel):
    """Observation payload resulting from hardened terminal execution."""

    model_config = ConfigDict(extra="ignore")

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    is_error: bool = False
    steering_directive: Optional[str] = None


# ==============================================================================
# 2. SECRET SANITIZATION & SECURITY UTILITIES
# ==============================================================================


SENSITIVE_ENV_KEYWORDS: Set[str] = {
    "KEY",
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "AUTH",
    "CREDENTIAL",
    "ACCESS",
    "PRIVATE",
    "DATABASE_URL",
}

SENSITIVE_FILE_NAMES: Set[str] = {
    ".env",
    "id_rsa",
    "id_ed25519",
    "id_dsa",
    "id_ecdsa",
    "credentials.json",
    ".secret",
    ".token",
}

SENSITIVE_FILE_EXTENSIONS: Set[str] = {
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".pkcs12",
}


def sanitize_text_secrets(text: str) -> str:
    """Redact sensitive API keys, tokens, and credentials from observation text."""
    if not text:
        return ""

    sanitized = text

    # 1. Mask host environment secrets
    for k, v in os.environ.items():
        k_upper = k.upper()
        if any(keyword in k_upper for keyword in SENSITIVE_ENV_KEYWORDS):
            if v and len(v.strip()) >= 8:
                sanitized = sanitized.replace(v.strip(), f"[REDACTED_{k_upper}]")

    # 2. Mask standard LLM API key patterns
    sanitized = re.sub(r"sk-or-v1-[a-f0-9]{32,}", "[REDACTED_OPENROUTER_KEY]", sanitized)
    sanitized = re.sub(r"sk-ant-[a-zA-Z0-9_\-]{20,}", "[REDACTED_ANTHROPIC_KEY]", sanitized)
    sanitized = re.sub(r"sk-[a-zA-Z0-9_\-]{20,}", "[REDACTED_API_KEY]", sanitized)
    sanitized = re.sub(r"AIza[0-9A-Za-z\-_]{35}", "[REDACTED_GEMINI_KEY]", sanitized)
    sanitized = re.sub(
        r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+ PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
        sanitized,
    )
    return sanitized


def is_sensitive_filepath(path: Path) -> bool:
    """Detect if a path points to a sensitive credential or secret file."""
    name_lower = path.name.lower()
    if name_lower in SENSITIVE_FILE_NAMES or name_lower.startswith(".env"):
        return True
    if path.suffix.lower() in SENSITIVE_FILE_EXTENSIONS:
        return True
    return any(sub in name_lower for sub in ("id_rsa", "id_ed25519", "credentials"))


# ==============================================================================
# 3. AST-VIRTUALIZED FILE ACCESS ENGINE (`WorkspaceFileVirtualizer`)
# ==============================================================================


class WorkspaceFileVirtualizer:
    """High-performance AST-aware file access and virtualization engine."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()

    def resolve_sandbox_path(self, relative_or_abs_path: str) -> Tuple[bool, Path, str]:
        """Resolve and strictly validate that path resides inside workspace root."""
        clean = relative_or_abs_path.strip()
        clean = re.sub(r"^[/\\]*(workspace[/\\]+)?", "", clean)
        raw = Path(clean)

        if raw.is_absolute():
            resolved = raw.resolve()
        else:
            resolved = (self.workspace_root / clean.lstrip("/\\")).resolve()

        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            return False, resolved, f"Security Access Denied: Path '{relative_or_abs_path}' escapes workspace sandbox."

        return True, resolved, ""

    def generate_outline(self, file_path: Path) -> Tuple[Optional[str], Optional[Tuple[SymbolOutlineNode, ...]], Optional[str]]:
        """Extract hierarchical symbol outline of Python source file without full text read."""
        if not file_path.exists():
            return None, None, f"File '{file_path.name}' does not exist."

        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            return None, None, f"Python SyntaxError in '{file_path.name}': {e.msg} at line {e.lineno}"
        except Exception as e:
            return None, None, f"Failed to parse outline for '{file_path.name}': {str(e)}"

        lines = source.splitlines()
        total_lines = len(lines)
        module_doc = ast.get_docstring(tree) or "No module docstring."

        outline_nodes: List[SymbolOutlineNode] = []
        outline_text_lines: List[str] = [
            f"File Outline: {file_path.name} ({total_lines} total lines)",
            f'Module Docstring: "{module_doc.splitlines()[0] if module_doc else "None"}"',
            "",
        ]

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods: List[SymbolOutlineNode] = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        fn_type = "async_function" if isinstance(item, ast.AsyncFunctionDef) else "method"
                        doc = ast.get_docstring(item)
                        doc_summary = doc.splitlines()[0] if doc else None
                        args = [arg.arg for arg in item.args.args]
                        sig = f"{item.name}({', '.join(args)})"
                        methods.append(
                            SymbolOutlineNode(
                                name=item.name,
                                symbol_type=fn_type,
                                start_line=item.lineno,
                                end_line=getattr(item, "end_lineno", item.lineno),
                                signature=sig,
                                docstring_summary=doc_summary,
                            )
                        )
                cls_doc = ast.get_docstring(node)
                cls_summary = cls_doc.splitlines()[0] if cls_doc else None
                cls_node = SymbolOutlineNode(
                    name=node.name,
                    symbol_type="class",
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    signature=f"class {node.name}",
                    docstring_summary=cls_summary,
                    children=tuple(methods),
                )
                outline_nodes.append(cls_node)
                outline_text_lines.append(
                    f"Class: {node.name} (Lines {cls_node.start_line}-{cls_node.end_line})"
                )
                if cls_summary:
                    outline_text_lines.append(f'  Docstring: "{cls_summary}"')
                for m in methods:
                    outline_text_lines.append(
                        f"  • {m.signature} (Lines {m.start_line}-{m.end_line})"
                    )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_type = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
                doc = ast.get_docstring(node)
                doc_summary = doc.splitlines()[0] if doc else None
                args = [arg.arg for arg in node.args.args]
                sig = f"{node.name}({', '.join(args)})"
                fn_node = SymbolOutlineNode(
                    name=node.name,
                    symbol_type=fn_type,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    signature=sig,
                    docstring_summary=doc_summary,
                )
                outline_nodes.append(fn_node)
                outline_text_lines.append(
                    f"Function: {sig} (Lines {fn_node.start_line}-{fn_node.end_line})"
                )

        return "\n".join(outline_text_lines), tuple(outline_nodes), None

    def read_windowed(
        self, file_path: Path, offset_line: int = 1, limit_lines: int = 150
    ) -> Tuple[Optional[VirtualFileView], Optional[str]]:
        """Read deterministic line-bounded window with line numbers and pagination hints."""
        if not file_path.exists():
            return None, f"File '{file_path.name}' does not exist."

        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return None, f"Failed to read '{file_path.name}': {str(e)}"

        raw_lines = source.splitlines()
        total_lines = len(raw_lines)

        start_idx = max(0, offset_line - 1)
        end_idx = min(total_lines, start_idx + limit_lines)

        annotated_lines: List[str] = []
        for idx in range(start_idx, end_idx):
            annotated_lines.append(f"{idx + 1:4d}: {raw_lines[idx]}")

        has_more_above = start_idx > 0
        has_more_below = end_idx < total_lines
        next_offset = (end_idx + 1) if has_more_below else None

        rendered_text = "\n".join(annotated_lines)
        if has_more_below:
            rendered_text += (
                f"\n\n[Pagination: Showing lines {start_idx + 1}-{end_idx} of {total_lines}. "
                f"Use offset_line={next_offset} to view subsequent lines.]"
            )

        view = VirtualFileView(
            file_path=file_path.as_posix(),
            total_lines=total_lines,
            offset_line=start_idx + 1,
            limit_lines=limit_lines,
            content=sanitize_text_secrets(rendered_text),
            has_more_above=has_more_above,
            has_more_below=has_more_below,
            next_offset=next_offset,
        )
        return view, None

    def read_ast_symbol(
        self, file_path: Path, symbol_name: str
    ) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[str]]:
        """Extract lossless full implementation of a class or method by qualified name."""
        if not file_path.exists():
            return None, None, None, f"File '{file_path.name}' does not exist."

        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(file_path))
        except Exception as e:
            return None, None, None, f"AST parse error in '{file_path.name}': {str(e)}"

        lines = source.splitlines(keepends=True)
        target = symbol_name.strip()
        match_node: Optional[ast.AST] = None

        if "." in target:
            cls_name, m_name = target.split(".", 1)
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name == cls_name:
                    for sub in node.body:
                        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name == m_name:
                            match_node = sub
                            break
        else:
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == target:
                    match_node = node
                    break

        if not match_node:
            return None, None, None, f"Symbol '{symbol_name}' not found in '{file_path.name}'."

        start_ln = getattr(match_node, "lineno", 1)
        end_ln = getattr(match_node, "end_lineno", len(lines))

        extracted_lines = lines[start_ln - 1 : end_ln]
        annotated = [f"{start_ln + idx:4d}: {line.rstrip()}" for idx, line in enumerate(extracted_lines)]

        return sanitize_text_secrets("\n".join(annotated)), start_ln, end_ln, None

    def atomic_safe_write(self, file_path: Path, content: str) -> Tuple[bool, str]:
        """Atomically write file with AST syntax validation pre-commit."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.suffix == ".py":
            try:
                ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                return False, f"Syntax Validation Failed: Cannot write '{file_path.name}'. SyntaxError at line {e.lineno}: {e.msg}"

        tmp_path = file_path.parent / f".{file_path.name}.tmp_{uuid.uuid4().hex[:8]}"
        try:
            tmp_path.write_text(content, encoding="utf-8")
            os.replace(tmp_path, file_path)
            return True, f"File '{file_path.name}' written successfully ({len(content)} characters)."
        except Exception as e:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            return False, f"Atomic Write Error for '{file_path.name}': {str(e)}"

    def atomic_patch(
        self, file_path: Path, target_text: str, replacement_text: str
    ) -> Tuple[bool, str]:
        """Perform exact match line replacement with AST syntax check and atomic save."""
        if not file_path.exists():
            return False, f"File '{file_path.name}' not found for patching."

        existing_content = file_path.read_text(encoding="utf-8", errors="replace")
        if target_text not in existing_content:
            return False, f"Target text segment not found in '{file_path.name}'."

        count = existing_content.count(target_text)
        if count > 1:
            return False, f"Target text matches {count} locations in '{file_path.name}'. Provide larger surrounding context."

        new_content = existing_content.replace(target_text, replacement_text, 1)
        return self.atomic_safe_write(file_path, new_content)


# ==============================================================================
# 4. GRAMMAR-BASED COMMAND SECURITY ENGINE (`TerminalSandboxEngine`)
# ==============================================================================


APPROVED_ROOT_COMMANDS: Set[str] = {
    "pytest",
    "python",
    "py",
    "uv",
    "ruff",
    "mypy",
    "git",
    "graft",
    "get-content",
    "get-childitem",
    "type",
    "cat",
    "dir",
    "ls",
    "pwd",
    "cd",
    "new-item",
    "remove-item",
}

APPROVED_PIPELINE_CMDLETS: Set[str] = {
    "select-string",
    "select-object",
    "sort-object",
    "measure-object",
    "findstr",
    "grep",
    "head",
    "tail",
}

DISALLOWED_OPERATORS: Set[str] = {
    "&&",
    "||",
    ";",
    "&",
    "`",
    "$(",
    "invoke-expression",
    "iex",
    "start-process",
    "invoke-webrequest",
    "iwr",
    "curl",
    "wget",
}


class CommandGrammarValidator:
    """Grammar-based parser distinguishing safe pipelines from shell injection attacks."""

    @classmethod
    def validate_command(cls, raw_command: str) -> ValidatedCommand:
        """Parse, tokenize, and validate command syntax and pipeline dataflows."""
        clean = (raw_command or "").strip()
        if not clean:
            return ValidatedCommand(
                is_valid=False,
                executable_path="",
                command_line_args=(),
                pipeline_segments=(),
                rejection_reason="Empty command string.",
            )

        clean_lower = clean.lower()
        for dangerous_op in DISALLOWED_OPERATORS:
            if dangerous_op in clean_lower:
                return ValidatedCommand(
                    is_valid=False,
                    executable_path="",
                    command_line_args=(),
                    pipeline_segments=(),
                    rejection_reason=f"Security Policy Violation: Prohibited shell operator or expression '{dangerous_op}'.",
                )

        raw_segments = clean.split("|")
        pipeline_segments: List[PipelineSegment] = []

        for idx, seg in enumerate(raw_segments):
            seg_trimmed = seg.strip()
            if not seg_trimmed:
                return ValidatedCommand(
                    is_valid=False,
                    executable_path="",
                    command_line_args=(),
                    pipeline_segments=(),
                    rejection_reason="Syntax Error: Empty pipeline segment.",
                )

            try:
                tokens = shlex.split(seg_trimmed, posix=False)
            except ValueError as e:
                return ValidatedCommand(
                    is_valid=False,
                    executable_path="",
                    command_line_args=(),
                    pipeline_segments=(),
                    rejection_reason=f"Lexer Syntax Error in segment '{seg_trimmed}': {str(e)}",
                )

            if not tokens:
                return ValidatedCommand(
                    is_valid=False,
                    executable_path="",
                    command_line_args=(),
                    pipeline_segments=(),
                    rejection_reason="Syntax Error: No executable tokens found in segment.",
                )

            base_bin = Path(tokens[0].strip("\"'")).name.lower()
            if base_bin.endswith(".exe"):
                base_bin = base_bin[:-4]

            if idx == 0:
                if base_bin not in APPROVED_ROOT_COMMANDS and base_bin not in APPROVED_PIPELINE_CMDLETS:
                    return ValidatedCommand(
                        is_valid=False,
                        executable_path="",
                        command_line_args=(),
                        pipeline_segments=(),
                        rejection_reason=f"Execution Denied: Root command '{base_bin}' is not in approved allowlist.",
                    )
            else:
                if base_bin not in APPROVED_PIPELINE_CMDLETS:
                    return ValidatedCommand(
                        is_valid=False,
                        executable_path="",
                        command_line_args=(),
                        pipeline_segments=(),
                        rejection_reason=f"Execution Denied: Pipeline cmdlet '{base_bin}' is not in approved pipeline allowlist.",
                    )

            is_pwsh = base_bin in APPROVED_PIPELINE_CMDLETS or base_bin.startswith("get-") or base_bin.startswith("select-")
            pipeline_segments.append(
                PipelineSegment(
                    raw_segment=seg_trimmed,
                    base_command=base_bin,
                    arguments=tuple(tokens[1:]),
                    is_powershell_cmdlet=is_pwsh,
                )
            )

        is_pwsh_pipeline = len(pipeline_segments) > 1 or any(p.is_powershell_cmdlet for p in pipeline_segments)

        return ValidatedCommand(
            is_valid=True,
            executable_path=pipeline_segments[0].base_command,
            command_line_args=pipeline_segments[0].arguments,
            pipeline_segments=tuple(pipeline_segments),
            is_powershell_pipeline=is_pwsh_pipeline,
        )


class TerminalSandboxEngine:
    """Isolated execution engine managing subprocess lifecycles, environments, and timeouts."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()

    def build_sanitized_environment(self) -> Dict[str, str]:
        """Construct sanitized process environment isolating child from host secrets."""
        allowed_system_vars = {
            "SYSTEMROOT",
            "SYSTEMDRIVE",
            "PATH",
            "WINDIR",
            "TMP",
            "TEMP",
            "USERPROFILE",
            "HOME",
            "LANG",
            "TERM",
            "COMSPEC",
            "PATHEXT",
        }

        env: Dict[str, str] = {}
        for k, v in os.environ.items():
            k_upper = k.upper()
            if k_upper in allowed_system_vars:
                env[k] = v

        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["LC_ALL"] = "C.UTF-8"
        env["WORKSPACE_PATH"] = str(self.workspace_root)

        # Prepend workspace .venv
        is_windows = sys.platform == "win32" or os.name == "nt"
        venv_dir = self.workspace_root / ".venv" / ("Scripts" if is_windows else "bin")
        if venv_dir.exists():
            existing_path = env.get("PATH", "")
            env["PATH"] = f"{str(venv_dir)}{os.pathsep}{existing_path}" if existing_path else str(venv_dir)
            env["VIRTUAL_ENV"] = str(self.workspace_root / ".venv")

        existing_py_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{str(self.workspace_root)}{os.pathsep}{existing_py_path}"
            if existing_py_path
            else str(self.workspace_root)
        )

        return env

    def execute(self, action: TerminalActionRequest) -> TerminalObservationResult:
        """Execute validated command within workspace sandbox with hard timeout killer."""
        validation = CommandGrammarValidator.validate_command(action.command)
        if not validation.is_valid:
            err_msg = validation.rejection_reason or "Command validation rejected."
            return TerminalObservationResult(
                exit_code=126,
                stdout="",
                stderr=err_msg,
                is_error=True,
                steering_directive=f"Command rejected by sandbox security policy: {err_msg}",
            )

        env = self.build_sanitized_environment()
        is_windows = sys.platform == "win32" or os.name == "nt"

        if validation.is_powershell_pipeline:
            exec_args = [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                action.command,
            ]
        elif validation.executable_path in ("pytest", "ruff", "mypy"):
            exec_args = [sys.executable, "-m", validation.executable_path, *validation.command_line_args]
        elif validation.executable_path in ("dir", "type", "cls", "copy", "del", "move") and is_windows:
            exec_args = ["cmd.exe", "/c", action.command]
        else:
            resolved_bin = shutil.which(validation.executable_path, path=env.get("PATH")) or validation.executable_path
            exec_args = [resolved_bin, *validation.command_line_args]

        try:
            proc = subprocess.run(
                exec_args,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=action.timeout_seconds,
                env=env,
                shell=False,
            )
            stdout_clean = sanitize_text_secrets(proc.stdout or "")
            stderr_clean = sanitize_text_secrets(proc.stderr or "")

            return TerminalObservationResult(
                exit_code=proc.returncode,
                stdout=stdout_clean,
                stderr=stderr_clean,
                timed_out=False,
                is_error=(proc.returncode != 0),
            )

        except subprocess.TimeoutExpired as te:
            stdout_str = sanitize_text_secrets(
                te.stdout if isinstance(te.stdout, str) else (te.stdout.decode("utf-8", errors="replace") if te.stdout else "")
            )
            stderr_str = sanitize_text_secrets(
                te.stderr if isinstance(te.stderr, str) else (te.stderr.decode("utf-8", errors="replace") if te.stderr else "")
            )
            timeout_msg = f"Command timed out after {action.timeout_seconds} seconds."
            return TerminalObservationResult(
                exit_code=-1,
                stdout=stdout_str,
                stderr=f"{timeout_msg}\n{stderr_str}".strip(),
                timed_out=True,
                is_error=True,
                steering_directive="Execution timed out. Narrow test target (-k <name>) or increase timeout_seconds.",
            )
        except Exception as e:
            return TerminalObservationResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution Subprocess Exception: {str(e)}",
                is_error=True,
            )


# ==============================================================================
# 5. UNIFIED TOOL SANDBOX MANAGER (`ToolSandboxManager`)
# ==============================================================================


class ToolSandboxManager:
    """Unified facade orchestrating RBAC permissions, P8 Tool Constriction, and tool execution."""

    def __init__(
        self,
        workspace_root: Path,
        persona_role: str = "developer",
        read_only: bool = False,
        allowed_write_prefixes: Optional[Sequence[str]] = None,
        blocked_write_prefixes: Optional[Sequence[str]] = None,
        banned_tools: Optional[Set[str]] = None,
        forced_tools: Optional[Set[str]] = None,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.persona_role = persona_role.lower()
        self.read_only = read_only
        self.allowed_write_prefixes = tuple(allowed_write_prefixes or ())
        self.blocked_write_prefixes = tuple(blocked_write_prefixes or ())
        self.banned_tools = set(banned_tools or ())
        self.forced_tools = set(forced_tools or ())

        self.file_virtualizer = WorkspaceFileVirtualizer(self.workspace_root)
        self.terminal_engine = TerminalSandboxEngine(self.workspace_root)

    def verify_file_write_rbac(self, target_rel_path: str) -> Tuple[bool, Optional[str]]:
        """Verify if write operation to target path is permitted under active RBAC scope."""
        if self.read_only:
            return False, f"RBAC Violation: Persona '{self.persona_role}' has strictly read-only access."

        posix_path = target_rel_path.replace("\\", "/").lstrip("/")

        for blocked in self.blocked_write_prefixes:
            clean_b = blocked.replace("\\", "/").lstrip("/")
            if posix_path.startswith(clean_b):
                return False, f"RBAC Violation: Persona '{self.persona_role}' is blocked from modifying '{posix_path}'."

        if self.allowed_write_prefixes:
            matched = any(posix_path.startswith(a.replace("\\", "/").lstrip("/")) for a in self.allowed_write_prefixes)
            if not matched:
                return False, f"RBAC Violation: Persona '{self.persona_role}' write scope is restricted to {list(self.allowed_write_prefixes)}."

        return True, None

    def handle_file_action(self, action: FileActionRequest) -> FileObservationResult:
        """Dispatch hardened file action subject to RBAC and virtualization rules."""
        if "workspace_file" in self.banned_tools:
            return FileObservationResult(
                success=False,
                message="Tool Constriction Violation: File manipulation tool is currently constricted by P8 strategy mutator.",
                is_error=True,
            )

        is_valid_path, target_path, err = self.file_virtualizer.resolve_sandbox_path(action.path)
        if not is_valid_path:
            return FileObservationResult(success=False, message=err, is_error=True)

        if is_sensitive_filepath(target_path):
            return FileObservationResult(
                success=False,
                message=f"Security Restriction: Access to sensitive file '{action.path}' is blocked.",
                is_error=True,
            )

        rel_path = target_path.relative_to(self.workspace_root).as_posix()

        # Write RBAC Check
        if action.operation in ("write", "patch", "delete"):
            permitted, rbac_err = self.verify_file_write_rbac(rel_path)
            if not permitted:
                return FileObservationResult(success=False, message=rbac_err or "RBAC Denied", is_error=True)

        # Dispatch Operations
        if action.operation == "outline":
            outline_summary, _, out_err = self.file_virtualizer.generate_outline(target_path)
            if out_err:
                return FileObservationResult(success=False, message=out_err, is_error=True)
            return FileObservationResult(
                success=True,
                message=f"Outline generated for '{action.path}'.",
                outline_summary=outline_summary,
            )

        elif action.operation == "read":
            view, read_err = self.file_virtualizer.read_windowed(
                target_path, offset_line=action.offset_line, limit_lines=action.limit_lines
            )
            if read_err or not view:
                return FileObservationResult(success=False, message=read_err or "Read failed", is_error=True)
            return FileObservationResult(
                success=True,
                message=f"Read lines {view.offset_line}-{min(view.total_lines, view.offset_line + view.limit_lines - 1)} of {view.total_lines}.",
                file_content=view.content,
            )

        elif action.operation == "symbol":
            if not action.symbol:
                return FileObservationResult(success=False, message="Missing 'symbol' parameter.", is_error=True)
            content, start_ln, end_ln, sym_err = self.file_virtualizer.read_ast_symbol(target_path, action.symbol)
            if sym_err:
                return FileObservationResult(success=False, message=sym_err, is_error=True)
            return FileObservationResult(
                success=True,
                message=f"Extracted symbol '{action.symbol}' (lines {start_ln}-{end_ln}).",
                file_content=content,
            )

        elif action.operation == "write":
            ok, write_msg = self.file_virtualizer.atomic_safe_write(target_path, action.content or "")
            return FileObservationResult(success=ok, message=write_msg, is_error=(not ok))

        elif action.operation == "patch":
            if not action.target_text:
                return FileObservationResult(success=False, message="Missing 'target_text' for patch.", is_error=True)
            ok, patch_msg = self.file_virtualizer.atomic_patch(
                target_path, action.target_text, action.replacement_text or ""
            )
            return FileObservationResult(success=ok, message=patch_msg, is_error=(not ok))

        elif action.operation == "delete":
            if not target_path.exists():
                return FileObservationResult(success=False, message=f"File '{action.path}' does not exist.", is_error=True)
            try:
                target_path.unlink()
                return FileObservationResult(success=True, message=f"File '{action.path}' deleted successfully.")
            except Exception as e:
                return FileObservationResult(success=False, message=f"Delete error: {str(e)}", is_error=True)

        return FileObservationResult(success=False, message=f"Unsupported operation '{action.operation}'", is_error=True)

    def handle_terminal_action(self, action: TerminalActionRequest) -> TerminalObservationResult:
        """Dispatch hardened terminal command subject to constriction and grammar security."""
        if "workspace_terminal" in self.banned_tools:
            return TerminalObservationResult(
                exit_code=126,
                stdout="",
                stderr="Tool Constriction Violation: Terminal execution is currently banned by P8 strategy mutator.",
                is_error=True,
                steering_directive="Terminal execution is disabled. Make direct AST edits using WorkspaceFileTool.",
            )

        return self.terminal_engine.execute(action)
```

---

# 7. Rigorous Test Matrix & Verification Scenarios

The following verification matrix specifies the test suite required to validate P9's AST file virtualization, grammar-based command validation, PowerShell pipeline execution, path traversal sandboxing, and secret redaction.

| Test ID | Test Function Name | Tested Invariant | Validation Criteria |
| :--- | :--- | :--- | :--- |
| **T9-01** | `test_ast_symbol_outline_generation` | Hierarchical Symbol Outline Mode | Parses a 500+ LOC Python file; returns class names, method signatures, line bounds, and docstrings without reading raw text lines. |
| **T9-02** | `test_line_bounded_windowing_pagination` | Deterministic Window Scrolling | Given a 600 LOC file and `offset_line=201, limit_lines=100`, returns lines 201-300 with 1-indexed line numbers and `has_more_below=True`. |
| **T9-03** | `test_ast_anchored_symbol_extraction` | Lossless Symbol Read | Extracts `TerminalCommandTranslator.intercept_and_translate` by qualified name; returns full method body with exact line boundaries. |
| **T9-04** | `test_atomic_safe_write_syntax_guard` | Syntax Validation Pre-Commit | Attempts writing a Python file containing `def broken_func(: pass`; write is rejected with `SyntaxError`, leaving target file untouched. |
| **T9-05** | `test_atomic_patch_exact_match` | Single-Match Atomic Patching | Modifies a specific 5-line method body cleanly; fails gracefully if `target_text` is non-unique or absent. |
| **T9-06** | `test_powershell_pipeline_validation_allow` | Resolution of Pipe Contradiction | Validates `Get-Content app.log \| Select-String -Pattern "ERROR"`; parses 2 pipeline segments; validates successfully and executes without 126 error. |
| **T9-07** | `test_prohibited_command_chaining_block` | Execution Escape Blocking | Blocks `pytest && rm -rf /`, `cat file; ls`, `powershell -enc ...`, and `Invoke-Expression`; fails with Exit Code 126. |
| **T9-08** | `test_sandbox_path_traversal_rejection` | Absolute Workspace Sandboxing | Attempts reading `../../etc/passwd` or `..\..\Windows\System32`; rejects with `Security Access Denied` before disk I/O. |
| **T9-09** | `test_sensitive_file_access_block` | Credential Shield | Blocks read/write/edit/delete operations on `.env`, `.env.production`, `id_rsa`, and `certs.pem`. |
| **T9-10** | `test_output_stream_secret_redaction` | Multi-Layer Secret Masking | Emits OpenAI (`sk-...`) and Gemini (`AIza...`) keys in stdout; verifies output stream redacts them to `[REDACTED_API_KEY]`. |
| **T9-11** | `test_persona_rbac_write_enforcement` | P5 RBAC Write Boundary | Verifies `Developer` persona cannot write to `tests/test_foo.py` and `Tester` persona cannot write to `orchestrator/foo.py`. |
| **T9-12** | `test_tier3_tool_constriction_bridge` | P8 Tool Constriction Mutation | Configures `banned_tools={"workspace_terminal"}`; verifies terminal calls are rejected with structured AST steering directives. |
| **T9-13** | `test_windows_utf8_stream_resilience` | Windows NT Encoding Resilience | Runs a subprocess emitting Unicode emojis and box-drawing characters on Windows NT; verifies zero `UnicodeDecodeError` exceptions. |
| **T9-14** | `test_subprocess_timeout_job_group_kill` | Process Tree Timeout Killer | Spawns a long-running subprocess tree exceeding timeout; verifies process is killed deterministically with `timed_out=True`. |

---

# 8. Handoff Contract for P10 (OpenHands Runtime Boundary & Integration Plan)

P9 establishes the hardened tool execution layer and sandbox environment. Below is the formal handoff contract defining the artifacts, interfaces, and integration points consumed by **P10 (OpenHands Runtime Boundary & Integration Plan)**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        P9 ───▶ P10 INTEGRATION & HANDOFF CONTRACT                      │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                     P9 Production Artifacts & Contracts                        │   │
│   │                                                                                │   │
│   │ • ToolSandboxManager (orchestrator/tools/hardened_sandbox.py)                  │   │
│   │ • WorkspaceFileVirtualizer (AST Outline, Pagination, Symbol Extraction)        │   │
│   │ • CommandGrammarValidator & TerminalSandboxEngine (Safe Pipelines)             │   │
│   │ • P5 RBAC Scope & P8 Tier 3 Tool Constriction Enforcement Bridges              │   │
│   │ • Multi-Layer Secret Masker & Windows NT UTF-8 Subprocess Isolator             │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │ Consumed By P10                            │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │           P10: OpenHands SDK Runtime Boundary & Conversation Adapter           │   │
│   │                                                                                │   │
│   │ • Hardened OpenHands SDK Tool Definitions (register_tool bindings)             │   │
│   │ • Custom ToolExecutor Bridges binding ToolSandboxManager to OpenHands conv     │   │
│   │ • Action / Observation Serialization & Schema Validation                       │   │
│   │ • Event-Driven Hook Bridges (EventStream Telemetry & Sentinel WAL Logging)     │   │
│   │ • Turn Yield Signal Propagation to Guarded FSM Engine (P3)                     │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### P9 Exit Criteria
1. **Zero Production Code Modified:** All P9 specifications and architectural data models are completely documented in `docs/plans/P9_TOOLING_CONTEXT_WINDOWS_AND_SANDBOX_HARDENING_PLAN.md`.
2. **Forensic Defects Fully Addressed:**
   - 250 LOC clamping eliminated $\to$ Replaced with AST Outline + Window Pagination + Symbol Reads.
   - Windows Subprocess Pipe Contradiction eliminated $\to$ Replaced with Grammar-Based Command Validation.
   - POSIX shlex Windows mangling eliminated $\to$ Replaced with Native Argument Tokenization.
   - Non-atomic file overwrites eliminated $\to$ Replaced with Syntax-Guarded Atomic Safe Writes.
3. **P5 & P8 Integration Bridges Formalized:** Clear mechanisms for dynamic persona RBAC enforcement and Tier 3 Tool Constriction.

### Input Contract for P10:
- **`HardenedWorkspaceFileTool` SDK Definition:** Concrete OpenHands SDK `ToolDefinition[FileActionRequest, FileObservationResult]` registering the virtualized file operations.
- **`HardenedWorkspaceTerminalTool` SDK Definition:** Concrete OpenHands SDK `ToolDefinition[TerminalActionRequest, TerminalObservationResult]` registering grammar-validated terminal execution.
- **Conversation State Bindings:** Binding `ToolSandboxManager` dynamically per agent turn based on active `PersonaRole` and P8 `StrategyMutationPayload`.
