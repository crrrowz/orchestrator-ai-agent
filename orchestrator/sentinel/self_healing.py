"""Self-Healing Code Engine for AST error repair, import resolution, and fuzzy edits."""

import ast
import re
from pathlib import Path
from typing import Dict, Tuple

from orchestrator.sentinel.protocols import ISelfHealingEngine


class SelfHealingEngine(ISelfHealingEngine):
    """Provides automated zero-token code repairs for syntax, imports, and fuzzy edits."""

    COMMON_TYPE_SYMBOLS: Dict[str, str] = {
        "Tuple": "from typing import Tuple",
        "List": "from typing import List",
        "Dict": "from typing import Dict",
        "Optional": "from typing import Optional",
        "Any": "from typing import Any",
        "Union": "from typing import Union",
        "Callable": "from typing import Callable",
        "Sequence": "from typing import Sequence",
        "Set": "from typing import Set",
        "Literal": "from typing import Literal",
        "TYPE_CHECKING": "from typing import TYPE_CHECKING",
        "dataclass": "from dataclasses import dataclass",
        "field": "from dataclasses import field",
        "Path": "from pathlib import Path",
        "Enum": "from enum import Enum",
        "ABC": "from abc import ABC",
        "abstractmethod": "from abc import abstractmethod",
        "os": "import os",
        "sys": "import sys",
        "re": "import re",
        "time": "import time",
        "json": "import json",
        "shutil": "import shutil",
        "subprocess": "import subprocess",
        "threading": "import threading",
    }

    def heal_syntax_error(
        self, file_path: Path, raw_code: str, error_message: str
    ) -> Tuple[bool, str, str]:
        """Attempts to fix syntax or indentation errors."""
        try:
            ast.parse(raw_code, filename=str(file_path))
            return True, raw_code, "Code is already valid AST."
        except SyntaxError as e:
            syntax_err = e
        except Exception as ex:
            return False, raw_code, f"Non-syntax AST parse error: {ex}"

        lines = raw_code.splitlines(keepends=True)
        err_lineno = getattr(syntax_err, "lineno", None) or 1
        line_idx = max(0, min(err_lineno - 1, len(lines) - 1))
        target_line = lines[line_idx] if lines else ""

        # Case 1: Missing colon at end of block
        colon_match = re.match(
            r"^(\s*(?:def\s+\w+\s*\(.*?\)|class\s+\w+(?:\(.*?\))?|if\s+.+|elif\s+.+|else|for\s+.+\s+in\s+.+|while\s+.+|try|except(?:\s+.+)?|with\s+.+|finally))\s*$",
            target_line.rstrip(),
        )
        if colon_match:
            lines[line_idx] = colon_match.group(1) + ":\n"
            fixed_code = "".join(lines)
            try:
                ast.parse(fixed_code, filename=str(file_path))
                return (
                    True,
                    fixed_code,
                    f"Auto-injected missing colon at line {err_lineno}.",
                )
            except SyntaxError:
                pass

        # Case 2: Indentation error on empty block
        if "expected an indented block" in str(syntax_err).lower():
            # Try candidate header lines backwards from line_idx
            start_search = line_idx - 1 if line_idx > 0 else line_idx
            for candidate_idx in range(start_search, -1, -1):
                cand_line = lines[candidate_idx].strip()
                if cand_line.endswith(":") or re.match(
                    r"^\s*(?:def|class|if|elif|else|for|while|try|except|with|finally)\b",
                    cand_line,
                ):
                    header_line = lines[candidate_idx]
                    base_indent = len(header_line) - len(header_line.lstrip())
                    child_indent = " " * (base_indent + 4)
                    test_lines = list(lines)
                    test_lines.insert(candidate_idx + 1, f"{child_indent}pass\n")
                    fixed_code = "".join(test_lines)
                    try:
                        ast.parse(fixed_code, filename=str(file_path))
                        return (
                            True,
                            fixed_code,
                            f"Auto-inserted 'pass' block for empty indented block after line {candidate_idx + 1}.",
                        )
                    except SyntaxError:
                        continue

        # Case 3: Tabs to spaces
        if (
            "inconsistent use of tabs and spaces" in str(syntax_err).lower()
            or "\t" in raw_code
        ):
            tab_fixed_lines = [line_item.replace("\t", "    ") for line_item in lines]
            fixed_code = "".join(tab_fixed_lines)
            try:
                ast.parse(fixed_code, filename=str(file_path))
                return (
                    True,
                    fixed_code,
                    "Normalized inconsistent tabs to 4-space indentation across file.",
                )
            except SyntaxError:
                pass

        return (
            False,
            raw_code,
            f"Unresolved syntax anomaly at line {err_lineno}: {syntax_err.msg}",
        )

    def inject_missing_import(
        self, file_path: Path, raw_code: str, missing_symbol: str
    ) -> Tuple[bool, str, str]:
        """Injects known missing standard/typing imports at top of file."""
        symbol = missing_symbol.strip()
        import_stmt = self.COMMON_TYPE_SYMBOLS.get(symbol)
        if not import_stmt:
            return (
                False,
                raw_code,
                f"Symbol '{symbol}' not found in standard resolution map.",
            )

        if import_stmt in raw_code:
            return (
                True,
                raw_code,
                f"Import statement '{import_stmt}' is already present.",
            )

        lines = raw_code.splitlines(keepends=True)
        insert_idx = 0
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                    insert_idx = i + 1
                    break
                in_docstring = not in_docstring
                insert_idx = i + 1
                continue
            if in_docstring:
                insert_idx = i + 1
                continue
            if stripped.startswith("from __future__"):
                insert_idx = i + 1
                continue
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_idx = i
                break
            if stripped and not stripped.startswith("#"):
                insert_idx = i
                break

        lines.insert(insert_idx, f"{import_stmt}\n")
        updated_code = "".join(lines)
        return (
            True,
            updated_code,
            f"Injected missing import '{import_stmt}' at line {insert_idx + 1}.",
        )

    def fix_fuzzy_edit(
        self, original_text: str, target_text: str, replacement_text: str
    ) -> Tuple[bool, str, str]:
        """Performs whitespace and line-ending tolerant replacement in code."""
        if not target_text:
            return False, original_text, "Target text cannot be empty."

        if target_text in original_text:
            updated = original_text.replace(target_text, replacement_text, 1)
            return True, updated, "Applied exact match replacement."

        orig_lines = original_text.splitlines(keepends=True)
        target_lines = target_text.splitlines()

        if not target_lines:
            return False, original_text, "Empty target lines."

        target_len = len(target_lines)
        target_stripped = [item.strip() for item in target_lines if item.strip()]

        for i in range(len(orig_lines) - target_len + 1):
            window = orig_lines[i : i + target_len]
            window_stripped = [item.strip() for item in window if item.strip()]

            if window_stripped == target_stripped:
                first_line = window[0]
                base_indent = len(first_line) - len(first_line.lstrip())
                indent_str = " " * base_indent

                repl_lines = replacement_text.splitlines(keepends=True)
                adjusted_repl = []
                for idx, rline in enumerate(repl_lines):
                    if rline.strip() and not rline.startswith(" "):
                        adjusted_repl.append(f"{indent_str}{rline}")
                    else:
                        adjusted_repl.append(rline)

                if adjusted_repl and not adjusted_repl[-1].endswith("\n"):
                    adjusted_repl[-1] = adjusted_repl[-1] + "\n"

                updated_lines = (
                    orig_lines[:i] + adjusted_repl + orig_lines[i + target_len :]
                )
                return (
                    True,
                    "".join(updated_lines),
                    f"Applied fuzzy whitespace match across lines {i + 1}-{i + target_len}.",
                )

        return (
            False,
            original_text,
            "Target snippet not found even with fuzzy whitespace matching.",
        )
