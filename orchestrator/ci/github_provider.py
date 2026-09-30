"""GitHub Actions CI Provider using official GitHub REST API."""

import os
import re
import subprocess
from typing import Any, Dict, List, Optional
import httpx

from orchestrator.ci.provider import CIProvider


class GitHubActionsProvider(CIProvider):
    """Interacts with GitHub Actions API to retrieve workflow runs, jobs, logs, and annotations."""

    def __init__(
        self,
        token: Optional[str] = None,
        repo: Optional[str] = None,  # format "owner/repo"
        api_base: str = "https://api.github.com",
    ):
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        self.repo = repo or os.getenv("GITHUB_REPOSITORY") or self._detect_repo_from_git()
        self.api_base = api_base.rstrip("/")
        self._headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ORAGAI-CI-Failure-Analyzer",
        }
        if self.token:
            self._headers["Authorization"] = f"Bearer {self.token}"

    def _detect_repo_from_git(self) -> str:
        """Infer owner/repo from local git remote url."""
        try:
            res = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                url = res.stdout.strip()
                # Matches git@github.com:owner/repo.git or https://github.com/owner/repo(.git)
                m = re.search(r"github\.com[:/]([A-Za-z0-9_\-\.]+)/([A-Za-z0-9_\-\.]+?)(?:\.git)?$", url)
                if m:
                    return f"{m.group(1)}/{m.group(2)}"
        except Exception:
            pass
        return "crrrowz/orchestrator-ai-agent"

    def get_run(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch metadata for a specific run ID, or retrieve the most recent run."""
        endpoint = (
            f"{self.api_base}/repos/{self.repo}/actions/runs/{run_id}"
            if run_id
            else f"{self.api_base}/repos/{self.repo}/actions/runs?per_page=1"
        )
        try:
            with httpx.Client(timeout=15.0, headers=self._headers) as client:
                resp = client.get(endpoint)
                if resp.status_code == 200:
                    data = resp.json()
                    if not run_id and "workflow_runs" in data:
                        runs = data["workflow_runs"]
                        return runs[0] if runs else {}
                    return data
        except Exception as exc:
            return {"error": str(exc), "status": "unavailable"}

        return {"status": "unavailable", "run_id": run_id}

    def get_jobs(self, run_id: str) -> List[Dict[str, Any]]:
        """Fetch all execution jobs and step details for a workflow run."""
        endpoint = f"{self.api_base}/repos/{self.repo}/actions/runs/{run_id}/jobs"
        try:
            with httpx.Client(timeout=15.0, headers=self._headers) as client:
                resp = client.get(endpoint)
                if resp.status_code == 200:
                    return resp.json().get("jobs", [])
        except Exception:
            pass
        return []

    def get_job_logs(self, job_id: str) -> str:
        """Fetch plain-text logs for a specific job."""
        endpoint = f"{self.api_base}/repos/{self.repo}/actions/jobs/{job_id}/logs"
        try:
            with httpx.Client(timeout=30.0, headers=self._headers, follow_redirects=True) as client:
                resp = client.get(endpoint)
                if resp.status_code == 200:
                    return resp.text
        except Exception:
            pass
        return ""

    def get_annotations(self, run_id: str) -> List[Dict[str, Any]]:
        """Fetch check annotations associated with check runs for the run."""
        jobs = self.get_jobs(run_id)
        annotations = []
        for job in jobs:
            check_run_id = job.get("id")
            if not check_run_id:
                continue
            endpoint = f"{self.api_base}/repos/{self.repo}/check-runs/{check_run_id}/annotations"
            try:
                with httpx.Client(timeout=15.0, headers=self._headers) as client:
                    resp = client.get(endpoint)
                    if resp.status_code == 200:
                        annotations.extend(resp.json())
            except Exception:
                continue
        return annotations
