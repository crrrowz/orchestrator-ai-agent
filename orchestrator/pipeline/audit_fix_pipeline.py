"""Autonomous Codebase Audit & Fix Pipeline: Scan -> Remediate -> Verify Loop without Git."""

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openhands.sdk import Conversation
from orchestrator.config import (
    OrchestratorConfig,
    SkillManager,
)
from orchestrator.agents import (
    create_developer_agent,
)
from orchestrator.control import (
    DynamicTokenGovernor,
    HumanInterventionChannel,
    PipelineController,
)
from orchestrator.control.human_channel import set_active_channel

from orchestrator.pipeline.audit_report_io import (
    locate_and_normalize_report,
    read_report,
)
from orchestrator.pipeline.base_pipeline import BasePipeline


from orchestrator.pipeline.iteration_state import StructuredIterationState
from orchestrator.telemetry import TelemetryRecorder, get_llm_usage
from orchestrator.tools import WorkspaceTerminalAction, execute_terminal_action
from orchestrator.tools.workspace_tools import reset_append_counts
from orchestrator.utils import (
    ConsoleOutput,
    GraftContextProvider,
    OrchestratorLiveVisualizer,
    SessionLogStore,
)


def extract_audit_findings_list(report_content: str) -> List[Dict[str, Any]]:
    """Extract discrete actionable audit findings, sorted by severity (CRITICAL, HIGH, MEDIUM, LOW)."""
    if not report_content:
        return []

    severity_weights = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings: List[Dict[str, Any]] = []

    # Pattern: ### X.Y [SEVERITY] Title ... up to next ### or ##
    pattern = r"###\s*(\d+\.\d+)\s*\[(CRITICAL|HIGH|MEDIUM|LOW)\]\s*([^\n]+)([\s\S]*?)(?=\n###|\n##|\Z)"
    for m in re.finditer(pattern, report_content, re.IGNORECASE):
        num, sev, title, body = m.groups()
        sev_upper = sev.upper()
        clean_title = title.strip()
        # Ignore sections indicating invariants or things NOT to break
        if any(
            skip in clean_title.lower() or skip in body[:150].lower()
            for skip in ["invariant", "do not break", "keep", "health score"]
        ):
            continue

        finding_text = f"### {num} [{sev_upper}] {clean_title}\n{body.strip()}"
        findings.append(
            {
                "id": num,
                "severity": sev_upper,
                "weight": severity_weights.get(sev_upper, 99),
                "title": clean_title,
                "content": finding_text,
            }
        )

    if not findings:
        fallback_text = ""
        # Priority 1: Section 6
        m6 = re.search(
            r"(##\s*6\.\s*Actionable Prioritized Remediation Roadmap[\s\S]*?)(?=\n##|\Z)",
            report_content,
            re.IGNORECASE,
        )
        if m6 and m6.group(1).strip():
            fallback_text = m6.group(1).strip()
        else:
            # Priority 2: Section 4 Key Recommendations
            m4 = re.search(
                r"(##\s*(?:4\.\s*)?Key Recommendations[\s\S]*?)(?=\n##|\Z)",
                report_content,
                re.IGNORECASE,
            )
            if m4 and m4.group(1).strip():
                fallback_text = m4.group(1).strip()
            else:
                m_rec = re.search(
                    r"(^##\s+.*(?:Recommendation|Actionable Tasks).*[\s\S]*?)(?=\n##|\Z)",
                    report_content,
                    re.IGNORECASE | re.MULTILINE,
                )
                if m_rec and m_rec.group(1).strip():
                    fallback_text = m_rec.group(1).strip()

        if fallback_text:
            clean_static = (
                "[clean]" in report_content.lower()
                or "0 defects detected" in report_content.lower()
            )
            generic_phrases = [
                "address any ast syntax failures and static linter warnings listed above",
                "address any ast syntax failures",
            ]
            is_generic_advice = any(
                gp in fallback_text.lower() for gp in generic_phrases
            )
            if clean_static and is_generic_advice and "###" not in fallback_text:
                pass
            else:
                findings.append(
                    {
                        "id": "1.0",
                        "severity": "HIGH",
                        "weight": 1,
                        "title": "Actionable Audit Recommendations",
                        "content": fallback_text,
                    }
                )

    findings.sort(key=lambda x: (x["weight"], x["id"]))
    return findings


def extract_actionable_recommendations(report_content: str) -> str:
    """Extract actionable recommendations sections, filtering out structural invariants."""
    if not report_content:
        return ""

    findings = extract_audit_findings_list(report_content)
    if findings:
        return "\n\n".join(f["content"] for f in findings[:3])

    # Fallback Priority 1: Section 6 "Actionable Prioritized Remediation Roadmap"
    match_sec6 = re.search(
        r"(##\s*6\.\s*Actionable Prioritized Remediation Roadmap[\s\S]*?)(?=\n##|\Z)",
        report_content,
        re.IGNORECASE,
    )
    if match_sec6 and match_sec6.group(1).strip():
        return match_sec6.group(1).strip()

    # Fallback Priority 2: Section 4 "Key Recommendations"
    match_sec4 = re.search(
        r"(##\s*(?:4\.\s*)?Key Recommendations[\s\S]*?)(?=\n##|\Z)",
        report_content,
        re.IGNORECASE,
    )
    if match_sec4 and match_sec4.group(1).strip():
        return match_sec4.group(1).strip()

    # Fallback Priority 3: Strictly match ## level recommendations, avoiding invariants
    match_rec = re.search(
        r"(^##\s+.*(?:Recommendation|Actionable Tasks).*[\s\S]*?)(?=\n##|\Z)",
        report_content,
        re.IGNORECASE | re.MULTILINE,
    )
    if match_rec and match_rec.group(1).strip():
        return match_rec.group(1).strip()

    return ""


def extract_affected_files(issues: List[str], workspace_path: Path) -> List[str]:
    """Extract distinct relative file paths mentioned in issues, resolving partial basenames."""
    affected = set()
    for text in issues:
        matches = re.findall(
            r"([\w\-./\\]+\.(?:py|ts|tsx|js|jsx|json|toml|yaml|yml))", text
        )
        for m in matches:
            clean = m.replace("\\", "/").strip("./:")
            candidate = workspace_path / clean
            if candidate.exists() and candidate.is_file():
                try:
                    affected.add(candidate.relative_to(workspace_path).as_posix())
                except ValueError:
                    affected.add(clean)
            else:
                # If only filename was mentioned (e.g. workspace_tools.py), search workspace
                file_name = Path(clean).name
                found = [
                    p.relative_to(workspace_path).as_posix()
                    for p in workspace_path.rglob(file_name)
                    if ".git" not in p.parts
                    and ".venv" not in p.parts
                    and "site-packages" not in p.parts
                ]
                for f in found:
                    affected.add(f)
    sorted_affected = sorted(list(affected))
    # Cap to top 3 priority files per iteration to prevent context window explosion
    return sorted_affected[:3]


DEFAULT_AUDIT_FIX_TASKS = {
    "autonomous codebase defect and optimization fix loop.",
    "autonomous codebase defect and optimization fix loop",
    "autonomous codebase audit & fix loop",
    "autonomous codebase audit and fix loop",
    "autonomous auto-fix validation",
    "comprehensive codebase architecture, security, and bug audit.",
    "comprehensive codebase architecture, security, and bug audit",
    "",
}


def check_and_rotate_stale_reports(
    workspace_path: Path,
) -> Tuple[str, set[str]]:
    """Inspect AUDIT_FIX_REPORT.md against AUDIT_REPORT.md.
    If all prior findings were resolved (CONVERGED_CLEAN), auto-archive both to diagnostics/reports/archive/
    and signal a fresh audit pass. If partially resolved, return set of already resolved finding titles.
    """
    audit_file = locate_and_normalize_report(workspace_path, "AUDIT_REPORT.md")
    fix_file = locate_and_normalize_report(workspace_path, "AUDIT_FIX_REPORT.md")

    if not audit_file or not audit_file.exists():
        return "", set()

    if not fix_file or not fix_file.exists():
        return audit_file.read_text(encoding="utf-8", errors="replace").strip(), set()

    try:
        fix_content = fix_file.read_text(encoding="utf-8", errors="replace")
        audit_content = audit_file.read_text(encoding="utf-8", errors="replace").strip()

        outcome_m = re.search(r"\*\*Final Outcome\*\*:\s*`([^`]+)`", fix_content)
        outcome = outcome_m.group(1).strip() if outcome_m else ""

        resolved_titles: set[str] = set()
        rem_sec = re.search(
            r"##\s*Remediated Audit Findings([\s\S]*?)(?=\n##|\Z)",
            fix_content,
            re.IGNORECASE,
        )
        if rem_sec:
            for line in rem_sec.group(1).splitlines():
                m = re.search(r"-\s*\[x\]\s*(?:\[[^\]]+\]\s*)?([^\n]+)", line)
                if m:
                    resolved_titles.add(m.group(1).strip().lower())

        is_post_fix = fix_file.stat().st_mtime >= (audit_file.stat().st_mtime - 5)
        has_remaining_backlog = bool(
            re.search(
                r"##\s*Remaining Audit Backlog\s*\n\s*-\s*\[\s*\]",
                fix_content,
                re.IGNORECASE,
            )
        )

        if (
            outcome == "CONVERGED_CLEAN"
            and is_post_fix
            and not has_remaining_backlog
            and resolved_titles
        ):
            archive_dir = workspace_path / "diagnostics" / "reports" / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            import shutil

            shutil.move(str(audit_file), str(archive_dir / f"{ts}_{audit_file.name}"))
            shutil.move(str(fix_file), str(archive_dir / f"{ts}_{fix_file.name}"))
            ConsoleOutput.info(
                f"Previous audit cycle was fully resolved (CONVERGED_CLEAN). "
                f"Auto-archived reports to {archive_dir.relative_to(workspace_path)} to initiate fresh diagnostic pass."
            )
            return "", set()

        return audit_content, resolved_titles
    except Exception as e:
        ConsoleOutput.warning(f"Error inspecting prior fix report: {e}")
        try:
            return audit_file.read_text(
                encoding="utf-8", errors="replace"
            ).strip(), set()
        except Exception:
            return "", set()


class AuditFixPipeline(BasePipeline):
    """Autonomous self-healing loop: audits defects/optimizations, applies fixes via Developer,
    and validates with Tester and static checks in a continuous loop without any Git operations.
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace_path: Optional[Path] = None,
        human_channel: Optional[HumanInterventionChannel] = None,
        controller: Optional[PipelineController] = None,
        auto_chain_audit: Optional[bool] = None,
    ):
        super().__init__(
            config=config,
            skill_manager=skill_manager,
            workspace_path=workspace_path,
            human_channel=human_channel,
            controller=controller,
        )
        self.auto_chain_audit = (
            auto_chain_audit
            if auto_chain_audit is not None
            else getattr(config, "auto_chain_audit", True)
        )

    def collect_codebase_metrics(self) -> dict:
        """Scan workspace to calculate file counts and lines of code."""
        return self.adapter.collect_codebase_metrics(self.workspace_path)

    def run_static_checks(self) -> Tuple[bool, List[str]]:
        """Execute zero-token syntax validation and static analysis via adapter."""
        return self.adapter.run_static_analysis(self.workspace_path)

    def run_test_suite(self, timeout_seconds: int = 60) -> Tuple[bool, str]:
        """Execute test suite via detected language adapter."""
        if not self.adapter.has_test_suite(self.workspace_path):
            return (
                True,
                f"No test suite detected for {self.adapter.language_name} in workspace.",
            )

        test_cmd = self.adapter.get_test_command(self.workspace_path)
        if not test_cmd:
            return (True, "No test command configured.")

        test_run = execute_terminal_action(
            WorkspaceTerminalAction(command=test_cmd, timeout_seconds=timeout_seconds),
            base_dir=self.workspace_path,
        )

        if test_run.exit_code == 0:
            return (
                True,
                f"All {self.adapter.language_name} unit tests passed successfully.",
            )

        compact = self.adapter.parse_test_failures(test_run.stdout, test_run.stderr)
        return (
            False,
            f"[{self.adapter.language_name.capitalize()} Test Failures (Exit Code {test_run.exit_code})]\n{compact}",
        )

    def run_zero_token_autofix(self) -> Tuple[bool, str]:
        """Execute local deterministic code fixes/formatting via adapter."""
        return self.adapter.run_zero_token_autofix(self.workspace_path)

    def run(self, task_description: str = "") -> dict:
        """Run the continuous autonomous audit-and-fix loop without Git operations."""
        set_active_channel(self.human_channel)
        if not self.controller.check_should_continue():
            return {"status": "AUDIT_FIX_ABORTED", "reason": "Controller abort signal"}

        ConsoleOutput.banner(
            "Autonomous Audit & Auto-Fix Loop (Git-Free)",
            f"Workspace: {self.workspace_path} | Stack: {self.adapter.language_name.capitalize()} | Max Iterations: {self.config.max_iterations}",
        )

        # Step 0: Zero-Token Pre-Fix Strategy (Deterministic Local Linter & Formatter)
        ConsoleOutput.agent_step(
            "PRE-FIX",
            f"Running zero-token automated lint & format fixer ({self.adapter.language_name.capitalize()})...",
        )
        autofix_ok, _ = self.run_zero_token_autofix()
        if autofix_ok:
            ConsoleOutput.info(
                "Zero-token local auto-fix executed successfully (0 tokens consumed)."
            )

        log_store = SessionLogStore(workspace_path=self.workspace_path)
        visualizer = OrchestratorLiveVisualizer(
            log_store, verbosity=self.config.verbosity
        )
        telemetry = TelemetryRecorder(
            task_description=task_description or "Autonomous Codebase Audit & Fix Loop",
            pipeline_mode="audit-fix",
            max_budget_usd=self.config.max_budget_usd,
        )

        metrics = self.collect_codebase_metrics()
        graft_map = GraftContextProvider.get_compact_map(self.workspace_path)
        graft_part = (
            f"\n\n[Codebase Architecture Map (Graft)]:\n{graft_map}"
            if graft_map
            else ""
        )

        # Check for existing AUDIT_REPORT.md and sync with prior AUDIT_FIX_REPORT.md
        existing_report_content, resolved_titles = check_and_rotate_stale_reports(
            self.workspace_path
        )
        if existing_report_content:
            ConsoleOutput.info(
                f"Loaded active audit report ({len(existing_report_content)} chars)."
            )

        audit_findings_queue: List[Dict[str, Any]] = []
        if existing_report_content:
            raw_findings = extract_audit_findings_list(existing_report_content)
            # Filter out findings that were already resolved in prior iterations
            if resolved_titles:
                audit_findings_queue = [
                    f
                    for f in raw_findings
                    if not any(
                        r in f["title"].lower() or f["title"].lower() in r
                        for r in resolved_titles
                    )
                ]
                ConsoleOutput.info(
                    f"Resuming backlog: {len(resolved_titles)} finding(s) previously resolved, "
                    f"{len(audit_findings_queue)} active finding(s) remaining."
                )
            else:
                audit_findings_queue = raw_findings
                if audit_findings_queue:
                    ConsoleOutput.info(
                        f"Identified {len(audit_findings_queue)} prioritized actionable audit finding(s) in backlog."
                    )

        # Determine dynamic or explicit iteration budget
        raw_max_iter = getattr(self.config, "max_iterations", "auto")
        if str(raw_max_iter).lower() == "auto":
            # Dynamic scaling: 2 iterations per active finding, minimum 4, maximum 16
            effective_max_iterations = (
                max(min(len(audit_findings_queue) * 2, 16), 4)
                if audit_findings_queue
                else 4
            )
            ConsoleOutput.info(
                f"Auto-iteration scaling engaged: dynamically allocated {effective_max_iterations} iteration(s) for {len(audit_findings_queue)} active backlog finding(s)."
            )
        else:
            try:
                effective_max_iterations = int(raw_max_iter)
            except (ValueError, TypeError):
                effective_max_iterations = 4

        developer_agent = create_developer_agent(
            self.config,
            self.skill_manager,
            self.workspace_path,
            allow_test_writes=True,
            task_text=task_description,
        )

        reset_append_counts()
        completed_fixes: List[str] = []
        resolved_findings: List[str] = []
        current_finding: Optional[Dict[str, Any]] = None
        consecutive_zero_mods: Dict[str, int] = {}
        retry_directive: Optional[str] = None
        fixes_applied_log: List[Dict[str, Any]] = []
        final_status = "IN_PROGRESS"
        last_issues: List[str] = []

        for iteration in range(1, effective_max_iterations + 1):
            if not self.controller.check_should_continue():
                ConsoleOutput.warning(
                    f"Audit-fix loop stopped by controller at iteration {iteration}."
                )
                final_status = "STOPPED_BY_CONTROLLER"
                break

            # Reset append safeguards per iteration
            reset_append_counts()

            # Fresh, isolated developer conversation per iteration (eliminates context ballooning)
            dev_conv = Conversation(
                agent=developer_agent,
                workspace=str(self.workspace_path),
                visualizer=visualizer,
            )
            dev_conv.human_channel = self.human_channel

            # Run zero-token auto-fix before each inspection pass
            self.run_zero_token_autofix()

            ConsoleOutput.agent_step(
                "AUDIT",
                f"Iteration {iteration}/{effective_max_iterations}: Scanning workspace...",
            )

            # 1. Run static checks
            static_clean, static_issues = self.run_static_checks()

            # 2. Run test suite
            tests_clean, test_feedback = self.run_test_suite()

            all_issues: List[str] = []
            if not static_clean:
                all_issues.extend(static_issues)
            if not tests_clean:
                all_issues.append(test_feedback)

            # 3. If static and tests are clean, pull from audit findings backlog
            if not all_issues:
                if (
                    iteration == 1
                    and not existing_report_content
                    and self.auto_chain_audit
                ):
                    from orchestrator.pipeline.audit_pipeline import AuditPipeline

                    ConsoleOutput.agent_step(
                        "AUDIT-CHAIN",
                        "Static checks and tests are clean. Auto-chaining deep architectural Auditor agent...",
                    )
                    audit_pipe = AuditPipeline(
                        config=self.config,
                        skill_manager=self.skill_manager,
                        workspace_path=self.workspace_path,
                        human_channel=self.human_channel,
                        controller=self.controller,
                    )
                    audit_pipe.run(task_description=task_description)
                    audit_content = read_report(self.workspace_path, "AUDIT_REPORT.md")
                    if audit_content:
                        existing_report_content = audit_content
                        audit_findings_queue = extract_audit_findings_list(
                            existing_report_content
                        )

                # If a finding was in-flight and needs a retry, re-present it
                if current_finding:
                    retry_prefix = f"⚠️ {retry_directive}\n\n" if retry_directive else ""
                    all_issues.append(
                        f"{retry_prefix}[Audit Finding Remediation: {current_finding['severity']} - {current_finding['title']}]\n"
                        f"{current_finding['content'][:2500]}"
                    )
                # Otherwise, pop the next highest priority finding from the queue
                elif audit_findings_queue:
                    current_finding = audit_findings_queue.pop(0)
                    all_issues.append(
                        f"[Audit Finding Remediation: {current_finding['severity']} - {current_finding['title']}]\n"
                        f"{current_finding['content'][:2500]}"
                    )
                elif (
                    task_description
                    and task_description.strip().lower() not in DEFAULT_AUDIT_FIX_TASKS
                    and iteration == 1
                ):
                    all_issues.append(
                        f"[User Optimization Directive]\n{task_description.strip()}"
                    )

            last_issues = all_issues

            # 4. Check Initial Convergence
            if not all_issues:
                ConsoleOutput.success(
                    f"Audit-Fix Loop Converged in iteration {iteration}! Zero defects detected."
                )
                final_status = "CONVERGED_CLEAN"
                break

            # 5. Remediation by Developer Agent
            ConsoleOutput.warning(
                f"Iteration {iteration}: {len(all_issues)} issue group(s) detected. Developer applying fixes..."
            )
            log_store.set_agent_context(
                "Developer",
                f"Fix Iteration {iteration}",
                model=developer_agent.llm.model,
                llm=developer_agent.llm,
            )

            issues_text = "\n\n".join(all_issues)
            user_directive = (
                task_description.strip()
                if task_description
                else "Audit and auto-fix all codebase defects and optimizations."
            )

            affected_files = extract_affected_files(all_issues, self.workspace_path)
            if affected_files:
                file_bullets = "\n".join(f"- `{f}`" for f in affected_files)
                scope_constraint = (
                    f"CRITICAL TARGET SCOPE LOCK:\n"
                    f"The issues are strictly isolated to the following file(s):\n"
                    f"{file_bullets}\n\n"
                    "MANDATORY PLAN-FIRST WORKFLOW:\n"
                    "1. First, state a concise 2-line plan:\n"
                    "   - Target File: <file>\n"
                    "   - Precise Fix: <exact lines or imports to modify>\n"
                    "2. You are STRICTLY FORBIDDEN from reading unmentioned files, diagnostics, or listing directories (`ls`, `dir`, `pwd`).\n"
                    "3. Open and modify ONLY the locked file(s) above using `workspace_file`.\n"
                    "4. Apply the fix and stop immediately."
                )
            else:
                scope_constraint = (
                    "MANDATORY PLAN-FIRST WORKFLOW:\n"
                    "1. First, state a concise 2-line plan (Target File and Planned Change).\n"
                    "2. Inspect ONLY the specific affected file where errors were reported.\n"
                    "3. You are STRICTLY FORBIDDEN from listing root directories (`ls`, `dir`, `list .`) or reading diagnostic files.\n"
                    "4. Apply the targeted fix directly and stop."
                )

            test_status_note = ""
            if tests_clean:
                test_status_note = (
                    "\nNOTICE: All project unit tests are currently PASSING (100% green).\n"
                    "Do NOT run pytest or examine test suites or diagnostics. Focus ONLY on the static issues above."
                )

            effective_graft = graft_part if len(graft_part) < 1500 else ""

            # Structured Iteration State (Replaces raw conversation history with compact JSON block)
            iter_state = StructuredIterationState(
                iteration=iteration,
                affected_files=affected_files,
                completed_fixes=completed_fixes,
                remaining_findings=all_issues[:3],
                tests_status="PASSED" if tests_clean else "FAILURES_DETECTED",
            )
            state_directive = iter_state.render_prompt_block()

            dev_prompt = (
                f"Task: {user_directive}\n\n"
                f"{state_directive}\n\n"
                f"Iteration {iteration} of {effective_max_iterations} - Auto-Fix Remediation Directive:\n"
                f"The automated audit detected the following issues that must be solved in this {self.adapter.language_name.capitalize()} project:\n\n"
                f"{issues_text}\n"
                f"{test_status_note}\n\n"
                f"{scope_constraint}\n\n"
                f"{effective_graft}\n\n"
                f"{self.adapter.get_developer_prompt_guidance()}"
            )

            # Capture workspace pre-execution snapshot to verify code modifications
            pre_mtimes = {
                p: p.stat().st_mtime
                for p in self.workspace_path.rglob("*.py")
                if ".git" not in p.parts and ".venv" not in p.parts
            }

            # Compute dynamic token budget and governor for this iteration
            finding_sev = (
                current_finding.get("severity", "MEDIUM")
                if current_finding
                else "MEDIUM"
            )
            finding_context = (
                (
                    current_finding.get("title", "")
                    + " "
                    + current_finding.get("content", "")
                )
                if current_finding
                else issues_text
            )
            hard_cap = getattr(self.config, "max_tokens_budget", 180_000)

            governor = DynamicTokenGovernor.compute_iteration_budget(
                role="developer",
                severity=finding_sev,
                affected_files_count=len(affected_files),
                task_text=finding_context,
                hard_ceiling=min(hard_cap, 180_000),
            )
            step_limit = getattr(
                governor,
                "suggested_max_steps",
                min(getattr(self.config, "max_agent_steps", 8), 8),
            )

            t_dev = time.perf_counter()
            dev_conv.send_message(self.human_channel.inject_into_prompt(dev_prompt))
            try:
                self._run_conv(
                    dev_conv,
                    "Developer",
                    max_steps=step_limit,
                    governor=governor,
                    task_complexity="high"
                    if governor.allocation.total_budget > 100_000
                    else "medium",
                )
            finally:
                if hasattr(visualizer, "close"):
                    visualizer.close()
            dur_dev = time.perf_counter() - t_dev
            u_dev = get_llm_usage(developer_agent.llm)

            # Detect modified files
            post_mtimes = {
                p: p.stat().st_mtime
                for p in self.workspace_path.rglob("*.py")
                if ".git" not in p.parts and ".venv" not in p.parts
            }
            files_modified = [
                p
                for p, mt in post_mtimes.items()
                if p not in pre_mtimes or pre_mtimes[p] != mt
            ]
            if files_modified:
                for p in files_modified:
                    try:
                        rel = str(p.relative_to(self.workspace_path))
                        completed_fixes.append(f"Modified {rel}")
                    except ValueError:
                        completed_fixes.append(f"Modified {p.name}")

            telemetry.record_step(
                "developer",
                "auto_fix",
                iteration,
                dur_dev,
                True,
                prompt_tokens=u_dev["prompt_tokens"],
                completion_tokens=u_dev["completion_tokens"],
                total_tokens=u_dev["total_tokens"],
                estimated_cost_usd=u_dev["estimated_cost_usd"],
            )

            fixes_applied_log.append(
                {
                    "iteration": iteration,
                    "issues_count": len(all_issues),
                    "duration_seconds": round(dur_dev, 2),
                    "tokens": u_dev["total_tokens"],
                    "cost_usd": u_dev["estimated_cost_usd"],
                }
            )

            # Check total cost against budget guard
            total_cost_usd = u_dev["estimated_cost_usd"]
            if self.budget_guard.update_cost(total_cost_usd):
                ConsoleOutput.error(
                    "Budget ceiling reached during auto-fix loop. Halting."
                )
                final_status = "BUDGET_EXHAUSTED"
                break

            # 6. Verification: Strict Convergence Predicate post-remediation
            post_static_ok, post_static_issues = self.run_static_checks()
            post_tests_ok, post_test_feedback = self.run_test_suite()

            from orchestrator.pipeline.checkpoint import PipelineCheckpointManager

            PipelineCheckpointManager.save(
                workspace=self.workspace_path,
                run_id=telemetry.report_id,
                task=task_description or "Autonomous Codebase Audit & Fix Loop",
                mode="audit-fix",
                current_phase=f"iteration_{iteration}",
                iteration=iteration,
                tests_passed=(post_static_ok and post_tests_ok),
            )

            remaining_issues: List[str] = []
            if not post_static_ok:
                remaining_issues.extend(post_static_issues)
            if not post_tests_ok:
                remaining_issues.append(post_test_feedback)

            if post_static_ok and post_tests_ok and not remaining_issues:
                if files_modified:
                    if current_finding:
                        finding_label = f"[{current_finding['severity']}] {current_finding['title']}"
                        ConsoleOutput.success(
                            f"Iteration {iteration}: Verified & resolved {finding_label}."
                        )
                        resolved_findings.append(finding_label)
                        consecutive_zero_mods.pop(current_finding["title"], None)
                        current_finding = None
                        retry_directive = None

                    if not audit_findings_queue and not current_finding:
                        ConsoleOutput.success(
                            f"Strict Verification Converged in iteration {iteration}! "
                            f"All audit backlog items resolved, tests pass, static checks clean."
                        )
                        final_status = "CONVERGED_CLEAN"
                        break
                    else:
                        ConsoleOutput.info(
                            f"Iteration {iteration} complete. "
                            f"{len(audit_findings_queue)} finding(s) remaining in backlog. Continuing loop."
                        )
                        continue
                else:
                    finding_title = (
                        current_finding["title"] if current_finding else "Active Task"
                    )
                    consecutive_zero_mods[finding_title] = (
                        consecutive_zero_mods.get(finding_title, 0) + 1
                    )
                    fail_count = consecutive_zero_mods[finding_title]

                    ConsoleOutput.warning(
                        f"Iteration {iteration}: Developer made 0 code modifications for active finding (attempt {fail_count}/2)."
                    )
                    if fail_count >= 2:
                        ConsoleOutput.warning(
                            f"Finding Circuit Breaker: [{finding_title}] produced 0 modifications in 2 consecutive attempts. "
                            "Rotating to backlog tail to prevent pipeline blockage."
                        )
                        if current_finding:
                            audit_findings_queue.append(current_finding)
                            current_finding = None
                        retry_directive = None
                    else:
                        retry_directive = (
                            f"CRITICAL ACTION-FIRST DIRECTIVE (Attempt 2/2):\n"
                            f"The previous attempt applied 0 code modifications to '{finding_title}'. "
                            "You are STRICTLY FORBIDDEN from reading files, listing directories, or executing exploration commands. "
                            "You already have the full file context. You must immediately call workspace_file(operation='edit') on step 1."
                        )
            else:
                ConsoleOutput.warning(
                    f"Iteration {iteration} verification: Issues remain "
                    f"(Static Clean: {post_static_ok}, Tests Clean: {post_tests_ok}). Proceeding to next iteration."
                )
                all_issues = remaining_issues
                retry_directive = None

        if final_status == "IN_PROGRESS":
            final_status = "MAX_ITERATIONS_REACHED"

        u_total = get_llm_usage(developer_agent.llm)
        total_tokens = u_total.get("total_tokens", 0)

        # Generate docs/AUDIT_FIX_REPORT.md
        docs_dir = self.workspace_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        report_file = docs_dir / "AUDIT_FIX_REPORT.md"
        report_content = self._generate_report_content(
            task_description=task_description,
            final_status=final_status,
            metrics=metrics,
            fixes_log=fixes_applied_log,
            last_issues=last_issues,
            completed_fixes=completed_fixes,
            resolved_findings=resolved_findings,
            remaining_backlog=audit_findings_queue,
            total_tokens=total_tokens,
        )
        report_file.write_text(report_content, encoding="utf-8")

        telemetry.finalize(
            completed_successfully=(final_status == "CONVERGED_CLEAN"),
            resolved_findings_delta=len(resolved_findings),
        )
        log_store.save_to_file()

        ConsoleOutput.banner(
            "Audit & Auto-Fix Run Finished",
            f"Status: {final_status} | Report: {report_file.name} | Total Tokens: {u_total['total_tokens']:,}",
        )

        return {
            "status": final_status,
            "report_path": str(report_file),
            "iterations": len(fixes_applied_log) or 1,
            "tokens": total_tokens,
            "cost_usd": u_total.get("estimated_cost_usd", 0.0),
        }

    def _generate_report_content(
        self,
        task_description: str,
        final_status: str,
        metrics: dict,
        fixes_log: List[dict],
        last_issues: List[str],
        completed_fixes: Optional[List[str]] = None,
        resolved_findings: Optional[List[str]] = None,
        remaining_backlog: Optional[List[dict]] = None,
        total_tokens: int = 0,
    ) -> str:
        """Construct the markdown summary of the audit-fix session."""
        ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        resolved_count = len(resolved_findings) if resolved_findings else 0
        per_score = TelemetryRecorder.calculate_per(resolved_count, total_tokens)
        lines = [
            "# Autonomous Codebase Audit & Auto-Fix Report",
            "",
            f"- **Execution Timestamp**: {ts}",
            f"- **Final Outcome**: `{final_status}`",
            f"- **Target Workspace**: `{self.workspace_path}`",
            f"- **Task Directive**: {task_description or 'Comprehensive Audit & Fix'}",
            f"- **Progress Efficiency Ratio (PER)**: `{per_score}` findings/100k tokens",
            f"- **Total Python Files**: {metrics.get('total_files', 0)}",
            f"- **Total Lines of Code**: {metrics.get('total_loc', 0)}",
            "",
            "## Iteration History",
            "",
        ]

        if not fixes_log:
            lines.append(
                "No remediation iterations were needed; workspace was clean on initial scan."
            )
        else:
            lines.append(
                "| Iteration | Issues Addressed | Duration (s) | Tokens Used | Est. Cost ($) |"
            )
            lines.append("|---|---|---|---|---|")
            for entry in fixes_log:
                lines.append(
                    f"| {entry['iteration']} | {entry['issues_count']} | "
                    f"{entry['duration_seconds']}s | {entry['tokens']:,} | ${entry['cost_usd']:.4f} |"
                )

        if resolved_findings:
            lines.append("")
            lines.append("## Remediated Audit Findings")
            lines.append("")
            for rf in resolved_findings:
                lines.append(f"- [x] {rf}")

        if completed_fixes:
            lines.append("")
            lines.append("## Code Modifications Applied")
            lines.append("")
            for cf in set(completed_fixes):
                lines.append(f"- [x] {cf}")

        if remaining_backlog:
            lines.append("")
            lines.append("## Remaining Audit Backlog")
            lines.append("")
            for rb in remaining_backlog:
                lines.append(
                    f"- [ ] [{rb.get('severity', 'FINDING')}] {rb.get('title', 'Unknown')}"
                )

        lines.append("")
        lines.append("## Final Verification State")
        lines.append("")
        if final_status == "CONVERGED_CLEAN":
            lines.append("- [x] AST Syntax Validation: **PASS**")
            lines.append("- [x] Ruff Static Linting: **CLEAN**")
            lines.append("- [x] Automated Pytest Suite: **PASS**")
            lines.append(
                "- [x] Zero Git Footprint: Edits made directly in workspace working tree."
            )
        else:
            lines.append(
                f"Status: `{final_status}`. Some remaining issues require further review:"
            )
            for issue in last_issues[:5]:
                lines.append(f"```text\n{issue[:500]}\n```")

        return "\n".join(lines)
