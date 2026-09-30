# Engine Plan 01: Core Engine

## 1. Objective
Design the central Core Engine responsible for runtime bootstrapping, configuration loading, dependency injection, engine registry management, and global shutdown orchestration.

## 2. Current Architecture Involved
- `orchestrator/core/config.py`
- `orchestrator/core/constants.py`
- `orchestrator/core/protocols.py`
- `orchestrator/orchestrator.py`

## 3. Problem
The current initialization logic is coupled inside `orchestrator/orchestrator.py` with hardcoded instantiation of SkillManager, LLMManager, and Dispatcher. There is no central dependency container or standardized engine lifecycle manager.

## 4. Proposed Design
Implement `CoreEngine` as the central runtime container:
- **Engine Registry**: Registers and manages the lifecycle of all 13 engines.
- **Config Management**: Hierarchical configuration loader supporting defaults, `.env`, `oragai.yaml`, CLI arguments, and runtime overrides.
- **Dependency Container**: Provides lightweight, typed dependency injection across engines.
- **Graceful Lifecycle**: Structured startup sequence (`bootstrap -> initialize -> start`) and shutdown sequence (`stop -> cleanup -> teardown`).

## 5. Files/Components Affected
- `orchestrator/engines/core/engine.py`
- `orchestrator/engines/core/registry.py`
- `orchestrator/engines/core/config.py`
- `orchestrator/engines/core/container.py`

## 6. Interfaces/Contracts
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")

class IEngine(ABC):
    engine_name: str

    @abstractmethod
    async def initialize(self, container: "IContainer") -> None: ...

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def healthcheck(self) -> Dict[str, Any]: ...

class IContainer(ABC):
    @abstractmethod
    def register_engine(self, engine: IEngine) -> None: ...

    @abstractmethod
    def get_engine(self, engine_type: Type[T]) -> T: ...
```

## 7. Data Flow
CLI/API invocation -> CoreEngine initializes Container -> Reads Config -> Instantiates Event Engine -> Registers all 13 engines in topological dependency order -> Starts services -> Dispatches requested workflow.

## 8. State Transitions
`UNINITIALIZED -> INITIALIZING -> READY -> RUNNING -> STOPPING -> TERMINATED`.

## 9. Error Handling
Startup validation traps missing configuration, port conflicts, or incompatible engine versions, halting before executing unvalidated workflows.

## 10. Migration Strategy
`Orchestrator` in `orchestrator.py` delegates its `__init__` directly to `CoreEngine.bootstrap()`.

## 11. Tests
- Engine registration and lookup tests.
- Circular dependency detection tests in engine startup.
- Graceful shutdown signal handling (SIGINT/SIGTERM) tests.

## 12. Acceptance Criteria
- Clean dependency injection container with zero global singleton side effects.
- 100% type-safe engine resolution.

## 13. Dependencies
None. Blocks all other engines.

## 14. Risks
Over-engineering DI container; keep implementation minimal (pure Python without heavy third-party DI frameworks).

## 15. Rollback Strategy
Fallback to manual factory instantiation in `orchestrator.py`.
