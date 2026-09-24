"""Cognitive Sentinel Supervisor orchestrating digital immunity and self-healing SRE mesh."""

import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from orchestrator.core.config import OrchestratorConfig
from orchestrator.core.exceptions import (
    BudgetExhaustedError,
    CircuitBreakerTrippedError,
    CognitiveLoopDetectedError,
    ProviderQuotaExceededError,
)
from orchestrator.core.protocols import (
    CognitiveIncident,
    ICognitiveSentinel,
    IncidentSeverity,
    InterventionAction,
)
from orchestrator.sentinel.ast_guard import ASTGuard
from orchestrator.sentinel.cloud_governor import CloudMeshGovernor
from orchestrator.sentinel.diagnostics_db import SentinelDiagnosticsDB
from orchestrator.sentinel.heuristics import HeuristicsDriftDetector


class CognitiveSentinelSupervisor(ICognitiveSentinel):
    """Central supervisor enforcing static, dynamic, semantic, and cloud immunity."""

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        workspace: Optional[Path] = None,
    ) -> None:
        self.config = config or OrchestratorConfig()
        self.workspace = workspace or self.config.workspace_path

        # Sub-modules
        self.diagnostics_db = SentinelDiagnosticsDB()
        self.ast_guard = ASTGuard(
            disallow_stubs=getattr(self.config, "self_healing_level", "full_autonomous") == "strict"
        )
        self.cloud_governor = CloudMeshGovernor(
            fallback_chain=getattr(self.config, "cloud_fallback_chain", None),
            max_prompt_ceiling=getattr(self.config, "max_tokens_budget", 350_000) // 2,
        )
        self.drift_detector = HeuristicsDriftDetector(
            max_steps_without_edit=4,
            token_burn_threshold=35_000,
        )

    def intercept_ast_mutation(
        self, file_path: Path, new_code: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Audits AST before disk write; returns (is_safe, error_msg, auto_healed_code)."""
        is_safe, msg, healed_code = self.ast_guard.intercept_ast(file_path, new_code)

        if not is_safe:
            incident = CognitiveIncident(
                incident_id=f"INC-AST-{uuid.uuid4().hex[:8]}",
                severity=IncidentSeverity.HIGH,
                origin_module="ast_guard",
                target_role="developer",
                error_signature=msg,
                raw_payload={"file": str(file_path)},
                suggested_action=InterventionAction.AUTO_PATCH_CODE,
                auto_healed=False,
                remedy_description=f"Rejected AST write to {file_path.name} due to syntax defect.",
                timestamp_epoch=time.time(),
            )
            self.diagnostics_db.record_incident(incident)
            return False, msg, None

        if healed_code and healed_code != new_code:
            incident = CognitiveIncident(
                incident_id=f"INC-AST-{uuid.uuid4().hex[:8]}",
                severity=IncidentSeverity.LOW,
                origin_module="ast_guard",
                target_role="developer",
                error_signature="missing_imports_healed",
                raw_payload={"file": str(file_path)},
                suggested_action=InterventionAction.AUTO_PATCH_CODE,
                auto_healed=True,
                remedy_description=msg,
                timestamp_epoch=time.time(),
            )
            self.diagnostics_db.record_incident(incident)
            return True, msg, healed_code

        return True, "", new_code

    def intercept_cloud_call(
        self, provider: str, model: str, prompt_tokens: int
    ) -> Tuple[bool, str, Optional[str]]:
        """Pre-evaluates cloud quota and cost ceilings; returns (can_proceed, reason, fallback_model)."""
        can_proceed, reason, fallback = self.cloud_governor.intercept_cloud_call(
            provider, model, prompt_tokens
        )
        if not can_proceed:
            incident = CognitiveIncident(
                incident_id=f"INC-CLOUD-{uuid.uuid4().hex[:8]}",
                severity=IncidentSeverity.CRITICAL if fallback else IncidentSeverity.FATAL,
                origin_module="cloud_governor",
                target_role="llm_client",
                error_signature=reason,
                raw_payload={"provider": provider, "model": model, "prompt_tokens": prompt_tokens},
                suggested_action=InterventionAction.SWITCH_CLOUD_PROVIDER
                if fallback
                else InterventionAction.THROTTLE_TOKENS,
                auto_healed=fallback is not None,
                remedy_description=f"Routed to fallback model '{fallback}'"
                if fallback
                else "Ceiling exceeded; throttling tokens.",
                timestamp_epoch=time.time(),
            )
            self.diagnostics_db.record_incident(incident)

        return can_proceed, reason, fallback

    def handle_runtime_error(
        self, exc: Exception, context: Dict[str, Any]
    ) -> CognitiveIncident:
        """Autonomously decodes runtime errors and synthesizes immediate self-healing actions."""
        exc_name = type(exc).__name__
        exc_msg = str(exc)

        # Categorize action and severity
        if isinstance(exc, (ProviderQuotaExceededError,)):
            action = InterventionAction.SWITCH_CLOUD_PROVIDER
            severity = IncidentSeverity.CRITICAL
            remedy = "Trip circuit breaker for provider and switch to fallback model."
        elif isinstance(exc, (CircuitBreakerTrippedError,)):
            action = InterventionAction.SWITCH_CLOUD_PROVIDER
            severity = IncidentSeverity.HIGH
            remedy = "Circuit breaker active; failover to next provider tier."
        elif isinstance(exc, (BudgetExhaustedError,)):
            action = InterventionAction.THROTTLE_TOKENS
            severity = IncidentSeverity.CRITICAL
            remedy = "Halt expensive calls and condense conversation context."
        elif isinstance(exc, (CognitiveLoopDetectedError,)):
            action = InterventionAction.MUTATE_PROMPT
            severity = IncidentSeverity.MEDIUM
            remedy = "Inject prompt directive to break out of exploration loop."
        else:
            action = InterventionAction.ESCALATE_TO_HUMAN
            severity = IncidentSeverity.HIGH
            remedy = f"Unexpected exception: {exc_name}. Logged for triage."

        incident = CognitiveIncident(
            incident_id=f"INC-RUN-{uuid.uuid4().hex[:8]}",
            severity=severity,
            origin_module=context.get("module", "pipeline"),
            target_role=context.get("role", "orchestrator"),
            error_signature=f"{exc_name}: {exc_msg}",
            raw_payload=context,
            suggested_action=action,
            auto_healed=False,
            remedy_description=remedy,
            timestamp_epoch=time.time(),
        )
        self.diagnostics_db.record_incident(incident)
        return incident

    def evaluate_investigation_drift(
        self, role: str, steps: int, tokens_burned: int, edits_done: int
    ) -> bool:
        """Detects cognitive loops and triggers proactive prompt redirection."""
        drift_detected, directive = self.drift_detector.evaluate_investigation_drift(
            role, steps, tokens_burned, edits_done
        )
        self.diagnostics_db.record_drift_check(
            role, steps, tokens_burned, edits_done, drift_detected, directive
        )

        if drift_detected:
            incident = CognitiveIncident(
                incident_id=f"INC-DRIFT-{uuid.uuid4().hex[:8]}",
                severity=IncidentSeverity.MEDIUM,
                origin_module="drift_detector",
                target_role=role,
                error_signature="unproductive_exploration_loop",
                raw_payload={"steps": steps, "tokens": tokens_burned, "edits": edits_done},
                suggested_action=InterventionAction.MUTATE_PROMPT,
                auto_healed=True,
                remedy_description=directive,
                timestamp_epoch=time.time(),
            )
            self.diagnostics_db.record_incident(incident)

        return drift_detected

    def get_health_status(self) -> Dict[str, Any]:
        """Aggregate health metrics of the entire Sentinel mesh."""
        db_stats = self.diagnostics_db.get_stats()
        cloud_stats = self.cloud_governor.get_health_status()
        return {
            "sentinel_active": True,
            "incidents": db_stats,
            "cloud_mesh": cloud_stats,
        }
