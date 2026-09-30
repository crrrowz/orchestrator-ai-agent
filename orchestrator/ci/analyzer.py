"""CI Failure Analyzer Engine: Coordinates Collect, Normalize, Classify, Correlate, Analyze, and Evidence Gate."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestrator.ci.classifier import FailureClassifier
from orchestrator.ci.collector import CIFailureCollector
from orchestrator.ci.correlator import FailureCorrelator
from orchestrator.ci.evidence_gate import EvidenceGate
from orchestrator.ci.github_provider import GitHubActionsProvider
from orchestrator.ci.models import (
    CIDiagnosticReport,
    CorrelationPattern,
    EvidenceGateDecision,
    FailureCategory,
    FailureItem,
    RootCauseHypothesis,
    RootCauseStatus,
)
from orchestrator.ci.normalizer import FailureNormalizer
from orchestrator.ci.provider import CIProvider
from orchestrator.ci.root_cause import RootCauseAnalyzer
from orchestrator.config import DEFAULT_DIAGNOSTICS_DIR


class CIFailureAnalyzer:
    """End-to-end evidence-first CI Failure Analyzer for ORAGAI."""

    def __init__(self, provider: Optional[CIProvider] = None, storage_dir: Optional[Path] = None):
        self.provider = provider or GitHubActionsProvider()
        self.storage_dir = (storage_dir or (DEFAULT_DIAGNOSTICS_DIR / "ci")).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def diagnose_run(
        self,
        run_id: Optional[str] = None,
        raw_failures: Optional[List[FailureItem]] = None,
        jobs_metadata: Optional[List[Dict[str, Any]]] = None,
        workflow_name: str = "CI",
    ) -> CIDiagnosticReport:
        """Run complete diagnostic pipeline on a CI run or synthetic failure items."""
        failures: List[FailureItem] = []
        jobs_meta: List[Dict[str, Any]] = jobs_metadata or []
        resolved_run_id = str(run_id or "local-run")

        if raw_failures is not None:
            failures = raw_failures
        else:
            collector = CIFailureCollector(self.provider)
            run_data, failures, jobs_meta = collector.collect(run_id)
            resolved_run_id = str(run_data.get("id") or resolved_run_id)
            workflow_name = run_data.get("name") or workflow_name

        # 1. Normalize and deduplicate evidence
        for f in failures:
            f.normalized_evidence = FailureNormalizer.normalize_text(f.raw_evidence or f.message)
            f.fingerprint = FailureNormalizer.compute_fingerprint(f.normalized_evidence)

        # 2. Correlate failures across environments and matrix
        patterns = FailureCorrelator.correlate(failures, all_jobs_meta=jobs_meta)

        # 3. Analyze root cause evidence
        root_cause = RootCauseAnalyzer.analyze(failures, patterns)

        # 4. Evaluate Evidence Gate
        gate_decision = EvidenceGate.evaluate(failures, root_cause)

        # 5. Calculate summary metrics
        total_jobs = len(jobs_meta) if jobs_meta else (len(failures) or 1)
        failed_jobs_count = len({f.job for f in failures if f.blocking})
        passed_jobs_count = max(0, total_jobs - failed_jobs_count)

        # 6. Formulate next actions
        next_actions = []
        if gate_decision.status == "BLOCKED":
            missing = ", ".join(gate_decision.required_evidence)
            next_actions.append(f"Retrieve {missing} before allowing code edits.")
        else:
            next_actions.append("Evidence verified. Dispatch structured diagnostic report to Developer Agent.")

        report = CIDiagnosticReport(
            run_id=resolved_run_id,
            workflow_name=workflow_name,
            status="FAILED" if failed_jobs_count > 0 else "PASSED",
            jobs_total=total_jobs,
            jobs_passed=passed_jobs_count,
            jobs_failed=failed_jobs_count,
            failures=failures,
            patterns=patterns,
            root_cause=root_cause,
            gate_decision=gate_decision,
            next_actions=next_actions,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

        # 7. Persist structured report
        self.save_report(report)

        return report

    def save_report(self, report: CIDiagnosticReport) -> Path:
        """Persist report JSON and Markdown into diagnostics store."""
        target_file = self.storage_dir / f"ci_report_{report.run_id}.json"
        md_file = self.storage_dir / f"ci_report_{report.run_id}.md"

        target_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        md_file.write_text(report.to_markdown(), encoding="utf-8")
        return target_file

    def load_latest_report(self) -> Optional[CIDiagnosticReport]:
        """Load the most recently generated CI diagnostic report."""
        files = sorted(self.storage_dir.glob("ci_report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            return None
        try:
            data = json.loads(files[0].read_text(encoding="utf-8"))
            return CIDiagnosticReport.model_validate(data)
        except Exception:
            return None
