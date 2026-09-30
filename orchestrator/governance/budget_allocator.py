"""Task-Aware Initial and Dynamic Budget Allocator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional
from orchestrator.governance.governance_policy import DEFAULT_TASK_PROFILES
from orchestrator.governance.models import TaskBudgetProfile, TaskCategory


class AdaptiveTaskBudgetAllocator:
    """Classifies task domain and calculates tailored initial and extension turn budgets."""

    @staticmethod
    def infer_category(
        task_description: str,
        role: str = "developer",
        mode: Optional[str] = None,
    ) -> TaskCategory:
        t_desc = task_description.lower()
        r_lower = role.lower()
        m_lower = (mode or "").lower()

        if m_lower == "audit" or "audit" in t_desc:
            return TaskCategory.AUDIT
        if m_lower == "docs" or "document" in t_desc or "readme" in t_desc:
            return TaskCategory.DOCUMENTATION
        if r_lower == "architect" or any(k in t_desc for k in ("architect", "system design")):
            return TaskCategory.ARCHITECTURE
        if r_lower == "reviewer" or "review" in t_desc:
            return TaskCategory.REVIEW
        if any(k in t_desc for k in ("fix", "bug", "repair", "exception", "error", "patch")):
            return TaskCategory.DEBUGGING
        if any(k in t_desc for k in ("security", "vulnerability", "cve")):
            return TaskCategory.SECURITY
        if any(k in t_desc for k in ("refactor", "clean code", "restructure")):
            return TaskCategory.REFACTORING
        if any(k in t_desc for k in ("test", "pytest", "coverage")) and not any(k in t_desc for k in ("build", "implement", "create")):
            return TaskCategory.TESTING
        if any(k in t_desc for k in ("generate", "scaffold")):
            return TaskCategory.CODE_GENERATION

        return TaskCategory.IMPLEMENTATION

    @classmethod
    def get_profile(
        cls,
        task_description: str,
        role: str = "developer",
        mode: Optional[str] = None,
    ) -> TaskBudgetProfile:
        category = cls.infer_category(task_description, role=role, mode=mode)
        return DEFAULT_TASK_PROFILES.get(
            category, DEFAULT_TASK_PROFILES[TaskCategory.IMPLEMENTATION]
        )

    @classmethod
    def calculate_initial_budget(
        cls,
        task_description: str,
        role: str = "developer",
        mode: Optional[str] = None,
        workspace_path: Optional[Path] = None,
        complexity_hint: float = 0.5,
    ) -> int:
        profile = cls.get_profile(task_description, role=role, mode=mode)
        base = profile.initial_turns

        # If complexity is high, scale budget moderately towards ceiling
        scale = max(0.0, min(1.0, complexity_hint))
        scaled_turns = int(base + (profile.max_extension_turns * scale * 0.5))

        return max(profile.min_turns, min(profile.max_total_ceiling_turns, scaled_turns))
