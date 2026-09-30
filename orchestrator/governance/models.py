"""Data models and enums for the Adaptive Iteration Governance Layer.

Defines execution health classifications, governance actions, task budget profiles,
step telemetry snapshots, and decision records.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field


class GovernanceAction(str, Enum):
    """Authoritative actions emitted by the Iteration Governor."""
    CONTINUE = "CONTINUE"
    EXTEND_BUDGET = "EXTEND_BUDGET"
    CHANGE_STRATEGY = "CHANGE_STRATEGY"
    REPLAN_TASK = "REPLAN_TASK"
    PAUSE_BLOCK = "PAUSE_BLOCK"
    RETRY = "RETRY"
    FAIL = "FAIL"
    VERIFY_COMPLETION = "VERIFY_COMPLETION"


class ExecutionHealth(str, Enum):
    """Health classification of the active agent execution stream."""
    HEALTHY = "HEALTHY"
    PROGRESSING = "PROGRESSING"
    CHAOTIC = "CHAOTIC"
    STAGNANT = "STAGNANT"
    CYCLING = "CYCLING"
    EXHAUSTED = "EXHAUSTED"
    BLOCKED = "BLOCKED"
    CRITICAL_FAILURE = "CRITICAL_FAILURE"


class TaskCategory(str, Enum):
    """Categorization of autonomous engineering tasks."""
    ARCHITECTURE = "ARCHITECTURE"
    IMPLEMENTATION = "IMPLEMENTATION"
    DEBUGGING = "DEBUGGING"
    TESTING = "TESTING"
    REVIEW = "REVIEW"
    AUDIT = "AUDIT"
    REFACTORING = "REFACTORING"
    RESEARCH = "RESEARCH"
    DOCUMENTATION = "DOCUMENTATION"
    SECURITY = "SECURITY"
    CODE_GENERATION = "CODE_GENERATION"


class TaskBudgetProfile(BaseModel):
    """Dynamic turn budget bounds and checkpoint configurations per task category."""
    model_config = ConfigDict(frozen=True)

    category: TaskCategory
    initial_turns: int = Field(default=15, ge=1)
    min_turns: int = Field(default=5, ge=1)
    max_extension_turns: int = Field(default=10, ge=0)
    max_total_ceiling_turns: int = Field(default=45, ge=5)
    checkpoint_interval: int = Field(default=5, ge=1)
    exploration_phase_turns: int = Field(default=6, ge=1)
    expected_tools: List[str] = Field(default_factory=list)


class StepRecord(BaseModel):
    """Observation record for an individual agent iteration step."""
    model_config = ConfigDict(frozen=True)

    step_index: int
    action_type: str
    tool_name: str
    target_path: Optional[str] = None
    command: Optional[str] = None
    is_mutation: bool = False
    is_read: bool = False
    is_terminal: bool = False
    is_error: bool = False
    error_message: Optional[str] = None
    timestamp: float = Field(default=0.0)


class ProgressMetricsSnapshot(BaseModel):
    """Quantitative metric summary computed over the execution window."""
    model_config = ConfigDict(frozen=True)

    total_steps: int = 0
    mutation_steps: int = 0
    read_steps: int = 0
    terminal_steps: int = 0
    error_steps: int = 0
    unique_files_mutated: int = 0
    unique_files_read: int = 0
    repetition_score: float = 0.0
    action_diversity_score: float = 0.0
    mutation_velocity: float = 0.0
    error_rate: float = 0.0
    consecutive_stagnant_steps: int = 0
    consecutive_errors: int = 0


class GovernanceDecision(BaseModel):
    """Decision produced by the Iteration Governor at a checkpoint or turn yield."""
    model_config = ConfigDict(frozen=True)

    action: GovernanceAction
    health: ExecutionHealth
    reason: str
    allocated_turns_extension: int = 0
    recommended_directive: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: Dict[str, Any] = Field(default_factory=dict)
