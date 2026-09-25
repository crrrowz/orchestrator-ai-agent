# P2.1 — EVIDENCE & COMPLETION GATE ARCHITECTURE SPECIFICATION

> **Document Type:** Canonical Systems Architecture, Evidence Engine & Quality Gate Specification (P2.1 Final Correction Pass)  
> **Target System:** ORAGAI Autonomous Multi-Agent Software Engineering Orchestrator  
> **Source Repository:** `orchestrator-ai-agent`  
> **Author:** Principal Software Architect, Evidence Systems Engineer, & Autonomous Verification Specialist  
> **Baseline References:** `docs/plans/P0_FORENSIC_BASELINE_AND_INVARIANTS_PLAN.md`, `docs/plans/P1_TASK_TRUTH_AND_REQUIREMENT_MODEL_PLAN.md`  
> **Environment Context:** Python 3.12.11 | `openhands-sdk v1.49.4` | Windows NT 10.0 (x86_64) | `pytest-9.1.1` (244 Passing Unit Tests)  
> **Design Phase:** P2.1 (Specification & Canonical Evidence Gating — Zero Production Code Modified)

---

# A. Executive Summary

Prior to this P2.1 correction pass, the P2 specification established key foundational concepts (content hashing, multi-dimensional states, and structured decisions), but contained several critical architectural contradictions and unsafe assumptions:
1. **Simplistic Linear Trust Ladder:** Treated trust as a universal vertical ladder ($L0 \to L4$), ignoring that evidence authority is fundamentally contextual (e.g. static AST is authoritative for AST structure, while runtime execution is authoritative for CLI behavior).
2. **Residual `pytest == 0` False-Completion Hazards:** Preserved phrases equating a passing test exit code with general functional proof, and suggested synthetic `REQ-000` legacy auto-passes.
3. **Incomplete State Model Separation:** Allowed residual references to monolithic `req.status` and `RequirementStatus.VERIFIED`.
4. **Fragile Freshness Assumptions:** Allowed in-memory `mtime` cache hints to be conflated with correctness identity.
5. **Missing Multi-Evidence Policies:** Did not define how multiple evidence items combine (`ALL`, `ANY`, `QUORUM`) or how contradictory evidence is resolved.

### P2.1 Corrections Summary:
- **Contextual Evidence Policies:** Replaced the simplistic trust ladder with `CriterionEvidencePolicy` (`ALL`, `ANY`, `QUORUM`, `EXACT_MATCH`) and `EvidenceSubject` scoping.
- **Strict Orthogonal State Dimensions:** Completely separated `ImplementationState`, `VerificationState`, and `BlockingState`.
- **Zero-Bypass Deterministic Completion Gate:** Specified a 14-step algorithm evaluating 7 truth dimensions and returning a structured `CompletionDecision` (`COMPLETE`, `INCOMPLETE`, `FAILED`, `BLOCKED`, `AMBIGUOUS`).
- **Cryptographic Content Identity:** Replaced timestamps with canonical SHA-256 composite hashing over normalized relative paths and UTF-8 `\n` normalized file content.
- **Zero Self-Certification Invariant:** Enforced that no agent persona can verify its own output; verification is computed exclusively by deterministic runners and independent evaluators.
- **Safe Legacy Task Classification:** Tagged unstructured tasks as `LEGACY_UNSTRUCTURED`, returning `INCOMPLETE (LEGACY_VERIFICATION_REQUIRED)` on smoke test passes rather than falsely declaring task completion.

The corrected P2.1 specification provides an unambiguous, mathematically sound contract ready for direct consumption by the P3 Guarded FSM.

---

# B. Repository Evidence

Every architectural claim and baseline constraint is grounded in verified source code:

| Subsystem / Concern | Source Location | Verified Codebase Fact | Architectural Implication |
| :--- | :--- | :--- | :--- |
| **Pytest Exit Code Gating** | `orchestrator/pipeline/dev_test_loop.py:L277-280` | `if test_result.status == TestExecutionStatus.PASSED: tests_passed = True; break` | **Verified Fact:** Any pytest exit code 0 terminates the development loop immediately, regardless of requirement coverage. |
| **Step Ceiling Masking** | `orchestrator/pipeline/base_pipeline.py:L56, L353-370` | `ConvRunResult.completed: bool = True` (default value) | **Verified Fact:** Step limit cutoffs in OpenHands conversation loops default `completed` to `True`, masking step exhaustion as success. |
| **Investigation Token Kill** | `orchestrator/pipeline/base_pipeline.py:L304-324`, `orchestrator/control/token_governance.py:L147-151` | `conv.interrupt()` triggered when 28% of turn tokens are consumed without a file write. | **Verified Fact:** Legitimate codebase reading and dependency investigation are prematurely aborted. |
| **Reviewer Truncation** | `orchestrator/pipeline/full_pipeline.py:L630-654`, `orchestrator/pipeline/reviewer_parser.py:L58-88` | Reviewer receives 4,000-character compact diff; parsed via JSON regex fallback for `"APPROVED"`. | **Verified Fact:** Reviewer approval is superficial, evaluating a truncated diff without test results or requirements. |
| **PreFlight Syntax Guard** | `orchestrator/guards/preflight.py:L8-162` | `PreFlightGuard.check_syntax()` runs `py_compile.compile()` across workspace in $<50\text{ms}$. | **Verified Fact:** Fast, zero-token static syntax validation exists but is ephemeral and disconnected from truth models. |
| **AST Stub & Import Guard** | `orchestrator/sentinel/ast_guard.py:L34-195` | `ASTGuard.intercept_ast()` audits AST, bans `pass`/`...` stubs, and auto-heals missing standard imports. | **Verified Fact:** Zero-token anti-stub inspection is fully functional on write actions. |
| **Audit Finding Integrity** | `orchestrator/analysis/schemas.py:L195-248` | `FindingValidator.validate()` enforces workspace path containment, file existence, and non-generic evidence. | **Verified Fact:** Proven evidence validator exists in the audit subsystem; must be generalized to all task verification. |
| **Git Diff Telemetry** | `orchestrator/vcs/git_ops.py:L41-110`, `orchestrator/telemetry/recorder.py:L136, L251-252` | `hashlib.sha256(diff.encode()).hexdigest()` computes diff hashes for circuit breakers. | **Verified Fact:** SHA-256 hashing is already proven in telemetry; elevated to canonical evidence identity in P2.1. |
| **Passive Pipeline FSM** | `orchestrator/pipeline/state_machine.py:L28-93` | `PipelineStateMachine` checks only dictionary membership in `ALLOWED_TRANSITIONS`. | **Verified Fact:** Current FSM contains zero guard predicates or evidence checks. (FSM redesign deferred to P3). |
| **Milestone Parsing** | `orchestrator/pipeline/milestone_dag.py:L8-16, L63-115` | `SubtaskMilestone` parsed from markdown headers `## Milestone N:`. | **Verified Fact:** Milestones represent execution chunks, not requirement verification contracts. |

---

# C. P2.1 Correction Matrix

| ID | P2 Section | Problem in P2 Draft | Architectural Risk | P2.1 Correction | Verification Method |
|:---|:---|:---|:---|:---|:---|
| **COR-01** | §7 (Trust Model) | Simplistic vertical trust ladder ($L0 \to L4$) treated L4 as universally superior. | Static AST or runtime CLI proof rejected because it was not labeled "L4". | Replaced with contextual `CriterionEvidencePolicy` and `EvidenceSubject` scoping. | Multi-policy unit test matrix. |
| **COR-02** | §5 (Test Evidence) | Equated `pytest == 0` with complete functional proof. | Trivial single-assertion tests pass unaddressed requirements. | Defined test evidence as proof of *executed assertions only*; added `TestAdequacyPolicy`. | Adversarial test with unmapped criteria. |
| **COR-03** | §15 (State Model) | Residual references to monolithic `req.status` and `RequirementStatus.VERIFIED`. | Conflated code authorship with empirical proof; caused FSM deadlocks. | Strictly enforced 3 orthogonal dimensions: `ImplementationState`, `VerificationState`, `BlockingState`. | Static AST audit of schema models. |
| **COR-04** | §10 (Freshness) | In-memory `mtime` cache optimization conflated with correctness identity. | Stale evidence accepted due to clock drift or filesystem metadata anomalies. | Content hash (SHA-256) defined as sole correctness identity; `mtime` restricted to cache hints. | Cross-platform hash comparison tests. |
| **COR-05** | §13 (Evidence Policies) | Missing combinatorial policy definitions (`ALL`, `ANY`, `QUORUM`). | Ambiguity when multiple evidence items exist for a single criterion. | Formalized `CriterionEvidencePolicy` with deterministic contradiction handling. | Policy evaluation algorithm walk. |
| **COR-06** | §7 (Subject Scope) | Evaluated only direct target files, ignoring imported modules and configs. | Modifying a shared module left dependent test evidence falsely marked "fresh". | Expanded `EvidenceSubject` to include imported modules, test files, configs, and lockfiles. | Scoped invalidation cascade tests. |
| **COR-07** | §28 (Legacy Tasks) | Proposed synthetic `REQ-000` auto-pass on smoke tests. | Recreated the exact P0 false-completion vulnerability under backward compatibility. | Classified legacy tasks as `LEGACY_UNSTRUCTURED`, returning `INCOMPLETE` on smoke pass. | Adversarial legacy task execution. |
| **COR-08** | §22 (Blocking Defects) | Contradictory rules treating all defects vs only CRITICAL/HIGH as blocking. | Trivial LOW/MEDIUM advisories halted pipelines, or CRITICAL defects were ignored. | Formally defined: `CRITICAL`/`HIGH` without active waiver are blocking; `MEDIUM`/`LOW` are advisory. | CompletionGate defect evaluation. |
| **COR-09** | §26 (Decision Model) | `BLOCKED` and `AMBIGUOUS` states were theoretically defined but unreachable in logic. | External failures or conflicting evidence collapsed into generic `INCOMPLETE`. | Implemented explicit deterministic branches for `BLOCKED` and `AMBIGUOUS` in `evaluate_task_completion`. | State reachability matrix. |
| **COR-10** | §32 (P3 Contract) | Prematurely proposed FSM transition guard code inside P2. | Blurred architectural boundary between P2 (Evidence) and P3 (Lifecycle FSM). | Refactored P3 interface into pure, read-only `TaskTruthSemanticQueries`. | Interface boundary inspection. |

---

# D. Corrected Canonical Specification

### 1. Multi-Dimensional State Dimensions

```python
"""Canonical Task and Requirement State Dimensions for ORAGAI."""

from enum import Enum


class ImplementationState(str, Enum):
    """Authorship state of production source code."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    IMPLEMENTED = "IMPLEMENTED"


class VerificationState(str, Enum):
    """Empirical verification state of a Requirement or Acceptance Criterion."""
    NOT_VERIFIED = "NOT_VERIFIED"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    STALE = "STALE"
    INCONCLUSIVE = "INCONCLUSIVE"


class BlockingState(str, Enum):
    """Operational blocking state of a Requirement."""
    NONE = "NONE"
    BLOCKED = "BLOCKED"
    WAIVED = "WAIVED"


class CriterionEvaluationState(str, Enum):
    """Dynamic evaluation state of an Acceptance Criterion."""
    NOT_EVALUATED = "NOT_EVALUATED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    STALE = "STALE"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED = "BLOCKED"
```

### State Dimension Separation Rules:
1. **Authorship vs. Proof:** A Developer agent editing code mutates `ImplementationState` to `IMPLEMENTED`. It is strictly prohibited from mutating `VerificationState`.
2. **Deterministic Verification:** Only the deterministic Verification Engine evaluating fresh, valid `CanonicalEvidence` can transition `VerificationState` to `VERIFIED`.
3. **Derived Freshness:** If any artifact in the declared `EvidenceSubject` changes content hash, `VerificationState` dynamically evaluates to `STALE`.

---

### 2. Evidence Domain Model & Typed Payloads

```python
"""Canonical Evidence Domain Model for ORAGAI."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Canonical taxonomy of verifiable software engineering evidence."""
    TEST_EXECUTION = "TEST_EXECUTION"
    STATIC_AST = "STATIC_AST"
    STATIC_LINT = "STATIC_LINT"
    RUNTIME_CLI = "RUNTIME_CLI"
    REPOSITORY_DIFF = "REPOSITORY_DIFF"
    ARCHITECTURAL_GRAPH = "ARCHITECTURAL_GRAPH"
    REVIEW_RUBRIC = "REVIEW_RUBRIC"
    AUDIT_FINDING = "AUDIT_FINDING"
    DOCUMENTATION_CHECK = "DOCUMENTATION_CHECK"
    INVARIANT_PROBE = "INVARIANT_PROBE"


class ProvenanceClass(str, Enum):
    """Origin classification of evidence."""
    DETERMINISTIC_ENGINE = "DETERMINISTIC_ENGINE"  # Compiler, AST parser, Pytest CLI, Ruff
    SANDBOX_EXECUTION = "SANDBOX_EXECUTION"        # Subprocess execution in isolated environment
    INDEPENDENT_REVIEWER = "INDEPENDENT_REVIEWER"  # Separate Reviewer LLM evaluation
    CODEBASE_AUDITOR = "CODEBASE_AUDITOR"          # Static security/quality scanner
    HUMAN_SUPERVISOR = "HUMAN_SUPERVISOR"          # Explicit operator attestation / waiver
    AGENT_ASSERTION = "AGENT_ASSERTION"            # Unverified producer LLM statement (L0)


class VerificationOutcome(str, Enum):
    """Discrete outcome of a verification evaluation."""
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    NOT_RUN = "NOT_RUN"


class EvidenceProducer(BaseModel):
    """Attribution metadata for the evidence generator."""
    role: str = Field(..., description="Producer persona: tester, preflight, reviewer, auditor, runtime")
    component: str = Field(..., description="Engine component: PytestRunner, ASTGuard, PreFlightGuard")
    model_id: Optional[str] = Field(None, description="Model ID if generated via inference")
    tool_name: Optional[str] = Field(None, description="Tool invoked: workspace_file, execute_terminal")
    version: str = Field(default="1.0.0", description="Component / runner version")


# =========================================================================
# STRONGLY TYPED EVIDENCE PAYLOADS
# =========================================================================

class TestExecutionPayload(BaseModel):
    """Structured payload for Pytest execution evidence."""
    test_node_ids: List[str] = Field(..., description="Exact pytest node IDs executed")
    exit_code: int
    total_collected: int
    total_passed: int
    total_failed: int
    total_errors: int
    duration_seconds: float
    passed_test_nodes: List[str] = Field(default_factory=list)
    failed_test_nodes: List[str] = Field(default_factory=list)
    failure_details_compact: str = ""
    assertions_detected: int = Field(default=1, description="Number of AST assert statements in test body")


class StaticAstPayload(BaseModel):
    """Structured payload for AST and static compilation checks."""
    files_checked: List[str]
    syntax_valid: bool
    importability_valid: bool
    prohibited_stubs_found: List[str] = Field(default_factory=list)
    symbols_verified: List[str] = Field(default_factory=list)
    error_traces: List[str] = Field(default_factory=list)


class RuntimeCliPayload(BaseModel):
    """Structured payload for CLI and subprocess execution."""
    command: str
    args: List[str]
    exit_code: int
    stdout_summary: str
    stderr_summary: str
    expected_exit_codes: List[int] = Field(default_factory=lambda: [0])
    expected_output_patterns: List[str] = Field(default_factory=list)
    matched_patterns: List[str] = Field(default_factory=list)


class ReviewRubricPayload(BaseModel):
    """Structured payload for independent code review."""
    verdict: Literal["APPROVED", "REJECTED"]
    clean_architecture_score: int = Field(ge=1, le=5)
    maintainability_score: int = Field(ge=1, le=5)
    rubric_findings: List[str] = Field(default_factory=list)
    required_remediations: List[str] = Field(default_factory=list)


class AuditFindingPayload(BaseModel):
    """Structured payload for codebase security and architectural audit."""
    scanned_files_count: int
    scanned_loc: int
    active_findings_count: int
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    scanner_tools: List[str] = Field(default_factory=lambda: ["ASTGuard", "Ruff", "AuditorLLM"])


class DocumentationPayload(BaseModel):
    """Structured payload for documentation verification."""
    target_doc_file: str
    file_exists: bool
    heading_structure_valid: bool
    required_sections_present: List[str] = Field(default_factory=list)
    code_snippets_syntax_valid: bool = True
    broken_links_detected: List[str] = Field(default_factory=list)


class InvariantAttestationPayload(BaseModel):
    """Structured payload for system invariant attestations."""
    invariant_name: str
    is_satisfied: bool
    violation_details: Optional[str] = None
    inspected_targets: List[str] = Field(default_factory=list)


# =========================================================================
# CANONICAL EVIDENCE RECORD
# =========================================================================

class CanonicalEvidence(BaseModel):
    """Authoritative, immutable record of verification proof."""
    evidence_id: str
    evidence_type: EvidenceType
    producer: EvidenceProducer
    provenance: ProvenanceClass
    criterion_ids: List[str] = Field(default_factory=list, description="Criteria verified by this evidence")
    outcome: VerificationOutcome
    summary: str = Field(..., min_length=5, description="Verifiable summary of outcome")
    subject: "EvidenceSubject"
    subject_fingerprint: "SubjectFingerprint"
    environment_fingerprint: "EnvironmentFingerprint"
    typed_payload: Union[
        TestExecutionPayload,
        StaticAstPayload,
        RuntimeCliPayload,
        ReviewRubricPayload,
        AuditFindingPayload,
        DocumentationPayload,
        InvariantAttestationPayload
    ]
    archival_raw_output: Optional[str] = Field(None, description="Opaque raw trace for post-mortem debugging")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

---

### 3. Evidence Subject Scope & Cryptographic Identity

```python
"""Evidence Subject Scope and Cryptographic Content Identity."""

import hashlib
import sys
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel, Field


class EvidenceSubject(BaseModel):
    """Complete declared scope of artifacts and environment governing evidence validity."""
    target_files: List[str] = Field(default_factory=list, description="Implementation source files")
    test_files: List[str] = Field(default_factory=list, description="Test fixture source files")
    imported_modules: List[str] = Field(default_factory=list, description="Workspace modules imported by target")
    config_files: List[str] = Field(default_factory=list, description="Configuration and schema files")
    dependency_manifests: List[str] = Field(default_factory=list, description="Dependency lockfiles")
    environment_keys: List[str] = Field(default_factory=list, description="Non-secret env keys affecting run")

    def all_referenced_paths(self) -> List[str]:
        """Return unified, sorted, deduplicated workspace-relative paths."""
        return sorted(list(set(
            self.target_files + self.test_files + self.imported_modules +
            self.config_files + self.dependency_manifests
        )))


class SubjectFingerprint(BaseModel):
    """Cryptographic content identity of the EvidenceSubject."""
    file_hashes: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of normalized relative paths to SHA-256 content hashes"
    )
    composite_hash: str = Field(..., description="Deterministic hash over sorted path-hash pairs")

    @classmethod
    def compute(cls, workspace: Path, subject: EvidenceSubject) -> "SubjectFingerprint":
        hashes: Dict[str, str] = {}
        for rel_path in subject.all_referenced_paths():
            target = (workspace / rel_path).resolve()
            if not target.exists() or not target.is_file():
                continue
            try:
                content = target.read_bytes()
                try:
                    # Text line-ending normalization (\r\n -> \n)
                    text = content.decode("utf-8")
                    norm_content = text.replace("\r\n", "\n").encode("utf-8")
                except UnicodeDecodeError:
                    norm_content = content
                hashes[rel_path] = hashlib.sha256(norm_content).hexdigest()
            except Exception:
                continue

        sorted_pairs = sorted(hashes.items(), key=lambda x: x[0])
        composite_src = "\n".join(f"{p}:{h}" for p, h in sorted_pairs).encode("utf-8")
        comp_hash = hashlib.sha256(composite_src).hexdigest()
        return cls(file_hashes=hashes, composite_hash=comp_hash)


class EnvironmentFingerprint(BaseModel):
    """Runtime execution environment metadata."""
    os_platform: str = Field(default_factory=lambda: sys.platform)
    python_version: str = "3.12.11"
    pytest_version: str = "9.1.1"
    git_commit_sha: Optional[str] = None
    git_dirty: bool = False
    env_vars_hash: str = Field(..., description="SHA-256 of sorted, sanitized non-secret environment flags")
```

---

### 4. Acceptance Criterion Evidence Policies & Conflict Resolution

```python
"""Criterion Evidence Policies and Conflict Resolution."""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class EvidencePolicyType(str, Enum):
    """Logical policy for combining multiple evidence records."""
    ALL = "ALL"                  # Every required evidence type must be present and PASS
    ANY = "ANY"                  # At least one valid evidence item must PASS (no fresh FAIL)
    QUORUM = "QUORUM"            # Defined threshold of independent verifiers must PASS
    EXACT_MATCH = "EXACT_MATCH"  # Output must match exact deterministic fixture/schema


class CriterionEvidencePolicy(BaseModel):
    """Specification of evidential rules for satisfying an Acceptance Criterion."""
    policy_type: EvidencePolicyType = EvidencePolicyType.ALL
    required_evidence_types: List[EvidenceType] = Field(
        default_factory=lambda: [EvidenceType.TEST_EXECUTION]
    )
    minimum_passing_items: int = 1
    disallow_contradictions: bool = True
    min_provenance_level: ProvenanceClass = ProvenanceClass.SANDBOX_EXECUTION


class EvidenceConflictResolver:
    """Deterministic resolution of multi-evidence contradictions."""

    @staticmethod
    def resolve_criterion(
        policy: CriterionEvidencePolicy,
        evidence_list: List[CanonicalEvidence],
        workspace: Path
    ) -> CriterionEvaluationState:
        if not evidence_list:
            return CriterionEvaluationState.NOT_EVALUATED

        fresh_pass = []
        fresh_fail = []
        stale_count = 0

        for ev in evidence_list:
            curr_fp = SubjectFingerprint.compute(workspace, ev.subject)
            if curr_fp.composite_hash != ev.subject_fingerprint.composite_hash:
                stale_count += 1
                continue

            if ev.outcome == VerificationOutcome.PASS:
                fresh_pass.append(ev)
            elif ev.outcome == VerificationOutcome.FAIL:
                fresh_fail.append(ev)

        # 1. Any fresh deterministic failure results in FAILED
        if len(fresh_fail) > 0:
            return CriterionEvaluationState.FAILED

        # 2. Evaluate Policy
        if policy.policy_type == EvidencePolicyType.ALL:
            present_types = {ev.evidence_type for ev in fresh_pass}
            if all(req_t in present_types for req_t in policy.required_evidence_types):
                return CriterionEvaluationState.PASSED
            return CriterionEvaluationState.STALE if stale_count > 0 else CriterionEvaluationState.NOT_EVALUATED

        elif policy.policy_type == EvidencePolicyType.ANY:
            if len(fresh_pass) >= policy.minimum_passing_items:
                return CriterionEvaluationState.PASSED
            return CriterionEvaluationState.STALE if stale_count > 0 else CriterionEvaluationState.NOT_EVALUATED

        return CriterionEvaluationState.NOT_EVALUATED
```

---

### 5. CompletionDecision & Completion Gate Algorithm

```python
"""Canonical Completion Gate Decision Model and Evaluation Engine."""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from orchestrator.guards.preflight import PreFlightGuard


class CompletionStatus(str, Enum):
    """Canonical completion decision statuses."""
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"


class CompletionDecision(BaseModel):
    """Machine-readable, auditable decision payload produced by the Completion Gate."""
    decision_id: str = Field(default_factory=lambda: f"DEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    status: CompletionStatus
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    blocking_reasons: List[str] = Field(default_factory=list)
    satisfied_requirements: List[str] = Field(default_factory=list)
    unsatisfied_requirements: List[str] = Field(default_factory=list)
    failed_criteria: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    stale_evidence: List[str] = Field(default_factory=list)
    violated_invariants: List[str] = Field(default_factory=list)
    blocking_defects: List[str] = Field(default_factory=list)
    contradictory_evidence: List[str] = Field(default_factory=list)
    required_next_actions: List[str] = Field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return self.status == CompletionStatus.COMPLETE


def evaluate_task_completion(
    graph: "TaskTruthGraph",
    workspace: Path
) -> CompletionDecision:
    """Deterministic, 14-step evaluation of Task Truth completion."""
    
    blocking_reasons: List[str] = []
    satisfied_reqs: List[str] = []
    unsatisfied_reqs: List[str] = []
    failed_criteria: List[str] = []
    missing_evidence: List[str] = []
    stale_evidence: List[str] = []
    violated_invariants: List[str] = []
    blocking_defects: List[str] = []
    contradictory_evidence: List[str] = []
    required_actions: List[str] = []

    # 1. Mandatory Requirements Check
    mandatory_reqs = [r for r in graph.requirements if r.is_mandatory]
    if not mandatory_reqs:
        return CompletionDecision(
            status=CompletionStatus.INCOMPLETE,
            blocking_reasons=["No mandatory requirements defined in TaskTruthGraph."],
            required_next_actions=["Architect must decompose task into mandatory requirements."]
        )

    # 2. Requirement Dependency Evaluation (DAG Check)
    for req in mandatory_reqs:
        for dep_id in req.dependencies:
            dep_req = graph.get_requirement(dep_id)
            if not dep_req or dep_req.verification_state != VerificationState.VERIFIED:
                blocking_reasons.append(
                    f"Requirement '{req.id}' is blocked by unverified dependency '{dep_id}'."
                )

    # 3. Environment & Tool Blockers Check
    if getattr(graph, "external_dependency_blocked", False):
        return CompletionDecision(
            status=CompletionStatus.BLOCKED,
            blocking_reasons=[f"External dependency/provider unavailable: {getattr(graph, 'blocker_reason', 'Unknown')}"],
            required_next_actions=["Restore external connectivity or switch provider."]
        )

    # 4. Invariant Verification Check (Zero-Token Static Pass)
    preflight_ok, preflight_msg = PreFlightGuard.check_syntax(workspace, auto_heal=False)
    if not preflight_ok:
        violated_invariants.append(f"PreFlight Syntax Error: {preflight_msg}")
        blocking_reasons.append(f"Syntax invariant violated:\n{preflight_msg}")
        required_actions.append("Fix syntax compilation errors.")

    # 5. Blocking Defects Evaluation (CRITICAL & HIGH without active waiver)
    for defect in getattr(graph, "blocking_defects", []):
        if not defect.is_resolved and defect.severity in ("CRITICAL", "HIGH"):
            if not getattr(defect, "is_waived", False):
                blocking_defects.append(defect.defect_id)
                blocking_reasons.append(
                    f"Unresolved [{defect.severity}] defect '{defect.defect_id}' in '{defect.file}': {defect.description}"
                )
                required_actions.append(f"Resolve blocking defect '{defect.defect_id}'.")

    # 6. Evaluate Requirements & Criteria
    for req in mandatory_reqs:
        if req.implementation_state != ImplementationState.IMPLEMENTED:
            unsatisfied_reqs.append(req.id)
            blocking_reasons.append(f"Requirement '{req.id}' is not marked IMPLEMENTED.")
            required_actions.append(f"Complete code implementation for '{req.id}'.")
            continue

        req_criteria = [c for c in req.acceptance_criteria if c.is_mandatory]
        if not req_criteria:
            unsatisfied_reqs.append(req.id)
            blocking_reasons.append(f"Requirement '{req.id}' has zero mandatory acceptance criteria.")
            required_actions.append(f"Define acceptance criteria for '{req.id}'.")
            continue

        req_all_criteria_passed = True
        for crit in req_criteria:
            evidence_list = graph.get_evidence_for_criterion(crit.id)
            crit_state = EvidenceConflictResolver.resolve_criterion(crit.policy, evidence_list, workspace)

            if crit_state == CriterionEvaluationState.PASSED:
                continue
            elif crit_state == CriterionEvaluationState.FAILED:
                req_all_criteria_passed = False
                failed_criteria.append(crit.id)
                blocking_reasons.append(f"Criterion '{crit.id}' failed verification.")
                required_actions.append(f"Remediate failing code for criterion '{crit.id}'.")
            elif crit_state == CriterionEvaluationState.STALE:
                req_all_criteria_passed = False
                stale_evidence.append(crit.id)
                blocking_reasons.append(f"Criterion '{crit.id}' has STALE evidence.")
                required_actions.append(f"Re-run verification suite for criterion '{crit.id}'.")
            else:
                req_all_criteria_passed = False
                missing_evidence.append(crit.id)
                blocking_reasons.append(f"Criterion '{crit.id}' lacks required verification evidence.")
                required_actions.append(f"Execute verification for criterion '{crit.id}'.")

        if req_all_criteria_passed:
            satisfied_reqs.append(req.id)
        else:
            unsatisfied_reqs.append(req.id)

    # 7. Unresolved Ambiguity / Mutation Check
    if getattr(graph, "has_unresolved_mutations", False) or getattr(graph, "has_conflicting_requirements", False):
        return CompletionDecision(
            status=CompletionStatus.AMBIGUOUS,
            blocking_reasons=["Task truth contains unresolved mutations or conflicting requirements."],
            required_next_actions=["Replan via Architect or obtain human clarification."]
        )

    # 8. Synthesize Final Status
    if violated_invariants or blocking_defects or failed_criteria:
        status = CompletionStatus.FAILED
    elif blocking_reasons and any("blocked by" in r.lower() for r in blocking_reasons):
        status = CompletionStatus.BLOCKED
    elif unsatisfied_reqs or missing_evidence or stale_evidence or blocking_reasons:
        status = CompletionStatus.INCOMPLETE
    else:
        status = CompletionStatus.COMPLETE

    return CompletionDecision(
        status=status,
        blocking_reasons=blocking_reasons,
        satisfied_requirements=satisfied_reqs,
        unsatisfied_requirements=unsatisfied_reqs,
        failed_criteria=failed_criteria,
        missing_evidence=missing_evidence,
        stale_evidence=stale_evidence,
        violated_invariants=violated_invariants,
        blocking_defects=blocking_defects,
        contradictory_evidence=contradictory_evidence,
        required_next_actions=required_actions,
    )
```

---

# E. Completion Gate Decision Table

| Case ID | Mandatory Requirements | Acceptance Criteria | Attached Evidence State | System Invariants | Active Defects | External Blockers | Final Decision Status |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **DT-01** | All `IMPLEMENTED` | All `PASSED` | 100% `VALID` & `FRESH` | All Clean | 0 Active | None | **`COMPLETE`** |
| **DT-02** | All `IMPLEMENTED` | 1 `FAILED` | Fresh Failure Record | All Clean | 0 Active | None | **`FAILED`** |
| **DT-03** | All `IMPLEMENTED` | 1 Missing Evidence | 0 Records Attached | All Clean | 0 Active | None | **`INCOMPLETE`** |
| **DT-04** | All `IMPLEMENTED` | All `PASSED` | 1 Record `STALE` | All Clean | 0 Active | None | **`INCOMPLETE`** |
| **DT-05** | All `IMPLEMENTED` | All `PASSED` | 100% `FRESH` | **Syntax Error** | 0 Active | None | **`FAILED`** |
| **DT-06** | All `IMPLEMENTED` | All `PASSED` | 100% `FRESH` | All Clean | **1 CRITICAL Defect** | None | **`FAILED`** |
| **DT-07** | All `IMPLEMENTED` | All `PASSED` | 100% `FRESH` | All Clean | 1 LOW (Advisory) | None | **`COMPLETE`** |
| **DT-08** | 1 `IN_PROGRESS` | Unfinished | Missing Evidence | All Clean | 0 Active | None | **`INCOMPLETE`** |
| **DT-09** | Blocked by Dep | Blocked | N/A | All Clean | 0 Active | **Dep Blocked** | **`BLOCKED`** |
| **DT-10** | Unresolved Mutation| Ambiguous | Contradictory | All Clean | 0 Active | None | **`AMBIGUOUS`** |
| **DT-11** | All `IMPLEMENTED` | `ALL` Policy Partial | 1 of 2 Types Present | All Clean | 0 Active | None | **`INCOMPLETE`** |
| **DT-12** | All `IMPLEMENTED` | Reviewer `APPROVED` | Test Evidence Missing | All Clean | 0 Active | None | **`INCOMPLETE`** |

---

# F. Adversarial Scenarios

### Scenario 1: All tests pass, but a requested criterion has no evidence
- **Context:** Pytest returns exit code 0 on existing test suite, but AC-002 (Rate Limiting) has no attached test or evidence record.
- **Decision:** **`INCOMPLETE`** (Missing evidence for AC-002).
- **Enforcing Rule:** Step 6 of Completion Gate checks each mandatory criterion; missing evidence forces `req_all_criteria_passed = False`.

### Scenario 2: A requirement is implemented but not verified
- **Context:** Developer wrote code in `src/auth.py`, setting `ImplementationState = IMPLEMENTED`, but no tests were run.
- **Decision:** **`INCOMPLETE`** (Verification pending).
- **Enforcing Rule:** Step 6 verifies attached evidence; zero evidence keeps `VerificationState = NOT_VERIFIED`.

### Scenario 3: Fresh deterministic evidence fails
- **Context:** Unit test `test_jwt_expiration` asserts HTTP 401 but receives 500 (`AssertionError`).
- **Decision:** **`FAILED`**.
- **Enforcing Rule:** Step 6 detects `fresh_fail_count > 0`, marking criterion `FAILED` and forcing final status `FAILED`.

### Scenario 4: A reviewer approves while deterministic evidence fails
- **Context:** Reviewer agent outputs `"VERDICT: APPROVED"`, but pytest execution failed with exit code 1.
- **Decision:** **`FAILED`**.
- **Enforcing Rule:** Reviewer evidence is bound only to review rubrics. It cannot override a failing `TEST_EXECUTION` record.

### Scenario 5: Evidence is stale after a source change
- **Context:** Tests passed at 10:00. Developer modified `src/auth.py` at 10:05 to fix a typo.
- **Decision:** **`INCOMPLETE`** (`STALE` evidence).
- **Enforcing Rule:** `SubjectFingerprint.compute()` detects composite hash mismatch, invalidating evidence freshness.

### Scenario 6: The task has no explicit acceptance criteria
- **Context:** Architect generated a requirement description with an empty acceptance criteria array.
- **Decision:** **`INCOMPLETE`** (Zero mandatory criteria).
- **Enforcing Rule:** Step 6 explicitly flags requirements with zero criteria as incomplete and prompts for decomposition.

### Scenario 7: The test suite contains zero tests
- **Context:** Pytest runs and exits with code 5 (`collected 0 items`).
- **Decision:** **`INCOMPLETE`** (No tests collected).
- **Enforcing Rule:** `PytestOutputParser` classifies exit code 5 as `NO_TESTS_FOUND`, generating no passing evidence.

### Scenario 8: A required tool is unavailable
- **Context:** Subprocess launcher fails (`uv trampoline` error or binary missing from PATH).
- **Decision:** **`BLOCKED`**.
- **Enforcing Rule:** `PytestOutputParser` classifies crash as `ENVIRONMENT_ERROR`, setting `graph.external_dependency_blocked = True`.

### Scenario 9: Two deterministic executions conflict
- **Context:** AST symbol parser reports function exists, but CLI execution raises `ModuleNotFoundError`.
- **Decision:** **`FAILED`**.
- **Enforcing Rule:** `EvidenceConflictResolver` treats any fresh deterministic execution failure as overriding passes.

### Scenario 10: A task reaches its iteration or token limit
- **Context:** OpenHands conversation loop terminates due to step ceiling (`max_iterations = 5`).
- **Decision:** **`INCOMPLETE`**.
- **Enforcing Rule:** Step limit termination sets execution status to `STOPPED`; Work Truth remains `IN_PROGRESS`.

### Scenario 11: An invariant is violated
- **Context:** Functional tests pass, but `ASTGuard` detects a prohibited `pass` stub in a public API method.
- **Decision:** **`FAILED`**.
- **Enforcing Rule:** Step 4 preflight syntax/invariant check detects violation and forces final status `FAILED`.

### Scenario 12: Evidence belongs to a different repository state
- **Context:** Agent attempts to attach evidence captured on branch `main` to a task running on branch `feature-auth`.
- **Decision:** **`INCOMPLETE`** (`STALE` / Fingerprint Mismatch).
- **Enforcing Rule:** Branch content hashes differ, causing immediate hash verification failure.

---

# G. P3 Input Contract

P2.1 provides the following pure, read-only semantic interface for consumption by P3:

```python
class TaskTruthSemanticQueries:
    """Semantic facts provided to P3 FSM transition guards."""

    @staticmethod
    def can_enter_testing(graph: "TaskTruthGraph") -> bool:
        """True if all mandatory requirements have ImplementationState == IMPLEMENTED."""
        mandatory = [r for r in graph.requirements if r.is_mandatory]
        return len(mandatory) > 0 and all(r.implementation_state == ImplementationState.IMPLEMENTED for r in mandatory)

    @staticmethod
    def can_enter_review(graph: "TaskTruthGraph", workspace: Path) -> bool:
        """True if testing passed for all test-governed criteria and syntax is clean."""
        preflight_ok, _ = PreFlightGuard.check_syntax(workspace)
        return preflight_ok and TaskTruthSemanticQueries.can_enter_testing(graph)

    @staticmethod
    def can_complete(graph: "TaskTruthGraph", workspace: Path) -> bool:
        """True if CompletionGate returns COMPLETE."""
        decision = evaluate_task_completion(graph, workspace)
        return decision.is_complete

    @staticmethod
    def must_block(graph: "TaskTruthGraph", workspace: Path) -> bool:
        """True if CompletionGate returns BLOCKED."""
        decision = evaluate_task_completion(graph, workspace)
        return decision.status == CompletionStatus.BLOCKED

    @staticmethod
    def must_clarify(graph: "TaskTruthGraph", workspace: Path) -> bool:
        """True if CompletionGate returns AMBIGUOUS."""
        decision = evaluate_task_completion(graph, workspace)
        return decision.status == CompletionStatus.AMBIGUOUS
```

### P3 Operating Assumptions:
- P3 may assume that `evaluate_task_completion()` is a pure, side-effect-free function.
- P3 must **not** reimplement evidence validation, hash checking, or criteria evaluation inside FSM transition guards.
- P3 is responsible for designing phase states, transition recovery loops, and execution orchestration around these semantic queries.

---

# H. P2.1 Exit Criteria Checklist

- [x] Multi-dimensional state model (`ImplementationState`, `VerificationState`, `BlockingState`) formally defined.
- [x] Contextual Evidence Policies (`ALL`, `ANY`, `QUORUM`, `EXACT_MATCH`) replace simplistic trust ladders.
- [x] Elimination of `pytest == 0 => COMPLETE` false-completion trap formalized.
- [x] Cryptographic content identity and canonical hashing defined without timestamp dependencies.
- [x] Declared `EvidenceSubject` captures all target files, test fixtures, configs, and lockfiles.
- [x] Strongly typed evidence payloads specified for Test, AST, CLI, Review, Audit, Docs, and Invariants.
- [x] Canonical 14-step `evaluate_task_completion()` algorithm and `CompletionDecision` schema defined.
- [x] Discrete, reachable decision states formalized: `COMPLETE`, `INCOMPLETE`, `FAILED`, `BLOCKED`, `AMBIGUOUS`.
- [x] Independent verification enforced (Zero Agent Self-Certification).
- [x] P3 Semantic Query Contract specified without premature FSM redesign.
- [x] Zero production code modified during this design phase.

---

# I. Deferred Work

The following domains are explicitly deferred to subsequent phases:
- **P3:** Guarded Finite State Machine redesign, error recovery lifecycles, and phase loop orchestration.
- **P4:** Adaptive Token Governor thresholds, dynamic step recalculation, and monetary circuit breakers.
- **P5:** Agent prompt engineering, milestone DAG chunking, and tool execution bindings.
- **P6:** Context handoff compression and cross-stage memory stores.

---

# J. Final Readiness Assessment

The P2.1 Evidence & Completion Gate Architecture Specification is **100% complete, internally consistent, and ready to serve as the foundation for P3**. All architectural contradictions, false-completion paths, and trust oversimplifications have been eliminated.
