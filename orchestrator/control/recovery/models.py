"""Data models, enums, and protocols for the Progress, Stagnation & Recovery Engine (P8)."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple

from pydantic import BaseModel, Field


# ============================================================================
# 1. Enums & Strong Typing Definitions
# ============================================================================

class BreakerState(str, Enum):
    """4-Tier Adaptive Circuit Breaker States."""
    CLOSED = "CLOSED"                        # Normal execution, full velocity
    DEGRADED = "DEGRADED"                    # Sluggish progress, tightened budgets
    STRATEGY_MUTATING = "STRATEGY_MUTATING"  # Active cognitive mutation in progress
    TRIPPED_ESCALATING = "TRIPPED_ESCALATING"  # Exhausted; quarantine & escalate


class ProgressHealth(str, Enum):
    """Classification of turn progress health."""
    THRIVING = "THRIVING"                    # Score >= 0.80 (Tests/evidence advancing)
    MAKING_PROGRESS = "MAKING_PROGRESS"      # 0.55 <= Score < 0.80 (Clean AST changes)
    MARGINAL_CHURN = "MARGINAL_CHURN"        # 0.40 <= Score < 0.55 (Cosmetic/exploratory)
    STAGNANT = "STAGNANT"                    # 0.20 <= Score < 0.40 (Zero diff / error repeat)
    REGRESSING = "REGRESSING"                # Score < 0.20 (Broken syntax / test failures)


class CyclePattern(str, Enum):
    """Classification of detected execution cycle."""
    NONE = "NONE"                            # No cycle detected
    DIRECT_STAGNATION = "DIRECT_STAGNATION"  # Period 1: Identical failure and zero diff
    FLIP_FLOP_P2 = "FLIP_FLOP_P2"            # Period 2: A -> B -> A cycle
    PERIODIC_PN = "PERIODIC_PN"              # Period 3..5: Multi-step cycle
    COSMETIC_CHURN = "COSMETIC_CHURN"        # Whitespace/comment diff evasion


class MutationStrategyType(str, Enum):
    """4-Tier Strategy Mutation Taxonomy."""
    PROMPT_STEERING = "PROMPT_STEERING"            # Level 1: Anti-oscillation & diagnostic hints
    TARGET_DECOMPOSITION = "TARGET_DECOMPOSITION"  # Level 2: Sub-atomic milestone split
    TOOL_CONSTRICTION = "TOOL_CONSTRICTION"        # Level 3: Restrict shell, force AST patch
    MODEL_ELEVATION = "MODEL_ELEVATION"            # Level 4: Route to Tier-1 reasoning model


class RecoveryActionType(str, Enum):
    """Deterministic recovery actions dispatched by RecoveryOrchestrator."""
    CONTINUE_NORMAL = "CONTINUE_NORMAL"
    INJECT_MUTATION = "INJECT_MUTATION"
    TRANSACTIONAL_ROLLBACK = "TRANSACTIONAL_ROLLBACK"
    QUARANTINE_MILESTONE = "QUARANTINE_MILESTONE"
    ESCALATE_HITL = "ESCALATE_HITL"


# ============================================================================
# 2. Domain Data Models & Telemetry Schemas
# ============================================================================

@dataclass(frozen=True)
class ASTSymbolSignature:
    """Normalized structural symbol signature stripped of comments and whitespace."""
    symbol_type: str  # "ClassDef", "FunctionDef", "AsyncFunctionDef", "Import"
    name: str
    body_ast_hash: str


@dataclass
class StateFingerprint:
    """Composite state fingerprint for sliding-window cycle detection."""
    turn_index: int
    ast_composite_hash: str
    failing_tests_hash: str
    defect_state_hash: str
    timestamp: float = field(default_factory=time.time)

    @property
    def composite_hash(self) -> str:
        payload = f"{self.ast_composite_hash}:{self.failing_tests_hash}:{self.defect_state_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class ProgressVelocityMetrics:
    """4-Dimensional Progress Velocity Vector."""
    v_code: float           # AST structural diff velocity in [0.0, 1.0]
    v_verif: float          # Passed test node advance delta
    v_evid: float           # Acceptance criteria satisfaction delta
    v_defect: float         # Verified defect resolution delta
    tokens_consumed: int
    per_score: float        # Progress Efficiency Ratio (PER 2.0)
    normalized_score: float # Sigmoidal score in [0.0, 1.0]
    health: ProgressHealth


@dataclass
class StrategyMutationDirective:
    """Concrete mutation payload delivered to execution plane."""
    mutation_type: MutationStrategyType
    tier_level: int
    prompt_injections: List[str] = field(default_factory=list)
    banned_tools: Set[str] = field(default_factory=set)
    forced_tools: Set[str] = field(default_factory=set)
    decomposed_subtasks: List[str] = field(default_factory=list)
    elevated_model: Optional[str] = None
    target_file_lock: Optional[str] = None


@dataclass
class RecoveryDecision:
    """Unified recovery decision emitted by RecoveryOrchestrator."""
    action: RecoveryActionType
    breaker_state: BreakerState
    health: ProgressHealth
    detected_cycle: CyclePattern
    cycle_period: int
    mutation_directive: Optional[StrategyMutationDirective] = None
    rollback_checkpoint_ref: Optional[str] = None
    explanation: str = ""


class QuarantinedMilestoneRecord(BaseModel):
    """Schema for persisted docs/quarantined_findings.json entry."""
    milestone_id: str
    task_id: str
    quarantine_timestamp: str
    exhausted_mutations: List[str] = Field(default_factory=list)
    failing_test_nodes: List[str] = Field(default_factory=list)
    last_ast_diff: str = ""
    diagnostic_summary: str = ""
    suggested_human_action: str = ""


class HITLEscalationPayload(BaseModel):
    """Structured escalation payload delivered to HumanChannel on deadlock."""
    run_id: str
    deadlock_type: str  # "CONTRADICTORY_REQUIREMENTS", "ENVIRONMENT_DEFECT", "MUTATION_EXHAUSTION"
    blocked_milestones: List[str] = Field(default_factory=list)
    failing_tests: List[str] = Field(default_factory=list)
    attempted_mutations: List[str] = Field(default_factory=list)
    quarantined_findings_path: str = ""
    recommended_options: List[str] = Field(default_factory=list)


# ============================================================================
# 3. Component Protocols
# ============================================================================

class ISemanticProgressTracker(Protocol):
    """Protocol for semantic progress tracking engine."""

    def record_turn_snapshot(
        self,
        turn_index: int,
        passed_test_nodes: Set[str],
        failed_test_nodes: Dict[str, str],
        satisfied_ac_ids: Set[str],
        open_defect_ids: Set[str],
        tokens_consumed: int,
    ) -> ProgressVelocityMetrics: ...


class IOscillationDetector(Protocol):
    """Protocol for oscillation and cycle detection engine."""

    def register_state(self, fingerprint: StateFingerprint) -> Tuple[CyclePattern, int]: ...
    def reset_window(self) -> None: ...


class IAdaptiveCircuitBreaker(Protocol):
    """Protocol for 4-tier adaptive circuit breaker."""

    def evaluate_state_transition(
        self,
        metrics: ProgressVelocityMetrics,
        cycle_pattern: CyclePattern,
    ) -> BreakerState: ...


class IStrategyMutator(Protocol):
    """Protocol for strategy mutation generator."""

    def generate_mutation(
        self,
        current_tier: int,
        failing_tests: Dict[str, str],
        cycle_pattern: CyclePattern,
        active_milestone_id: str,
    ) -> StrategyMutationDirective: ...
