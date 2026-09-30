"""Failure Correlator: Cross-Job, Cross-Matrix, and Multi-Environment Analysis."""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple
from orchestrator.ci.models import CorrelationPattern, FailureCategory, FailureItem


class FailureCorrelator:
    """Discovers shared patterns, environmental skews, and common signatures across matrix runs."""

    @classmethod
    def correlate(
        cls,
        failures: List[FailureItem],
        all_jobs_meta: Optional[List[Dict[str, Any]]] = None,
    ) -> List[CorrelationPattern]:
        """Analyze collection of failures alongside job matrix metadata to uncover patterns."""
        if not failures:
            return []

        patterns: List[CorrelationPattern] = []

        # 1. Deduplicate & group by error fingerprint
        by_fingerprint: Dict[str, List[FailureItem]] = defaultdict(list)
        for f in failures:
            if f.fingerprint:
                by_fingerprint[f.fingerprint].append(f)

        for fp, items in by_fingerprint.items():
            if len(items) > 1:
                env_names = sorted(list({i.environment.display_name() for i in items}))
                patterns.append(
                    CorrelationPattern(
                        pattern_type="SAME_ERROR_SIGNATURE",
                        description=f"Identical error signature detected across {len(items)} jobs ({items[0].category.value}).",
                        affected_environments=env_names,
                        failure_ids=[i.id for i in items],
                        shared_signature=fp,
                        confidence=0.95,
                    )
                )

        # 2. Environmental matrix correlation (OS-specific and Python-version-specific)
        # Partition jobs into passed vs failed per OS and per runtime
        failed_blocking = [f for f in failures if f.blocking]
        if failed_blocking:
            failed_os: Set[str] = {f.environment.os_family for f in failed_blocking if f.environment.os_family != "unknown"}
            failed_runtimes: Set[str] = {f.environment.runtime_version for f in failed_blocking if f.environment.runtime_version != "unknown"}

            passed_os: Set[str] = set()
            passed_runtimes: Set[str] = set()

            if all_jobs_meta:
                for j in all_jobs_meta:
                    conclusion = str(j.get("conclusion") or j.get("status") or "").lower()
                    if conclusion in ("success", "passed"):
                        os_name = str(j.get("os", "")).lower()
                        family = "windows" if "win" in os_name else ("linux" if "ubuntu" in os_name or "linux" in os_name else "unknown")
                        ver = str(j.get("python-version") or j.get("python") or "")
                        if family != "unknown":
                            passed_os.add(family)
                        if ver:
                            passed_runtimes.add(ver)

            # Detect OS-specific pattern
            # If all failures are on Windows and Linux completely passed
            if failed_os and passed_os and failed_os.isdisjoint(passed_os):
                affected = [os_f.capitalize() for os_f in sorted(failed_os)]
                unaffected = [os_f.capitalize() for os_f in sorted(passed_os)]
                patterns.append(
                    CorrelationPattern(
                        pattern_type="OS_SPECIFIC",
                        description="OS-specific failure detected.",
                        affected_environments=affected,
                        unaffected_environments=unaffected,
                        failure_ids=[f.id for f in failed_blocking],
                        confidence=0.90,
                    )
                )

            # Detect Python-version-specific pattern
            if failed_runtimes and passed_runtimes and failed_runtimes.isdisjoint(passed_runtimes):
                affected = [f"Python {v}" for v in sorted(failed_runtimes)]
                unaffected = [f"Python {v}" for v in sorted(passed_runtimes)]
                patterns.append(
                    CorrelationPattern(
                        pattern_type="RUNTIME_SPECIFIC",
                        description="Python runtime version-specific failure detected.",
                        affected_environments=affected,
                        unaffected_environments=unaffected,
                        failure_ids=[f.id for f in failed_blocking],
                        confidence=0.85,
                    )
                )

        # 3. Step-specific correlation
        by_step: Dict[str, List[FailureItem]] = defaultdict(list)
        for f in failures:
            by_step[f.step].append(f)

        for step_name, items in by_step.items():
            if len(items) >= 2:
                patterns.append(
                    CorrelationPattern(
                        pattern_type="STEP_SPECIFIC",
                        description=f"Recurrent failure concentrated in workflow step '{step_name}'.",
                        affected_environments=[i.environment.display_name() for i in items],
                        failure_ids=[i.id for i in items],
                        confidence=0.80,
                    )
                )

        # 4. Secondary / Non-blocking co-occurrence (e.g. Cache failures alongside test failures)
        cache_fails = [f for f in failures if f.category == FailureCategory.CACHE_FAILURE]
        test_fails = [f for f in failures if f.category == FailureCategory.TEST_FAILURE]
        if cache_fails and test_fails:
            patterns.append(
                CorrelationPattern(
                    pattern_type="CO_OCCURRING_NON_BLOCKING",
                    description="Cache service failure co-occurred with test failure; cache failure is non-blocking.",
                    affected_environments=[f.environment.display_name() for f in cache_fails],
                    failure_ids=[f.id for f in cache_fails],
                    confidence=0.95,
                )
            )

        return patterns
