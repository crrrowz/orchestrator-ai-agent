"""Core constants and filesystem paths for the Orchestrator."""

from pathlib import Path

# Package root and persistent diagnostics / workspace directories
ORCHESTRATOR_ROOT: Path = Path(__file__).resolve().parent.parent.parent
DEFAULT_DIAGNOSTICS_DIR: Path = ORCHESTRATOR_ROOT / "diagnostics"
DEFAULT_WORKSPACE_DIR: Path = ORCHESTRATOR_ROOT / "workspace"
DEFAULT_CONFIG_FILENAME: str = "orchestrator.config.json"

# Sentinel Cognitive Supervision & SRE constants
SENTINEL_CIRCUIT_BREAKER_THRESHOLD: int = 3
MAX_SEMANTIC_HALLUCINATION_STEPS: int = 4
SENTINEL_DIAGNOSTICS_DB_PATH: Path = DEFAULT_DIAGNOSTICS_DIR / "sentinel_mesh.db"
