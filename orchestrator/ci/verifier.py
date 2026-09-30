"""Local CI Verifier: Replicates GitHub Actions CI pipeline gates locally."""

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Optional
from orchestrator.ci.classifier import FailureClassifier
from orchestrator.ci.models import (
    CIDiagnosticReport,
    EnvironmentInfo,
    EvidenceGateDecision,
    FailureCategory,
    FailureItem,
    RootCauseHypothesis,
    RootCauseStatus,
    Severity,
)
from orchestrator.ci.normalizer import FailureNormalizer


@dataclass
class CIGateResult:
    """Outcome of an individual local CI pipeline gate."""

    name: str
    command: str
    returncode: int
    passed: bool
    stdout: str
    stderr: str
    duration_seconds: float


@dataclass
class CIVerificationSummary:
    """Overall local CI verification run outcome."""

    all_passed: bool
    gates: List[CIGateResult] = field(default_factory=list)
    failures: List[FailureItem] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render markdown summary of local CI gate execution."""
        lines = [
            "# Local CI Verification Summary",
            "",
            f"**Status**: {'🟢 ALL GATES PASSED' if self.all_passed else '🔴 GATES FAILED'}",
            "",
            "| Gate | Command | Status | Duration |",
            "|---|---|---|---|",
        ]
        for g in self.gates:
            status_str = "PASSED" if g.passed else f"FAILED (exit {g.returncode})"
            lines.append(f"| {g.name} | `{g.command}` | `{status_str}` | {g.duration_seconds:.2f}s |")
        lines.append("")
        return "\n".join(lines)


class LocalCIVerifier:
    """Executes the exact static analysis and test validation gates configured in .github/workflows/ci.yml."""

    PIPELINE_GATES = [
        ("Lint with Ruff", ["uv", "run", "ruff", "check", "."], ["ruff", "check", "."]),
        ("Run Test Suite", ["uv", "run", "pytest", "tests/", "-v"], ["pytest", "tests/", "-v"]),
    ]

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = (workspace_path or Path.cwd()).resolve()

    def run_command(self, cmd_candidates: List[List[str]], timeout_seconds: int = 120) -> CIGateResult:
        """Try uv invocation first, then fall back to bare executable."""
        start = time.time()
        last_error = ""
        for cmd in cmd_candidates:
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(self.workspace_path),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout_seconds,
                    check=False,
                )
                duration = time.time() - start
                return CIGateResult(
                    name=cmd[0],
                    command=" ".join(cmd),
                    returncode=proc.returncode,
                    passed=(proc.returncode == 0),
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    duration_seconds=duration,
                )
            except FileNotFoundError:
                last_error = f"Binary {cmd[0]} not found."
                continue
            except Exception as exc:
                last_error = str(exc)
                break

        duration = time.time() - start
        return CIGateResult(
            name="CommandExecution",
            command=" ".join(cmd_candidates[0]),
            returncode=-1,
            passed=False,
            stdout="",
            stderr=last_error,
            duration_seconds=duration,
        )

    def verify(self) -> CIVerificationSummary:
        """Execute all CI verification gates sequentially."""
        results: List[CIGateResult] = []
        failures: List[FailureItem] = []
        all_passed = True

        import platform
        os_sys = platform.system().lower()
        family = "windows" if "win" in os_sys else "linux"
        env = EnvironmentInfo(
            os=f"local-{os_sys}",
            os_family=family,
            runtime="python",
            runtime_version=platform.python_version(),
        )

        for gate_name, primary_cmd, fallback_cmd in self.PIPELINE_GATES:
            res = self.run_command([primary_cmd, fallback_cmd])
            res.name = gate_name
            results.append(res)

            if not res.passed:
                all_passed = False
                output = f"{res.stdout}\n{res.stderr}".strip()
                cat, sev, blocking, desc = FailureClassifier.classify(
                    message=output or f"Gate {gate_name} failed with exit code {res.returncode}",
                    step_name=gate_name,
                    exit_code=res.returncode,
                )
                clean_norm = FailureNormalizer.normalize_text(output)
                fp = FailureNormalizer.compute_fingerprint(clean_norm)

                failures.append(
                    FailureItem(
                        id=f"local::{gate_name}",
                        provider="local",
                        workflow="local-ci-verify",
                        run_id="local",
                        job="local-runner",
                        step=gate_name,
                        environment=env,
                        category=cat,
                        severity=sev,
                        status="failure",
                        message=desc,
                        raw_evidence=output[:3000],
                        normalized_evidence=clean_norm[:2000],
                        fingerprint=fp,
                        blocking=blocking,
                    )
                )

        return CIVerificationSummary(
            all_passed=all_passed,
            gates=results,
            failures=failures,
        )
