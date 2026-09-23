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
        """Parse structured JSON verdict or fallback to legacy text markers."""
        if not text:
            return cls(approved=False, verdict="REJECTED", raw_text="")

        clean_text = text.strip()

        # 1. Look for ```json { ... } ``` code block
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", clean_text)
        raw_json = json_match.group(1) if json_match else None

        # 2. Look for bare JSON with "verdict" key
        if not raw_json:
            bare_match = re.search(r"(\{\s*\"verdict\"[\s\S]*?\})", clean_text)
            if bare_match:
                raw_json = bare_match.group(1)

        if raw_json:
            try:
                data = json.loads(raw_json)
                v_str = str(data.get("verdict", "")).strip().upper()
                is_approved = v_str == "APPROVED"
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
            except Exception:
                pass

        # 3. Fallback: text pattern matching
        upper_text = clean_text.upper()
        if "VERDICT: APPROVED" in upper_text or "VERDICT - APPROVED" in upper_text or '"VERDICT": "APPROVED"' in upper_text:
            return cls(approved=True, verdict="APPROVED", raw_text=clean_text)

        return cls(approved=False, verdict="REJECTED", raw_text=clean_text)
