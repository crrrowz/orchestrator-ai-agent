"""Polyglot Project Adapter package."""

from orchestrator.adapters.base import ProjectAdapter
from orchestrator.adapters.generic_adapter import GenericAdapter
from orchestrator.adapters.node_adapter import NodeAdapter
from orchestrator.adapters.python_adapter import PythonAdapter
from orchestrator.adapters.registry import detect_adapter, get_available_adapters

__all__ = [
    "ProjectAdapter",
    "PythonAdapter",
    "NodeAdapter",
    "GenericAdapter",
    "detect_adapter",
    "get_available_adapters",
]
