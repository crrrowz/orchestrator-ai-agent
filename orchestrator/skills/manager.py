"""Skill lifecycle manager for discovering, compressing, and provisioning skills."""

from pathlib import Path
from typing import Dict, List, Optional
from openhands.sdk import AgentContext
from openhands.sdk.skills import Skill, load_project_skills

from orchestrator.core.constants import ORCHESTRATOR_ROOT
from orchestrator.skills.compressor import CompactSkillInjector
from orchestrator.skills.registry import SkillRegistry


class SkillManager:
    """Discovers, validates, and provisions skills to agents."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = (project_root or ORCHESTRATOR_ROOT).resolve()
        self._skills_cache: Dict[str, Skill] = {}
        self.registry = SkillRegistry()
        self.refresh()

    def refresh(self) -> None:
        """Scan project directory and cache all discoverable skills."""
        discovered = load_project_skills(self.project_root)
        self._skills_cache = {s.name: s for s in discovered}
        self.registry = SkillRegistry(discovered)

    @property
    def available_skills(self) -> List[str]:
        return list(self._skills_cache.keys())

    def get_skill(self, name: str) -> Optional[Skill]:
        """Fetch a validated skill by name."""
        return self._skills_cache.get(name)

    def get_skills_for_role(self, role_skill_names: list[str]) -> list[Skill]:
        """Resolve a list of skill names to loaded Skill instances."""
        resolved = []
        for name in role_skill_names:
            skill = self.get_skill(name)
            if skill:
                resolved.append(skill)
        return resolved

    def build_agent_context(
        self,
        skill_names: list[str],
        compact: bool = True,
        task_text: str = "",
    ) -> AgentContext:
        """Construct an AgentContext loaded with specified skills (optionally compressed and task-filtered to save tokens)."""
        filtered_names = list(skill_names)
        if task_text:
            text_lower = task_text.lower()
            if (
                "docker" not in text_lower
                and "container" not in text_lower
                and "dockerfile" not in text_lower
            ):
                filtered_names = [
                    n for n in filtered_names if n != "docker-devops-containerization"
                ]
            if (
                "graft" not in text_lower
                and "graph" not in text_lower
                and "dependency" not in text_lower
            ):
                if len(filtered_names) > 2:
                    filtered_names = [
                        n
                        for n in filtered_names
                        if n != "graft-architecture-intelligence"
                    ]

        role_skills = self.get_skills_for_role(filtered_names)
        if compact:
            role_skills = [
                CompactSkillInjector.create_compact_skill(s) for s in role_skills
            ]
        return AgentContext(
            skills=role_skills,
            load_project_skills=False,
            load_user_skills=False,
            load_memory=True,
        )
