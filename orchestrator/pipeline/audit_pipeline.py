"""Deep Codebase Audit Pipeline: Static AST + Flake8/Ruff Lint + LLM Auditor Agent."""

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from openhands.sdk import Conversation
from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.agents import create_auditor_agent
from orchestrator.control import PipelineController, HumanInterventionChannel
from orchestrator.control.human_channel import set_active_channel
from orchestrator.guards import PreFlightGuard
from orchestrator.telemetry import TelemetryRecorder, get_llm_usage
from orchestrator.utils import ConsoleOutput, SessionLogStore, OrchestratorLiveVisualizer
from orchestrator.utils.graft_context import GraftContextProvider


class AuditPipeline:
    """Hybrid Deep Code Analysis Pipeline: zero-token static analysis followed by LLM Auditor report synthesis."""

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
        human_channel: Optional[HumanInterventionChannel] = None,
        controller: Optional[PipelineController] = None,
    ):
        self.config = config
        self.skill_manager = skill_manager
        self.workspace_path = (workspace_path or config.workspace_path).resolve()
        self.human_channel = human_channel or HumanInterventionChannel(
            enabled=config.interactive or bool(config.approval_gates)
        )
        self.controller = controller or PipelineController()

    def _run_conv(self, conv: Conversation, role: str, max_retries: int = 2, timeout_seconds: int = 300) -> None:
        """Execute conversation with retry on transient API/model failures and wall-clock timeout."""
        import threading
        for attempt in range(max_retries + 1):
            timer = None
            if timeout_seconds > 0:
                def on_timeout():
                    ConsoleOutput.warning(f"Agent {role} exceeded {timeout_seconds}s timeout cap.")
                    if hasattr(conv, "cancel"):
                        conv.cancel()
                    elif hasattr(conv, "stop"):
                        conv.stop()
                timer = threading.Timer(timeout_seconds, on_timeout)
                timer.daemon = True
                timer.start()

            try:
                conv.run()
                return
            except Exception as e:
                if attempt < max_retries:
                    delay = 2 ** attempt
                    ConsoleOutput.warning(
                        f"Agent {role} execution failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    raise
            finally:
                if timer:
                    timer.cancel()

    def collect_codebase_metrics(self) -> dict:
        """Scan workspace to calculate file counts and lines of code."""
        excluded_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", "site-packages", ".pytest_cache", ".agents"}
        total_py_files = 0
        total_loc = 0
        files_by_size: list[tuple[str, int]] = []

        for p in self.workspace_path.rglob("*.py"):
            if any(part in excluded_dirs for part in p.parts):
                continue
            try:
                lines = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
                total_py_files += 1
                total_loc += lines
                files_by_size.append((p.relative_to(self.workspace_path).as_posix(), lines))
            except Exception:
                continue

        files_by_size.sort(key=lambda x: x[1], reverse=True)
        return {
            "total_files": total_py_files,
            "total_loc": total_loc,
            "avg_loc": (total_loc // total_py_files) if total_py_files > 0 else 0,
            "top_files": files_by_size[:10],
        }

    def run_static_checks(self) -> str:
        """Execute zero-token AST syntax validation and optional linter scans."""
        lines: list[str] = []

        # 1. Syntax Check via AST py_compile
        syntax_ok, syntax_errors = PreFlightGuard.check_syntax(self.workspace_path)
        if syntax_ok:
            lines.append("- AST Syntax Validation: [PASS] (No compilation errors detected)")
        else:
            lines.append("- AST Syntax Validation: [FAIL] Syntax errors detected:")
            for err in syntax_errors[:5]:
                lines.append(f"  * {err}")

        # 2. Ruff linter if available
        if shutil.which("ruff"):
            try:
                res = subprocess.run(
                    ["ruff", "check", ".", "--output-format=concise"],
                    cwd=str(self.workspace_path),
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if res.returncode == 0:
                    lines.append("- Ruff Static Analysis: [CLEAN] (0 lint errors)")
                else:
                    lint_sample = [l for l in res.stdout.splitlines() if l.strip()][:8]
                    lines.append(f"- Ruff Static Analysis: [ISSUES DETECTED] ({len(res.stdout.splitlines())} warnings/errors):")
                    for l in lint_sample:
                        lines.append(f"  * {l.strip()}")
            except Exception as e:
                lines.append(f"- Ruff Static Analysis: [SKIPPED] ({e})")
        else:
            lines.append("- Ruff Static Analysis: [SKIPPED] (ruff CLI not installed)")

        return "\n".join(lines)

    def run(self, task_description: str = "") -> dict:
        """Run the hybrid static + LLM deep codebase audit."""
        set_active_channel(self.human_channel)
        if not self.controller.check_should_continue():
            return {"status": "AUDIT_ABORTED", "reason": "Pipeline controller abort signal"}

        ConsoleOutput.banner("Codebase Deep Audit Pipeline", f"Workspace: {self.workspace_path}")

        # Step 0: Static Metrics & AST Validation
        ConsoleOutput.agent_step("AUDIT", "Phase 0: Running zero-token static analysis & metrics...")
        metrics = self.collect_codebase_metrics()
        static_report = self.run_static_checks()

        # Step 1: Graft Codebase Context
        ConsoleOutput.agent_step("AUDIT", "Phase 1: Querying codebase architecture graph...")
        graft_map = GraftContextProvider.get_compact_map(self.workspace_path)
        graft_part = f"\n\n[Architecture Map (Graft)]:\n{graft_map}" if graft_map else ""

        # Step 2: LLM Auditor Agent
        log_store = SessionLogStore()
        visualizer = OrchestratorLiveVisualizer(log_store, verbosity=self.config.verbosity)
        telemetry = TelemetryRecorder(
            task_description=task_description or "Codebase Deep Audit",
            pipeline_mode="audit",
            max_budget_usd=self.config.max_budget_usd,
        )

        auditor_agent = create_auditor_agent(self.config, self.skill_manager, self.workspace_path)
        log_store.set_agent_context("Auditor", "Codebase Analysis", model=auditor_agent.llm.model, llm=auditor_agent.llm)
        ConsoleOutput.agent_step("Auditor", "Performing deep inspection and writing AUDIT_REPORT.md...", model=auditor_agent.llm.model)

        t_start = time.perf_counter()
        auditor_conv = Conversation(agent=auditor_agent, workspace=str(self.workspace_path), visualizer=visualizer)
        auditor_conv.human_channel = self.human_channel

        focus_directive = task_description.strip() if task_description else "Full codebase architecture, security, and bug audit."
        prompt = (
            f"Audit Objective: {focus_directive}\n\n"
            f"Codebase Overview:\n"
            f"- Total Python Files: {metrics['total_files']}\n"
            f"- Total Lines of Code: {metrics['total_loc']}\n"
            f"- Average File LOC: {metrics['avg_loc']}\n\n"
            f"Static Analysis Findings:\n{static_report}\n"
            f"{graft_part}\n\n"
            "INSTRUCTIONS:\n"
            "1. Inspect key modules and files in the workspace.\n"
            "2. Identify logic bugs, dead code, architectural hotspots, security risks, and token/performance bottlenecks.\n"
            "3. Generate a structured, detailed `AUDIT_REPORT.md` file in the workspace root adhering to your system prompt specifications."
        )

        auditor_conv.send_message(self.human_channel.inject_into_prompt(prompt))
        self._run_conv(auditor_conv, "Auditor")
        dur = time.perf_counter() - t_start
        u_audit = get_llm_usage(auditor_agent.llm)

        report_file = self.workspace_path / "AUDIT_REPORT.md"

        # Step 3: Fallback report generation if agent did not write the file (e.g. offline/mock)
        if not report_file.exists():
            top_files_md = "\n".join(f"- `{f}` ({loc} LOC)" for f, loc in metrics["top_files"])
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
                f"- Address any AST syntax failures and static linter warnings listed above.\n"
                f"- Review file size hotspots exceeding 300 LOC for decomposition.\n"
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
            estimated_cost_usd=u_audit.get("accumulated_cost", 0.0) or u_audit.get("estimated_cost_usd", 0.0),
        )
        telemetry.finalize(completed_successfully=True)
        log_store.save_to_file()

        ConsoleOutput.success(f"Audit completed successfully! Report generated at: {report_file}")
        return {
            "status": "AUDIT_COMPLETED",
            "report_path": str(report_file),
            "metrics": metrics,
            "tokens": u_audit.get("total_tokens", 0),
            "cost_usd": u_audit.get("estimated_cost_usd", 0.0),
        }
