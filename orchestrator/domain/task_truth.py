"""Pure Domain Core Entities & Value Objects for ORAGAI.

Classification: Enterprise Architectural Blueprint & Canonical System Standard
Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant: Zero external framework dependencies (stdlib + pydantic only).
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RequirementCategory(str, Enum):
    """Categorization of decomposed requirements."""

    FUNCTIONAL = "FUNCTIONAL"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"
    ARCHITECTURAL = "ARCHITECTURAL"
    SECURITY = "SECURITY"


class ImplementationState(str, Enum):
    """Lifecycle state of requirement code implementation."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    IMPLEMENTED = "IMPLEMENTED"
    BLOCKED = "BLOCKED"
    DEPRECATED = "DEPRECATED"


class VerificationState(str, Enum):
    """Deterministic verification state evaluated by cryptographic completion gates."""

    UNVERIFIED = "UNVERIFIED"
    TEST_WRITTEN = "TEST_WRITTEN"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class AcceptanceCriterion(BaseModel):
    """Atomic, testable acceptance criterion bound to a parent Requirement."""

    id: str = Field(..., description="Stable identifier, e.g., 'AC-001-A'")
    requirement_id: str = Field(..., description="Parent Requirement ID")
    description: str = Field(..., description="Specific, testable criterion text")
    verification_method: str = Field(..., description="e.g., 'PYTEST_UNIT', 'AST_STATIC'")
    target_path: Optional[str] = Field(None, description="Path to file or module tested")
    is_satisfied: bool = Field(False, description="Deterministic satisfaction status")
    evidence_id: Optional[str] = Field(None, description="Linked EvidenceReference ID")


class Requirement(BaseModel):
    """Formal requirement entity extracted from task specifications."""

    id: str = Field(..., description="Stable identifier, e.g., 'REQ-001'")
    title: str = Field(..., description="Concise requirement title")
    description: str = Field(..., description="Formal requirement specification")
    category: RequirementCategory = Field(default=RequirementCategory.FUNCTIONAL)
    is_mandatory: bool = Field(default=True)
    implementation_state: ImplementationState = Field(default=ImplementationState.PENDING)
    verification_state: VerificationState = Field(default=VerificationState.UNVERIFIED)
    acceptance_criteria: List[AcceptanceCriterion] = Field(default_factory=list)
    source_prompt_hash: str = Field(default="", description="SHA-256 hash of originating prompt")


class TaskMilestone(BaseModel):
    """Topological milestone node grouping requirements."""

    id: str = Field(..., description="Milestone ID, e.g., 'M-01'")
    name: str = Field(..., description="Human-readable milestone name")
    requirement_ids: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list, description="Dependency milestone IDs")
    is_completed: bool = Field(default=False)
    checkpoint_commit_sha: Optional[str] = Field(default=None, description="Commit SHA upon completion")


class TaskTruthGraph(BaseModel):
    """Immutable Master Task Truth Graph governing orchestrator verification."""

    task_id: str = Field(..., description="Globally unique task ID")
    raw_prompt: str = Field(..., description="Original user prompt")
    requirements: Dict[str, Requirement] = Field(default_factory=dict)
    milestones: Dict[str, TaskMilestone] = Field(default_factory=dict)
    active_milestone_id: Optional[str] = None
    workspace_root: str = Field(..., description="Absolute path to workspace root")
    created_at_utc: str = Field(..., description="ISO-8601 UTC timestamp")

    def is_task_complete(self) -> bool:
        mandatory_reqs = [r for r in self.requirements.values() if r.is_mandatory]
        if not mandatory_reqs:
            return False
        return all(r.verification_state == VerificationState.VERIFIED for r in mandatory_reqs)
