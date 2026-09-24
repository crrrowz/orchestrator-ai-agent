"""Milestone and Subtask DAG Parser for iterative, decomposed execution."""

import re
from typing import List
from pydantic import BaseModel, Field


class SubtaskMilestone(BaseModel):
    """Structured milestone extracted from architectural PLAN.md."""

    index: int
    title: str
    content: str
    target_files: List[str] = Field(default_factory=list)
    dependencies: List[int] = Field(default_factory=list)


class MilestoneParser:
    """Parses PLAN.md into discrete executable milestones and resolves dependency graphs."""

    @classmethod
    def resolve_execution_order(
        cls, milestones: List[SubtaskMilestone]
    ) -> List[SubtaskMilestone]:
        """Topologically sort milestones based on declared dependencies with cycle fallback."""
        if len(milestones) <= 1:
            return milestones

        index_map = {m.index: m for m in milestones}
        adj = {
            m.index: [d for d in m.dependencies if d in index_map] for m in milestones
        }
        in_degree = {m.index: 0 for m in milestones}
        for u in adj:
            for v in adj[u]:
                pass  # u depends on v, meaning v must precede u

        # Build graph: v -> u (v must be executed before u)
        graph: dict[int, list[int]] = {m.index: [] for m in milestones}
        for u, deps in adj.items():
            for v in deps:
                graph[v].append(u)
                in_degree[u] += 1

        queue = [idx for idx, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            curr = queue.pop(0)
            order.append(index_map[curr])
            for nxt in graph[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        if len(order) == len(milestones):
            return order

        # Cycle detected in plan dependencies -> fallback safely to natural index order
        return sorted(milestones, key=lambda m: m.index)

    @classmethod
    def parse_plan(cls, plan_text: str) -> List[SubtaskMilestone]:
        """Extract milestone sections from PLAN.md markdown text."""
        if not plan_text or not plan_text.strip():
            return []

        # Find sections matching ## Milestone <N>: or ## Step <N>: or ### Phase <N>:
        pattern = r"(?m)^(#{2,3}\s+(?:Milestone|Step|Phase|Task)\s+\d+[:\s][^\n]*)"
        splits = re.split(pattern, plan_text)

        if len(splits) < 2:
            # Fallback: check for standard ordered headers ## 1. <Title>
            pattern2 = r"(?m)^(#{2,3}\s+\d+\.\s+[^\n]*)"
            splits = re.split(pattern2, plan_text)
            if len(splits) < 2:
                # Monolithic plan (no milestones detected)
                return [
                    SubtaskMilestone(
                        index=1,
                        title="Full Implementation",
                        content=plan_text.strip(),
                        target_files=cls._extract_file_references(plan_text),
                    )
                ]

        milestones: List[SubtaskMilestone] = []
        idx = 1
        for i in range(1, len(splits), 2):
            header = splits[i].strip("# \t\r\n")
            body = splits[i + 1].strip() if i + 1 < len(splits) else ""
            combined_content = f"{header}\n\n{body}".strip()

            deps = []
            dep_match = re.search(
                r"(?:Depends on|Prerequisites|Requires)[:\s]+([^\n]+)",
                combined_content,
                re.IGNORECASE,
            )
            if dep_match:
                found_nums = re.findall(r"\b(\d+)\b", dep_match.group(1))
                deps = [int(n) for n in found_nums if int(n) != idx]

            milestones.append(
                SubtaskMilestone(
                    index=idx,
                    title=header,
                    content=combined_content,
                    target_files=cls._extract_file_references(combined_content),
                    dependencies=deps,
                )
            )
            idx += 1

        return cls.resolve_execution_order(milestones)

    @staticmethod
    def _extract_file_references(text: str) -> List[str]:
        """Extract referenced file paths from markdown text (both quoted and bare paths)."""
        matches = re.findall(
            r"(?:[`'\"]\s*)?([a-zA-Z0-9_\-\.\/]+\.(?:py|json|md|toml|ya?ml|html|css|js|ts))(?:\s*[`'\"])?",
            text,
        )
        cleaned = []
        for m in matches:
            m_clean = m.strip("`'\".,;:()")
            if not m_clean.startswith("http") and (
                "/" in m_clean or m_clean.endswith(".py")
            ):
                if m_clean not in cleaned:
                    cleaned.append(m_clean)
        return cleaned
