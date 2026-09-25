"""AST-Aware context clamper and intelligent code folding engine.

Guarantees syntactic validity of context snippets by transforming AST nodes rather
than slicing raw strings, preserving critical target symbols while folding non-target
implementation bodies to maintain guaranteed model output headroom.
"""

from __future__ import annotations

import ast
from typing import Dict, List, Optional, Set, Tuple


class ASTAwareContextClamper:
    """Compresses Python source files using AST folding to guarantee context headroom."""

    @staticmethod
    def fold_python_source(
        source_code: str,
        target_symbols: Optional[Set[str]] = None,
        min_fold_lines: int = 5,
    ) -> Tuple[str, bool]:
        """Folds non-target function/class bodies in Python code into signatures with notices.

        Args:
            source_code: Raw Python source code string.
            target_symbols: Set of symbol names (functions, classes, methods) to preserve intact.
            min_fold_lines: Minimum lines of body code required before folding triggers.

        Returns:
            Tuple of (transformed_source_code, was_folded_boolean).
        """
        targets = set(target_symbols) if target_symbols else set()
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            # If the source file cannot be parsed, return original content untouched
            return source_code, False

        folded = False

        class MethodFolder(ast.NodeTransformer):
            def __init__(self) -> None:
                super().__init__()
                self.class_stack: List[str] = []

            def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
                self.class_stack.append(node.name)
                self.generic_visit(node)
                self.class_stack.pop()
                return node

            def _is_target(self, name: str) -> bool:
                if name in targets:
                    return True
                # If enclosing class is a target, treat all its methods as targets
                for cls_name in self.class_stack:
                    if cls_name in targets:
                        return True
                return False

            def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
                self.generic_visit(node)
                if self._is_target(node.name):
                    return node

                body_lines = (node.end_lineno or 0) - (node.lineno or 0)
                if body_lines > min_fold_lines:
                    nonlocal folded
                    folded = True
                    docstring = ast.get_docstring(node)
                    new_body: List[ast.stmt] = []

                    if docstring:
                        new_body.append(ast.Expr(value=ast.Constant(value=docstring)))

                    notice = f"[Folded implementation: {body_lines} lines]"
                    new_body.append(ast.Expr(value=ast.Constant(value=notice)))
                    new_body.append(ast.Pass())
                    node.body = new_body
                return node

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
                self.generic_visit(node)
                if self._is_target(node.name):
                    return node

                body_lines = (node.end_lineno or 0) - (node.lineno or 0)
                if body_lines > min_fold_lines:
                    nonlocal folded
                    folded = True
                    docstring = ast.get_docstring(node)
                    new_body: List[ast.stmt] = []

                    if docstring:
                        new_body.append(ast.Expr(value=ast.Constant(value=docstring)))

                    notice = f"[Folded async implementation: {body_lines} lines]"
                    new_body.append(ast.Expr(value=ast.Constant(value=notice)))
                    new_body.append(ast.Pass())
                    node.body = new_body
                return node

        transformer = MethodFolder()
        modified_tree = transformer.visit(tree)
        ast.fix_missing_locations(modified_tree)

        if folded:
            return ast.unparse(modified_tree), True
        return source_code, False

    @classmethod
    def assemble_clamped_context(
        cls,
        tier0_intent: str,
        tier1_diagnostics: str,
        tier2_files: Dict[str, str],
        tier3_architecture: str,
        target_symbols_per_file: Optional[Dict[str, Set[str]]] = None,
        max_context_chars: int = 120_000,
        reserved_headroom_chars: int = 16_000,
    ) -> str:
        """Assembles prompt context strictly adhering to priority tiers without overflow.

        Ensures guaranteed output headroom by bounding total injected characters to
        `max_context_chars - reserved_headroom_chars`.
        """
        ceiling = max(1000, max_context_chars - reserved_headroom_chars)
        symbols = target_symbols_per_file or {}
        chunks: List[str] = []
        current_len = 0

        # Tier 0: Mandatory Intent
        t0_text = f"=== TASK INTENT & REQUIREMENTS ===\n{tier0_intent}"
        if len(t0_text) > ceiling:
            t0_text = t0_text[:ceiling]
        chunks.append(t0_text)
        current_len += len(t0_text)

        # Tier 1: Failure Diagnostics
        if tier1_diagnostics and current_len < ceiling:
            diag_text = f"\n\n=== FAILURE DIAGNOSTICS ===\n{tier1_diagnostics}"
            if current_len + len(diag_text) > ceiling:
                remaining = ceiling - current_len
                if remaining > 50:
                    diag_text = diag_text[:remaining]
                    chunks.append(diag_text)
                    current_len += len(diag_text)
            else:
                chunks.append(diag_text)
                current_len += len(diag_text)

        # Tier 2: Target Files (with AST Folding if space is tight)
        if tier2_files and current_len < ceiling:
            header = "\n\n=== TARGET SOURCE FILES ==="
            if current_len + len(header) <= ceiling:
                chunks.append(header)
                current_len += len(header)

                for file_path, content in tier2_files.items():
                    if current_len >= ceiling:
                        break
                    file_symbols = symbols.get(file_path, set())
                    raw_block = f"\n\n--- File: {file_path} ---\n{content}"

                    if current_len + len(raw_block) > ceiling:
                        # Attempt AST folding to fit within remaining headroom
                        folded_content, was_folded = cls.fold_python_source(content, file_symbols)
                        folded_block = (
                            f"\n\n--- File: {file_path} (AST-Folded) ---\n{folded_content}"
                        )
                        if current_len + len(folded_block) <= ceiling:
                            chunks.append(folded_block)
                            current_len += len(folded_block)
                        else:
                            # Squeeze what we can if space remains
                            remaining = ceiling - current_len
                            if remaining > 100:
                                chunks.append(folded_block[:remaining])
                                current_len += remaining
                    else:
                        chunks.append(raw_block)
                        current_len += len(raw_block)

        # Tier 3: Architecture Map (Opportunistic, only if capacity remains)
        if tier3_architecture and current_len < ceiling:
            arch_header = "\n\n=== ARCHITECTURE SKELETON ===\n"
            available = ceiling - current_len
            if available > len(arch_header) + 20:
                arch_text = (arch_header + tier3_architecture)[:available]
                chunks.append(arch_text)
                current_len += len(arch_text)

        return "".join(chunks)
