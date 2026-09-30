"""Abstract CI Provider Interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class CIProvider(ABC):
    """Abstract base provider for continuous integration platforms (GitHub, GitLab, CircleCI, Local)."""

    @abstractmethod
    def get_run(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch metadata for a specific run or the latest run."""
        pass

    @abstractmethod
    def get_jobs(self, run_id: str) -> List[Dict[str, Any]]:
        """Fetch all execution jobs and step statuses for a run."""
        pass

    @abstractmethod
    def get_job_logs(self, job_id: str) -> str:
        """Fetch execution logs for a specific job."""
        pass

    @abstractmethod
    def get_annotations(self, run_id: str) -> List[Dict[str, Any]]:
        """Fetch annotations and warnings reported by the CI provider."""
        pass
