"""Adaptive Governance Engine models and decision verdicts."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class GovernanceVerdict(str, Enum):
    CONTINUE = "continue"
    EXTEND_BUDGET = "extend_budget"
    REPLAN = "replan"
    RETRY = "retry"
    DECOMPOSE = "decompose"
    VERIFY = "verify"
    HALT = "halt"


class GovernanceDecision(BaseModel):
    verdict: GovernanceVerdict
    reason: str = ""
    budget_adjustment_tokens: int = 0
    budget_adjustment_usd: float = 0.0
    suggested_action: Optional[str] = None
    metrics_snapshot: Dict[str, Any] = Field(default_factory=dict)
