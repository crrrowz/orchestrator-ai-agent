"""Evidence & Verification Models for ORAGAI Pure Domain Core.

Classification: Enterprise Architectural Blueprint & Canonical System Standard
Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant: Zero external framework dependencies (stdlib + pydantic only).
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Types of cryptographically verifiable execution evidence."""

    PYTEST_EXECUTION = "PYTEST_EXECUTION"
    AST_PREFLIGHT = "AST_PREFLIGHT"
    LINTER_OUTPUT = "LINTER_OUTPUT"
    SECURITY_AUDIT = "SECURITY_AUDIT"
    DIFF_VERIFICATION = "DIFF_VERIFICATION"
    USER_SIGN_OFF = "USER_SIGN_OFF"


class EvidenceReference(BaseModel):
    """Cryptographically verifiable evidence reference validating requirement satisfaction."""

    id: str = Field(..., description="Unique Evidence ID, e.g., 'EVID-PYTEST-001'")
    evidence_type: EvidenceType
    content_sha256: str = Field(..., description="SHA-256 hash of execution payload/logs")
    exit_code: int = Field(..., description="Process exit code (0 for success)")
    execution_duration_sec: float
    output_summary: str = Field(..., description="Truncated diagnostic output")
    timestamp_utc: str
    verified_by_persona: str = Field(..., description="Persona that executed verification")
    is_valid: bool = Field(..., description="Evaluated validity flag")
