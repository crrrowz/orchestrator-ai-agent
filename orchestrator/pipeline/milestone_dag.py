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


class MilestoneParser:
    """Parses PLAN.md into discrete executable milestones to prevent LLM context exhaustion."""

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

            milestones.append(
                SubtaskMilestone(
                    index=idx,
                    title=header,
                    content=combined_content,
                    target_files=cls._extract_file_references(combined_content),
                )
            )
            idx += 1

        return milestones

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
