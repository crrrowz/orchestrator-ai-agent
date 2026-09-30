"""Verification models, defect schemas, and validation reports."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


class VerificationDefect(BaseModel):
    category: str
    severity: str = "HIGH"
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None


class VerificationReport(BaseModel):
    task_id: str
    status: VerificationStatus
    score: float = 1.0
    passed: bool = True
    defects: List[VerificationDefect] = Field(default_factory=list)
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)
    feedback_for_agent: str = ""
