"""Zero-token AST inspection and instant self-healing guard."""

import ast
import builtins
from pathlib import Path
from typing import Optional, Set, Tuple

# Well-known symbol mappings to standard library imports
KNOWN_STD_SYMBOLS = {
    "Path": ("pathlib", "Path"),
    "dataclass": ("dataclasses", "dataclass"),
    "field": ("dataclasses", "field"),
    "Enum": ("enum", "Enum"),
    "List": ("typing", "List"),
    "Dict": ("typing", "Dict"),
    "Tuple": ("typing", "Tuple"),
    "Optional": ("typing", "Optional"),
    "Union": ("typing", "Union"),
    "Any": ("typing", "Any"),
    "Callable": ("typing", "Callable"),
    "Protocol": ("typing", "Protocol"),
    "runtime_checkable": ("typing", "runtime_checkable"),
    "Literal": ("typing", "Literal"),
    "json": ("json", None),
    "sys": ("sys", None),
    "os": ("os", None),
    "time": ("time", None),
    "re": ("re", None),
}

BUILTIN_NAMES = set(dir(builtins))


class ASTGuard:
    """Audits AST before disk write; validates syntax and auto-heals missing imports."""

    def __init__(self, disallow_stubs: bool = False) -> None:
        self.disallow_stubs = disallow_stubs

    def intercept_ast(
        self, file_path: Path, code_content: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Audits AST before disk write.

        Returns:
            Tuple[bool, str, Optional[str]]: (is_safe, error_message, auto_healed_code)
        """
        # Only inspect Python files
        if file_path.suffix != ".py":
            return True, "", code_content

        try:
            tree = ast.parse(code_content, filename=str(file_path))
        except SyntaxError as e:
            return False, f"SyntaxError in {file_path.name}: {e.msg} (line {e.lineno})", None

        # Check for disallowed stubs if configured
        if self.disallow_stubs:
            stub_error = self._check_disallowed_stubs(tree, file_path)
            if stub_error:
                return False, stub_error, None

        # Check and heal missing imports
        healed_code, healed_symbols = self._heal_missing_imports(tree, code_content)
        if healed_symbols:
            return True, f"Auto-healed missing imports: {', '.join(healed_symbols)}", healed_code

        return True, "", code_content

    def _check_disallowed_stubs(self, tree: ast.AST, file_path: Path) -> Optional[str]:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # If body is just `pass` or `...` and no docstring
                if len(node.body) == 1:
                    stmt = node.body[0]
                    if isinstance(stmt, ast.Pass):
                        return f"Prohibited empty stub in {file_path.name}: function '{node.name}' has body 'pass'"
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
                        return f"Prohibited empty stub in {file_path.name}: function '{node.name}' has body '...'"
        return None

    def _heal_missing_imports(
        self, tree: ast.AST, code_content: str
    ) -> Tuple[str, Set[str]]:
        """Identify missing standard library symbols and inject their imports."""
        imported_names: Set[str] = set()
        defined_names: Set[str] = set()
        used_names: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
                # Also collect function arguments
                for arg in node.args.args:
                    defined_names.add(arg.arg)
                for arg in getattr(node.args, "posonlyargs", []):
                    defined_names.add(arg.arg)
                for arg in getattr(node.args, "kwonlyargs", []):
                    defined_names.add(arg.arg)
                if node.args.vararg:
                    defined_names.add(node.args.vararg.arg)
                if node.args.kwarg:
                    defined_names.add(node.args.kwarg.arg)
            elif isinstance(node, ast.ClassDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, (ast.Store, ast.Param)):
                    defined_names.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)

        # Missing symbols that we know how to import
        missing_known = {
            name
            for name in used_names
            if name in KNOWN_STD_SYMBOLS
            and name not in imported_names
            and name not in defined_names
            and name not in BUILTIN_NAMES
        }

        if not missing_known:
            return code_content, set()

        # Build import lines
        # Group by module
        from_modules: dict[str, list[str]] = {}
        direct_modules: list[str] = []

        for sym in sorted(missing_known):
            mod, target = KNOWN_STD_SYMBOLS[sym]
            if target is None:
                direct_modules.append(mod)
            else:
                from_modules.setdefault(mod, []).append(target)

        injected_lines: list[str] = []
        for mod in sorted(direct_modules):
            injected_lines.append(f"import {mod}")
        for mod, targets in sorted(from_modules.items()):
            injected_lines.append(f"from {mod} import {', '.join(sorted(targets))}")

        injected_block = "\n".join(injected_lines) + "\n"

        # Determine injection position (after docstring if present, or top)
        lines = code_content.splitlines(keepends=True)
        insert_idx = 0

        # Check if first statement is a module docstring
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            insert_idx = tree.body[0].end_lineno or 1
            # Adjust if next line is empty
            while insert_idx < len(lines) and lines[insert_idx].strip() == "":
                insert_idx += 1

        new_lines = lines[:insert_idx] + [injected_block] + lines[insert_idx:]
        healed_code = "".join(new_lines)

        # Verify that healed code parses cleanly
        try:
            ast.parse(healed_code)
            return healed_code, missing_known
        except Exception:
            return code_content, set()
