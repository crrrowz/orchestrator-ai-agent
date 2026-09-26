"""Data models and schemas for the Autonomous Benchmark & Verification Engine (P11).

Provides canonical data structures for benchmark task specification, empirical evaluation,
metrics computation (TCR, FCR, RCR, PEI, PER), and suite aggregation.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# 1. Enums & Strong Typing Definitions
# ============================================================================

class BenchmarkSuiteType(str, Enum):
    """Classification of benchmark execution suites."""
    CANONICAL = "CANONICAL"                    # Layer 2: Canonical BM-01 to BM-08 suite
    MOCK_REACT = "MOCK_REACT"                  # Layer 1: Zero-token mock ReAct simulator
    ADVERSARIAL_FUZZING = "ADVERSARIAL_FUZZING"# Layer 3: Security & sandbox fuzzing
    REGRESSION_BASELINE = "REGRESSION_BASELINE"# Layer 0: 435 baseline test regression gate
    CUSTOM = "CUSTOM"                          # Ad-hoc evaluation runs


class BenchmarkTaskTier(str, Enum):
    """Complexity tiers for benchmark tasks."""
    TIER_1_LOW = "TIER_1_LOW"            # 1-2 files, algorithmic edge case / race condition
    TIER_2_MEDIUM = "TIER_2_MEDIUM"      # 3-8 files, modular cache / cross-platform CLI
    TIER_3_HIGH = "TIER_3_HIGH"          # 8-20 files, architecture decoupling / full audit
    TIER_4_CRITICAL = "TIER_4_CRITICAL"  # 50+ files / multi-persona / cycle recovery


class BenchmarkMetricType(str, Enum):
    """Formal taxonomy of empirical evaluation metrics."""
    TCR = "TCR"                          # True Task Completion Rate: |R_verif| / |R_mand|
    FCR = "FCR"                          # False Completion Rate: claimed success with TCR < 1.0
    RCR = "RCR"                          # Requirement Coverage Ratio: verified ACs / total ACs
    PEI = "PEI"                          # Progress Efficiency Index: progress / cost
    PER = "PER"                          # Progress Efficiency Ratio: velocity vector score
    CHI_DELTA = "CHI_DELTA"              # Codebase Health Index Delta: CHI_post - CHI_pre
    COST_EFFICIENCY = "COST_EFFICIENCY"  # Verifications per dollar spent
    STEP_EFFICIENCY = "STEP_EFFICIENCY"  # ACs resolved per turn step


class BenchmarkStatus(str, Enum):
    """Outcome status of benchmark execution."""
    PASSED = "PASSED"                    # All criteria verified, zero regressions, zero stubs
    FAILED = "FAILED"                    # Explicit failure or unfulfilled criteria
    FALSE_COMPLETION = "FALSE_COMPLETION"# Claimed success without meeting ground-truth criteria
    TIMEOUT = "TIMEOUT"                  # Execution exceeded time limit
    ERROR = "ERROR"                      # Unhandled crash or sandbox fault
    SKIPPED = "SKIPPED"                  # Task skipped in execution profile


class BenchmarkDomain(str, Enum):
    """Categorical engineering domain of benchmark task."""
    CONCURRENCY = "CONCURRENCY"
    MODULAR_ARCHITECTURE = "MODULAR_ARCHITECTURE"
    REFACTORING = "REFACTORING"
    SECURITY_AUDIT = "SECURITY_AUDIT"
    AUTONOMOUS_REMEDIATION = "AUTONOMOUS_REMEDIATION"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    CROSS_PLATFORM = "CROSS_PLATFORM"
    CYCLE_RECOVERY = "CYCLE_RECOVERY"


class AgentExitReason(str, Enum):
    """Turn termination classifications."""
    AGENT_YIELDED = "AGENT_YIELDED"
    STEP_LIMIT_EXHAUSTED = "STEP_LIMIT_EXHAUSTED"
    GOVERNOR_INTERRUPT = "GOVERNOR_INTERRUPT"
    TOOL_ERROR_FATAL = "TOOL_ERROR_FATAL"
    TIMEOUT_EXCEEDED = "TIMEOUT_EXCEEDED"
    UNHANDLED_EXCEPTION = "UNHANDLED_EXCEPTION"


# ============================================================================
# 2. Invariant & Requirement Specification Models
# ============================================================================

class InvariantAssertionSpec(BaseModel):
    """Formal invariants that must hold true during and after benchmark execution."""
    require_clean_syntax: bool = Field(
        default=True,
        description="Must pass PreFlightGuard syntax check with zero compile errors",
    )
    anti_stub_check: bool = Field(
        default=True,
        description="Verify zero public stubs (pass, ..., NotImplementedError, # TODO)",
    )
    rbac_enforced: bool = Field(
        default=True,
        description="Verify persona RBAC boundaries strictly respected",
    )
    no_flattery_report: bool = Field(
        default=False,
        description="Audit reports must not give unwarranted high scores (>90/100) to flawed code",
    )
    tarjan_scc_acyclic: bool = Field(
        default=False,
        description="Verify zero circular import components (|SCC| == 0 for |V| > 1)",
    )
    min_test_count: int = Field(
        default=1,
        description="Minimum number of passing unit/integration tests required",
    )
    custom_rules: List[str] = Field(
        default_factory=list,
        description="Additional domain-specific invariant assertion keys",
    )


class BenchmarkRequirementCriterion(BaseModel):
    """Discrete requirement acceptance criterion evaluated against ground truth."""
    criterion_id: str = Field(..., description="Unique criterion identifier, e.g. AC-BM01-01-A")
    description: str = Field(..., description="Human-readable description of criterion")
    is_mandatory: bool = Field(default=True, description="Whether criterion is required for TCR=1.0")
    expected_ast_symbol: Optional[str] = Field(
        default=None,
        description="Expected AST symbol (function or class) that must exist in target files",
    )
    verification_test_file: Optional[str] = Field(
        default=None,
        description="Relative path to test file verifying this criterion",
    )
    verification_test_func: Optional[str] = Field(
        default=None,
        description="Specific test function or pattern inside verification test file",
    )


class BenchmarkTaskSpec(BaseModel):
    """Canonical specification model for a benchmark task."""
    task_id: str = Field(..., description="Canonical task ID: BM-01 through BM-08")
    name: str = Field(..., description="Short descriptive benchmark name")
    tier: BenchmarkTaskTier = Field(..., description="Complexity tier")
    domain: BenchmarkDomain = Field(..., description="Engineering domain")
    description: str = Field(default="", description="Detailed goal and background")
    requirements_spec: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping requirement IDs to specifications",
    )
    acceptance_criteria_keys: List[str] = Field(
        default_factory=list,
        description="List of acceptance criteria keys that must be satisfied",
    )
    expected_artifacts: List[str] = Field(
        default_factory=list,
        description="List of relative file paths that must exist upon task completion",
    )
    target_files: List[str] = Field(
        default_factory=list,
        description="List of primary implementation files modified or inspected",
    )
    max_turns_ceiling: int = Field(default=5, ge=1, description="Turn budget ceiling")
    timeout_seconds: float = Field(default=300.0, gt=0.0, description="Wall-clock timeout in seconds")
    budget_usd_cap: float = Field(default=5.0, gt=0.0, description="Financial expenditure cap in USD")
    invariant_assertions: InvariantAssertionSpec = Field(
        default_factory=InvariantAssertionSpec,
        description="Invariants enforced on workspace and output",
    )
    criteria: List[BenchmarkRequirementCriterion] = Field(
        default_factory=list,
        description="Detailed list of criteria evaluated for TCR and RCR",
    )
    initial_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Initial workspace file fixtures (relative path -> text content)",
    )
    broken_test_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Baseline tests (some may intentionally fail or represent flawed baselines)",
    )
    verifier_test_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Independent ground-truth verifier tests injected during empirical evaluation",
    )
    target_personas: List[str] = Field(
        default_factory=lambda: ["developer", "tester"],
        description="Persona pipeline sequence assigned to execute this task",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary task metadata, domain hints, and seed parameters",
    )


# ============================================================================
# 3. Mock Simulation Script Models
# ============================================================================

class MockTurnStep(BaseModel):
    """Deterministic action-observation step for zero-token ReAct simulation."""
    thought: str = Field(default="", description="Simulated agent reasoning/thought")
    action_type: str = Field(
        default="file_write",
        description="Type of action: file_write, file_read, terminal_exec, yield, stagnate",
    )
    action_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Payload parameters for the action",
    )
    simulated_delay_ms: int = Field(default=0, ge=0, description="Simulated execution latency in ms")
    force_error: Optional[str] = Field(
        default=None,
        description="If set, causes step to simulate an error outcome",
    )


class MockConversationScript(BaseModel):
    """Complete scripted turn sequence for fast zero-token CI testing."""
    scenario_name: str = Field(..., description="Scenario identifier")
    steps: List[MockTurnStep] = Field(default_factory=list, description="Ordered steps to execute")
    max_steps: int = Field(default=10, ge=1, description="Step limit threshold")
    target_exit_reason: str = Field(
        default="AGENT_YIELDED",
        description="Target exit reason: AGENT_YIELDED, STEP_LIMIT_EXHAUSTED, TOOL_ERROR_FATAL",
    )


# ============================================================================
# 4. Evaluation Results & Suite Telemetry Aggregates
# ============================================================================

class BenchmarkEvaluationResult(BaseModel):
    """Empirical evaluation result for a single benchmark task run."""
    task_id: str = Field(..., description="Canonical benchmark task ID")
    status: BenchmarkStatus = Field(..., description="Final benchmark status")
    tcr: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="True Task Completion Rate: verified mandatory requirements / total mandatory",
    )
    fcr: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="False Completion Rate contribution: 1.0 if falsely claimed complete, 0.0 otherwise",
    )
    rcr: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Requirement Coverage Ratio: verified criteria / total criteria",
    )
    passed: bool = Field(..., description="True if TCR == 1.0 and FCR == 0.0 and zero regressions")
    is_false_completion: bool = Field(
        default=False,
        description="Flag indicating pipeline claimed success while TCR < 1.0",
    )
    turns_used: int = Field(default=0, ge=0, description="Number of turns consumed")
    steps_used: int = Field(default=0, ge=0, description="Number of agent tool steps executed")
    tokens_used: int = Field(default=0, ge=0, description="Total LLM tokens consumed")
    cost_usd: float = Field(default=0.0, ge=0.0, description="Total financial spend in USD")
    duration_seconds: float = Field(default=0.0, ge=0.0, description="Total wall-clock duration in seconds")
    pei: float = Field(
        default=0.0,
        description="Progress Efficiency Index: progress points / (cost_usd + 1e-6)",
    )
    per: float = Field(
        default=0.0,
        description="Progress Efficiency Ratio (PER 2.0 velocity vector score)",
    )
    chi_initial: float = Field(default=0.0, ge=0.0, le=100.0, description="Baseline Codebase Health Index")
    chi_final: float = Field(default=0.0, ge=0.0, le=100.0, description="Post-execution Codebase Health Index")
    chi_delta: float = Field(default=0.0, description="Codebase Health Delta: chi_final - chi_initial")
    unverified_criteria: List[str] = Field(
        default_factory=list,
        description="List of criterion IDs that failed verification",
    )
    ast_invariants_satisfied: bool = Field(
        default=True,
        description="Whether AST invariants (syntax, anti-stub, complexity) held true",
    )
    failure_reason: Optional[str] = Field(default=None, description="Diagnostic explanation if failed")
    workspace_hash: str = Field(default="", description="Deterministic SHA-256 composite workspace digest")
    artifact_verification: Dict[str, bool] = Field(
        default_factory=dict,
        description="Map of expected artifact paths to presence/validity boolean",
    )
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of evaluation")


class BenchmarkSuiteSummary(BaseModel):
    """Aggregated quantitative summary across a completed benchmark suite pass."""
    suite_type: BenchmarkSuiteType = Field(..., description="Suite category evaluated")
    total_tasks: int = Field(..., ge=0, description="Total number of tasks in the suite")
    passed_tasks: int = Field(..., ge=0, description="Number of tasks that passed")
    failed_tasks: int = Field(..., ge=0, description="Number of tasks that failed")
    false_completions: int = Field(..., ge=0, description="Number of false completion runs detected")
    tcr_average: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Mean Task Completion Rate across all tasks",
    )
    fcr: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Suite False Completion Rate: false_completions / total_tasks (must be 0.000)",
    )
    rcr_average: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Mean Requirement Coverage Ratio across all criteria",
    )
    total_cost_usd: float = Field(default=0.0, ge=0.0, description="Sum of cost across all tasks")
    total_tokens: int = Field(default=0, ge=0, description="Sum of tokens across all tasks")
    total_steps: int = Field(default=0, ge=0, description="Sum of tool steps across all tasks")
    total_duration_seconds: float = Field(default=0.0, ge=0.0, description="Total execution duration")
    mean_chi_delta: float = Field(default=0.0, description="Average CHI delta across tasks")
    mean_pei: float = Field(default=0.0, description="Average Progress Efficiency Index")
    mean_per: float = Field(default=0.0, description="Average Progress Efficiency Ratio")
    results: List[BenchmarkEvaluationResult] = Field(
        default_factory=list,
        description="Detailed result records for each task",
    )
    all_passed: bool = Field(default=False, description="True if all tasks passed with TCR==1.0")
    zero_fcr_verified: bool = Field(
        default=True,
        description="Strictly verified that FCR is exactly 0.000",
    )
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of summary generation")
