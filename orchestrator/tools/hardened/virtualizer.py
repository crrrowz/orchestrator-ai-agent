"""AST-Virtualized File Access Engine.

Provides hierarchical symbol outline extraction, line-bounded windowing,
lossless AST-anchored symbol reads, zero-stub enforcement, and atomic safe writes.
"""

from __future__ import annotations

import ast
import os
import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from orchestrator.tools.hardened.models import (
    SymbolOutlineNode,
    VirtualFileView,
)
from orchestrator.tools.hardened.security import (
    PROHIBITED_DEVICE_NAMES,
    is_sensitive_filepath,
    sanitize_text_secrets,
)

MAX_READ_LINES: int = 250
MAX_READ_CHARS: int = 12_000
MAX_APPENDS_PER_FILE: int = 5

# Global session append counters
_HARDENED_APPEND_COUNTS: Dict[str, int] = {}


def reset_hardened_append_counts() -> None:
    """Reset session append counters."""
    _HARDENED_APPEND_COUNTS.clear()


class WorkspaceFileVirtualizer:
    """High-performance AST-aware file access and virtualization engine."""

    def __init__(self, workspace_root: Path, disallow_stubs: bool = True) -> None:
        self.workspace_root = workspace_root.resolve()
        self.disallow_stubs = disallow_stubs

    def resolve_sandbox_path(self, relative_or_abs_path: str) -> Tuple[bool, Path, str]:
        """Resolve and strictly validate that path resides inside workspace root."""
        clean = (relative_or_abs_path or "").strip()
        if not clean:
            return False, self.workspace_root, "Security Access Denied: Path cannot be empty."

        # Check for reserved Windows device names
        for part in re.split(r"[/\\]+", clean):
            stem = part.split(".")[0].upper()
            if stem in PROHIBITED_DEVICE_NAMES:
                return (
                    False,
                    self.workspace_root,
                    f"Security Access Denied: Path '{clean}' contains reserved device name '{stem}'.",
                )

        clean = re.sub(r"^[/\\]*workspace[/\\]+", "", clean)
        raw = Path(clean)

        if raw.is_absolute() or clean.startswith("/") or clean.startswith("\\"):
            resolved = raw.resolve()
        else:
            resolved = (self.workspace_root / clean).resolve()

        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            return (
                False,
                resolved,
                f"Access denied: path '{relative_or_abs_path}' escapes workspace directory '{self.workspace_root}'.",
            )

        return True, resolved, ""

    def generate_outline(
        self, file_path: Path
    ) -> Tuple[Optional[str], Optional[Tuple[SymbolOutlineNode, ...]], Optional[str]]:
        """Extract hierarchical symbol outline of Python source file without full text read."""
        if not file_path.exists():
            return None, None, f"File '{file_path.name}' does not exist."

        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            return (
                None,
                None,
                f"Python SyntaxError in '{file_path.name}': {e.msg} at line {e.lineno}",
            )
        except Exception as e:
            return None, None, f"Failed to parse outline for '{file_path.name}': {str(e)}"

        lines = source.splitlines()
        total_lines = len(lines)
        module_doc = ast.get_docstring(tree) or "No module docstring."

        outline_nodes: List[SymbolOutlineNode] = []
        outline_text_lines: List[str] = [
            f"File Outline: {file_path.name} ({total_lines} total lines)",
            f'Module Docstring: "{module_doc.splitlines()[0] if module_doc else "None"}"',
            "",
        ]

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods: List[SymbolOutlineNode] = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        fn_type = (
                            "async_function"
                            if isinstance(item, ast.AsyncFunctionDef)
                            else "method"
                        )
                        doc = ast.get_docstring(item)
                        doc_summary = doc.splitlines()[0] if doc else None
                        args = [arg.arg for arg in item.args.args]
                        sig = f"{item.name}({', '.join(args)})"
                        methods.append(
                            SymbolOutlineNode(
                                name=item.name,
                                symbol_type=fn_type,
                                start_line=item.lineno,
                                end_line=getattr(item, "end_lineno", item.lineno),
                                signature=sig,
                                docstring_summary=doc_summary,
                            )
                        )
                cls_doc = ast.get_docstring(node)
                cls_summary = cls_doc.splitlines()[0] if cls_doc else None
                cls_node = SymbolOutlineNode(
                    name=node.name,
                    symbol_type="class",
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    signature=f"class {node.name}",
                    docstring_summary=cls_summary,
                    children=tuple(methods),
                )
                outline_nodes.append(cls_node)
                outline_text_lines.append(
                    f"Class: {node.name} (Lines {cls_node.start_line}-{cls_node.end_line})"
                )
                if cls_summary:
                    outline_text_lines.append(f'  Docstring: "{cls_summary}"')
                for m in methods:
                    outline_text_lines.append(
                        f"  • {m.signature} (Lines {m.start_line}-{m.end_line})"
                    )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_type = (
                    "async_function"
                    if isinstance(node, ast.AsyncFunctionDef)
                    else "function"
                )
                doc = ast.get_docstring(node)
                doc_summary = doc.splitlines()[0] if doc else None
                args = [arg.arg for arg in node.args.args]
                sig = f"{node.name}({', '.join(args)})"
                fn_node = SymbolOutlineNode(
                    name=node.name,
                    symbol_type=fn_type,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    signature=sig,
                    docstring_summary=doc_summary,
                )
                outline_nodes.append(fn_node)
                outline_text_lines.append(
                    f"Function: {sig} (Lines {fn_node.start_line}-{fn_node.end_line})"
                )

        return "\n".join(outline_text_lines), tuple(outline_nodes), None

    def read_windowed(
        self,
        file_path: Path,
        offset_line: int = 1,
        limit_lines: int = 150,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> Tuple[Optional[VirtualFileView], Optional[str]]:
        """Read deterministic line-bounded window with line numbers and pagination hints."""
        if not file_path.exists():
            return None, f"File '{file_path.name}' does not exist."

        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return None, f"Failed to read '{file_path.name}': {str(e)}"

        raw_lines = source.splitlines()
        total_lines = len(raw_lines)

        # If file is small, no offset/limit override, and no start/end lines given -> return clean unannotated content
        if (
            start_line is None
            and end_line is None
            and offset_line == 1
            and total_lines <= MAX_READ_LINES
            and limit_lines >= total_lines
            and len(source) <= MAX_READ_CHARS
        ):
            view = VirtualFileView(
                file_path=file_path.as_posix(),
                total_lines=total_lines,
                offset_line=1,
                limit_lines=total_lines,
                content=sanitize_text_secrets(source),
                has_more_above=False,
                has_more_below=False,
                next_offset=None,
            )
            return view, None

        # Handle explicit start_line / end_line if passed
        if start_line is not None or end_line is not None:
            actual_start = max(1, start_line or 1)
            actual_end = min(total_lines, end_line if end_line is not None else total_lines)
            start_idx = max(0, actual_start - 1)
            end_idx = max(start_idx, min(total_lines, actual_end))
            limit_lines = max(1, end_idx - start_idx)
        else:
            start_idx = max(0, offset_line - 1)
            effective_limit = min(limit_lines, MAX_READ_LINES)
            end_idx = min(total_lines, start_idx + effective_limit)

        annotated_lines: List[str] = []
        char_count = 0
        clamped_by_budget = False
        actual_end_idx = start_idx

        for idx in range(start_idx, end_idx):
            line_str = f"{idx + 1:4d}: {raw_lines[idx]}"
            line_len = len(line_str) + 1
            if char_count + line_len > MAX_READ_CHARS and (idx > start_idx):
                clamped_by_budget = True
                break
            annotated_lines.append(line_str)
            char_count += line_len
            actual_end_idx = idx + 1

        has_more_above = start_idx > 0
        has_more_below = actual_end_idx < total_lines
        next_offset = (actual_end_idx + 1) if has_more_below else None

        rendered_text = "\n".join(annotated_lines)
        if total_lines > MAX_READ_LINES and not (start_line is not None and end_line is not None):
            rendered_text += (
                f"\n\n[Governance Notice: Showing lines {start_idx + 1}-{actual_end_idx} of {total_lines} total lines. "
                f"To read further, call operation='read' with start_line={actual_end_idx + 1} or offset_line={actual_end_idx + 1}.]"
            )
        elif has_more_below:
            rendered_text += (
                f"\n\n[Pagination: Showing lines {start_idx + 1}-{actual_end_idx} of {total_lines}. "
                f"Use offset_line={next_offset} to view subsequent lines.]"
            )

        if clamped_by_budget:
            rendered_text += (
                f"\n\n[Governance Notice: Read clamped by character budget (~{MAX_READ_CHARS} chars / ~3,000 tokens safe input ceiling). "
                f"Narrow scope with start_line and end_line parameters or operation='symbol'.]"
            )

        view = VirtualFileView(
            file_path=file_path.as_posix(),
            total_lines=total_lines,
            offset_line=start_idx + 1,
            limit_lines=limit_lines,
            content=sanitize_text_secrets(rendered_text),
            has_more_above=has_more_above,
            has_more_below=has_more_below,
            next_offset=next_offset,
        )
        return view, None

    def read_ast_symbol(
        self, file_path: Path, symbol_name: str
    ) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[str]]:
        """Extract lossless full implementation of a class or method by qualified name."""
        if not file_path.exists():
            return None, None, None, f"File '{file_path.name}' does not exist."

        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(file_path))
        except Exception as e:
            return None, None, None, f"AST parse error in '{file_path.name}': {str(e)}"

        lines = source.splitlines(keepends=True)
        target = symbol_name.strip()
        match_node: Optional[ast.AST] = None
        all_symbols: List[str] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                all_symbols.append(node.name)

        if "." in target:
            cls_name, m_name = target.split(".", 1)
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name == cls_name:
                    for sub in node.body:
                        if (
                            isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and sub.name == m_name
                        ):
                            match_node = sub
                            break
        else:
            for node in tree.body:
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    and node.name == target
                ):
                    match_node = node
                    break

        if not match_node:
            avail_str = ", ".join(all_symbols[:15]) if all_symbols else "None"
            return (
                None,
                None,
                None,
                f"Symbol '{symbol_name}' not found in '{file_path.name}'. Available symbols: {avail_str}",
            )

        start_ln = getattr(match_node, "lineno", 1)
        end_ln = getattr(match_node, "end_lineno", len(lines))

        extracted_lines = lines[start_ln - 1 : end_ln]
        annotated = [
            f"{start_ln + idx:4d}: {line.rstrip()}"
            for idx, line in enumerate(extracted_lines)
        ]
        annotated_content = "\n".join(annotated)

        if len(annotated_content) > MAX_READ_CHARS:
            cut_point = annotated_content.rfind("\n", 0, MAX_READ_CHARS)
            if cut_point < MAX_READ_CHARS // 2:
                cut_point = MAX_READ_CHARS
            annotated_content = (
                annotated_content[:cut_point]
                + f"\n\n[Governance Notice: Symbol output clamped at {MAX_READ_CHARS} chars to protect token budget.]"
            )

        return sanitize_text_secrets(annotated_content), start_ln, end_ln, None

    def _check_anti_stub_violations(
        self, tree: ast.AST, file_path: Path, content: str
    ) -> Optional[str]:
        """Detect prohibited empty stubs (pass, ..., NotImplementedError, # TODO, # FIXME)."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 1. Inspect function statements
                non_doc_stmts = [
                    stmt
                    for stmt in node.body
                    if not (
                        isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Constant)
                        and isinstance(stmt.value.value, str)
                    )
                ]
                if len(non_doc_stmts) == 1:
                    stmt = non_doc_stmts[0]
                    # Check pass
                    if isinstance(stmt, ast.Pass):
                        return f"Prohibited empty stub in {file_path.name}: function '{node.name}' has body 'pass'"
                    # Check Ellipsis ...
                    if (
                        isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Constant)
                        and stmt.value.value is Ellipsis
                    ):
                        return f"Prohibited empty stub in {file_path.name}: function '{node.name}' has body '...'"
                    # Check raise NotImplementedError
                    if isinstance(stmt, ast.Raise):
                        exc = stmt.exc
                        if (isinstance(exc, ast.Name) and exc.id == "NotImplementedError") or (
                            isinstance(exc, ast.Call)
                            and isinstance(exc.func, ast.Name)
                            and exc.func.id == "NotImplementedError"
                        ):
                            return f"Prohibited empty stub in {file_path.name}: function '{node.name}' raises NotImplementedError"

        # 2. Check for explicit TODO / FIXME comments in code if disallow_stubs is active
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                if "TODO" in stripped.upper() or "FIXME" in stripped.upper():
                    return f"Prohibited stub comment in {file_path.name} at line {idx + 1}: '{stripped}'"

        return None

    def _heal_missing_imports(self, tree: ast.AST, content: str) -> Tuple[str, Optional[str]]:
        """Auto-heal standard library imports using ASTGuard."""
        try:
            from orchestrator.sentinel.ast_guard import ASTGuard

            guard = ASTGuard()
            _, _, healed = guard.intercept_ast(Path("temp.py"), content)
            if healed and healed != content:
                return healed, "Auto-healed missing imports"
        except Exception:
            pass
        return content, None

    def atomic_safe_write(
        self, file_path: Path, content: str, disallow_stubs: Optional[bool] = None
    ) -> Tuple[bool, str]:
        """Atomically write file with AST syntax validation pre-commit and anti-stub check."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        should_check_stubs = self.disallow_stubs if disallow_stubs is None else disallow_stubs

        content_to_write = content

        if file_path.suffix == ".py":
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                return (
                    False,
                    f"AST Integrity Violation: SyntaxError in {file_path.name}: {e.msg} (line {e.lineno})",
                )

            if should_check_stubs:
                stub_err = self._check_anti_stub_violations(tree, file_path, content)
                if stub_err:
                    return False, f"AST Integrity Violation: {stub_err}"

            # Auto-heal missing imports
            healed, _ = self._heal_missing_imports(tree, content)
            if healed:
                content_to_write = healed

        tmp_path = file_path.parent / f".{file_path.name}.tmp_{uuid.uuid4().hex[:8]}"
        try:
            tmp_path.write_text(content_to_write, encoding="utf-8")
            os.replace(tmp_path, file_path)
            return True, f"File '{file_path.name}' written successfully ({len(content_to_write)} chars)."
        except Exception as e:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            return False, f"Atomic Write Error for '{file_path.name}': {str(e)}"

    def atomic_patch(
        self,
        file_path: Path,
        target_text: str,
        replacement_text: str,
        disallow_stubs: Optional[bool] = None,
    ) -> Tuple[bool, str]:
        """Perform exact match or scope-indent fuzzy line replacement with AST syntax check."""
        if not file_path.exists():
            return False, f"File '{file_path.name}' not found for editing."

        if not target_text:
            return False, "Missing 'target_text' required for editing."

        existing_content = file_path.read_text(encoding="utf-8", errors="replace")
        new_content: Optional[str] = None

        if target_text in existing_content:
            new_content = existing_content.replace(target_text, replacement_text, 1)
        else:
            # Try fuzzy replacement via SelfHealingEngine
            try:
                from orchestrator.sentinel.self_healing import SelfHealingEngine

                healer = SelfHealingEngine()
                success, healed_text, _ = healer.fix_fuzzy_edit(
                    existing_content, target_text, replacement_text
                )
                if success:
                    new_content = healed_text
            except Exception:
                pass

        if new_content is None:
            return False, f"Target text segment not found in '{file_path.name}'."

        return self.atomic_safe_write(file_path, new_content, disallow_stubs=disallow_stubs)

    def append(self, file_path: Path, content: str) -> Tuple[bool, str]:
        """Append to an existing file enforcing non-existent guard and MAX_APPENDS_PER_FILE limit."""
        if not file_path.exists():
            return (
                False,
                f"Append guard: Cannot append to non-existent file '{file_path.name}'. "
                "Use operation='write' to initialize the file first.",
            )

        key = str(file_path.resolve())
        current_appends = _HARDENED_APPEND_COUNTS.get(key, 0)
        if current_appends >= MAX_APPENDS_PER_FILE:
            return (
                False,
                f"Append guard: Maximum append limit ({MAX_APPENDS_PER_FILE} appends) reached for '{file_path.name}'. "
                "Use operation='edit' with target_text or overwrite with 'write'.",
            )

        _HARDENED_APPEND_COUNTS[key] = current_appends + 1
        content_to_append = content or ""
        try:
            with file_path.open("a", encoding="utf-8") as f:
                f.write(content_to_append)
            return (
                True,
                f"File '{file_path.name}' appended successfully "
                f"({len(content_to_append)} chars added, append {current_appends + 1}/{MAX_APPENDS_PER_FILE}).",
            )
        except Exception as e:
            return False, f"Append Error for '{file_path.name}': {str(e)}"

    def delete(self, file_path: Path) -> Tuple[bool, str]:
        """Safely delete file within sandbox."""
        if not file_path.exists():
            return False, f"File '{file_path.name}' does not exist."
        try:
            file_path.unlink()
            return True, f"File '{file_path.name}' deleted successfully."
        except Exception as e:
            return False, f"Delete error: {str(e)}"

    def list_dir(self, dir_path: Path) -> Tuple[bool, List[str], str]:
        """List directory contents, pruning .git, node_modules, and cache directories."""
        if not dir_path.exists():
            return False, [], f"Directory '{dir_path.name}' does not exist."

        results: List[str] = []
        ignored_names = {
            ".git",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".venv",
            "venv",
            ".mypy_cache",
            ".ruff_cache",
        }

        try:
            for root, dirs, files in os.walk(dir_path):
                # Prune ignored directories in place
                dirs[:] = [d for d in dirs if d not in ignored_names]
                for file_name in files:
                    full_p = Path(root) / file_name
                    try:
                        rel_p = full_p.relative_to(self.workspace_root).as_posix()
                        results.append(rel_p)
                    except ValueError:
                        continue
            return True, sorted(results), f"Found {len(results)} files."
        except Exception as e:
            return False, [], f"List directory error: {str(e)}"
