"""Structured Iteration State for multi-agent self-healing loops.

Replaces token-heavy conversation memory accumulation with a compact, structured state (~150 tokens)
passed between iterations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class StructuredIterationState:
    """Compact state payload passed between remediation iterations."""

    iteration: int
    affected_files: List[str] = field(default_factory=list)
    completed_fixes: List[str] = field(default_factory=list)
    remaining_findings: List[str] = field(default_factory=list)
    tests_status: str = "pending"  # "passed" | "failed" | "static_clean"
    appended_files: List[str] = field(default_factory=list)

    def render_prompt_block(self) -> str:
        """Render a compact, token-efficient state directive for the agent."""
        completed_str = (
            "\n".join(f"- [x] {fix}" for fix in self.completed_fixes)
            if self.completed_fixes
            else "(None yet)"
        )
        remaining_str = (
            "\n".join(f"- [ ] {finding}" for finding in self.remaining_findings)
            if self.remaining_findings
            else "(All findings resolved)"
        )
        files_str = (
            ", ".join(f"`{f}`" for f in self.affected_files)
            if self.affected_files
            else "(None)"
        )

        return (
            f"=== ITERATION STATE [Cycle {self.iteration}] ===\n"
            f"- Locked Target File(s): {files_str}\n"
            f"- Test & Syntax State: {self.tests_status}\n"
            f"- Verified Completed Fixes (DO NOT REVERT OR REPEAT):\n{completed_str}\n"
            f"- Active Remaining Findings To Solve:\n{remaining_str}\n"
            f"================================================"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "affected_files": self.affected_files,
            "completed_fixes": self.completed_fixes,
            "remaining_findings": self.remaining_findings,
            "tests_status": self.tests_status,
            "appended_files": self.appended_files,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StructuredIterationState":
        return cls(
            iteration=data.get("iteration", 1),
            affected_files=data.get("affected_files", []),
            completed_fixes=data.get("completed_fixes", []),
            remaining_findings=data.get("remaining_findings", []),
            tests_status=data.get("tests_status", "pending"),
            appended_files=data.get("appended_files", []),
        )
