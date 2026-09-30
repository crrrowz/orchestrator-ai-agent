"""Log Normalizer, Secret Redactor, and Evidence Deduplicator."""

import hashlib
import re
from typing import List, Tuple


class FailureNormalizer:
    """Sanitizes raw log traces by redacting credentials and stripping volatile run-specific noise."""

    # 1. Secret patterns for automated redaction
    SECRET_PATTERNS = [
        (re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,255}"), "[REDACTED_GITHUB_TOKEN]"),
        (re.compile(r"(?:bearer|token|authorization)\s*[:=]\s*[A-Za-z0-9_\-\.]{20,}", re.IGNORECASE), "Authorization: [REDACTED_TOKEN]"),
        (re.compile(r"AIza[0-9A-Za-z-_]{35}"), "[REDACTED_GOOGLE_API_KEY]"),
        (re.compile(r"sk-[A-Za-z0-9_-]{32,}"), "[REDACTED_API_KEY]"),
        (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
        (re.compile(r"(?:password|secret|key)\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE), "secret: [REDACTED]"),
    ]

    # 2. Dynamic noise patterns (timestamps, UUIDs, temporary paths, runner directories)
    NOISE_PATTERNS = [
        # ISO-8601 timestamps (e.g. 2026-09-30T10:01:58.123456Z or 2026-09-30 10:01:58)
        (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"), "<TIMESTAMP>"),
        # Hex memory addresses (e.g. 0x00007ff812ab34cd or 0x7f9a12bc)
        (re.compile(r"\b0x[0-9a-fA-F]{6,16}\b"), "<MEM_ADDR>"),
        # UUIDs / GUIDs
        (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "<UUID>"),
        # GitHub Actions runner temporary directories (Linux & Windows)
        (re.compile(r"/home/runner/work/[^/\s]+/[^/\s]+"), "<RUNNER_WORKDIR>"),
        (re.compile(r"[A-Za-z]:[\\/]a[\\/][^\\/\s]+[\\/][^\\/\s]+"), "<RUNNER_WORKDIR>"),
        # Temp directories
        (re.compile(r"/tmp/[a-zA-Z0-9_\-]+"), "<TMP_DIR>"),
        (re.compile(r"[A-Za-z]:\\Users\\[^\\]+\\AppData\\Local\\Temp\\[a-zA-Z0-9_\-]+", re.IGNORECASE), "<TMP_DIR>"),
        # HTTP Request IDs
        (re.compile(r"(?:request-id|x-request-id|ray-id|req-id)\s*[:=]\s*[a-zA-Z0-9_\-]+", re.IGNORECASE), "request-id: <REQUEST_ID>"),
    ]

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        """Sanitize secrets, access keys, and authorization headers from text."""
        if not text:
            return ""
        sanitized = text
        for pattern, replacement in cls.SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Strip dynamic timestamps, runner paths, memory addresses, and volatile tokens."""
        if not text:
            return ""
        cleaned = cls.redact_secrets(text)
        for pattern, replacement in cls.NOISE_PATTERNS:
            cleaned = pattern.sub(replacement, cleaned)
        # Normalize Windows vs Linux backslashes in paths
        cleaned = re.sub(r"\\+", "/", cleaned)
        # Normalize multiple spaces / tabs
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        return cleaned.strip()

    @classmethod
    def compute_fingerprint(cls, text: str) -> str:
        """Calculate a deterministic hash signature from normalized text for deduplication."""
        normalized = cls.normalize_text(text)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def deduplicate_lines(cls, lines: List[str], max_sample_chars: int = 2000) -> List[Tuple[str, int]]:
        """Deduplicate repeated lines or errors, returning list of (normalized_message, count)."""
        counts: dict[str, int] = {}
        order: list[str] = []

        for line in lines:
            normalized = cls.normalize_text(line)
            if not normalized:
                continue
            if normalized not in counts:
                counts[normalized] = 0
                order.append(normalized)
            counts[normalized] += 1

        results = [(item[:max_sample_chars], counts[item]) for item in order]
        return results
