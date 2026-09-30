# Engine Plan 06: Skill Engine

## 1. Objective
Design a first-class, modular Skill Engine for discovering, resolving dependencies, dynamically injecting, and token-compressing specialized capabilities (Python, Rust, React, Git, Docker, Security, Graft, etc.).

## 2. Current Architecture Involved
- `orchestrator/skills/manager.py`
- `orchestrator/skills/registry.py`
- `orchestrator/skills/resolver.py`
- `orchestrator/skills/compressor.py`
- `orchestrator/utils/skill_compressor.py`

## 3. Problem
Skill management is currently tightly bound to local filesystem directories containing `SKILL.md` files and custom text concatenation. It lacks remote repository discovery, versioning, capability manifests, and dynamic runtime skill swapping.

## 4. Proposed Design
Implement `SkillEngine`:
- **Skill Manifest Specification**: Standardized `skill.yaml` / `SKILL.md` schema defining skill identity, version, dependencies, capabilities, prompt templates, and associated tools.
- **Skill Registry & Discovery**: Scans local directories (`.agents/skills/`, `skills/`) and remote registries for installable skills.
- **Dependency Resolver**: Resolves hierarchical skill dependencies (e.g. `fastapi-backend` depends on `clean-python-architecture` and `api-design-guide`).
- **Context & Token Compressor**: Dynamically summarizes or truncates skill documentation based on active agent token budget thresholds.

## 5. Files/Components Affected
- `orchestrator/engines/skills/engine.py`
- `orchestrator/engines/skills/models.py`
- `orchestrator/engines/skills/registry.py`
- `orchestrator/engines/skills/resolver.py`
- `orchestrator/engines/skills/compressor.py`

## 6. Interfaces/Contracts
```python
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.engines.core.engine import IEngine

class SkillManifest(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str
    dependencies: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    tools_required: List[str] = Field(default_factory=list)
    system_prompt_snippet: str
    reference_docs: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

class ISkillEngine(IEngine):
    def discover_skills(self, search_paths: List[str]) -> Dict[str, SkillManifest]: ...
    def resolve_skill_chain(self, skill_names: List[str]) -> List[SkillManifest]: ...
    def build_prompt_context(self, skill_names: List[str], max_tokens: Optional[int] = None) -> str: ...
```

## 7. Data Flow
Agent Engine requests skill chain -> Skill Engine discovers manifests -> Dependency resolver produces topological order -> Compressor prunes content to fit token budget -> Consolidated skill context returned for agent prompt assembly.

## 8. State Transitions
`UNINDEXED -> DISCOVERED -> RESOLVED -> COMPRESSED -> INJECTED`.

## 9. Error Handling
Missing skill dependencies trigger warning logs and fallback to parent or generic skills without crashing agent execution.

## 10. Migration Strategy
Port existing `SkillManager` and `SkillCompressor` logic into `SkillEngine`, retaining backward compatibility with existing `SKILL.md` files.

## 11. Tests
- Skill dependency topological sort tests.
- Token budget compression tests asserting that prompt size stays within limits.
- Dynamic skill discovery across multiple workspace directories tests.

## 12. Acceptance Criteria
- Full backward compatibility with existing 20+ `.agents/skills/` repositories.
- Support for declarative YAML manifests alongside markdown instructions.

## 13. Dependencies
Depends on Core Engine, Memory Engine. Blocks Agent Engine.

## 14. Risks
Token inflation from large skill repositories; mitigated by token-budget-aware progressive compression.

## 15. Rollback Strategy
Fallback to `orchestrator/skills/manager.py`.
