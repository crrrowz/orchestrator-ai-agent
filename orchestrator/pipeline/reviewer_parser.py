"""Structured Output Parser for Reviewer Agent Verdicts."""

import json
import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class ReviewerVerdict:
    approved: bool
    verdict: str  # "APPROVED" or "REJECTED"
    reasoning: List[str] = field(default_factory=list)
    required_fixes: List[str] = field(default_factory=list)
    raw_text: str = ""

    @classmethod
    def parse(cls, text: str) -> "ReviewerVerdict":
        """Parse structured JSON verdict or fallback to fuzzy semantic recovery."""
        if not text:
            return cls(approved=False, verdict="REJECTED", raw_text="")

        clean_text = text.strip()

        # 1. Look for ```json { ... } ``` code block
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", clean_text)
        raw_json = json_match.group(1) if json_match else None

        # 2. Look for bare JSON with "verdict" or 'verdict' key
        if not raw_json:
            bare_match = re.search(r"(\{\s*[\"']?verdict[\"']?[\s\S]*?\})", clean_text)
            if bare_match:
                raw_json = bare_match.group(1)

        if raw_json:
            # First attempt: safe Python literal_eval for single quotes & trailing commas
            data = None
            try:
                import ast
                evaluated = ast.literal_eval(raw_json)
                if isinstance(evaluated, dict):
                    data = evaluated
            except Exception:
                pass

            if data is None:
                # Normalize trailing commas and single quotes for json.loads
                normalized_json = re.sub(r",\s*([\]}])", r"\1", raw_json)
                normalized_json = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", r'"\1"', normalized_json)
                try:
                    data = json.loads(normalized_json)
                except Exception:
                    pass

            if data and isinstance(data, dict):
                v_str = str(data.get("verdict", "")).strip().upper()
                is_approved = v_str in ("APPROVED", "APPROVE", "PASSED", "PASS", "LGTM")
                reasons = data.get("reasoning", [])
                if isinstance(reasons, str):
                    reasons = [reasons]
                fixes = data.get("required_fixes", [])
                if isinstance(fixes, str):
                    fixes = [fixes]
                return cls(
                    approved=is_approved,
                    verdict="APPROVED" if is_approved else "REJECTED",
                    reasoning=list(reasons),
                    required_fixes=list(fixes),
                    raw_text=clean_text,
                )

        # 3. Fallback: robust regex and semantic pattern matching
        upper_text = clean_text.upper()
        approval_markers = [
            r"VERDICT[\s:\-]+APPROVED",
            r'"VERDICT"\s*:\s*"APPROVED"',
            r'\'VERDICT\'\s*:\s*\'APPROVED\'',
            r"STATUS[\s:\-]+APPROVED",
            r"DECISION[\s:\-]+APPROVED",
            r"###\s*VERDICT:\s*APPROVED",
            r"\*\*VERDICT\*\*:\s*APPROVED",
        ]
        if any(re.search(marker, upper_text) for marker in approval_markers):
            return cls(approved=True, verdict="APPROVED", raw_text=clean_text)

        return cls(approved=False, verdict="REJECTED", raw_text=clean_text)
