"""Context & Handoff Domain Models for ORAGAI Pure Domain Core.

Classification: Enterprise Architectural Blueprint & Canonical System Standard
Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant: Zero external framework dependencies (stdlib + pydantic only).
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List
from pydantic import BaseModel, Field


class ContextTier(str, Enum):
    """Priority tiers for prompt synthesis and context preservation."""

    TIER_0_SYSTEM_MANDATES = "TIER_0_SYSTEM_MANDATES"
    TIER_1_TASK_TRUTH = "TIER_1_TASK_TRUTH"
    TIER_2_EVIDENCE_HANDOFF = "TIER_2_EVIDENCE_HANDOFF"
    TIER_3_ARCHITECTURE_SUMMARY = "TIER_3_ARCHITECTURE_SUMMARY"


class HandoffType(str, Enum):
    """Categorization of inter-persona state handoff packages."""

    ARCHITECT_TO_DEVELOPER = "ARCHITECT_TO_DEVELOPER"
    DEVELOPER_TO_TESTER = "DEVELOPER_TO_TESTER"
    TESTER_TO_REVIEWER = "TESTER_TO_REVIEWER"
    AUDITOR_TO_ARCHITECT = "AUDITOR_TO_ARCHITECT"
    REVIEWER_TO_CHECKPOINT = "REVIEWER_TO_CHECKPOINT"


class HandoffEnvelope(BaseModel):
    """Cryptographically sealed envelope transferring context across agent personas."""

    handoff_type: HandoffType
    source_persona: str
    target_persona: str
    active_milestone_id: str
    merkle_root: str = Field(..., description="SHA-256 Merkle root of workspace")
    modified_files: List[str] = Field(default_factory=list)
    evidence_manifest: List[str] = Field(default_factory=list, description="Evidence IDs")
    context_slices: Dict[ContextTier, str] = Field(default_factory=dict)
    timestamp_utc: str
