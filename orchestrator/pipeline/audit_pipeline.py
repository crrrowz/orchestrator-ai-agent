"""Deep Codebase Audit Pipeline: Static AST + Flake8/Ruff Lint + LLM Auditor Agent."""

import time
from pathlib import Path
from typing import Optional

from openhands.sdk import Conversation
from orchestrator.agents import create_auditor_agent
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.control import (
    DynamicTokenGovernor,
    HumanInterventionChannel,
    PipelineController,
)
from orchestrator.control.human_channel import set_active_channel
from orchestrator.pipeline.audit_report_io import locate_and_normalize_report
from orchestrator.pipeline.base_pipeline import BasePipeline
from orchestrator.telemetry import TelemetryRecorder, get_llm_usage
from orchestrator.utils import (
    ConsoleOutput,
    OrchestratorLiveVisualizer,
    SessionLogStore,
)
from orchestrator.utils.graft_context import GraftContextProvider


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
        ConsoleOutput.agent_step(
            "AUDIT", "Phase 0: Running zero-token static analysis & metrics..."
        )
        metrics = self.collect_codebase_metrics()
        static_report = self.run_static_checks()

        # Step 1: Graft Codebase Context
        ConsoleOutput.agent_step(
            "AUDIT", "Phase 1: Querying codebase architecture graph..."
        )
        graft_map = GraftContextProvider.get_compact_map(self.workspace_path)
        graft_part = (
            f"\n\n[Architecture Map (Graft)]:\n{graft_map}" if graft_map else ""
        )

        # Step 2: LLM Auditor Agent
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
            "STRICT CONSTRAINTS & INSTRUCTIONS:\n"
            "1. Inspect 3-5 critical hotspot files identified above to verify key architecture, boundaries, and duplication.\n"
            "2. Produce an exhaustive, in-depth architectural audit in `docs/AUDIT_REPORT.md` (under `docs/`).\n"
            "   - You may write the report overview using `operation='write'` and append subsequent detailed sections with `operation='append'` if needed.\n"
            "3. Your report MUST follow this rigorous structure:\n"
            "   - # Codebase Architecture & Security Audit Report\n"
            "   - ## 1. Executive Summary & Architecture Health Score\n"
            "   - ## 2. Structural Hotspots & Module Boundaries (Analyze files > 300 LOC, coupling, cohesion)\n"
            "   - ## 3. DRY Violations & Duplicate Logic (Identify exact duplicate functions, e.g. `_run_conv` in pipelines)\n"
            "   - ## 4. Security, Secret Leak & Subprocess Vulnerability Audit\n"
            "   - ## 5. Error Handling, Edge Cases & Failure Recovery Gaps\n"
            "   - ## 6. Actionable Prioritized Remediation Roadmap (Specific code tasks for Developer agent)\n"
            "4. For Section 6, define concrete target file paths and precise planned code changes.\n"
            "5. Once `docs/AUDIT_REPORT.md` is complete, call FinishAction to conclude your turn."
        )

        auditor_conv.send_message(self.human_channel.inject_into_prompt(prompt))
        auditor_governor = DynamicTokenGovernor.compute_iteration_budget(
            role="auditor",
            severity="HIGH",
            affected_files_count=metrics.get("total_files", 10),
            task_text=focus_directive,
            hard_ceiling=getattr(self.config, "max_tokens_budget", 400_000),
        )
        self._run_conv(
            auditor_conv,
            "Auditor",
            max_steps=getattr(self.config, "max_agent_steps", 8),
            max_tokens=auditor_governor.allocation.total_budget,
            task_complexity="high",
            governor=auditor_governor,
        )
        dur = time.perf_counter() - t_start
        u_audit = get_llm_usage(auditor_agent.llm)

        # Step 2: Locate and normalize AUDIT_REPORT.md
        report_file = locate_and_normalize_report(
            self.workspace_path, "AUDIT_REPORT.md"
        )
        if not report_file:
            report_file = self.workspace_path / "docs" / "AUDIT_REPORT.md"
            report_file.parent.mkdir(parents=True, exist_ok=True)

        # Step 3: Fallback report generation if agent did not write the file (e.g. offline/mock)
        if not report_file.exists():
            top_files_md = "\n".join(
                f"- `{f}` ({loc} LOC)" for f, loc in metrics["top_files"]
            )
            if "CLEAN" in static_report:
                rec_text = (
                    "- Workspace static analysis is clean; zero syntax or linter defects detected.\n"
                    "- Review file size hotspots exceeding 300 LOC for decomposition."
                )
            else:
                rec_text = (
                    "- Address any AST syntax failures and static linter warnings listed above.\n"
                    "- Review file size hotspots exceeding 300 LOC for decomposition."
                )

            fallback_content = (
                f"# Codebase Architecture & Security Audit Report\n\n"
                f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                f"**Audit Focus**: {focus_directive}\n\n"
                f"## 1. Executive Summary & Code Metrics\n"
                f"- **Total Files**: {metrics['total_files']}\n"
                f"- **Total Lines of Code**: {metrics['total_loc']}\n"
                f"- **Average File Size**: {metrics['avg_loc']} LOC\n\n"
                f"### Largest Modules\n{top_files_md}\n\n"
                f"## 2. Static Analysis Findings\n"
                f"{static_report}\n\n"
                f"## 3. Architecture Overview\n"
                f"```text\n{graft_map or 'No Graft map available.'}\n```\n\n"
                f"## 4. Key Recommendations\n"
                f"{rec_text}\n"
            )
            report_file.write_text(fallback_content, encoding="utf-8")


        telemetry.record_step(
            "auditor",
            "codebase_audit",
            iteration=1,
            duration_seconds=dur,
            success=True,
            prompt_tokens=u_audit.get("prompt_tokens", 0),
            completion_tokens=u_audit.get("completion_tokens", 0),
            total_tokens=u_audit.get("total_tokens", 0),
            estimated_cost_usd=u_audit.get("accumulated_cost", 0.0)
            or u_audit.get("estimated_cost_usd", 0.0),
        )
        telemetry.finalize(completed_successfully=True)
        log_store.save_to_file()

        ConsoleOutput.success(
            f"Audit completed successfully! Report generated at: {report_file}"
        )
        return {
            "status": "AUDIT_COMPLETED",
            "report_path": str(report_file),
            "metrics": metrics,
            "tokens": u_audit.get("total_tokens", 0),
            "cost_usd": u_audit.get("estimated_cost_usd", 0.0),
        }
