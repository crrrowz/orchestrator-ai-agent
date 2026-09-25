"""Skill Compression and Optimization Engine (re-exported from orchestrator.skills)."""

import warnings

warnings.warn(
    "Importing CompactSkillInjector from 'orchestrator.utils.skill_compressor' is deprecated and scheduled for removal in Phase 3. "
    "Please import from 'orchestrator.skills.compressor' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from orchestrator.skills.compressor import CompactSkillInjector

__all__ = ["CompactSkillInjector"]
