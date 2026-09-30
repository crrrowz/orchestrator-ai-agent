"""CI Failure Collector: Extracts structured failures from raw workflow runs and job logs."""

import re
from typing import Any, Dict, List, Optional, Tuple
from orchestrator.ci.classifier import FailureClassifier
from orchestrator.ci.models import EnvironmentInfo, FailureCategory, FailureItem, Severity
from orchestrator.ci.normalizer import FailureNormalizer
from orchestrator.ci.provider import CIProvider


class CIFailureCollector:
    """Collects, extracts, and parses failures from CI providers."""

    def __init__(self, provider: CIProvider):
        self.provider = provider

    def collect(self, run_id: Optional[str] = None) -> Tuple[Dict[str, Any], List[FailureItem], List[Dict[str, Any]]]:
        """Collect run metadata, all failures, and raw jobs metadata.

        Returns:
            Tuple of (run_metadata, list_of_FailureItems, list_of_raw_jobs)
        """
        run_data = self.provider.get_run(run_id)
        resolved_run_id = str(run_data.get("id") or run_id or "unknown")
        workflow_name = run_data.get("name") or run_data.get("workflow_name") or "CI"

        jobs = self.provider.get_jobs(resolved_run_id)
        failures: List[FailureItem] = []

        # Annotations (from GitHub checks)
        annotations = self.provider.get_annotations(resolved_run_id)
        annotation_map: Dict[str, List[Dict[str, Any]]] = {}
        for ann in annotations:
            path = ann.get("path", "")
            annotation_map.setdefault(path, []).append(ann)

        for job in jobs:
            job_name = job.get("name", "job")
            job_id = str(job.get("id", ""))
            job_conclusion = (job.get("conclusion") or job.get("status") or "").lower()

            # Parse matrix / environment parameters from job name or metadata
            env_info = self._parse_environment(job_name, job)

            # Inspect steps
            steps = job.get("steps", [])
            has_failed_step = False

            for step in steps:
                step_name = step.get("name", "step")
                step_conclusion = (step.get("conclusion") or "").lower()
                step_number = step.get("number", 0)

                # Even if step succeeded, check for non-blocking warnings or cache errors reported in step
                is_failed = step_conclusion in ("failure", "timed_out", "action_required")

                if is_failed:
                    has_failed_step = True
                    # Fetch step/job logs if available
                    log_text = self.provider.get_job_logs(job_id) if job_id else ""
                    step_log_snippet = self._extract_step_log_snippet(log_text, step_name)

                    classified_items = FailureClassifier.classify_all(
                        message=step_log_snippet or f"Step '{step_name}' failed with {step_conclusion}",
                        step_name=step_name,
                    )

                    clean_norm = FailureNormalizer.normalize_text(step_log_snippet or step_name)
                    fp = FailureNormalizer.compute_fingerprint(clean_norm)

                    for idx, (cat, sev, blocking, desc) in enumerate(classified_items):
                        item_id = f"{job_name}::{step_name}::{step_number}::{idx}"
                        failures.append(
                            FailureItem(
                                id=item_id,
                                provider="github",
                                workflow=workflow_name,
                                run_id=resolved_run_id,
                                job=job_name,
                                step=step_name,
                                environment=env_info,
                                category=cat,
                                severity=sev,
                                status=step_conclusion,
                                message=desc,
                                raw_evidence=step_log_snippet[:4000],
                                normalized_evidence=clean_norm[:2000],
                                fingerprint=fp,
                                blocking=blocking,
                            )
                        )

            # If job failed but no specific step was marked failed (e.g. container startup crash or timeout)
            if job_conclusion in ("failure", "cancelled") and not has_failed_step:
                log_text = self.provider.get_job_logs(job_id) if job_id else ""
                cat, sev, blocking, desc = FailureClassifier.classify(
                    message=log_text[:1000] or f"Job '{job_name}' concluded with {job_conclusion}",
                    step_name=job_name,
                )
                clean_norm = FailureNormalizer.normalize_text(log_text[:1000] or desc)
                fp = FailureNormalizer.compute_fingerprint(clean_norm)
                failures.append(
                    FailureItem(
                        id=f"{job_name}::job",
                        provider="github",
                        workflow=workflow_name,
                        run_id=resolved_run_id,
                        job=job_name,
                        step=job_name,
                        environment=env_info,
                        category=cat,
                        severity=sev,
                        status=job_conclusion,
                        message=desc,
                        raw_evidence=log_text[:2000],
                        normalized_evidence=clean_norm[:1000],
                        fingerprint=fp,
                        blocking=blocking,
                    )
                )

        return run_data, failures, jobs

    def _parse_environment(self, job_name: str, job_dict: Dict[str, Any]) -> EnvironmentInfo:
        """Extract OS, architecture, and runtime versions from job naming or matrix attributes."""
        # Check explicit runner labels or runner name
        labels = [str(l).lower() for l in job_dict.get("labels", [])]
        combined_text = f"{job_name} {' '.join(labels)}".lower()

        os_str = "unknown"
        if "windows" in combined_text or "win" in combined_text:
            os_str = "windows-latest"
        elif "ubuntu" in combined_text or "linux" in combined_text:
            os_str = "ubuntu-latest"
        elif "macos" in combined_text or "darwin" in combined_text:
            os_str = "macos-latest"

        # Python version matching, e.g. "3.12", "Python 3.13"
        python_ver = "unknown"
        m = re.search(r"python\s*([23]\.\d+)", combined_text)
        if m:
            python_ver = m.group(1)
        else:
            m2 = re.search(r"\b(3\.\d+)\b", job_name)
            if m2:
                python_ver = m2.group(1)

        matrix = {"os": os_str, "python-version": python_ver}
        return EnvironmentInfo.from_matrix(matrix=matrix, os_str=os_str, python_ver=python_ver)

    def _extract_step_log_snippet(self, log_text: str, step_name: str) -> str:
        """Extract lines corresponding to a specific step or trailing error lines."""
        if not log_text:
            return ""

        lines = log_text.splitlines()
        # Look for error markers or traceback
        failing_lines = []
        capture = False
        for line in lines:
            if "FAILURES" in line or "Traceback (most recent call last)" in line:
                capture = True
            if capture:
                failing_lines.append(line)
                if len(failing_lines) >= 60:
                    break

        if failing_lines:
            return "\n".join(failing_lines)

        # Fallback to last 40 lines
        return "\n".join(lines[-40:])
