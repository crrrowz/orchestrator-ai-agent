"""Data schemas for execution telemetry and self-diagnostic reports."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StepIncident(BaseModel):
    """Specific error or failure incident encountered during a step."""
    step_name: str
    incident_type: str  # "test_failure", "tool_error", "timeout", "circuit_breaker"
    details: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StepMetric(BaseModel):
    """Metrics recorded for a single agent action or pipeline step."""
    agent_role: str
    action_type: str
    iteration: int
    duration_seconds: float
    success: bool
    diff_hash: Optional[str] = None
    diff_size_bytes: int = 0
    error_summary: Optional[str] = None


class DiagnosticReport(BaseModel):
    """Comprehensive diagnostic report generated after every task execution."""
    report_id: str
    task_description: str
    pipeline_mode: str
    start_time: datetime
    end_time: datetime
    total_duration_seconds: float
    total_iterations: int
    completed_successfully: bool
    circuit_breaker_triggered: bool = False
    metrics: List[StepMetric] = Field(default_factory=list)
    incidents: List[StepIncident] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
