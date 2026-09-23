"""Intelligent dynamic skill resolution based on task semantics and intent."""

import re
from typing import Dict, List, Set


class SkillResolver:
    """Automatically resolves relevant skills from task descriptions using semantic keyword heuristics."""

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
    def resolve(
        cls,
        task: str,
        available_skills: List[str],
        base_skills: List[str] | None = None,
    ) -> List[str]:
        """Return an ordered list of matched skills present in available_skills."""
        task_lower = task.lower()
        matched: Set[str] = set()

        for pattern, skills in cls.SKILL_TRIGGERS.items():
            if re.search(pattern, task_lower):
                for s in skills:
                    if s in available_skills:
                        matched.add(s)

        # Include base skills
        if base_skills is None:
            base_skills = ["clean-python-architecture"]
        for bs in base_skills:
            if bs in available_skills:
                matched.add(bs)

        return sorted(matched)
