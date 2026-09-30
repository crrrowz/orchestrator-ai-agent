"""Stagnation and Exploration Churn Detector."""

from __future__ import annotations

import collections
from typing import Sequence, Tuple
from orchestrator.governance.models import StepRecord


class StagnationDetector:
    """Detects when an agent is stagnant, reading without mutating, or cycling."""

    def __init__(
        self,
        max_exploration_turns: int = 7,
        max_repeated_reads: int = 3,
        stagnant_steps_threshold: int = 8,
    ) -> None:
        self.max_exploration_turns = max_exploration_turns
        self.max_repeated_reads = max_repeated_reads
        self.stagnant_steps_threshold = stagnant_steps_threshold

    def check_stagnation(
        self,
        steps: Sequence[StepRecord],
        has_prior_mutations: bool = False,
    ) -> Tuple[bool, str]:
        """Evaluate if the agent is stagnant or churning without progress."""
        if not steps:
            return False, ""

        total_steps = len(steps)

        # 1. Total lack of mutations after exploration threshold
        has_any_mutation = has_prior_mutations or any(s.is_mutation for s in steps)
        if total_steps >= self.max_exploration_turns and not has_any_mutation:
            return True, (
                f"Exploration exhaustion: {total_steps} turns elapsed with 0 code mutations. "
                "Agent is churning across read/inspect operations without modifying code."
            )

        # 2. Trailing non-mutating steps after some mutations
        trailing_non_mutations = 0
        for s in reversed(steps):
            if not s.is_mutation:
                trailing_non_mutations += 1
            else:
                break

        if trailing_non_mutations >= self.stagnant_steps_threshold:
            return True, (
                f"Stagnation: {trailing_non_mutations} consecutive turns without code modifications."
            )

        # 3. Repeated identical file reads
        read_paths = [s.target_path for s in steps if s.is_read and s.target_path]
        if read_paths:
            counts = collections.Counter(read_paths)
            most_read, count = counts.most_common(1)[0]
            if count >= self.max_repeated_reads:
                return True, f"Repetitive inspection loop: file '{most_read}' was read {count} times."

        return False, ""
