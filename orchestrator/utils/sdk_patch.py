"""Deprecated SDK Patch Module.

DEPRECATION NOTICE (Phase 3):
Direct monkey-patching of openhands.sdk and litellm has been eradicated in Phase 3.
Clean integration is achieved through official ToolDefinition protocols, Pydantic v2 schemas,
and synchronous event streams in orchestrator.engine.openhands_bridge.

This module is neutralized and scheduled for complete removal in Phase 5.
"""

import logging
import warnings
from typing import Any

logger = logging.getLogger(__name__)

warnings.warn(
    "Importing from 'orchestrator.utils.sdk_patch' is deprecated and scheduled for removal. "
    "Clean OpenHands SDK integration is handled by orchestrator.engine.openhands_bridge.",
    DeprecationWarning,
    stacklevel=2,
)


def resilient_parse_tool_call_arguments(raw_arguments: str) -> dict[str, Any]:
    """Deprecated legacy parser maintained temporarily for backward compatibility."""
    import json
    if not raw_arguments:
        return {}
    if isinstance(raw_arguments, dict):
        return raw_arguments
    try:
        parsed = json.loads(raw_arguments, strict=False)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}


def patch_openhands_telemetry() -> None:
    """Neutralized: No-op in Phase 3."""
    pass


def apply_sdk_patches() -> None:
    """Neutralized: Zero monkey-patching in Phase 3."""
    warnings.warn(
        "apply_sdk_patches is deprecated and neutralized in Phase 3. "
        "OpenHands SDK monkey-patching is disabled.",
        DeprecationWarning,
        stacklevel=2,
    )

