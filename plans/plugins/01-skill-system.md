# Plugin Plan 01: Skill System

## 1. Objective
Define the first-class Skill System specification in ORAGAI, enabling skills to be packaged, versioned, discovered, dynamically loaded, compressed, and attached to agents as modular plugins.

## 2. Current Architecture Involved
- `orchestrator/skills/manager.py`
- `orchestrator/skills/registry.py`
- `orchestrator/skills/compressor.py`
- `.agents/skills/`

## 3. Problem
Skills are currently tied to raw markdown files in filesystem folders with loose metadata and no formal manifest, lifecycle hooks, tool associations, or versioning.

## 4. Proposed Design
Standardize the Skill Package format:

### Skill Package Structure
```text
my-skill-package/
├── skill.yaml              # Structured metadata manifest
├── SKILL.md                # Natural language instructions & guidelines
├── tools/                  # Optional specialized tool definitions
│   └── custom_tool.py
├── examples/               # In-context golden demonstration examples
│   └── example_1.md
└── tests/                  # Conformance tests for the skill
    └── test_skill.py
```

### Skill Manifest Specification (`skill.yaml`)
```yaml
name: "fastapi-production-standards"
version: "2.1.0"
author: "Backend Architecture Team"
description: "Production FastAPI patterns with async SQLAlchemy, Pydantic v2, and JWT auth"
dependencies:
  - "clean-python-architecture"
  - "api-design-guide"
capabilities:
  - "fastapi_routing"
  - "dependency_injection"
  - "pydantic_v2_schemas"
tools:
  - "fastapi_route_inspector"
token_budget_hint: 1500
tags:
  - "python"
  - "backend"
  - "api"
```

## 5. Files/Components Affected
- `orchestrator/engines/skills/`
- `orchestrator/plugins/skills/`
- `.agents/skills/*/skill.yaml`

## 6. Interfaces/Contracts
```python
from typing import List, Optional
from pydantic import BaseModel, Field

class SkillPackage(BaseModel):
    manifest: SkillManifest
    instructions_markdown: str
    examples: List[str] = Field(default_factory=list)
    attached_tools: List[str] = Field(default_factory=list)
```

## 7. Data Flow
Skill Engine scans directories -> Reads `skill.yaml` + `SKILL.md` -> Validates dependencies -> Builds compressed instruction prompt -> Attaches referenced tools to agent environment.

## 8. State Transitions
`PACKAGE_DISCOVERED -> MANIFEST_VALIDATED -> DEPENDENCIES_RESOLVED -> READY_FOR_INJECTION`.

## 9. Error Handling
Missing dependencies raise `SkillDependencyResolutionError` with suggested install commands.

## 10. Migration Strategy
Auto-generate `skill.yaml` manifests for all existing 20+ `.agents/skills/` directories during Migration Phase 1.

## 11. Tests
- Manifest validation tests.
- Multi-tier skill dependency resolution tests.
- Skill compressor token budget truncation tests.

## 12. Acceptance Criteria
- Full support for both legacy `SKILL.md` and new `skill.yaml` packages.
- Dynamic skill tool attachment.

## 13. Dependencies
Depends on Core Engine, Tool Engine.

## 14. Risks
Token overhead from rich examples; mitigated by progressive disclosure and compression.

## 15. Rollback Strategy
Fallback to plain text file reading via `orchestrator/skills/manager.py`.
