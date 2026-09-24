"""Protocols and interfaces for the Cognitive Sentinel Mesh."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from orchestrator.sentinel.schemas import CognitiveIncident


class ISelfHealingEngine(ABC):
    """Protocol for AST-based and heuristic code auto-patching."""

    @abstractmethod
    def heal_syntax_error(
        self, file_path: Path, raw_code: str, error_message: str
    ) -> Tuple[bool, str, str]:
        """Attempts to fix syntax or indentation errors."""
        pass

    @abstractmethod
    def inject_missing_import(
        self, file_path: Path, raw_code: str, missing_symbol: str
    ) -> Tuple[bool, str, str]:
        """Attempts to resolve and inject a missing standard/project import."""
        pass

    @abstractmethod
    def fix_fuzzy_edit(
        self, original_text: str, target_text: str, replacement_text: str
    ) -> Tuple[bool, str, str]:
        """Performs whitespace/indent-tolerant replacement on code."""
        pass


class ICloudResilienceMesh(ABC):
    """Protocol for multi-tier provider failover, quota tracking, and latency probing."""

    @abstractmethod
    def record_call_success(self, provider: str, latency_ms: float) -> None:
        """Records a successful cloud call."""
        pass

    @abstractmethod
    def record_call_failure(
        self, provider: str, error_text: str
    ) -> Tuple[bool, Optional[str]]:
        """Records a failure; returns (should_failover, next_provider_or_model)."""
        pass

    @abstractmethod
    def get_healthy_provider(self, requested_model: Optional[str] = None) -> str:
        """Returns the healthiest provider/model candidate."""
        pass


class ICognitiveSentinel(ABC):
    """Protocol for the primary Sentinel supervisor."""

    @abstractmethod
    def intercept_file_write(
        self, file_path: Path, content: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Intercepts and verifies code before writing to disk."""
        pass

    @abstractmethod
    def intercept_terminal_command(
        self, command: str, os_name: str = "nt"
    ) -> Tuple[bool, str, str]:
        """Inspects and safely rewrites terminal commands for the target platform."""
        pass

    @abstractmethod
    def diagnose_and_heal(
        self, error: Exception, context: Dict[str, Any]
    ) -> CognitiveIncident:
        """Autonomously diagnoses an error and determines the remedy."""
        pass
