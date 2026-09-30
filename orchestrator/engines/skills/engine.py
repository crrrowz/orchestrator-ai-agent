"""Modular Skill Engine for discovery, dependency resolution, and prompt injection."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.skills.models import SkillManifest


class SkillEngine(IEngine):
    """Engine responsible for skill packaging, manifest discovery, and prompt synthesis."""

    engine_name: str = "skills"

    def __init__(self) -> None:
        self._skills: Dict[str, SkillManifest] = {}
        self._is_running: bool = False

    async def initialize(self, container: IContainer) -> None:
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    def register_skill(self, manifest: SkillManifest) -> None:
        self._skills[manifest.name] = manifest

    def get_skill(self, name: str) -> Optional[SkillManifest]:
        return self._skills.get(name)

    def resolve_dependencies(self, requested_skills: List[str]) -> List[SkillManifest]:
        resolved: List[SkillManifest] = []
        visited = set()

        def dfs(name: str):
            if name in visited:
                return
            visited.add(name)
            skill = self._skills.get(name)
            if skill:
                for dep in skill.dependencies:
                    dfs(dep)
                resolved.append(skill)

        for req in requested_skills:
            dfs(req)

        return resolved

    def build_skill_prompt(self, requested_skills: List[str], max_tokens: Optional[int] = None) -> str:
        chain = self.resolve_dependencies(requested_skills)
        snippets = []
        for skill in chain:
            if skill.system_prompt_snippet:
                snippets.append(f"### Skill: {skill.name}\n{skill.system_prompt_snippet}")
        return "\n\n".join(snippets)

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "registered_skills_count": len(self._skills),
            "skill_names": list(self._skills.keys()),
        }
