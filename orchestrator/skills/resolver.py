"""Intelligent dynamic skill resolution based on task semantics and path-based persona discovery."""

from pathlib import Path
import re
from typing import Dict, List, Optional, Set

from orchestrator.core.constants import ORCHESTRATOR_ROOT


class SkillResolver:
    """Automatically discovers and resolves relevant skills from role directory paths and task descriptions."""

    SKILL_TRIGGERS: Dict[str, List[str]] = {
        r"(test|pytest|unittest|coverage|mock|fixture|assertion)": [
            "pytest-rigorous-testing"
        ],
        r"(docker|container|dockerfile|compose|k8s|kubernetes|deploy)": [
            "docker-devops-containerization"
        ],
        r"(security|auth|jwt|oauth|xss|injection|csrf|secret|hash|sanitize)": [
            "security-audit-hardening"
        ],
        r"(api|rest|endpoint|router|fastapi|contract|pydantic|openapi|schema)": [
            "api-design-contract"
        ],
        r"(architect|design|decompos|modul|structure|layer|pipeline)": [
            "architectural-decomposition"
        ],
        r"(debug|fix|error|crash|bug|traceback|exception|remedy)": [
            "systematic-debugging"
        ],
        r"(clean|refactor|solid|pattern|cohesion|decoupling|type)": [
            "clean-python-architecture"
        ],
        r"(review|audit|quality|lint|standard|adherence)": ["code-review-standards"],
        r"(graft|codebase|map|skeleton|dependency|graph|wiring)": [
            "graft-architecture-intelligence"
        ],
    }

    @classmethod
    def get_default_skills_root(cls) -> Path:
        """Return canonical root path for agent skills."""
        return (ORCHESTRATOR_ROOT / ".agents" / "skills").resolve()

    @classmethod
    def discover_role_skills(
        cls, role: str, skills_root: Optional[Path] = None
    ) -> List[str]:
        """Dynamically discover all skill names registered for a role under skills_root / role."""
        root = (skills_root or cls.get_default_skills_root()).resolve()
        role_dir = root / role.lower()
        if not role_dir.is_dir():
            return []

        discovered_names: Set[str] = set()
        for item in sorted(role_dir.iterdir()):
            if item.is_dir():
                # Check for standard SKILL.md, rules.md, or any .md
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    try:
                        import frontmatter

                        fm = frontmatter.load(skill_md)
                        name = fm.metadata.get("name") or item.name
                        discovered_names.add(str(name))
                    except Exception:
                        discovered_names.add(item.name)
                else:
                    discovered_names.add(item.name)
            elif item.suffix.lower() == ".md" and item.stem.lower() != "skill":
                discovered_names.add(item.stem)

        return sorted(discovered_names)

    @classmethod
    def discover_all_skills_by_role(
        cls, skills_root: Optional[Path] = None
    ) -> Dict[str, List[str]]:
        """Dynamically discover all persona roles and their associated skills from directory hierarchy."""
        root = (skills_root or cls.get_default_skills_root()).resolve()
        if not root.is_dir():
            return {}

        role_skills: Dict[str, List[str]] = {}
        for role_dir in sorted(root.iterdir()):
            if role_dir.is_dir():
                role_name = role_dir.name.lower()
                skills = cls.discover_role_skills(role_name, root)
                if skills:
                    role_skills[role_name] = skills
        return role_skills

    @classmethod
    def resolve_for_role(
        cls,
        role: str,
        task: str = "",
        skills_root: Optional[Path] = None,
        available_skills: Optional[List[str]] = None,
    ) -> List[str]:
        """Resolve skills bound to a persona role path, optionally augmented with task semantic matches."""
        role_skills = cls.discover_role_skills(role, skills_root)
        if not task:
            return role_skills

        avail = available_skills or role_skills
        semantic_skills = cls.resolve(
            task, available_skills=avail, base_skills=role_skills
        )
        return semantic_skills

    @classmethod
    def resolve(
        cls,
        task: str,
        available_skills: List[str],
        base_skills: List[str] | None = None,
        role: Optional[str] = None,
        skills_root: Optional[Path] = None,
    ) -> List[str]:
        """Return an ordered list of matched skills present in available_skills."""
        task_lower = task.lower()
        matched: Set[str] = set()

        for pattern, skills in cls.SKILL_TRIGGERS.items():
            if re.search(pattern, task_lower):
                for s in skills:
                    if s in available_skills:
                        matched.add(s)

        # Include role skills if role is supplied
        if role:
            discovered_role_skills = cls.discover_role_skills(role, skills_root)
            for rs in discovered_role_skills:
                if rs in available_skills:
                    matched.add(rs)

        # Include base skills
        if base_skills is None:
            base_skills = ["clean-python-architecture"]
        for bs in base_skills:
            if bs in available_skills:
                matched.add(bs)

        return sorted(matched)

