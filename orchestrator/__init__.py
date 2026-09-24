"""Antigravity Multi-Agent Orchestrator."""

from orchestrator.utils.sdk_patch import apply_sdk_patches

__version__ = "0.1.0"

# Apply resilient patches to OpenHands SDK on initialization
apply_sdk_patches()
