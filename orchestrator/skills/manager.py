"""Skill lifecycle manager for discovering, compressing, and provisioning skills."""

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union
from openhands.sdk import AgentContext
from openhands.sdk.skills import Skill, load_project_skills

from orchestrator.core.constants import ORCHESTRATOR_ROOT
from orchestrator.skills.compressor import CompactSkillInjector
from orchestrator.skills.registry import SkillRegistry


class SkillManager:
    """Discovers, validates, and provisions skills to agents using path-based persona discovery."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = (project_root or ORCHESTRATOR_ROOT).resolve()
        self._skills_cache: Dict[str, Skill] = {}
        self._role_skills: Dict[str, List[Skill]] = {}
        self.registry = SkillRegistry()
        self.refresh()

    @property
    def skills_root(self) -> Path:
        """Return the root path containing role and skill directories."""
        agents_skills = self.project_root / ".agents" / "skills"
        if agents_skills.exists():
            return agents_skills
        if self.project_root.name == "skills" and self.project_root.is_dir():
            return self.project_root
        return agents_skills

    def refresh(self) -> None:
        """Scan role directories and project root to dynamically load and cache all discoverable skills."""
        self._skills_cache = {}
        self._role_skills = {}
        self.registry = SkillRegistry()

        skills_dir = self.skills_root

        # 1. Path-based discovery by persona role hierarchy (.agents/skills/<role>/<skill_name>/)
        if skills_dir.exists() and skills_dir.is_dir():
            for item in sorted(skills_dir.iterdir()):
                if not item.is_dir():
                    continue

                # Check if item is a role directory containing sub-skills
                sub_skills = [s for s in item.iterdir() if s.is_dir()]
                if sub_skills:
                    role_name = item.name.lower()
                    if role_name not in self._role_skills:
                        self._role_skills[role_name] = []

                    for skill_subdir in sorted(sub_skills):
                        skill = self._load_skill_from_dir(skill_subdir)
                        if skill:
                            self._skills_cache[skill.name] = skill
                            if skill not in self._role_skills[role_name]:
                                self._role_skills[role_name].append(skill)
                            self.registry.register(skill, role=role_name)
                else:
                    # Item is a flat skill directory (.agents/skills/<skill_name>/)
                    skill = self._load_skill_from_dir(item)
                    if skill:
                        self._skills_cache[skill.name] = skill
                        self.registry.register(skill)

        # 2. Merge any top-level or third-party skills discovered by OpenHands SDK
        try:
            discovered = load_project_skills(self.project_root)
            for s in discovered:
                if s.name not in self._skills_cache:
                    self._skills_cache[s.name] = s
                    self.registry.register(s)
        except Exception:
            pass

    def _load_skill_from_dir(self, skill_dir: Path) -> Optional[Skill]:
        """Attempt to load a Skill instance from a skill directory containing SKILL.md or rules.md."""
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            try:
                return Skill.load(skill_md, strict=False)
            except Exception:
                pass

        rules_md = skill_dir / "rules.md"
        if rules_md.exists():
            try:
                content = rules_md.read_text(encoding="utf-8")
                return Skill(
                    name=skill_dir.name,
                    content=content,
                    description=f"{skill_dir.name} skill",
                    source=str(rules_md),
                )
            except Exception:
                pass

        # Check for any .md file in the directory
        for md_file in skill_dir.glob("*.md"):
            try:
                return Skill.load(md_file, strict=False)
            except Exception:
                pass

        return None

    @property
    def available_skills(self) -> List[str]:
        """Return all distinct discovered skill names."""
        return sorted(list(self._skills_cache.keys()))

    @property
    def available_roles(self) -> List[str]:
        """Return all persona roles discovered in skills hierarchy."""
        return sorted(list(self._role_skills.keys()))

    def get_skill(self, name: str) -> Optional[Skill]:
        """Fetch a validated skill by name."""
        return self._skills_cache.get(name)

    def get_skills_for_role(
        self, role_or_skill_names: Union[str, Sequence[str]]
    ) -> List[Skill]:
        """Resolve either a role name (e.g. 'developer') or an explicit list of skill names to loaded Skill instances."""
        if isinstance(role_or_skill_names, str):
            role_key = role_or_skill_names.lower()
            if role_key in self._role_skills:
                return list(self._role_skills[role_key])
            # Single skill name fallback
            single = self.get_skill(role_or_skill_names)
            return [single] if single else []

        resolved = []
        for name in role_or_skill_names:
            skill = self.get_skill(name)
            if skill:
                resolved.append(skill)
        return resolved

    def build_agent_context(
        self,
        skill_names_or_role: Union[str, Sequence[str]],
        compact: bool = True,
        task_text: str = "",
    ) -> AgentContext:
        """Construct an AgentContext loaded with specified skills (optionally compressed and task-filtered to save tokens)."""
        if isinstance(skill_names_or_role, str):
            role_key = skill_names_or_role.lower()
            if role_key in self._role_skills:
                skill_names = [s.name for s in self._role_skills[role_key]]
            else:
                skill_names = [skill_names_or_role]
        else:
            skill_names = list(skill_names_or_role)

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

