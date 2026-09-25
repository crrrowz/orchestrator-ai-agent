"""Secret Sanitization, Security Verification, and Policy Filter Utilities.

Redacts credentials and high-entropy API keys from streams and enforces
sensitive filepath boundary protections.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Set

SENSITIVE_ENV_KEYWORDS: Set[str] = {
    "KEY",
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "AUTH",
    "CREDENTIAL",
    "ACCESS",
    "PRIVATE",
    "DATABASE_URL",
}

SENSITIVE_FILE_NAMES: Set[str] = {
    ".env",
    "id_rsa",
    "id_ed25519",
    "id_dsa",
    "id_ecdsa",
    "credentials.json",
    ".secret",
    ".token",
}

SENSITIVE_FILE_EXTENSIONS: Set[str] = {
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".pkcs12",
}

DISALLOWED_OPERATORS: Set[str] = {
    "&&",
    "||",
    ";",
    "&",
    "`",
    "$(",
    "invoke-expression",
    "iex",
    "start-process",
    "invoke-webrequest",
    "iwr",
    "curl",
    "wget",
}

APPROVED_ROOT_COMMANDS: Set[str] = {
    "pytest",
    "python",
    "py",
    "pip",
    "uv",
    "ruff",
    "mypy",
    "git",
    "graft",
    "get-content",
    "get-childitem",
    "type",
    "cat",
    "dir",
    "ls",
    "pwd",
    "cd",
    "new-item",
    "remove-item",
    "tree",
    "find",
    "findstr",
    "del",
    "copy",
    "move",
    "cls",
    "grep",
    "rm",
    "cp",
    "mv",
    "clear",
}

APPROVED_PIPELINE_CMDLETS: Set[str] = {
    "select-string",
    "select-object",
    "sort-object",
    "measure-object",
    "findstr",
    "grep",
    "head",
    "tail",
}

PROHIBITED_DEVICE_NAMES: Set[str] = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
    "CONIN$",
    "CONOUT$",
}


def sanitize_text_secrets(text: str) -> str:
    """Redact sensitive API keys, tokens, and credentials from observation text."""
    if not text:
        return ""

    sanitized = text

    # 1. Mask host environment secrets
    for k, v in os.environ.items():
        k_upper = k.upper()
        if any(keyword in k_upper for keyword in SENSITIVE_ENV_KEYWORDS):
            if v and len(v.strip()) >= 8:
                sanitized = sanitized.replace(v.strip(), f"[REDACTED_{k_upper}]")

    # 2. Mask standard LLM API key patterns
    sanitized = re.sub(r"sk-or-v1-[a-f0-9]{32,}", "[REDACTED_OPENROUTER_KEY]", sanitized)
    sanitized = re.sub(r"sk-ant-[a-zA-Z0-9_\-]{20,}", "[REDACTED_ANTHROPIC_KEY]", sanitized)
    sanitized = re.sub(r"sk-[a-zA-Z0-9_\-]{20,}", "[REDACTED_API_KEY]", sanitized)
    sanitized = re.sub(r"AIza[0-9A-Za-z\-_]{35}", "[REDACTED_GEMINI_KEY]", sanitized)
    sanitized = re.sub(
        r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+ PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
        sanitized,
    )
    return sanitized


def is_sensitive_filepath(path: Path) -> bool:
    """Detect if a path points to a sensitive credential or secret file."""
    name_lower = path.name.lower()
    if name_lower == ".env" or name_lower.startswith(".env.") or name_lower.startswith(".env"):
        return True
    if path.suffix.lower() in SENSITIVE_FILE_EXTENSIONS:
        return True
    if any(sub in name_lower for sub in ("id_rsa", "id_ed25519", "id_dsa", "id_ecdsa", "credentials.json", ".secret", ".token")):
        return True
    return False
