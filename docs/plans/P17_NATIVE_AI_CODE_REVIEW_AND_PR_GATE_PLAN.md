# PLAN 17: NATIVE AI CODE REVIEW & AUTOMATED PR GATE ENGINE
## Semantic Diff Parsing, AST-Guided Invariant Auditing, Multi-Turn Review Feedback Loops & GitHub PR Integration

---

### Executive Metadata
- **Document ID:** `ORAGAI-PLAN-17-CODE-REVIEW-PR-GATE`
- **Classification:** Enterprise Architectural Blueprint & Production Implementation Plan
- **Scope:** Native CodeRabbit-Equivalent Semantic Review, High-Precision AST Diff Intelligence, OWASP Security & Credential Scanning, Zero-Stub Enforcement, Automated Pull Request (PR) Quality Gate CLI & CI/CD Pipeline
- **Target Seam:** `orchestrator/ports/driving/pr_gate_port.py`, `orchestrator/analysis/pr_gate.py`, `orchestrator/workstreams/review/`
- **Governing Standard:** Hexagonal Architecture (Ports & Adapters), Zero Stubs, Zero Token Waste, Cryptographic Verification, Incremental Execution (`oragai-incremental-execution/SKILL.md`)

---

## 1. Problem Statement & Architectural Gap

As surfaced by the *ORAGAI Native Code Intelligence & Review System* and the *360° Forensic Performance Analysis*, ORAGAI's review mechanism suffered from notable structural defects:

1. **Truncated Diff Ingestion & Context Blindness:**
   - In legacy pipelines (`orchestrator/pipeline/full_pipeline.py`), the Reviewer agent received a raw diff truncated arbitrarily to 4,000 characters.
   - The Reviewer had zero visibility into surrounding symbol context, caller hierarchies, or unit test coverage, leading to superficial reviews and "rubber-stamp" approvals.
2. **Untracked PR Review Prototype:**
   - A prototype review gate script was recently added at `orchestrator/analysis/pr_gate.py` and GitHub Actions (`.github/workflows/pr_review_gate.yml`), but it is not yet integrated into the Hexagonal Core as a formal driving/driven port.
   - It executes as a standalone CLI script without leveraging `TaskTruthGraph`, `CompletionGate`, `ILanguageDriver`, or `GuardedFSMEngine`.
3. **Absence of AST-Aware Hunk Classification:**
   - Current diff inspection (`DiffVerifier`) only checks for primitive string patterns like `"# TODO"`.
   - It cannot identify whether an added function breaks backward compatibility, alters a public method signature, introduces SQL injection / command injection vulnerabilities, or fails to catch expected exceptions.
4. **Unenforced Contributor Feedback Loop:**
   - When issues are found in a PR or milestone diff, there is no structured state machine transition to send actionable feedback back to the `Developer` agent with exact file and line coordinates for self-healing.

---

## 2. Target Architecture & Hexagonal Placement

The Native AI Code Review & PR Gate is formalized as an integrated Hexagonal subsystem:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                             DRIVING INBOUND ADAPTERS                              │
│       • CLI Command: `oragai review-pr [--pr-num | --branch | --staged]`          │
│       • GitHub Actions CI: `.github/workflows/pr_review_gate.yml`                  │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │             DRIVING PORT: IPRGatePort             │
                │     (orchestrator/ports/driving/pr_gate_port.py)  │
                └─────────────────────────┬─────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                 APPLICATION CORE                                  │
│             ReviewWorkstream & Semantic Diff Intelligence Engine                  │
│       • Phase 1: Hard Deterministic Gates (0 Tokens: Secrets, AST, Linter, Tests)│
│       • Phase 2: AST Hunk Classifier & Cross-File Impact Analyzer                 │
│       • Phase 3: AI Senior Architect Reviewer Agent (Bounded Context)             │
│       • Phase 4: Structured Actionable Remediation Generator                      │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │          DRIVEN OUTBOUND ADAPTERS / PORTS         │
                │   • ILanguageDriver (Syntax & Anti-Stub Validation)│
                │   • ICodeIntelligencePort (Blast Radius & Callers)│
                │   • VCSPort / GitHub API (PR Comments & Status)   │
                └───────────────────────────────────────────────────┘
```

---

## 3. Detailed Component Specifications

### 3.1 Driving Port Protocol: `IPRGatePort`
Location: `orchestrator/ports/driving/pr_gate_port.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Protocol, runtime_checkable

class IssueSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IssueCategory(str, Enum):
    SECURITY = "SECURITY"
    ARCHITECTURE = "ARCHITECTURE"
    SYNTAX_AST = "SYNTAX_AST"
    TESTS = "TESTS"
    STUB_DETECTION = "STUB_DETECTION"
    CODE_QUALITY = "CODE_QUALITY"

@dataclass(frozen=True)
class ReviewIssue:
    category: IssueCategory
    severity: IssueSeverity
    file_path: str
    line: Optional[int]
    message: str
    remediation: str
    blocking: bool

@dataclass(frozen=True)
class PRReviewOutcome:
    total_files: int
    passed: bool
    issues: List[ReviewIssue]
    ai_summary: Optional[str]
    ai_verdict: str  # "APPROVED", "CHANGES_REQUESTED", "REJECTED"
    markdown_report: str

@runtime_checkable
class IPRGatePort(Protocol):
    def review_diff(self, base_ref: str, head_ref: str) -> PRReviewOutcome:
        ...
    def review_working_tree(self, staged_only: bool = False) -> PRReviewOutcome:
        ...
    def post_review_feedback(self, pr_number: int, outcome: PRReviewOutcome) -> bool:
        ...
```

### 3.2 Semantic Diff & AST Hunk Classifier
Location: `orchestrator/workstreams/review/semantic_diff.py`
- Parses Git diffs into structured hunks and maps every change to its enclosing AST symbol (function, class, module).
- Cross-references changes with `ICodeIntelligencePort` to detect modified public API signatures.
- Categorizes hunks into:
  - Additive (safe, new features)
  - Modifying (potential breaking changes, checks callers)
  - Deleting (high risk, asserts zero active references in codebase)

### 3.3 Zero-Token Deterministic Hard Gates
Location: `orchestrator/workstreams/review/hard_gates.py`
- Runs prior to any LLM invocation (cost: 0 tokens):
  1. **Entropy & Secret Scanner:** Detects AWS keys, GitHub tokens, private keys, JWTs, and high-entropy strings.
  2. **Universal Anti-Stub Scanner:** Uses `ILanguageDriver.find_stubs()` to reject `# TODO`, `pass`, `NotImplementedError`, `todo!()`, `panic!()`.
  3. **Hexagonal Boundary Guard:** Verifies inward-only dependencies (ensures Domain/Ports do not import Adapters/CLI).
  4. **Regression Test Runner:** Executes affected tests; if tests fail, review aborts immediately with `TEST_FAILURES` blocker.

### 3.4 Bounded Context AI Reviewer Agent
Location: `orchestrator/workstreams/review/agent_reviewer.py`
- Ingests only the semantic hunks, relevant symbol skeletons, and test results (strict budget $<6,000$ tokens).
- Evaluates code logic, edge-case vulnerability, concurrency safety, and documentation clarity.
- Outputs structured JSON conforming strictly to `PRReviewOutcome`.

---

## 4. Invariants & Verification Plan

1. **Non-Bypassable Hard Gates Invariant:**
   - No PR or diff can receive `APPROVED` status if any hard gate fails (e.g., test failure, secret leak, or stub detection), regardless of AI recommendations.
2. **Deterministic Output Invariant:**
   - Hard gates must produce identical verdicts given the same repository Git state.
3. **Structured Remediation Guarantee:**
   - Every detected issue must include concrete file coordinates and actionable remediation instructions.
4. **Zero Regressions Invariant:**
   - 100% pass rate across all existing unit, integration, and architecture tests.

---

## 5. Execution Bites Breakdown

- **BITE-P17-01:** Define `IPRGatePort` and review data models in `orchestrator/ports/driving/pr_gate_port.py`.
- **BITE-P17-02:** Develop `SemanticDiffClassifier` in `orchestrator/workstreams/review/semantic_diff.py`.
- **BITE-P17-03:** Formalize zero-token hard gates in `orchestrator/workstreams/review/hard_gates.py`.
- **BITE-P17-04:** Refactor `orchestrator/analysis/pr_gate.py` to become the concrete implementation of `IPRGatePort` conforming to Hexagonal Ports.
- **BITE-P17-05:** Wire CLI commands `oragai review` and GitHub Action runner into the unified core.
- **BITE-P17-06:** Test suite `tests/test_pr_gate_p17.py` validating hard gates, AST diff classification, and PR report rendering.
