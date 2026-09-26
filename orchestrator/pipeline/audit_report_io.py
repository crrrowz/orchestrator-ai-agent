"""Unified I/O utilities for locating, normalizing, and reading audit reports."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def locate_and_normalize_report(
    workspace_path: Path, filename: str = "AUDIT_REPORT.md"
) -> Optional[Path]:
    """Locate an audit report, migrating root-level report files to docs/ if found.

    Args:
        workspace_path: Root path of the target workspace.
        filename: Name of the report markdown file (e.g. AUDIT_REPORT.md or AUDIT_FIX_REPORT.md).

    Returns:
        The canonical Path under docs/ if found or migrated, otherwise None.
    """
    docs_dir = workspace_path / "docs"
    candidates = [filename, filename.lower(), filename.upper()]

    # 1. Check under docs/
    for name in candidates:
        cand_path = docs_dir / name
        if cand_path.exists() and cand_path.is_file():
            return cand_path

    # 2. Check at workspace root and migrate to docs/
    for name in candidates:
        root_cand = workspace_path / name
        if root_cand.exists() and root_cand.is_file():
            docs_dir.mkdir(parents=True, exist_ok=True)
            target = docs_dir / filename
            try:
                root_cand.replace(target)
                return target
            except OSError:
                return root_cand

    return None


def read_report(workspace_path: Path, filename: str = "AUDIT_REPORT.md") -> str:
    """Read the contents of an audit report, normalizing its location to docs/ if necessary.

    Returns:
        Stripped text content of the report file, or empty string if not found.
    """
    report_path = locate_and_normalize_report(workspace_path, filename=filename)
    if not report_path or not report_path.exists():
        return ""
    try:
        return report_path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def extract_audit_findings_list(report_content: str) -> List[Dict[str, Any]]:
    """Extract discrete actionable audit findings, sorted by severity (CRITICAL, HIGH, MEDIUM, LOW)."""
    if not report_content:
        return []

    severity_weights = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings: List[Dict[str, Any]] = []

    pattern = (
        r"###\s*(?:(?:(\d+(?:\.\d+)?|[A-Z]+-\d+|Issue\s*\d+)(?:\.|\:)?\s*)?\[(CRITICAL|HIGH|MEDIUM|LOW)\]|"
        r"\[(CRITICAL|HIGH|MEDIUM|LOW)\]\s*(?:(\d+(?:\.\d+)?|[A-Z]+-\d+|Issue\s*\d+)(?:\.|\:)?\s*)?)\s*"
        r"([^\n]+)([\s\S]*?)(?=\n###|\n##|\Z)"
    )
    for m in re.finditer(pattern, report_content, re.IGNORECASE):
        num1, sev1, sev2, num2, title, body = m.groups()
        sev = (sev1 or sev2 or "HIGH").upper()
        num = num1 or num2 or f"AUD-{len(findings) + 1:03d}"
        clean_title = title.strip()
        # Ignore sections indicating invariants or things NOT to break
        if any(
            skip in clean_title.lower() or skip in body[:150].lower()
            for skip in ["invariant", "do not break", "keep", "health score"]
        ):
            continue

        finding_text = f"### {num} [{sev}] {clean_title}\n{body.strip()}"
        findings.append(
            {
                "id": str(num),
                "severity": sev,
                "weight": severity_weights.get(sev, 99),
                "title": clean_title,
                "content": finding_text,
            }
        )

    if not findings:
        report_lower = report_content.lower()
        has_zero_findings = bool(
            re.search(
                r"\|\s*\*\*actionable findings total\*\*\s*\|\s*`0`\s*\|",
                report_lower,
            )
            or re.search(
                r"zero actionable (?:code )?defects? (?:detected|found)",
                report_lower,
            )
            or "0 actionable findings" in report_lower
            or "0 defects detected" in report_lower
        )

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

        if fallback_text and not has_zero_findings:
            clean_static = (
                "[clean]" in report_lower
                or "0 defects detected" in report_lower
                or "zero actionable code defects found" in report_lower
                or "clean (0 errors)" in report_lower
            )
            has_explicit_file = bool(
                re.search(r"[\w\-./\\]+\.(?:py|js|ts|json)", fallback_text)
            )
            generic_phrases = [
                "address any ast syntax failures and static linter warnings listed above",
                "address any ast syntax failures",
                "review file size hotspots",
                "zero syntax or linter defects",
                "clean architecture",
                "zero actionable code defects",
                "no pending remediation work items required",
                "codebase is in healthy state",
                "no remediation required",
                "no action required",
                "audit execution interrupted",
                "zero actionable code defects detected",
            ]
            is_generic_advice = any(
                gp in fallback_text.lower() for gp in generic_phrases
            )
            if (
                (
                    clean_static
                    and (is_generic_advice or not has_explicit_file)
                    and "###" not in fallback_text
                )
                or is_generic_advice
                or not has_explicit_file
            ):
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

    return ""
