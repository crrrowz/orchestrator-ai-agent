"""Independent, Evidence-Based Verification Engine."""

from typing import Any, Dict, List, Optional
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.verification.models import (
    VerificationDefect,
    VerificationReport,
    VerificationStatus,
)


class VerificationEngine(IEngine):
    """Engine providing independent verification gates, test suite validation, and defect generation."""

    engine_name: str = "verification"

    def __init__(self) -> None:
        self._is_running: bool = False

    async def initialize(self, container: IContainer) -> None:
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    async def verify_evidence(
        self,
        task_id: str,
        test_passed: bool = True,
        diff_present: bool = True,
        security_clean: bool = True,
    ) -> VerificationReport:
        defects: List[VerificationDefect] = []

        if not test_passed:
            defects.append(
                VerificationDefect(
                    category="testing",
                    severity="CRITICAL",
                    description="PyTest test suite failed execution.",
                    suggested_fix="Review failure trace and fix broken assertions.",
                )
            )

        if not diff_present:
            defects.append(
                VerificationDefect(
                    category="evidence",
                    severity="MEDIUM",
                    description="No code diff artifacts found for verification.",
                )
            )

        if not security_clean:
            defects.append(
                VerificationDefect(
                    category="security",
                    severity="HIGH",
                    description="Security audit detected vulnerability in modified files.",
                )
            )

        passed = len(defects) == 0
        score = 1.0 if passed else max(0.0, 1.0 - (len(defects) * 0.3))

        return VerificationReport(
            task_id=task_id,
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            score=score,
            passed=passed,
            defects=defects,
            feedback_for_agent="All checks verified successfully." if passed else "Defects detected during verification.",
        )

    async def healthcheck(self) -> Dict[str, Any]:
        return {"status": "healthy" if self._is_running else "stopped"}
