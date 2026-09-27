"""Shadow AST Virtualizer and Anti-Stub Guard.

Specification: docs/plans/P13_FINAL_ORAGAI_TARGET_ARCHITECTURE_SPECIFICATION.md
Invariant 4: The Zero Stub Invariant.
"""

from __future__ import annotations

import ast
from typing import List, Tuple
from pathlib import Path


class ASTVirtualizer:
    """Pre-write AST compiler and anti-stub placeholder scanner."""

    FORBIDDEN_STUB_PATTERNS = ["# TODO", "raise NotImplementedError", "pass"]

    @staticmethod
    def validate_code_string(
        content: str, filename: str = "<string>"
    ) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        try:
            tree = ast.parse(content, filename=filename)
        except SyntaxError as e:
            return False, [f"SyntaxError: {e}"]

        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                    if node.exc.func.id == "NotImplementedError":
                        errors.append(
                            f"NotImplementedError stub detected at line {node.lineno}"
                        )
                elif isinstance(node.exc, ast.Name):
                    if node.exc.id == "NotImplementedError":
                        errors.append(
                            f"NotImplementedError stub detected at line {node.lineno}"
                        )

        for i, line in enumerate(content.splitlines(), start=1):
            if "# TODO" in line:
                errors.append(f"# TODO comment detected at line {i}")

        return len(errors) == 0, errors
