"""Skill registry and metadata index for discovered project skills."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from openhands.sdk.skills import Skill


@dataclass
class SkillMetadata:
    """Detailed metadata describing a discovered skill."""

    name: str
    description: str
    source: str
    char_count: int
    is_compacted: bool = False
    tags: List[str] = field(default_factory=list)


class SkillRegistry:
    """Maintains an indexed catalog of available skills with search and query capabilities."""

    def __init__(self, skills: Optional[List[Skill]] = None):
        self._skills: Dict[str, Skill] = {}
        self._metadata: Dict[str, SkillMetadata] = {}
        if skills:
            for s in skills:
                self.register(s)

    def register(self, skill: Skill) -> None:
        """Register a skill into the registry."""
        self._skills[skill.name] = skill
        desc = skill.description or ""
        tags = [w.lower() for w in skill.name.replace("-", " ").split()]
        self._metadata[skill.name] = SkillMetadata(
            name=skill.name,
            description=desc,
            source=str(skill.source) if skill.source else "local",
            char_count=len(skill.content or ""),
            tags=tags,
        )

    def get(self, name: str) -> Optional[Skill]:
        """Fetch a skill by exact name."""
        return self._skills.get(name)

    def get_metadata(self, name: str) -> Optional[SkillMetadata]:
        """Fetch metadata for a skill."""
        return self._metadata.get(name)

    def list_all(self) -> List[SkillMetadata]:
        """Return metadata for all registered skills."""
        return list(self._metadata.values())

    def search(self, query: str) -> List[Skill]:
        """Search skills matching keywords in query."""
        q = query.lower()
        results = []
        for name, meta in self._metadata.items():
            if (
                q in meta.name.lower()
                or q in meta.description.lower()
                or any(q in t for t in meta.tags)
            ):
                results.append(self._skills[name])
        return results
