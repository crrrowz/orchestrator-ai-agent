"""Outbound Driven Agent Runtime Port Protocol.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
"""

from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field
from orchestrator.domain.context_models import HandoffEnvelope


@dataclass
class AgentExecutionOutcome:
    """Strongly-typed execution outcome from an ephemeral agent turn."""

    success: bool
    iterations_used: int
    tokens_consumed: int
    cost_usd: float
    output_text: str
    modified_files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@runtime_checkable
class AgentRuntimePort(Protocol):
    """Outbound port for executing bounded agent turns via an underlying runtime."""

    def execute_bounded_turn(
        self,
        persona: str,
        envelope: HandoffEnvelope,
        max_turns: int,
        token_budget: int,
    ) -> AgentExecutionOutcome:
        ...
