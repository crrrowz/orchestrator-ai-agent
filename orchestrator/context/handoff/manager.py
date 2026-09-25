"""Unified Cross-Agent Context Manager and Orchestration Façade.

File Location: orchestrator/context/handoff/manager.py
Architecture Reference: docs/plans/P6_CONTEXT_AND_EVIDENCE_HANDOFF_PLAN.md Sections 3 & 6
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from orchestrator.context.handoff.compactor import DiagnosticTraceCompactor
from orchestrator.context.handoff.freshness import FreshnessValidator
from orchestrator.context.handoff.models import (
    DEFAULT_TOKEN_RESERVE_HEADROOM,
    CrossAgentHandoffPayload,
    DiagnosticTraceSummary,
    FreshnessState,
    HandoffEnvelope,
    HandoffIntegrityError,
    HandoffTypeEnum,
    MissingHandoffArtifactError,
    PersonaViewType,
    WorkspaceDigest,
)
from orchestrator.context.handoff.synthesizer import ContextSynthesizer


class CrossAgentContextManager:
    """Central orchestration façade managing handoff lifecycle, freshness, and synthesis.

    Unifies context assembly, cryptographic envelope sealing, dependency freshness validation,
    diagnostic compaction, and role-tailored view dispatch.
    """

    def __init__(
        self,
        workspace_path: Path,
        max_tokens: int = 32_000,
        reserve_headroom_tokens: int = DEFAULT_TOKEN_RESERVE_HEADROOM,
    ):
        self.workspace_path = Path(workspace_path).resolve()
        self.synthesizer = ContextSynthesizer(
            max_context_tokens=max_tokens,
            reserve_headroom_tokens=reserve_headroom_tokens,
        )
        self.compactor = DiagnosticTraceCompactor
        self.freshness = FreshnessValidator
        self._envelopes: Dict[str, HandoffEnvelope] = {}
        self.latest_digest: WorkspaceDigest = self.freshness.create_workspace_digest(self.workspace_path)

    def refresh_workspace_digest(self) -> WorkspaceDigest:
        """Recompute and cache the workspace composite cryptographic digest."""
        self.latest_digest = self.freshness.create_workspace_digest(self.workspace_path)
        return self.latest_digest

    # ========================================================================
    # HANDOFF LIFECYCLE & ENVELOPE RECORDING
    # ========================================================================

    def record_handoff(
        self,
        envelope: HandoffEnvelope,
        verify: bool = True,
    ) -> HandoffEnvelope:
        """Seal and persist a cross-agent handoff envelope bound to current workspace state."""
        self.refresh_workspace_digest()
        sealed = envelope.seal(self.latest_digest.composite_sha256)
        if verify and not sealed.verify_integrity():
            raise HandoffIntegrityError(
                f"Cryptographic sealing failed for envelope `{sealed.envelope_id}`. Digest mismatch."
            )
        self._envelopes[sealed.envelope_id] = sealed
        return sealed

    def record_payload(
        self,
        payload: CrossAgentHandoffPayload,
    ) -> HandoffEnvelope:
        """Convert a CrossAgentHandoffPayload into an envelope, seal, and record it."""
        self.refresh_workspace_digest()
        payload.seal(self.latest_digest.composite_sha256)
        envelope = HandoffEnvelope.from_payload(payload, workspace_sha256=self.latest_digest.composite_sha256)
        return self.record_handoff(envelope)

    def get_envelope(self, envelope_id: str) -> Optional[HandoffEnvelope]:
        """Retrieve an envelope by its unique UUID."""
        return self._envelopes.get(envelope_id)

    def get_latest_envelope(self, handoff_type: HandoffTypeEnum) -> Optional[HandoffEnvelope]:
        """Retrieve most recent sealed envelope matching the specified handoff type."""
        matching = [e for e in self._envelopes.values() if e.handoff_type == handoff_type]
        if not matching:
            return None
        matching.sort(key=lambda e: e.created_at_utc, reverse=True)
        return matching[0]

    def validate_required_handoff(
        self,
        handoff_type: HandoffTypeEnum,
        milestone_id: str = "",
    ) -> HandoffEnvelope:
        """Enforces presence and integrity of upstream handoff artifact.

        Eliminates unguided raw fallbacks: if an upstream artifact is missing or corrupted,
        halts with MissingHandoffArtifactError.
        """
        matching = [
            e for e in self._envelopes.values()
            if e.handoff_type == handoff_type
            and (not milestone_id or e.milestone_id == milestone_id)
        ]
        if not matching:
            raise MissingHandoffArtifactError(
                f"Mandatory upstream handoff `{handoff_type.value}` "
                f"{f'for milestone `{milestone_id}` ' if milestone_id else ''}is absent. "
                f"Falling back to unguided raw tasks is prohibited by P6 invariant."
            )
        matching.sort(key=lambda e: e.created_at_utc, reverse=True)
        latest = matching[0]
        if not latest.verify_integrity():
            raise HandoffIntegrityError(
                f"Upstream handoff `{latest.envelope_id}` has been tampered with or corrupted."
            )
        return latest

    # ========================================================================
    # FRESHNESS & EVIDENCE VALIDATION
    # ========================================================================

    def evaluate_evidence_freshness(
        self,
        evidence_workspace_sha256: str,
        target_files: List[str],
        dependency_map: Optional[Dict[str, List[str]]] = None,
    ) -> Tuple[FreshnessState, str]:
        """Check if an evidence artifact remains valid against current workspace state."""
        self.refresh_workspace_digest()
        return self.freshness.evaluate_evidence_freshness(
            evidence_workspace_sha256=evidence_workspace_sha256,
            current_workspace_digest=self.latest_digest,
            target_files=target_files,
            dependency_map=dependency_map,
        )

    # ========================================================================
    # DIAGNOSTIC COMPACTION
    # ========================================================================

    def compact_test_output(
        self,
        stdout: str,
        stderr: str = "",
        max_traces: int = 5,
        exit_code: int = 1,
    ) -> DiagnosticTraceSummary:
        """Compact raw test output into distilled actionable failure traces."""
        return self.compactor.compact_pytest_output(
            stdout=stdout,
            stderr=stderr,
            max_traces=max_traces,
            exit_code=exit_code,
        )

    # ========================================================================
    # PERSONA PROMPT VIEW COMPOSITION
    # ========================================================================

    def build_architect_prompt(
        self,
        task_description: str,
        acceptance_criteria: List[str],
        architecture_skeleton: str = "",
        public_api_contracts: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Synthesize prompt for Architect persona."""
        return self.synthesizer.build_architect_view(
            task_description=task_description,
            acceptance_criteria=acceptance_criteria,
            architecture_skeleton=architecture_skeleton,
            public_api_contracts=public_api_contracts,
        )

    def build_developer_prompt(
        self,
        milestone_id: str,
        requirements_md: str,
        acceptance_criteria_md: str,
        upstream_architect_envelope: Optional[HandoffEnvelope],
        target_code_map: Dict[str, str],
        target_symbols: Optional[Set[str]] = None,
        red_test_trace: Optional[str] = None,
    ) -> str:
        """Synthesize prompt for Developer persona."""
        return self.synthesizer.build_developer_view(
            milestone_id=milestone_id,
            requirements_md=requirements_md,
            acceptance_criteria_md=acceptance_criteria_md,
            upstream_architect_envelope=upstream_architect_envelope,
            target_code_map=target_code_map,
            target_symbols=target_symbols,
            red_test_trace=red_test_trace,
        )

    def build_tester_prompt(
        self,
        milestone_id: str,
        acceptance_criteria_md: str,
        developer_diff_md: str,
        modified_files: List[str],
        preflight_status_md: str = "PreFlight Status: CLEAN",
        boundary_hazards: Optional[List[str]] = None,
    ) -> str:
        """Synthesize prompt for Tester persona."""
        return self.synthesizer.build_tester_view(
            milestone_id=milestone_id,
            acceptance_criteria_md=acceptance_criteria_md,
            developer_diff_md=developer_diff_md,
            modified_files=modified_files,
            preflight_status_md=preflight_status_md,
            boundary_hazards=boundary_hazards,
        )

    def build_reviewer_prompt(
        self,
        milestone_id: str,
        git_diff_md: str,
        acceptance_criteria_md: str,
        test_execution_summary: str,
        preflight_report_md: str = "PreFlight Report: CLEAN",
        architectural_invariants_md: str = "",
    ) -> str:
        """Synthesize prompt for Reviewer persona."""
        return self.synthesizer.build_reviewer_view(
            milestone_id=milestone_id,
            git_diff_md=git_diff_md,
            acceptance_criteria_md=acceptance_criteria_md,
            test_execution_summary=test_execution_summary,
            preflight_report_md=preflight_report_md,
            architectural_invariants_md=architectural_invariants_md,
        )

    def build_remediation_prompt(
        self,
        milestone_id: str,
        defect_directives: List[Dict[str, Any]],
        failing_code_map: Dict[str, str],
        failing_assertion_trace: str = "",
    ) -> str:
        """Synthesize prompt for Remediation Specialist."""
        return self.synthesizer.build_remediation_view(
            milestone_id=milestone_id,
            defect_directives=defect_directives,
            failing_code_map=failing_code_map,
            failing_assertion_trace=failing_assertion_trace,
        )
