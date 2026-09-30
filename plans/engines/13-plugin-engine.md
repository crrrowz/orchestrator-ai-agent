# Engine Plan 13: Plugin Engine

## 1. Objective
Design an extensible Plugin Engine providing dynamic discovery, validation, dependency resolution, sandboxing, and lifecycle management for third-party Agents, Models, Tools, Skills, Memory Providers, Governance Policies, Verifiers, and UI Components.

## 2. Current Architecture Involved
- `orchestrator/skills/registry.py`
- Static Python module imports throughout `orchestrator/`.

## 3. Problem
Currently, adding a new model provider, tool, verifier, or agent requires directly modifying ORAGAI source code. There is no packaging specification, dynamic plugin loading mechanism, or isolation boundary for external extensions.

## 4. Proposed Design
Implement `PluginEngine`:
- **Plugin Manifest Specification (`plugin.yaml`)**: Declares plugin metadata, entrypoints, exported components, dependencies, and permissions.
- **Dynamic Plugin Loader**: Discovers plugins from filesystem directories (`plugins/`, `~/.oragai/plugins/`) or Python packages.
- **Manifest Validator & Sandbox**: Validates semantic versioning, dependencies, and security boundaries before loading.
- **Component Registry Bridge**: Registers exported components into their respective target engines (e.g. Tools into Tool Engine, Models into Model Engine).

```yaml
# Example plugin.yaml
name: "oragai-docker-tools"
version: "1.2.0"
author: "DevOps Team"
description: "Container management and Docker Compose execution tools"
components:
  - type: "tool"
    name: "docker_compose_up"
    entrypoint: "docker_plugin.tools:DockerComposeUpTool"
  - type: "verifier"
    name: "container_health_verifier"
    entrypoint: "docker_plugin.verifier:ContainerHealthVerifier"
dependencies:
  oragai_core: ">=2.0.0"
permissions:
  - "terminal.execute"
  - "filesystem.read"
```

## 5. Files/Components Affected
- `orchestrator/engines/plugins/engine.py`
- `orchestrator/engines/plugins/manifest.py`
- `orchestrator/engines/plugins/loader.py`
- `orchestrator/engines/plugins/validator.py`
- `orchestrator/engines/plugins/registry.py`

## 6. Interfaces/Contracts
```python
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.engines.core.engine import IEngine

class PluginManifest(BaseModel):
    name: str
    version: str
    description: str
    author: str
    entrypoints: Dict[str, str] = Field(default_factory=dict)
    components: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)

class IPluginEngine(IEngine):
    def scan_directory(self, path: str) -> List[PluginManifest]: ...
    async def load_plugin(self, manifest: PluginManifest) -> bool: ...
    async def unload_plugin(self, plugin_name: str) -> bool: ...
    def get_loaded_plugins(self) -> Dict[str, PluginManifest]: ...
```

## 7. Data Flow
Core startup or user command triggers `PluginEngine.scan_directory()` -> Validates manifest schemas -> Resolves version constraints -> Dynamically imports component classes -> Injects components into respective domain engine registries -> Emits `PLUGIN_LOADED` event.

## 8. State Transitions
`DISCOVERED -> VALIDATED -> LOADING -> ACTIVE -> UNLOADING -> UNLOADED / QUARANTINED`.

## 9. Error Handling
Faulty plugins (syntax errors, missing imports, failed validations) are quarantined with detailed error logs without crashing the host system.

## 10. Migration Strategy
Package internal default tools, skills, and model providers as built-in standard plugins under `orchestrator/plugins/core/`.

## 11. Tests
- Dynamic module loading and unloading tests.
- Version mismatch rejection tests.
- Malformed manifest quarantine tests.

## 12. Acceptance Criteria
- Complete isolation of third-party plugins from core system stability.
- Support for hot-reloading plugins during development.

## 13. Dependencies
Depends on Core Engine, Component Model, Event Engine. Blocks dynamic node registration in Graph Engine and Visual UI.

## 14. Risks
Arbitrary code execution risks during plugin loading; mitigated by AST security scanning and permission manifest enforcement.

## 15. Rollback Strategy
Unload faulty plugin and restore standard builtin component defaults.
