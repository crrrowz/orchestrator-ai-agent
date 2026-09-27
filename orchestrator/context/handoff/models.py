"""Canonical Data Models, Schemas, and Cryptographic Envelopes for P6 Context Handoff.

File Location: orchestrator/context/handoff/models.py
Architecture Reference: docs/plans/P6_CONTEXT_AND_EVIDENCE_HANDOFF_PLAN.md
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field


# ============================================================================
# 1. EXCEPTIONS
# ============================================================================

class HandoffError(Exception):
    """Base exception for all context handoff errors."""
    pass


class MissingHandoffArtifactError(HandoffError):
    """Raised when an expected upstream handoff artifact is missing or empty."""
    pass


class HandoffIntegrityError(HandoffError):
    """Raised when cryptographic verification of a handoff payload fails."""
    pass


class ContextHeadroomExhaustionError(HandoffError):
    """Raised when immutable Tier 0 intent exceeds safe context window ceiling."""
    pass


class StaleEvidenceError(HandoffError):
    """Raised when an action relies on evidence invalidated by working tree mutations."""
    pass


# ============================================================================
# 2. ENUMS & CONSTANTS
# ============================================================================

class ContextTierEnum(str, Enum):
    """Priority tiers for prompt assembly and dynamic context clamping."""
    TIER_0_INTENT = "TIER_0_INTENT"          # Immutable: Task Truth, ACs, Invariants, RBAC
    TIER_1_DIAGNOSTICS = "TIER_1_DIAGNOSTICS" # High: Compacted Traces, Upstream Handoff
    TIER_2_CODE = "TIER_2_CODE"               # Medium: AST-Folded Code, Target Symbols, Diffs
    TIER_3_ARCHITECTURE = "TIER_3_ARCHITECTURE" # Low: Graft Skeleton, Skills, Memory Lessons


# Backwards compatibility / convenience alias
ContextTier = ContextTierEnum


class HandoffTypeEnum(str, Enum):
    """Categorical classification of inter-agent handoff payloads."""
    ARCHITECT_TO_DEVELOPER = "ARCHITECT_TO_DEVELOPER"
    DEVELOPER_TO_TESTER = "DEVELOPER_TO_TESTER"
    TESTER_TO_REVIEWER = "TESTER_TO_REVIEWER"
    REVIEWER_TO_REMEDIATION = "REVIEWER_TO_REMEDIATION"
    REMEDIATION_TO_TESTER = "REMEDIATION_TO_TESTER"
    AUDITOR_TO_ARCHITECT = "AUDITOR_TO_ARCHITECT"
    GENERIC_HANDOFF = "GENERIC_HANDOFF"


# Convenience alias
HandoffType = HandoffTypeEnum


class PersonaViewType(str, Enum):
    """Persona-specific prompt view formats."""
    ARCHITECT_VIEW = "ARCHITECT_VIEW"
    DEVELOPER_VIEW = "DEVELOPER_VIEW"
    TESTER_VIEW = "TESTER_VIEW"
    REVIEWER_VIEW = "REVIEWER_VIEW"
    REMEDIATION_VIEW = "REMEDIATION_VIEW"
    AUDITOR_VIEW = "AUDITOR_VIEW"


# Convenience alias
PersonaRole = PersonaViewType


PersonaViewTypeEnum = PersonaViewType


class FreshnessState(str, Enum):
    """Freshness lifecycle status of evidence artifacts."""
    FRESH = "FRESH"
    STALE = "STALE"
    INVALID = "INVALID"
    INVALIDATED = "INVALIDATED"


FreshnessStateEnum = FreshnessState


DEFAULT_TOKEN_RESERVE_HEADROOM = 2048
CHARS_PER_TOKEN_ESTIMATE = 4.0
DEFAULT_MAX_CONTEXT_CHARS = 128_000
DEFAULT_OUTPUT_HEADROOM_CHARS = 16_000


# ============================================================================
# 3. PYDANTIC SPECS & CRITERIA MODELS
# ============================================================================

class RequiredSymbolSpec(BaseModel):
    """Specification of an architectural symbol required in implementation."""
    name: str
    type: str = "function"  # "class", "function", "method", "protocol"
    interfaces: list[str] = Field(default_factory=list)
    docstring: str = ""


class LineAnchoredFix(BaseModel):
    """Line-anchored defect directive targeting surgical code remediation."""
    file: str
    line: int
    symbol: str = ""
    issue: str = ""
    remediation: str = ""
    severity: str = "MAJOR"  # "CRITICAL", "MAJOR", "MINOR"


# ============================================================================
# 4. DIAGNOSTIC TRACE MODELS
# ============================================================================

@dataclass(frozen=True)
class CompactedFrame:
    """Individual call site frame extracted from a failure traceback."""
    file_path: str
    line_number: int
    function_name: str
    code_line: str


@dataclass(frozen=True)
class DiagnosticFailureTrace:
    """Compacted failure diagnostic extracted from test execution output."""
    node_id: str
    exception_type: str
    exception_message: str
    primary_frame: Optional[CompactedFrame] = None
    assertion_diff: Optional[str] = None
    captured_stdout_tail: Optional[str] = None

    def to_markdown(self) -> str:
        """Render a compact, high-signal Markdown representation."""
        lines = [f"**FAILED TEST:** `{self.node_id}`"]
        if self.primary_frame:
            lines.append(
                f"- **Location:** `{self.primary_frame.file_path}:{self.primary_frame.line_number}` "
                f"in `{self.primary_frame.function_name}`"
            )
            if self.primary_frame.code_line:
                lines.append(f"  ```python\n  {self.primary_frame.code_line}\n  ```")
        lines.append(f"- **Exception:** `{self.exception_type}`: {self.exception_message}")
        if self.assertion_diff:
            lines.append(f"- **Assert Diff:**\n```diff\n{self.assertion_diff}\n```")
        if self.captured_stdout_tail:
            lines.append(f"- **Stdout (Tail):**\n```\n{self.captured_stdout_tail}\n```")
        return "\n".join(lines)


@dataclass
class DiagnosticTraceSummary:
    """Consolidated summary of multiple diagnostic failure traces."""
    total_failures: int = 0
    traces: List[DiagnosticFailureTrace] = field(default_factory=list)
    summary_text: str = ""
    exit_code: int = 0
    raw_output_length: int = 0
    compacted_output_length: int = 0

    def to_markdown(self) -> str:
        """Render complete failure summary formatted for prompt injection."""
        lines = [f"### Pytest Diagnostic Summary (Failures: {self.total_failures}, Exit Code: {self.exit_code})"]
        if self.summary_text:
            lines.append(f"**Overview:** {self.summary_text}")
        for idx, trace in enumerate(self.traces, 1):
            lines.append(f"\n#### Failure [{idx}/{self.total_failures}]")
            lines.append(trace.to_markdown())
        return "\n".join(lines)


# ============================================================================
# 5. TYPED HANDOFF PAYLOADS
# ============================================================================

@dataclass
class ArchitectHandoffPayload:
    """Typed handoff payload emitted by Architect for Developer consumption."""
    milestone_id: str
    target_files: List[str]
    target_symbols: List[str]
    public_api_contracts: List[Dict[str, Any]] = field(default_factory=list)
    acceptance_criteria: List[Dict[str, str]] = field(default_factory=list)
    architectural_boundaries: List[str] = field(default_factory=list)
    implementation_guidance: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown_summary(self) -> str:
        return (
            f"### Architect Blueprint for `{self.milestone_id}`\n"
            f"- **Target Files:** {', '.join(self.target_files) if self.target_files else 'None'}\n"
            f"- **Target Symbols:** {', '.join(self.target_symbols) if self.target_symbols else 'None'}\n"
            f"- **Acceptance Criteria Count:** {len(self.acceptance_criteria)}\n"
            f"- **Layering Boundaries:** {'; '.join(self.architectural_boundaries) if self.architectural_boundaries else 'Standard'}\n\n"
            f"**Guidance:** {self.implementation_guidance}"
        )


@dataclass
class DeveloperHandoffPayload:
    """Typed handoff payload emitted by Developer for Tester consumption."""
    milestone_id: str
    modified_files: List[str]
    modified_symbols: List[Dict[str, Any]] = field(default_factory=list)
    preflight_hash: str = ""
    implementation_notes: str = ""
    boundary_hazards: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown_summary(self) -> str:
        symbols_str = ", ".join(s.get("name", str(s)) for s in self.modified_symbols) or "None"
        hash_disp = self.preflight_hash[:16] if self.preflight_hash else "None"
        return (
            f"### Developer Implementation Summary (`{self.milestone_id}`)\n"
            f"- **Modified Files:** {', '.join(self.modified_files) if self.modified_files else 'None'}\n"
            f"- **Modified Symbols:** {symbols_str}\n"
            f"- **PreFlight Hash:** `{hash_disp}`\n"
            f"- **Identified Hazards:** {'; '.join(self.boundary_hazards) if self.boundary_hazards else 'None'}\n\n"
            f"**Notes:** {self.implementation_notes}"
        )


@dataclass
class TesterHandoffPayload:
    """Typed handoff payload emitted by Tester for Reviewer consumption."""
    milestone_id: str = ""
    test_execution_status: str = "PASSED"
    pytest_exit_code: int = 0
    total_tests_run: int = 0
    passed_count: int = 0
    failed_count: int = 0
    executed_node_ids: List[str] = field(default_factory=list)
    ac_verification_map: Dict[str, bool] = field(default_factory=dict)
    compacted_failures: List[Dict[str, Any]] = field(default_factory=list)

    # Prevent pytest from collecting this dataclass as a test case
    __test__ = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown_summary(self) -> str:
        status_emoji = "✅" if self.test_execution_status == "PASSED" else "❌"
        verified_count = sum(1 for v in self.ac_verification_map.values() if v)
        total_ac = len(self.ac_verification_map)
        return (
            f"### Tester Verification Proof (`{self.milestone_id}`) {status_emoji}\n"
            f"- **Status:** `{self.test_execution_status}` (Exit Code: {self.pytest_exit_code})\n"
            f"- **Summary:** Total: {self.total_tests_run} | Passed: {self.passed_count} | Failed: {self.failed_count}\n"
            f"- **Executed Tests:** {len(self.executed_node_ids)} nodes\n"
            f"- **AC Coverage:** {verified_count} / {total_ac} verified"
        )


@dataclass
class ReviewerHandoffPayload:
    """Typed handoff payload emitted by Reviewer for Remediation consumption."""
    milestone_id: str
    review_verdict: str  # APPROVED | REJECTED_WITH_DEFECTS | BLOCKED
    defect_directives: List[Dict[str, Any]] = field(default_factory=list)
    rubric_scores: Dict[str, int] = field(default_factory=dict)
    general_critique: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown_summary(self) -> str:
        lines = [
            f"### Code Review Critique (`{self.milestone_id}`): `{self.review_verdict}`",
            f"**Critique:** {self.general_critique}",
            f"**Directives ({len(self.defect_directives)}):**"
        ]
        for d in self.defect_directives:
            lines.append(
                f"- **[{d.get('severity', 'MAJOR')}]** `{d.get('file_path', d.get('file'))}:{d.get('line_anchor', d.get('line'))}` "
                f"({d.get('symbol_name', d.get('symbol', 'unknown'))}): {d.get('expected_behavior', d.get('remediation', d.get('issue')))}"
            )
        return "\n".join(lines)


# ============================================================================
# 6. CROSS-AGENT HANDOFF PAYLOAD & ENVELOPE
# ============================================================================

class CrossAgentHandoffPayload(BaseModel):
    """Immutable, cryptographically verifiable handoff packet between agent personas."""
    handoff_type: HandoffTypeEnum
    milestone_id: str = ""
    source_role: str = "Architect"
    target_role: str = "Developer"
    timestamp: float = Field(default_factory=time.time)
    payload_hash: str = ""
    workspace_sha256: str = ""

    # Context data
    target_files: list[str] = Field(default_factory=list)
    required_symbols: list[RequiredSymbolSpec] = Field(default_factory=list)
    authored_symbols: list[str] = Field(default_factory=list)
    acceptance_criteria_ids: list[str] = Field(default_factory=list)
    test_node_ids: list[str] = Field(default_factory=list)
    review_verdict: Optional[str] = None
    required_fixes: list[LineAnchoredFix] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def compute_hash(self) -> str:
        """Compute deterministic SHA-256 digest of payload contents."""
        serialized = self.model_dump_json(exclude={"payload_hash"})
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def seal(self, workspace_sha256: str = "") -> "CrossAgentHandoffPayload":
        """Compute and set the cryptographic hash, optionally binding workspace hash."""
        if workspace_sha256:
            self.workspace_sha256 = workspace_sha256
        self.payload_hash = self.compute_hash()
        return self

    def verify_integrity(self) -> bool:
        """Validate payload authenticity against recorded SHA-256 hash."""
        if not self.payload_hash:
            return False
        return self.compute_hash() == self.payload_hash


@dataclass
class HandoffEnvelope:
    """Cryptographically sealed inter-agent communication envelope."""
    envelope_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    schema_version: str = "1.0.0"
    handoff_type: HandoffTypeEnum = HandoffTypeEnum.ARCHITECT_TO_DEVELOPER
    sender_persona: str = "Architect"
    recipient_persona: str = "Developer"
    milestone_id: str = ""
    workspace_sha256: str = ""
    created_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    typed_payload: Dict[str, Any] = field(default_factory=dict)
    payload_sha256: str = ""

    def compute_hash(self) -> str:
        """Compute deterministic SHA-256 digest of payload data."""
        serialized = json.dumps(self.typed_payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def seal(self, current_workspace_sha256: str = "") -> "HandoffEnvelope":
        """Compute SHA-256 payload digest and bind to workspace state."""
        if current_workspace_sha256:
            self.workspace_sha256 = current_workspace_sha256
        self.payload_sha256 = self.compute_hash()
        return self

    def verify_integrity(self) -> bool:
        """Validate payload authenticity against recorded SHA-256 hash."""
        if not self.payload_sha256:
            return False
        return self.compute_hash() == self.payload_sha256

    @classmethod
    def from_payload(
        cls,
        payload: CrossAgentHandoffPayload,
        workspace_sha256: str = "",
    ) -> "HandoffEnvelope":
        """Wrap and seal a CrossAgentHandoffPayload into a HandoffEnvelope."""
        envelope = cls(
            handoff_type=payload.handoff_type,
            sender_persona=payload.source_role,
            recipient_persona=payload.target_role,
            milestone_id=payload.milestone_id,
            workspace_sha256=workspace_sha256 or payload.workspace_sha256,
            typed_payload=payload.model_dump(),
        )
        envelope.seal(workspace_sha256 or payload.workspace_sha256)
        return envelope


# ============================================================================
# 7. CONTEXT BLOCK & FINGERPRINT MODELS
# ============================================================================

@dataclass
class ContextBlock:
    """A bounded segment of prompt context with assigned priority tier."""
    tier: ContextTierEnum
    title: str
    content: str
    estimated_tokens: int = 0
    estimated_chars: int = 0

    def __post_init__(self):
        self.estimated_chars = len(self.content)
        if self.estimated_tokens == 0:
            self.estimated_tokens = max(1, int(self.estimated_chars / CHARS_PER_TOKEN_ESTIMATE))


@dataclass(frozen=True)
class SubjectFingerprint:
    """Content hash of a single tracked workspace subject/file."""
    subject_path: str
    sha256_hash: str
    byte_size: int
    last_modified_timestamp: float


FileContentDigest = SubjectFingerprint


@dataclass(frozen=True)
class WorkspaceDigest:
    """Deterministic composite content digest of the active workspace."""
    composite_sha256: str
    file_digests: Dict[str, SubjectFingerprint]
    captured_at_utc: str
