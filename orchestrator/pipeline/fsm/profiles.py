"""Lifecycle Profile definitions for GuardedFSMEngine.

Synthesizes previously disjoint pipeline scripts (dev_test_loop.py, full_pipeline.py,
audit_pipeline.py, audit_fix_pipeline.py, documentation_pipeline.py) into unified,
declarative configuration profiles over the Guarded FSM graph.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Set, Union

from orchestrator.pipeline.fsm.states import FSMState


class PipelineMode(str, Enum):
    """Supported pipeline execution modes."""

    DEV_TEST = "dev-test"
    FULL = "full"
    AUDIT = "audit"
    AUDIT_FIX = "audit-fix"
    DOCS = "docs"


@dataclass(frozen=True)
class LifecycleProfile:
    """Configuration profile defining active states and execution rules for a mode."""

    mode: PipelineMode
    allowed_states: Set[FSMState]
    enable_planning: bool = True
    enable_review: bool = True
    enable_git_commit: bool = True
    max_fix_iterations: int = 5
    max_total_iterations: int = 25
    default_agent_turn_limit: int = 8


# Canonical Profiles
PROFILES: Dict[PipelineMode, LifecycleProfile] = {
    PipelineMode.DEV_TEST: LifecycleProfile(
        mode=PipelineMode.DEV_TEST,
        allowed_states={
            FSMState.INIT,
            FSMState.PREFLIGHT,
            FSMState.IMPLEMENTATION,
            FSMState.VERIFICATION,
            FSMState.RESOLUTION,
            FSMState.COMPLETED,
            FSMState.FAILED,
            FSMState.BLOCKED,
            FSMState.ABORTED,
        },
        enable_planning=False,
        enable_review=False,
        enable_git_commit=True,
        max_fix_iterations=3,
        max_total_iterations=15,
        default_agent_turn_limit=8,
    ),
    PipelineMode.FULL: LifecycleProfile(
        mode=PipelineMode.FULL,
        allowed_states={
            FSMState.INIT,
            FSMState.PREFLIGHT,
            FSMState.PLANNING,
            FSMState.IMPLEMENTATION,
            FSMState.VERIFICATION,
            FSMState.RESOLUTION,
            FSMState.REVIEW,
            FSMState.COMPLETED,
            FSMState.FAILED,
            FSMState.BLOCKED,
            FSMState.AMBIGUOUS,
            FSMState.ABORTED,
        },
        enable_planning=True,
        enable_review=True,
        enable_git_commit=True,
        max_fix_iterations=5,
        max_total_iterations=30,
        default_agent_turn_limit=30,
    ),
    PipelineMode.AUDIT: LifecycleProfile(
        mode=PipelineMode.AUDIT,
        allowed_states={
            FSMState.INIT,
            FSMState.PREFLIGHT,
            FSMState.IMPLEMENTATION,  # Auditor Agent execution
            FSMState.VERIFICATION,  # Finding schema validation
            FSMState.COMPLETED,
            FSMState.FAILED,
            FSMState.BLOCKED,
            FSMState.ABORTED,
        },
        enable_planning=False,
        enable_review=False,
        enable_git_commit=False,
        max_fix_iterations=1,
        max_total_iterations=5,
        default_agent_turn_limit=15,
    ),
    PipelineMode.AUDIT_FIX: LifecycleProfile(
        mode=PipelineMode.AUDIT_FIX,
        allowed_states={
            FSMState.INIT,
            FSMState.PREFLIGHT,
            FSMState.PLANNING,  # Finding prioritization DAG
            FSMState.IMPLEMENTATION,  # Fixer agent
            FSMState.VERIFICATION,  # Re-audit & pytest verification
            FSMState.RESOLUTION,
            FSMState.COMPLETED,
            FSMState.FAILED,
            FSMState.BLOCKED,
            FSMState.ABORTED,
        },
        enable_planning=True,
        enable_review=False,
        enable_git_commit=True,
        max_fix_iterations=4,
        max_total_iterations=20,
        default_agent_turn_limit=8,
    ),
    PipelineMode.DOCS: LifecycleProfile(
        mode=PipelineMode.DOCS,
        allowed_states={
            FSMState.INIT,
            FSMState.PREFLIGHT,
            FSMState.IMPLEMENTATION,  # Documentation agent
            FSMState.VERIFICATION,  # Markdown validation
            FSMState.COMPLETED,
            FSMState.FAILED,
            FSMState.BLOCKED,
            FSMState.ABORTED,
        },
        enable_planning=False,
        enable_review=False,
        enable_git_commit=True,
        max_fix_iterations=2,
        max_total_iterations=10,
        default_agent_turn_limit=8,
    ),
}


def get_profile(mode: Union[PipelineMode, str]) -> LifecycleProfile:
    """Retrieve canonical profile for the requested pipeline mode string or enum."""
    if isinstance(mode, PipelineMode):
        return PROFILES.get(mode, PROFILES[PipelineMode.DEV_TEST])
    
    clean_mode = str(mode).strip().lower().replace("_", "-")
    for pm, prof in PROFILES.items():
        if pm.value == clean_mode or pm.name.lower() == clean_mode:
            return prof
    return PROFILES[PipelineMode.DEV_TEST]
