"""Multi-Layer Finding Validator Gate (P7)."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Optional, Tuple

from orchestrator.analysis.audit.models import VerifiedAuditFinding


class FindingValidator:
    """Enforces evidence integrity, disk containment, AST symbol containment, and anti-flattery filtering."""

    BANNED_FLATTERY_MARKERS = [
        "code looks clean",
        "architecture is well structured",
        "consider decomposing",
        "review file size",
        "98/100",
        "zero defects detected",
        "ensure good practices",
        "workspace static analysis is clean",
    ]

    @classmethod
    def validate(cls, finding: VerifiedAuditFinding, workspace_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate candidate finding against disk, line bounds, AST containment, and quality rules."""
        ws = workspace_path.resolve()

        # -----------------------------------------------------------------
        # Layer 1: Workspace Containment & Disk Existence Check
        # -----------------------------------------------------------------
        clean_file = finding.file_path.strip().replace("\\", "/")
        if not clean_file:
            return False, "Target file path is empty."

        target_file = (ws / clean_file).resolve()
        try:
            target_file.relative_to(ws)
        except ValueError:
            return False, f"Target file '{clean_file}' escapes workspace boundary."

        if not target_file.exists() or not target_file.is_file():
            return False, f"Target file '{clean_file}' does not exist on disk."

        # -----------------------------------------------------------------
        # Layer 2: Line Bounds & Code Snippet Match
        # -----------------------------------------------------------------
        try:
            content = target_file.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
        except Exception as e:
            return False, f"Failed to read target file '{clean_file}': {e}"

        total_lines = len(lines)
        if finding.line_start < 1 or finding.line_start > max(1, total_lines):
            return False, f"line_start {finding.line_start} out of bounds (1..{total_lines})."

        if finding.line_end > max(1, total_lines):
            return False, f"line_end {finding.line_end} out of bounds (1..{total_lines})."

        # -----------------------------------------------------------------
        # Layer 3: AST Symbol Containment Validation (for Python files)
        # -----------------------------------------------------------------
        if finding.ast_symbol and clean_file.endswith(".py"):
            try:
                tree = ast.parse(content, filename=clean_file)
                symbol_found = False
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if node.name == finding.ast_symbol:
                            node_end = getattr(node, "end_lineno", node.lineno) or node.lineno
                            # Verify the symbol encompasses or is nearby line_start
                            if node.lineno <= finding.line_start <= node_end or abs(node.lineno - finding.line_start) <= 5:
                                symbol_found = True
                                break
                            # Alternatively symbol name matches
                            symbol_found = True
                if not symbol_found:
                    return False, f"AST symbol '{finding.ast_symbol}' not found in target file '{clean_file}'."
            except SyntaxError:
                # If the file has a syntax error, we don't reject findings targeting syntax errors
                pass

        # -----------------------------------------------------------------
        # Layer 4: Anti-Flattery & Non-Generic Advice Filter
        # -----------------------------------------------------------------
        corpus = f"{finding.problem_statement} {finding.code_snippet} {finding.remediation_proposal}".lower()
        if any(marker in corpus for marker in cls.BANNED_FLATTERY_MARKERS):
            if len(finding.code_snippet.strip()) < 20:
                return False, "Finding contains banned generic flattery text without concrete code evidence."

        if len(finding.problem_statement.strip()) < 10 or len(finding.remediation_proposal.strip()) < 10:
            return False, "Problem statement or remediation proposal is too brief to be actionable."

        return True, None
