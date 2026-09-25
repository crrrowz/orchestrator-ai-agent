"""Strategy Mutator for ORAGAI (P8).

Implements the 4-Tier Strategy Mutation Taxonomy:
- Tier 1: Prompt Steering (Anti-oscillation hints, test traces, read-before-edit mandate)
- Tier 2: Target Decomposition (Decomposes blocked milestone into sub-atomic tasks)
- Tier 3: Tool Constriction (Disables bash/terminal execution; forces file patch/read)
- Tier 4: Model Elevation (Routes milestone to high-reasoning frontier models)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from .models import (
    CyclePattern,
    MutationStrategyType,
    StrategyMutationDirective,
)


class StrategyMutator:
    """
    Generates 4-Tier Strategy Mutation Directives:
    Tier 1: Prompt Steering
    Tier 2: Target Decomposition
    Tier 3: Tool Constriction
    Tier 4: Model Elevation
    """

    def generate_mutation(
        self,
        current_tier: int,
        failing_tests: Dict[str, str],
        cycle_pattern: CyclePattern,
        active_milestone_id: str,
        last_ast_diff: Optional[str] = None,
    ) -> StrategyMutationDirective:
        """
        Generate a StrategyMutationDirective according to the specified tier (1..4).
        """
        tier = max(1, min(4, current_tier))

        if tier == 1:
            # Tier 1: Prompt Steering
            hints = [
                "CRITICAL ARCHITECTURAL DIRECTIVE: Autonomous execution has stalled due to repetitive failure.",
                "DO NOT perform cosmetic edits, comments, or docstring modifications.",
                "Perform a strict Read-Before-Write pass on the exact failing module.",
            ]
            if cycle_pattern == CyclePattern.FLIP_FLOP_P2:
                hints.append(
                    "OSCILLATION DETECTED: You are flip-flopping between two conflicting implementations (A -> B -> A). "
                    "Reject prior assumptions and address the underlying structural incompatibility."
                )
            elif cycle_pattern == CyclePattern.PERIODIC_PN:
                hints.append(
                    "PERIODIC CYCLE DETECTED: Multi-step cycle identified. Halt exploratory changes and isolate root cause."
                )

            if last_ast_diff:
                hints.append(f"Recent Structural Diff:\n{last_ast_diff[:400]}")

            for node, trace in list(failing_tests.items())[:2]:
                compact_trace = trace[:300].strip() if trace else "No trace available"
                hints.append(f"Failing Test Target: {node}\nTrace: {compact_trace}")

            return StrategyMutationDirective(
                mutation_type=MutationStrategyType.PROMPT_STEERING,
                tier_level=1,
                prompt_injections=hints,
            )

        elif tier == 2:
            # Tier 2: Target Decomposition
            target_test = list(failing_tests.keys())[0] if failing_tests else "active failure"
            subtasks = [
                f"SUBTASK-1: Isolate minimal reproducer for {target_test}",
                "SUBTASK-2: Refactor single target function without modifying neighboring classes",
                "SUBTASK-3: Run isolated single-node test verification",
            ]
            return StrategyMutationDirective(
                mutation_type=MutationStrategyType.TARGET_DECOMPOSITION,
                tier_level=2,
                decomposed_subtasks=subtasks,
                prompt_injections=[
                    f"MILESTONE {active_milestone_id} DECOMPOSED into 3 micro-subtasks. "
                    "Execute strictly SUBTASK-1 in this turn."
                ],
            )

        elif tier == 3:
            # Tier 3: Tool Constriction
            banned = {"execute_bash", "run_terminal_command", "bash"}
            forced = {"read_file", "write_file", "check_syntax"}
            return StrategyMutationDirective(
                mutation_type=MutationStrategyType.TOOL_CONSTRICTION,
                tier_level=3,
                banned_tools=banned,
                forced_tools=forced,
                prompt_injections=[
                    "TOOL RESTRICTION ACTIVE: Terminal/shell access disabled. "
                    "Inspect file AST directly and apply surgical file patch via workspace tools only."
                ],
            )

        else:
            # Tier 4: Model Elevation
            return StrategyMutationDirective(
                mutation_type=MutationStrategyType.MODEL_ELEVATION,
                tier_level=4,
                elevated_model="frontier-reasoning-tier-1",
                prompt_injections=[
                    "MODEL ELEVATION TRIGGERED: Routing milestone to high-reasoning frontier model. "
                    "Allocating extended reasoning headroom."
                ],
            )
