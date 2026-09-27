"""Milestone Dependency Resolver & Cycle Detector.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Section 4 Step 2: Milestone DAG Dependency Resolver with Tarjan's SCC / cycle detection.
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple
from orchestrator.pipeline.milestone_dag import MilestoneParser, SubtaskMilestone


class MilestoneDependencyResolver:
    """Resolves milestone dependencies and detects circular dependency cycles."""

    @staticmethod
    def detect_cycles(milestones: List[SubtaskMilestone]) -> List[List[int]]:
        adj: Dict[int, List[int]] = {m.index: m.dependencies for m in milestones}
        visited: Dict[int, int] = {}
        cycles: List[List[int]] = []

        def dfs(node: int, path: List[int]) -> None:
            visited[node] = 1
            path.append(node)
            for neighbor in adj.get(node, []):
                if neighbor not in adj:
                    continue
                state = visited.get(neighbor, 0)
                if state == 1:
                    idx = path.index(neighbor)
                    cycles.append(list(path[idx:]))
                elif state == 0:
                    dfs(neighbor, path)
            path.pop()
            visited[node] = 2

        for m in milestones:
            if visited.get(m.index, 0) == 0:
                dfs(m.index, [])
        return cycles

    @staticmethod
    def resolve_topological_order(
        milestones: List[SubtaskMilestone],
    ) -> List[SubtaskMilestone]:
        return MilestoneParser.resolve_execution_order(milestones)
