"""Deep Codebase Audit Pipeline: Static AST + Flake8/Ruff Lint + LLM Auditor Agent."""

import re
import time
from pathlib import Path
from typing import Optional

from openhands.sdk import Conversation
from orchestrator.agents import create_auditor_agent
from orchestrator.analysis.schemas import (
    AuditFinding,
    AuditResult,
    AuditState,
    FindingValidator,
)
from orchestrator.analysis.graft_context import GraftContextProvider
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.control import (
    DynamicTokenGovernor,
    HumanInterventionChannel,
    PipelineController,
)
from orchestrator.control.human_channel import set_active_channel
from orchestrator.pipeline.audit_report_io import locate_and_normalize_report
from orchestrator.pipeline.base_pipeline import BasePipeline
from orchestrator.rendering.output import ConsoleOutput
from orchestrator.telemetry import TelemetryRecorder, get_llm_usage
from orchestrator.ui.session_store import SessionLogStore
from orchestrator.ui.visualizer import OrchestratorLiveVisualizer


class AuditPipeline(BasePipeline):
    """Hybrid Deep Code Analysis Pipeline: zero-token static analysis followed by LLM Auditor report synthesis."""

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
        human_channel: Optional[HumanInterventionChannel] = None,
        controller: Optional[PipelineController] = None,
    ):
        super().__init__(
            config=config,
            skill_manager=skill_manager,
            workspace_path=workspace_path,
            human_channel=human_channel,
            controller=controller,
        )

    def collect_codebase_metrics(self) -> dict:
        """Scan workspace to calculate file counts and lines of code."""
        return self.adapter.collect_codebase_metrics(self.workspace_path)

    def run_static_checks(self) -> str:
        """Execute zero-token syntax validation and static analysis via adapter."""
        lines: list[str] = []
        is_clean, issues = self.adapter.run_static_analysis(self.workspace_path)
        if is_clean:
            lines.append(
                f"- {self.adapter.language_name.capitalize()} Static Analysis: [CLEAN] (0 defects detected)"
            )
        else:
            lines.append(
                f"- {self.adapter.language_name.capitalize()} Static Analysis: [ISSUES DETECTED] ({len(issues)} warnings/errors):"
            )
            for iss in issues[:10]:
                for line in iss.splitlines():
                    lines.append(f"  * {line.strip()}")

        return "\n".join(lines)

    def run(self, task_description: str = "") -> dict:
        """Run the hybrid static + LLM deep codebase audit."""
        set_active_channel(self.human_channel)
        if not self.controller.check_should_continue():
            return {
                "status": "AUDIT_ABORTED",
                "reason": "Pipeline controller abort signal",
            }

        ConsoleOutput.banner(
            "Codebase Deep Audit Pipeline", f"Workspace: {self.workspace_path}"
        )

        # Step 0: Static Metrics & AST Validation
        ConsoleOutput.pipeline_stage(
            "STATIC METRICS & AST VALIDATION",
            1,
            2,
            "Zero-token static analysis & metrics",
        )
        metrics = self.collect_codebase_metrics()
        static_report = self.run_static_checks()

        # Step 1: Graft Codebase Context
        graft_map = GraftContextProvider.get_compact_map(self.workspace_path)
        graft_part = (
            f"\n\n[Architecture Map (Graft)]:\n{graft_map}" if graft_map else ""
        )

        # Step 2: LLM Auditor Agent
        ConsoleOutput.pipeline_stage(
            "ARCHITECTURAL AUDITOR AGENT",
            2,
            2,
            "LLM deep pattern, security & bug audit",
        )
        log_store = SessionLogStore(workspace_path=self.workspace_path)
        visualizer = OrchestratorLiveVisualizer(
            log_store, verbosity=self.config.verbosity
        )
        telemetry = TelemetryRecorder(
            task_description=task_description or "Codebase Deep Audit",
            pipeline_mode="audit",
            max_budget_usd=self.config.max_budget_usd,
        )
        telemetry.reset()

        auditor_agent = create_auditor_agent(
            self.config, self.skill_manager, self.workspace_path
        )
        log_store.set_agent_context(
            "Auditor",
            "Codebase Analysis",
            model=auditor_agent.llm.model,
            llm=auditor_agent.llm,
        )
        ConsoleOutput.agent_step(
            "Auditor",
            "Performing deep inspection and writing docs/AUDIT_REPORT.md...",
            model=auditor_agent.llm.model,
        )

        t_start = time.perf_counter()
        auditor_conv = Conversation(
            agent=auditor_agent,
            workspace=str(self.workspace_path),
            visualizer=visualizer,
        )
        auditor_conv.human_channel = self.human_channel

        focus_directive = (
            task_description.strip()
            if task_description
            else "Full codebase architecture, security, and bug audit."
        )
        prompt = (
            f"Audit Objective: {focus_directive}\n\n"
            f"Codebase Overview:\n"
            f"- Total Python Files: {metrics['total_files']}\n"
            f"- Total Lines of Code: {metrics['total_loc']}\n"
            f"- Average File LOC: {metrics['avg_loc']}\n\n"
            f"Static Analysis Findings:\n{static_report}\n"
            f"{graft_part}\n\n"
            "STRICT CONSTRAINTS & INSTRUCTIONS (MANDATORY 2-PHASE WORKFLOW):\n"
            "PHASE 1 (Inspection - Max 3-4 steps):\n"
            "1. Perform targeted inspection of 2-3 key hotspot files and architecture boundaries. Do NOT run repetitive or unbounded terminal exploration scripts.\n"
            "PHASE 2 (Report Generation - MUST EXECUTE AT STEP 4-5):\n"
            "2. Produce the exhaustive architectural audit in `docs/AUDIT_REPORT.md` (under `docs/`) and write verified structured findings to `docs/audit_findings.json` using `workspace_file` with operation='write'.\n"
            '   - Format for `docs/audit_findings.json`: {"status": "AUDIT_COMPLETED", "findings": [{"id": "AUD-001", "severity": "HIGH", "type": "BUG", "file": "path/to/file.py", "line": 42, "evidence": "code snippet", "problem": "exact issue", "recommended_fix": "exact fix", "actionable": true}]}\n'
            "   - If no actionable code defects are found, write findings as [] and status as 'AUDIT_CLEAN'.\n"
            "3. Your report in `docs/AUDIT_REPORT.md` MUST follow this structure:\n"
            "   - # Codebase Architecture & Security Audit Report\n"
            "   - ## 1. Executive Summary & Architecture Health Score\n"
            "   - ## 2. Structural Hotspots & Module Boundaries\n"
            "   - ## 3. DRY Violations & Duplicate Logic\n"
            "   - ## 4. Security, Secret Leak & Subprocess Vulnerability Audit\n"
            "   - ## 5. Error Handling, Edge Cases & Failure Recovery Gaps\n"
            "   - ## 6. Actionable Prioritized Remediation Roadmap\n"
            "4. Once `docs/AUDIT_REPORT.md` and `docs/audit_findings.json` are written, conclude your turn immediately."
        )

        auditor_conv.send_message(self.human_channel.inject_into_prompt(prompt))
        auditor_budget_ceiling = getattr(self.config, "max_tokens_budget", 350_000)
        auditor_governor = DynamicTokenGovernor.compute_iteration_budget(
            role="auditor",
            severity="HIGH",
            affected_files_count=metrics.get("total_files", 10),
            task_text=focus_directive,
            hard_ceiling=auditor_budget_ceiling,
        )
        step_budget = max(
            getattr(self.config, "max_agent_steps", 12),
            getattr(auditor_governor, "suggested_max_steps", 20),
            20,
        )
        conv_result = self._run_conv(
            auditor_conv,
            "Auditor",
            max_steps=step_budget,
            max_tokens=auditor_governor.allocation.total_budget,
            task_complexity="high",
            governor=auditor_governor,
        )
        dur = time.perf_counter() - t_start
        u_audit = get_llm_usage(auditor_agent.llm)

        # Step 2: Locate or synthesize AuditResult contract and report
        findings_json_file = self.workspace_path / "docs" / "audit_findings.json"
        report_file = locate_and_normalize_report(
            self.workspace_path, "AUDIT_REPORT.md"
        )
        if not report_file:
            report_file = self.workspace_path / "docs" / "AUDIT_REPORT.md"
            report_file.parent.mkdir(parents=True, exist_ok=True)

        is_clean_static, static_issues = self.adapter.run_static_analysis(
            self.workspace_path
        )
        loaded_result = AuditResult.load_json(findings_json_file)

        validated_findings: list[AuditFinding] = []
        if loaded_result and loaded_result.findings:
            for f in loaded_result.findings:
                is_valid, reason = FindingValidator.validate(f, self.workspace_path)
                if is_valid:
                    validated_findings.append(f)
                else:
                    ConsoleOutput.warning(
                        f"[EVIDENCE INTEGRITY] Dropped invalid finding '{f.id}': {reason}"
                    )

        # Fallback parsing: if docs/audit_findings.json has no findings,
        # but docs/AUDIT_REPORT.md exists, extract findings from markdown report
        if not validated_findings and report_file and report_file.exists():
            try:
                report_text = report_file.read_text(encoding="utf-8")
                from orchestrator.pipeline.audit_fix_pipeline import (
                    extract_audit_findings_list,
                )

                extracted_items = extract_audit_findings_list(report_text)
                for idx, item in enumerate(extracted_items, start=1):
                    f_path = ""
                    f_match = re.search(
                        r"(?:Target File:\s*|File:\s*|in\s+`?)([\w\-./\\]+\.(?:py|js|ts|json|toml|md))`?",
                        item.get("content", ""),
                    )
                    if f_match:
                        f_path = f_match.group(1).replace("\\", "/")
                    elif item.get("title") and ":" in item["title"]:
                        cand = item["title"].split(":")[0].strip().replace("\\", "/")
                        if (self.workspace_path / cand).exists():
                            f_path = cand

                    finding = AuditFinding(
                        id=item.get("id") or f"AUD-{idx:03d}",
                        severity=item.get("severity") or "HIGH",
                        type="BUG",
                        file=f_path or "unknown.py",
                        evidence=item.get("content", "")[:200],
                        problem=item.get("title") or item.get("content", "")[:100],
                        recommended_fix="Implement recommended changes specified in report",
                        actionable=True,
                        source="auditor_report",
                    )
                    is_valid, reason = FindingValidator.validate(
                        finding, self.workspace_path
                    )
                    if is_valid:
                        validated_findings.append(finding)
            except Exception as e:
                ConsoleOutput.warning(
                    f"Failed to parse markdown audit report fallback: {e}"
                )

        # Incorporate deterministic static defects if present
        if not is_clean_static and static_issues:
            for idx, iss in enumerate(static_issues, start=1):
                f_match = re.search(r"([\w\-./\\]+\.py)", iss)
                f_target = (
                    f_match.group(1).replace("\\", "/") if f_match else "unknown.py"
                )
                if (self.workspace_path / f_target).exists():
                    validated_findings.append(
                        AuditFinding(
                            id=f"STATIC-{idx:03d}",
                            severity="HIGH",
                            type="BUG",
                            file=f_target,
                            evidence=iss,
                            problem="Deterministic static analysis defect or syntax error",
                            recommended_fix="Correct the syntax or linter error specified in evidence",
                            actionable=True,
                            source="deterministic_linter",
                        )
                    )

        # Check execution status from Conversation runner
        conv_has_error = bool(conv_result and conv_result.error_message)
        conv_tokens_exceeded = bool(conv_result and conv_result.interrupted_by_tokens)
        conv_timeout_exceeded = bool(conv_result and conv_result.interrupted_by_timeout)

        # Determine formal lifecycle state
        if conv_has_error:
            audit_state = AuditState.AUDIT_FAILED
            summary_msg = f"Auditor agent execution failed: {conv_result.error_message}"
            ConsoleOutput.error(f"[AUDIT FAILED] {summary_msg}")
        elif conv_tokens_exceeded:
            audit_state = AuditState.AUDIT_INCOMPLETE
            toks = conv_result.tokens_consumed if conv_result else 0
            summary_msg = (
                f"Auditor exceeded token budget ceiling ({toks:,} tokens) "
                "before completing audit report."
            )
            ConsoleOutput.warning(f"[AUDIT INCOMPLETE] {summary_msg}")
        elif conv_timeout_exceeded:
            audit_state = AuditState.AUDIT_INCOMPLETE
            summary_msg = "Auditor exceeded timeout cap before completing audit report."
            ConsoleOutput.warning(f"[AUDIT INCOMPLETE] {summary_msg}")
        elif validated_findings:
            audit_state = AuditState.AUDIT_COMPLETED
            summary_msg = f"Audit completed: {len(validated_findings)} actionable finding(s) verified."
        elif is_clean_static and conv_result and conv_result.completed:
            audit_state = AuditState.AUDIT_CLEAN
            summary_msg = "Workspace verified clean. Zero actionable defects detected."
        else:
            audit_state = AuditState.AUDIT_INCOMPLETE
            summary_msg = "Auditor agent did not generate complete verified findings."
            ConsoleOutput.warning(f"[AUDIT INCOMPLETE] {summary_msg}")

        final_audit_result = AuditResult(
            status=audit_state,
            summary=summary_msg,
            findings=validated_findings,
            total_files_scanned=metrics["total_files"],
            total_loc=metrics["total_loc"],
            clean_static=is_clean_static,
        )
        final_audit_result.save_json(findings_json_file)

        # Synchronize presentation markdown with verified audit result
        if not report_file.exists() or report_file.stat().st_size < 100:
            report_file.write_text(final_audit_result.to_markdown(), encoding="utf-8")

        telemetry.record_step(
            "auditor",
            "codebase_audit",
            iteration=1,
            duration_seconds=dur,
            success=(
                audit_state
                not in (AuditState.AUDIT_FAILED, AuditState.AUDIT_INCOMPLETE)
            ),
            prompt_tokens=u_audit.get("prompt_tokens", 0),
            completion_tokens=u_audit.get("completion_tokens", 0),
            total_tokens=u_audit.get("total_tokens", 0),
            estimated_cost_usd=u_audit.get("accumulated_cost", 0.0)
            or u_audit.get("estimated_cost_usd", 0.0),
        )
        telemetry.finalize(
            completed_successfully=(
                audit_state
                not in (AuditState.AUDIT_FAILED, AuditState.AUDIT_INCOMPLETE)
            )
        )
        log_store.save_to_file()

        if audit_state in (AuditState.AUDIT_FAILED, AuditState.AUDIT_INCOMPLETE):
            ConsoleOutput.warning(
                f"Audit halted with state [{audit_state.value}]. See report: {report_file}"
            )
        else:
            ConsoleOutput.success(
                f"Audit completed [{audit_state.value}]! Report generated at: {report_file}"
            )
        return {
            "status": "AUDIT_COMPLETED",
            "audit_state": audit_state.value,
            "result": final_audit_result,
            "report_path": str(report_file),
            "findings_json_path": str(findings_json_file),
            "findings_count": len(validated_findings),
            "metrics": metrics,
            "tokens": u_audit.get("total_tokens", 0),
            "cost_usd": u_audit.get("estimated_cost_usd", 0.0),
        }
