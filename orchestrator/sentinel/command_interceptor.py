"""Terminal command interception and platform-specific translation engine."""

import os
import re
from typing import Tuple


class TerminalCommandTranslator:
    """Safely inspects and rewrites terminal commands for Windows & Linux environments.

    Translates prohibited/incompatible UNIX shell utilities (like `grep`, `cat`,
    `head`, `tail`, `ls`, `touch`, `rm -rf`, `find -name`) into valid PowerShell / Python
    equivalents without failing the calling agent turn.
    """

    UNIX_TO_PWSH_TRANSLATIONS = [
        (
            r'^\s*grep\s+(?:-[a-zA-Z]+\s+)?["\']?([^"\']+)["\']?\s+(.*)$',
            r'Select-String -Pattern "\1" -Path \2',
        ),
        (
            r'^\s*grep\s+["\']?([^"\']+)["\']?$',
            r'Select-String -Pattern "\1"',
        ),
        (
            r'^\s*cat\s+([^\s|]+)\s*\|\s*grep\s+(?:-[a-zA-Z]+\s+)?["\']?([^"\']+)["\']?\s*$',
            r'Get-Content \1 | Select-String -Pattern "\2"',
        ),
        (
            r"^\s*cat\s+([^\s|]+)\s*\|\s*head(?:\s+-n\s*(\d+)|\s+-(\d+))?\s*$",
            r"Get-Content \1 | Select-Object -First \2\3",
        ),
        (
            r"^\s*cat\s+([^\s|]+)\s*\|\s*tail(?:\s+-n\s*(\d+)|\s+-(\d+))?\s*$",
            r"Get-Content \1 | Select-Object -Last \2\3",
        ),
        (
            r"^\s*cat\s+([^\s|]+)\s*$",
            r"Get-Content \1",
        ),
        (
            r"^\s*head(?:\s+-n\s*(\d+)|\s+-(\d+))\s+([^\s]+)\s*$",
            r"Get-Content \3 | Select-Object -First \1\2",
        ),
        (
            r"^\s*tail(?:\s+-n\s*(\d+)|\s+-(\d+))\s+([^\s]+)\s*$",
            r"Get-Content \3 | Select-Object -Last \1\2",
        ),
        (
            r"^\s*ls\s+-(?:la|al|l|a)\s*$",
            r"Get-ChildItem -Force",
        ),
        (
            r"^\s*ls\s+-(?:la|al|l|a)\s+([^\s]+)\s*$",
            r"Get-ChildItem -Force \1",
        ),
        (
            r"^\s*touch\s+([^\s]+)\s*$",
            r"New-Item -ItemType File -Force -Path \1",
        ),
        (
            r"^\s*rm\s+-(?:rf|fr|r)\s+([^\s]+)\s*$",
            r"Remove-Item -Recurse -Force -LiteralPath \1",
        ),
        (
            r"^\s*which\s+([^\s]+)\s*$",
            r"Get-Command \1",
        ),
        (
            r'^\s*find\s+\.?\s+-name\s+["\']?([^"\']+)["\']?\s*$',
            r'Get-ChildItem -Recurse -Filter "\1"',
        ),
    ]

    @classmethod
    def intercept_and_translate(
        cls, command: str, os_name: str = os.name
    ) -> Tuple[bool, str, str]:
        """Translates prohibited or platform-incompatible shell commands."""
        raw_cmd = command.strip()
        if not raw_cmd:
            return True, raw_cmd, "Empty command"

        is_windows = os_name == "nt" or os.name == "nt"

        if is_windows:
            for pattern, repl in cls.UNIX_TO_PWSH_TRANSLATIONS:
                if re.search(pattern, raw_cmd, flags=re.IGNORECASE):
                    translated = re.sub(pattern, repl, raw_cmd, flags=re.IGNORECASE)
                    translated = re.sub(r"-First\s*$", "-First 10", translated)
                    translated = re.sub(r"-Last\s*$", "-Last 10", translated)
                    return (
                        True,
                        translated,
                        f"Translated UNIX command '{raw_cmd}' to PowerShell equivalent '{translated}'.",
                    )

            if ">/dev/null" in raw_cmd or "> /dev/null" in raw_cmd:
                translated = re.sub(r">\s*/dev/null", "> $null", raw_cmd)
                translated = re.sub(r"2>&1", "", translated)
                return (
                    True,
                    translated,
                    "Replaced /dev/null with $null for Windows PowerShell.",
                )

        return True, raw_cmd, "Command validated and passed as-is."
