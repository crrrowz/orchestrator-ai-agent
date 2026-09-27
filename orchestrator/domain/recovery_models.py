"""Stagnation & Velocity Domain Models for ORAGAI Pure Domain Core.

Classification: Enterprise Architectural Blueprint & Canonical System Standard
Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant: Zero external framework dependencies (stdlib + pydantic only).
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MutationStrategy(str, Enum):
    """4-Tier Strategy Mutation Enum for Stagnation Recovery."""

    PROMPT_SPECIALIZATION = "PROMPT_SPECIALIZATION"
    MILESTONE_SPLITTING = "MILESTONE_SPLITTING"
    PERSONA_REPLACEMENT = "PERSONA_REPLACEMENT"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"


class VelocityVector(BaseModel):
    """4-Dimensional Progress Velocity Vector V_k."""

    turn_index: int
    v_req: float = Field(..., description="Delta implemented requirements")
    v_verif: float = Field(..., description="Delta verified criteria")
    v_ast: float = Field(..., description="Delta AST syntax compliance")
    v_test: float = Field(..., description="Delta net test passes (passes - regressions)")
    is_positive: bool = Field(..., description="True if progress was made across any dimension")


class RecoveryDecision(BaseModel):
    """Deterministic recovery supervisor decision."""

    is_stagnated: bool
    stagnation_reason: Optional[str] = None
    recommended_strategy: Optional[MutationStrategy] = None
    mutation_payload: Optional[str] = None
    target_milestone_id: Optional[str] = None
