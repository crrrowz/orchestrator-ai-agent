"""Terminal output styling and formatted status tables."""

import warnings

warnings.warn(
    "Importing from 'orchestrator.utils.output' is deprecated and scheduled for removal in Phase 3. "
    "Please import from 'orchestrator.rendering.output' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from orchestrator.rendering.output import (
    ConsoleOutput,
    console,
    custom_theme,
)

__all__ = ["ConsoleOutput", "console", "custom_theme"]
