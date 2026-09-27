"""AST-Virtualized File Access Engine.

Provides hierarchical symbol outline extraction, line-bounded windowing,
lossless AST-anchored symbol reads, zero-stub enforcement, and atomic safe writes.
"""

from __future__ import annotations

import ast
import os
import py_compile
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


def _format_function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Format parameter signature of function or method."""
    args: List[str] = []
    for arg in node.args.args:
        ann = ""
        if arg.annotation:
            try:
                ann = f": {ast.unparse(arg.annotation)}"
            except Exception:
                ann = ""
        args.append(f"{arg.arg}{ann}")
    if node.args.vararg:
        args.append(f"*{node.args.vararg.arg}")
    for arg in node.args.kwonlyargs:
        ann = ""
        if arg.annotation:
            try:
                ann = f": {ast.unparse(arg.annotation)}"
            except Exception:
                ann = ""
        args.append(f"{arg.arg}{ann}")
    if node.args.kwarg:
        args.append(f"**{node.args.kwarg.arg}")

    ret_ann = ""
    if getattr(node, "returns", None):
        try:
            ret_ann = f" -> {ast.unparse(node.returns)}"
        except Exception:
            ret_ann = ""

    prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
    return f"{prefix}{node.name}({', '.join(args)}){ret_ann}"


def _extract_symbol_nodes(
    body: Sequence[ast.AST], is_inside_class: bool = False
) -> List[SymbolOutlineNode]:
    """Recursively extract SymbolOutlineNodes for classes, methods, and functions."""
    nodes: List[SymbolOutlineNode] = []
    for item in body:
        if isinstance(item, ast.ClassDef):
            cls_doc = ast.get_docstring(item)
            cls_summary = cls_doc.splitlines()[0] if cls_doc else None
            children = _extract_symbol_nodes(item.body, is_inside_class=True)
            bases_str = ""
            if item.bases:
                try:
                    bases_str = f"({', '.join(ast.unparse(b) for b in item.bases)})"
                except Exception:
                    bases_str = ""
            sig = f"class {item.name}{bases_str}"
            start_ln = getattr(item, "lineno", 1)
            end_ln = getattr(item, "end_lineno", start_ln)
            nodes.append(
                SymbolOutlineNode(
                    name=item.name,
                    symbol_type="class",
                    start_line=start_ln,
                    end_line=end_ln,
                    signature=sig,
                    docstring_summary=cls_summary,
                    children=tuple(children),
                )
            )
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_doc = ast.get_docstring(item)
            fn_summary = fn_doc.splitlines()[0] if fn_doc else None
            fn_type = (
                "async_function"
                if isinstance(item, ast.AsyncFunctionDef)
                else ("method" if is_inside_class else "function")
            )
            sig = _format_function_signature(item)
            start_ln = getattr(item, "lineno", 1)
            end_ln = getattr(item, "end_lineno", start_ln)
            # Recursively extract any nested functions or classes inside this function
            children = _extract_symbol_nodes(item.body, is_inside_class=False)
            nodes.append(
                SymbolOutlineNode(
                    name=item.name,
                    symbol_type=fn_type,
                    start_line=start_ln,
                    end_line=end_ln,
                    signature=sig,
                    docstring_summary=fn_summary,
                    children=tuple(children),
                )
            )
    return nodes


def _format_outline_text(nodes: Sequence[SymbolOutlineNode], depth: int = 0) -> List[str]:
    """Render human-readable outline with hierarchical indentation."""
    lines: List[str] = []
    indent = "  " * depth
    for n in nodes:
        if n.symbol_type == "class":
            lines.append(f"{indent}Class: {n.name} (Lines {n.start_line}-{n.end_line})")
            if n.docstring_summary:
                lines.append(f'{indent}  Docstring: "{n.docstring_summary}"')
            if n.children:
                lines.extend(_format_outline_text(n.children, depth + 1))
        else:
            bullet = "•" if depth > 0 else "Function:"
            lines.append(f"{indent}{bullet} {n.signature} (Lines {n.start_line}-{n.end_line})")
            if n.docstring_summary:
                lines.append(f'{indent}  Docstring: "{n.docstring_summary}"')
            if n.children:
                lines.extend(_format_outline_text(n.children, depth + 1))
    return lines


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

        # Reject Windows drive letter paths (e.g. C:\Windows...) across all platforms
        if re.match(r"^[a-zA-Z]:", clean):
            return (
                False,
                self.workspace_root,
                f"Access denied: path '{relative_or_abs_path}' escapes workspace directory '{self.workspace_root}'.",
            )

        # Normalize backslashes to forward slashes for cross-platform traversal resolution
        normalized_clean = clean.replace("\\", "/")
        raw = Path(normalized_clean)

        if raw.is_absolute() or normalized_clean.startswith("/"):
            resolved = raw.resolve()
        else:
            resolved = (self.workspace_root / normalized_clean).resolve()

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

        outline_nodes: List[SymbolOutlineNode] = _extract_symbol_nodes(tree.body, is_inside_class=False)
        outline_text_lines: List[str] = [
            f"File Outline: {file_path.name} ({total_lines} total lines)",
            f'Module Docstring: "{module_doc.splitlines()[0] if module_doc else "None"}"',
            "",
        ]
        outline_text_lines.extend(_format_outline_text(outline_nodes))

        return "\n".join(outline_text_lines), tuple(outline_nodes), None

    def read_windowed(
        self,
        file_path: Path,
        offset_line: int = 1,
        limit_lines: int = 150,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        include_outline: bool = True,
    ) -> Tuple[Optional[VirtualFileView], Optional[str]]:
        """Read deterministic line-bounded window with line numbers, pagination, and outline metadata."""
        if not file_path.exists():
            return None, f"File '{file_path.name}' does not exist."

        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return None, f"Failed to read '{file_path.name}': {str(e)}"

        raw_lines = source.splitlines()
        total_lines = len(raw_lines)

        outline_nodes: Optional[Tuple[SymbolOutlineNode, ...]] = None
        if include_outline and file_path.suffix == ".py":
            _, outline_tuple, _ = self.generate_outline(file_path)
            outline_nodes = outline_tuple

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
                outline=outline_nodes,
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
            effective_limit = min(max(1, limit_lines), MAX_READ_LINES)
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
            outline=outline_nodes,
        )
        return view, None

    def read_ast_symbol(
        self,
        file_path: Path,
        symbol_name: str,
        max_chars: Optional[int] = MAX_READ_CHARS,
    ) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[str]]:
        """Extract full implementation of a class or method by qualified name with zero truncation up to token budget."""
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

        # Multi-part qualified resolution (e.g. Outer.Inner.method or Class.method)
        parts = [p.strip() for p in target.split(".") if p.strip()]
        if len(parts) > 1:
            current_nodes: Sequence[ast.AST] = tree.body
            found_node: Optional[ast.AST] = None
            for p in parts:
                matched = False
                for node in current_nodes:
                    if (
                        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                        and node.name == p
                    ):
                        found_node = node
                        current_nodes = getattr(node, "body", [])
                        matched = True
                        break
                if not matched:
                    found_node = None
                    break
            match_node = found_node
        else:
            # First check top-level body
            for node in tree.body:
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    and node.name == target
                ):
                    match_node = node
                    break
            # If not top-level, search all nodes via walk
            if not match_node:
                for node in ast.walk(tree):
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

        # Apply character ceiling only if max_chars is provided and content exceeds it
        if max_chars is not None and len(annotated_content) > max_chars:
            cut_point = annotated_content.rfind("\n", 0, max_chars)
            if cut_point < max_chars // 2:
                cut_point = max_chars
            annotated_content = (
                annotated_content[:cut_point]
                + f"\n\n[Governance Notice: Symbol output clamped at {max_chars} chars to protect token budget.]"
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
            if file_path.suffix == ".py":
                try:
                    py_compile.compile(str(tmp_path), doraise=True)
                except py_compile.PyCompileError as pe:
                    if tmp_path.exists():
                        try:
                            tmp_path.unlink()
                        except Exception:
                            pass
                    return (
                        False,
                        f"AST Integrity Violation: py_compile syntax error in {file_path.name}: {pe.msg}",
                    )
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
