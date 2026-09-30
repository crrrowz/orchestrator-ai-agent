"""Quantitative evaluation of agent iteration steps and execution velocity."""

from __future__ import annotations

import collections
from typing import List, Sequence
from orchestrator.governance.models import ProgressMetricsSnapshot, StepRecord


class ProgressMetricsCalculator:
    """Computes comprehensive health, velocity, and repetition metrics from step records."""

    @staticmethod
    def calculate(steps: Sequence[StepRecord]) -> ProgressMetricsSnapshot:
        if not steps:
            return ProgressMetricsSnapshot()

        total = len(steps)
        mutation_count = 0
        read_count = 0
        terminal_count = 0
        error_count = 0
        mutated_files = set()
        read_files = set()

        action_signatures: List[str] = []
        consecutive_stagnant = 0
        consecutive_errors = 0
        current_stagnant = 0
        current_errors = 0

        for s in steps:
            sig = f"{s.tool_name}:{s.action_type}:{s.target_path or ''}:{s.command or ''}"
            action_signatures.append(sig)

            if s.is_mutation:
                mutation_count += 1
                if s.target_path:
                    mutated_files.add(s.target_path)
                current_stagnant = 0
            else:
                current_stagnant += 1

            if current_stagnant > consecutive_stagnant:
                consecutive_stagnant = current_stagnant

            if s.is_read:
                read_count += 1
                if s.target_path:
                    read_files.add(s.target_path)

            if s.is_terminal:
                terminal_count += 1

            if s.is_error:
                error_count += 1
                current_errors += 1
                if current_errors > consecutive_errors:
                    consecutive_errors = current_errors
            else:
                current_errors = 0

        # Repetition calculation: frequency of most repeated actions
        counts = collections.Counter(action_signatures)
        max_rep = max(counts.values()) if counts else 1
        repetition_score = round(max_rep / total, 4) if total > 0 else 0.0

        # Action diversity: unique action signatures / total
        diversity = round(len(counts) / total, 4) if total > 0 else 1.0

        mutation_velocity = round(mutation_count / total, 4) if total > 0 else 0.0
        error_rate = round(error_count / total, 4) if total > 0 else 0.0

        return ProgressMetricsSnapshot(
            total_steps=total,
            mutation_steps=mutation_count,
            read_steps=read_count,
            terminal_steps=terminal_count,
            error_steps=error_count,
            unique_files_mutated=len(mutated_files),
            unique_files_read=len(read_files),
            repetition_score=repetition_score,
            action_diversity_score=diversity,
            mutation_velocity=mutation_velocity,
            error_rate=error_rate,
            consecutive_stagnant_steps=consecutive_stagnant,
            consecutive_errors=consecutive_errors,
        )
