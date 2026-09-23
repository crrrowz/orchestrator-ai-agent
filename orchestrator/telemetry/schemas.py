"""Data schemas for execution telemetry and self-diagnostic reports."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class StepIncident(BaseModel):
    """Specific error or failure incident encountered during a step."""

    step_name: str
    incident_type: str  # "test_failure", "tool_error", "timeout", "circuit_breaker", "budget_exceeded"
    details: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


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
    budget_exhausted: bool = False
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    progress_efficiency_ratio: float = 0.0
    metrics: List[StepMetric] = Field(default_factory=list)
    incidents: List[StepIncident] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

