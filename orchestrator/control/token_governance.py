"""Token Governance & Dynamic Phase Budget Allocation.

Implements multi-layer token governance separating:
1. Model Output Limit (max_tokens_per_call: 2K-8K)
2. Agent Call Budget (ContextBudgetManager pre-flight evaluation)
3. Dynamic Iteration Budget & Phase Allocation (Investigation, Implementation, Testing, Reserve)
4. Total Task Budget (global budget and token ceilings)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class TokenPhase(str, Enum):
    INVESTIGATION = "INVESTIGATION"
    IMPLEMENTATION = "IMPLEMENTATION"
    TESTING = "TESTING"
    RESERVE = "RESERVE"


@dataclass
class PhaseBudgetAllocation:
    """Represents the dynamic token breakdown for a single execution iteration."""

    total_budget: int
    investigation_budget: int
    implementation_budget: int
    testing_budget: int
    reserve_budget: int

    investigation_consumed: int = 0
    implementation_consumed: int = 0
    testing_consumed: int = 0
    reserve_consumed: int = 0

    @property
    def total_consumed(self) -> int:
        return (
            self.investigation_consumed
            + self.implementation_consumed
            + self.testing_consumed
            + self.reserve_consumed
        )

    @property
    def remaining_total(self) -> int:
        return max(0, self.total_budget - self.total_consumed)

    @property
    def remaining_investigation(self) -> int:
        return max(0, self.investigation_budget - self.investigation_consumed)

    @property
    def remaining_implementation(self) -> int:
        return max(0, self.implementation_budget - self.implementation_consumed)

    @property
    def remaining_testing(self) -> int:
        return max(0, self.testing_budget - self.testing_consumed)


class DynamicTokenGovernor:
    """Computes and tracks dynamic iteration token budgets and phase allocations.

    Prevents runaway token burns by enforcing investigation circuit breakers
    when an agent consumes its exploration budget without attempting code edits.
    """

    DEFAULT_SAFETY_CEILING = 180_000

    ARCHITECTURAL_KEYWORDS = {
        "refactor",
        "refactoring",
        "collapse",
        "alias",
        "architecture",
        "divergence",
        "unify",
        "unification",
        "migration",
        "redesign",
        "boilerplate",
        "decouple",
    }

    def __init__(self, allocation: PhaseBudgetAllocation, role: str = "developer"):
        self.allocation = allocation
        self.role: str = (role or "developer").lower()
        self.has_performed_edit: bool = False
        self.investigation_exhausted: bool = False

    @classmethod
    def compute_iteration_budget(
        cls,
        role: str = "developer",
        severity: str = "MEDIUM",
        affected_files_count: int = 1,
        task_text: str = "",
        hard_ceiling: int = DEFAULT_SAFETY_CEILING,
    ) -> "DynamicTokenGovernor":
        """Compute task-aware iteration budget and allocate into operational phases."""
        sev = (severity or "MEDIUM").strip().upper()
        text_lower = (task_text or "").lower()
        role_lower = (role or "developer").lower()

        # 1. Base budget by affected file count
        if affected_files_count <= 1:
            base_budget = 40_000
            max_agent_steps = 5
        elif affected_files_count == 2:
            base_budget = 80_000
            max_agent_steps = 7
        else:
            base_budget = 120_000
            max_agent_steps = 8

        # 2. Adjust for severity
        if sev == "CRITICAL":
            base_budget += 30_000
        elif sev == "HIGH":
            base_budget += 20_000
        elif sev == "LOW":
            base_budget = min(base_budget, 40_000)
            max_agent_steps = min(max_agent_steps, 5)

        # 3. Detect architectural complexity keywords
        has_arch_keywords = any(kw in text_lower for kw in cls.ARCHITECTURAL_KEYWORDS)
        if has_arch_keywords:
            base_budget = max(base_budget, 140_000)
            max_agent_steps = max(max_agent_steps, 8)

        # Clamp strictly to safety ceiling and lower bound
        total = min(max(base_budget, 35_000), hard_ceiling)

        # 4. Partition into Phase Allocations
        if "auditor" in role_lower:
            # Auditor's primary role is investigation and generating AUDIT_REPORT.md
            investigation = int(total * 0.70)
            implementation = int(total * 0.20)
            testing = 0
            reserve = total - (investigation + implementation)
        else:
            investigation = int(total * 0.28)
            implementation = int(total * 0.47)
            testing = int(total * 0.15)
            reserve = total - (investigation + implementation + testing)

        alloc = PhaseBudgetAllocation(
            total_budget=total,
            investigation_budget=investigation,
            implementation_budget=implementation,
            testing_budget=testing,
            reserve_budget=reserve,
        )
        governor = cls(alloc, role=role_lower)
        governor.suggested_max_steps = max_agent_steps
        return governor

    @staticmethod
    def classify_action(
        action_type: Optional[str], arguments: Optional[Dict[str, Any]] = None
    ) -> TokenPhase:
        """Classify tool action into an operational phase."""
        if not action_type:
            return TokenPhase.INVESTIGATION

        args = arguments or {}

        if action_type == "WorkspaceFileAction":
            op = str(args.get("operation", "")).lower()
            if op in ("edit", "write", "append"):
                return TokenPhase.IMPLEMENTATION
            return TokenPhase.INVESTIGATION

        if action_type == "WorkspaceTerminalAction":
            cmd = str(args.get("command", "")).lower()
            if "pytest" in cmd or "test" in cmd:
                return TokenPhase.TESTING
            if any(k in cmd for k in ("git diff", "git status", "git log")):
                return TokenPhase.TESTING
            return TokenPhase.INVESTIGATION

        if action_type == "ThinkAction":
            return TokenPhase.INVESTIGATION

        return TokenPhase.INVESTIGATION

    def record_step_tokens(self, phase: TokenPhase, tokens: int) -> None:
        """Record token consumption under the corresponding phase."""
        if tokens <= 0:
            return

        if phase == TokenPhase.INVESTIGATION:
            self.allocation.investigation_consumed += tokens
            if (
                self.allocation.investigation_consumed
                >= self.allocation.investigation_budget
                and not self.has_performed_edit
            ):
                self.investigation_exhausted = True
        elif phase == TokenPhase.IMPLEMENTATION:
            self.has_performed_edit = True
            self.allocation.implementation_consumed += tokens
        elif phase == TokenPhase.TESTING:
            self.allocation.testing_consumed += tokens
        elif phase == TokenPhase.RESERVE:
            self.allocation.reserve_consumed += tokens

    def is_investigation_exhausted(self) -> bool:
        """Indicates whether the agent has exhausted exploration tokens with zero edits."""
        if "auditor" in getattr(self, "role", ""):
            return False
        return (
            not self.has_performed_edit
            and self.allocation.investigation_consumed
            >= self.allocation.investigation_budget
        )
