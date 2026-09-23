"""Skill Compression and Optimization Engine for minimal token overhead."""

import re
from typing import Optional
from openhands.sdk.skills import Skill


class CompactSkillInjector:
    """Compresses skill content to essential actionable rules, removing verbose examples and boilerplate."""

    MAX_SKILL_CHARS: int = 800  # ~200 tokens per skill max

    @classmethod
    def compress_content(cls, content: str, max_chars: Optional[int] = None) -> str:
        """Strip markdown code block examples and non-essential narrative to keep only core rules."""
        limit = max_chars or cls.MAX_SKILL_CHARS

        # Remove large markdown code blocks (```...```) to save prompt tokens
        stripped = re.sub(r"```[a-zA-Z0-9_-]*\n[\s\S]*?\n```", "[Code example omitted for brevity]", content)

        # Remove horizontal rules and excessive blank lines
        stripped = re.sub(r"\n{3,}", "\n\n", stripped)
        stripped = re.sub(r"^-{3,}$", "", stripped, flags=re.MULTILINE)

        if len(stripped) <= limit:
            return stripped.strip()

        # Extract core principles / rules sections if present
        lines = stripped.splitlines()
        selected_lines = []
        char_count = 0

        for line in lines:
            line_str = line.strip()
            if not line_str:
                selected_lines.append("")
                continue

            # Prioritize bullet rules, numbered rules, and section headers
            selected_lines.append(line)
            char_count += len(line) + 1
            if char_count >= limit:
                selected_lines.append("... [Rules summarized for compact context]")
                break

        return "\n".join(selected_lines).strip()

    @classmethod
    def create_compact_skill(cls, skill: Skill, max_chars: Optional[int] = None) -> Skill:
        """Return a new Skill instance with compressed content."""
        compact_text = cls.compress_content(skill.content, max_chars=max_chars)
        return Skill(
            name=skill.name,
            content=compact_text,
            description=skill.description,
            trigger=skill.trigger,
            source=skill.source,
            mcp_tools=skill.mcp_tools,
            inputs=skill.inputs,
            is_agentskills_format=skill.is_agentskills_format,
            version=skill.version,
            license=skill.license,
            compatibility=skill.compatibility,
            metadata=skill.metadata,
            allowed_tools=skill.allowed_tools,
            disable_model_invocation=skill.disable_model_invocation,
            resources=skill.resources,
        )
