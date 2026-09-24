"""Context Budget Manager: Central Token Governance & Dynamic Context Control."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class CallDecision(str, Enum):
    ALLOW = "ALLOW"
    SHRINK = "SHRINK"
    REJECT = "REJECT"


@dataclass
class BudgetEvaluation:
    decision: CallDecision
    allocated_output_tokens: int
    reason: str


class ContextBudgetManager:
    """Central Token & Context Governance engine.

    Enforces dynamic output budgets, payload clamping, and pre-execution call approvals
    to eliminate token wastage, JSON truncations, and unbounded context ballooning.
    """

    ROLE_BASE_BUDGETS = {
        "reviewer": 2048,
        "tester": 2048,
        "developer": 4096,
        "architect": 8192,
        "auditor": 8192,
    }

    COMPLEXITY_BUDGETS = {
        "low": 2048,
        "medium": 4096,
        "high": 8192,
    }

    DEFAULT_MAX_CHARS = 12_000  # ~3,000 tokens safe input ceiling

    @classmethod
    def get_dynamic_output_budget(
        cls,
        role: str,
        complexity: str = "medium",
        hard_ceiling: int = 8192,
    ) -> int:
        """Calculate dynamic output token budget based on role and task complexity.

        Prevents flat 8K allocation on simple operations while guaranteeing sufficient
        headroom for deep architectural audits and multi-file refactoring.
        """
        r = (role or "").strip().lower()
        role_budget = cls.ROLE_BASE_BUDGETS.get(r, 4096)
        comp_budget = cls.COMPLEXITY_BUDGETS.get(complexity.lower(), 4096)

        # Weigh role and complexity: take max needed for the specific operation
        # but clamp strictly to hard ceiling
        calculated = min(max(role_budget, comp_budget), hard_ceiling)
        return max(1024, calculated)

    @classmethod
    def evaluate_call(
        cls,
        estimated_input_tokens: int,
        role: str,
        complexity: str = "medium",
        current_tokens_used: int = 0,
        max_tokens_budget: int = 350_000,
        current_cost_usd: float = 0.0,
        max_budget_usd: float = 0.50,
        hard_ceiling: int = 8192,
    ) -> BudgetEvaluation:
        """Pre-flight evaluation of agent LLM call against token & monetary ceilings."""
        allocated_output = cls.get_dynamic_output_budget(
            role=role, complexity=complexity, hard_ceiling=hard_ceiling
        )

        total_est_call_tokens = estimated_input_tokens + allocated_output

        # Hard monetary budget check
        if max_budget_usd > 0 and current_cost_usd >= max_budget_usd:
            return BudgetEvaluation(
                decision=CallDecision.REJECT,
                allocated_output_tokens=0,
                reason=f"Monetary budget ceiling reached (${current_cost_usd:.4f} >= ${max_budget_usd:.4f}).",
            )

        # Hard token budget check
        projected_total = current_tokens_used + total_est_call_tokens
        if max_tokens_budget > 0 and projected_total > max_tokens_budget:
            # Check if we can shrink output to fit within budget
            remaining_tokens = max(0, max_tokens_budget - current_tokens_used)
            if remaining_tokens < 1024:
                return BudgetEvaluation(
                    decision=CallDecision.REJECT,
                    allocated_output_tokens=0,
                    reason=f"Token budget ceiling reached ({current_tokens_used:,} tokens used, budget {max_tokens_budget:,}).",
                )
            shrunk_output = max(1024, remaining_tokens - estimated_input_tokens)
            return BudgetEvaluation(
                decision=CallDecision.SHRINK,
                allocated_output_tokens=min(shrunk_output, allocated_output),
                reason=f"Token budget near limit. Output clamped from {allocated_output} to {shrunk_output}.",
            )

        # Context window warning: if estimated input exceeds 60,000 tokens, advise shrinking
        if estimated_input_tokens > 60_000:
            return BudgetEvaluation(
                decision=CallDecision.SHRINK,
                allocated_output_tokens=allocated_output,
                reason="Input context exceeds 60,000 tokens; aggressive history compaction required.",
            )

        return BudgetEvaluation(
            decision=CallDecision.ALLOW,
            allocated_output_tokens=allocated_output,
            reason="Call approved within dynamic budget.",
        )

    @classmethod
    def clamp_tool_payload(
        cls,
        payload: str,
        max_chars: Optional[int] = None,
    ) -> Tuple[str, bool]:
        """Enforce dual-constraint payload clamping on tool output strings.

        Ensures tool observations cannot exceed token budgets regardless of file/output length.
        """
        limit = max_chars or cls.DEFAULT_MAX_CHARS
        if not payload or len(payload) <= limit:
            return payload, False

        # Truncate at nearest newline within limit
        cut_point = payload.rfind("\n", 0, limit)
        if cut_point < limit // 2:
            cut_point = limit

        truncated = payload[:cut_point]
        omitted_chars = len(payload) - cut_point
        notice = f"\n\n[Governance Notice: Payload truncated ({omitted_chars:,} chars omitted to preserve token budget). Use pagination or targeted queries.]"
        return truncated + notice, True
