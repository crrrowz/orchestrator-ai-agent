"""Core dependency container interface and implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T")


class IEngine(ABC):
    """Base interface for all 13 ORAGAI engines."""

    engine_name: str

    @abstractmethod
    async def initialize(self, container: "IContainer") -> None:
        """Initialize engine with dependency container."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start engine background services."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop engine and release resources."""
        pass

    @abstractmethod
    async def healthcheck(self) -> Dict[str, Any]:
        """Return engine operational status."""
        pass


class IContainer(ABC):
    """Dependency injection container interface."""

    @abstractmethod
    def register_engine(self, engine: IEngine) -> None:
        pass

    @abstractmethod
    def get_engine(self, engine_type: Type[T]) -> T:
        pass

    @abstractmethod
    def get_engine_by_name(self, name: str) -> Optional[IEngine]:
        pass


class ServiceContainer(IContainer):
    """Lightweight in-memory dependency container."""

    def __init__(self) -> None:
        self._engines: Dict[str, IEngine] = {}
        self._type_map: Dict[Type[Any], IEngine] = {}

    def register_engine(self, engine: IEngine) -> None:
        self._engines[engine.engine_name] = engine
        self._type_map[type(engine)] = engine
        for base in type(engine).__mro__:
            if issubclass(base, IEngine) and base is not IEngine:
                self._type_map[base] = engine

    def get_engine(self, engine_type: Type[T]) -> T:
        if engine_type in self._type_map:
            return self._type_map[engine_type]  # type: ignore
        for engine in self._engines.values():
            if isinstance(engine, engine_type):
                return engine  # type: ignore
        raise KeyError(f"Engine of type {engine_type.__name__} not registered in container.")

    def get_engine_by_name(self, name: str) -> Optional[IEngine]:
        return self._engines.get(name)

    def all_engines(self) -> Dict[str, IEngine]:
        return dict(self._engines)
