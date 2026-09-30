"""Polyglot Driver Mesh, Registry, and Concrete Implementations for ORAGAI.

Specification: docs/plans/P14_POLYGLOT_ADAPTATION_AND_INTELLIGENT_LANGUAGE_MESH_PLAN.md
"""

from __future__ import annotations

import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Tuple

from orchestrator.ports.driven.language_port import (
    CodebaseMetrics,
    CompactedFailureFrame,
    DynamicEcosystemProfile,
    ILanguageDriver,
    LanguageType,
    StaticAnalysisResult,
    StubSeverity,
    StubViolation,
    SymbolEntity,
    SymbolKind,
    SymbolOutline,
    SyntaxCheckResult,
    TestExecutionOutcome,
    TestStatus,
)


class LanguageDetector:
    """Automated ecosystem discriminator scanning manifests and file volume."""

    MANIFEST_SIGNATURES: Dict[LanguageType, List[str]] = {
        LanguageType.RUST: ["Cargo.toml", "Cargo.lock"],
        LanguageType.GO: ["go.mod", "go.sum", "go.work"],
        LanguageType.PYTHON: ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile"],
        LanguageType.TYPESCRIPT: ["tsconfig.json"],
        LanguageType.JAVASCRIPT: ["package.json"],
        LanguageType.CPP: ["CMakeLists.txt", "meson.build", "conanfile.txt", "vcpkg.json"],
        LanguageType.C: ["Makefile"],
        LanguageType.JAVA: ["pom.xml", "build.gradle", "build.gradle.kts"],
    }

    FILE_EXTENSION_MAP: Dict[str, LanguageType] = {
        ".py": LanguageType.PYTHON,
        ".ts": LanguageType.TYPESCRIPT,
        ".tsx": LanguageType.TYPESCRIPT,
        ".js": LanguageType.JAVASCRIPT,
        ".jsx": LanguageType.JAVASCRIPT,
        ".mjs": LanguageType.JAVASCRIPT,
        ".cjs": LanguageType.JAVASCRIPT,
        ".rs": LanguageType.RUST,
        ".go": LanguageType.GO,
        ".c": LanguageType.C,
        ".h": LanguageType.C,
        ".cpp": LanguageType.CPP,
        ".hpp": LanguageType.CPP,
        ".cc": LanguageType.CPP,
        ".cxx": LanguageType.CPP,
        ".java": LanguageType.JAVA,
    }

    IGNORE_DIRS: Set[str] = {
        ".git", ".venv", "venv", "node_modules", "target", "vendor",
        "dist", "build", "out", "__pycache__", ".idea", ".vscode"
    }

    def detect_ecosystem(
        self, workspace: Path, forced_language: Optional[str] = None
    ) -> LanguageType:
        """Detect primary ecosystem for a workspace."""
        if forced_language:
            norm = forced_language.strip().lower()
            for lang in LanguageType:
                if lang.value == norm:
                    return lang
            if norm in ("js", "node", "nodejs"):
                return LanguageType.JAVASCRIPT
            if norm == "ts":
                return LanguageType.TYPESCRIPT
            if norm in ("c++", "cxx"):
                return LanguageType.CPP
            if norm in ("py", "python3"):
                return LanguageType.PYTHON
            if norm in ("golang",):
                return LanguageType.GO

        # 1. Manifest Matching
        for lang, manifests in self.MANIFEST_SIGNATURES.items():
            for manifest in manifests:
                if (workspace / manifest).is_file():
                    # If package.json has tsconfig.json, upgrade to TS
                    if lang == LanguageType.JAVASCRIPT and (workspace / "tsconfig.json").is_file():
                        return LanguageType.TYPESCRIPT
                    return lang

        # 2. File Count & Volume Ranking
        counts: Dict[LanguageType, int] = {lt: 0 for lt in LanguageType}
        try:
            for root, dirs, files in os.walk(workspace):
                dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext in self.FILE_EXTENSION_MAP:
                        counts[self.FILE_EXTENSION_MAP[ext]] += 1
        except Exception:
            return LanguageType.GENERIC

        dominant_lang = max(counts, key=lambda k: counts[k])
        if counts[dominant_lang] > 0:
            return dominant_lang

        return LanguageType.GENERIC


# ============================================================================
# CONCRETE DRIVER: PythonDriver
# ============================================================================

class PythonDriver:
    """Driver for Python ecosystem (in-process AST, py_compile, pytest)."""

    def __init__(self) -> None:
        self._stub_comment_patterns: List[Tuple[Pattern[str], str, StubSeverity]] = [
            (re.compile(r'#\s*TODO\s*:\s*implement', re.IGNORECASE), "# TODO: implement", StubSeverity.CRITICAL),
            (re.compile(r'#\s*FIXME\s*:\s*implement', re.IGNORECASE), "# FIXME: implement", StubSeverity.CRITICAL),
            (re.compile(r'raise\s+NotImplementedError\s*\(\s*["\']TODO["\']\s*\)', re.IGNORECASE), "raise NotImplementedError('TODO')", StubSeverity.CRITICAL),
        ]

    @property
    def language_type(self) -> LanguageType:
        return LanguageType.PYTHON

    @property
    def language_name(self) -> str:
        return "Python"

    def detect(self, workspace: Path) -> bool:
        manifests = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile"]
        if any((workspace / m).is_file() for m in manifests):
            return True
        return bool(list(workspace.glob("*.py")) or list(workspace.glob("tests/**/*.py")))

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        """Perform zero-token deterministic syntax validation using AST and py_compile."""
        if not file_path.is_file():
            return SyntaxCheckResult(
                is_clean=False,
                error_count=1,
                error_messages=[f"File not found: {file_path}"],
                failing_file=file_path,
            )

        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return SyntaxCheckResult(
                is_clean=False,
                error_count=1,
                error_messages=[f"Failed to read file: {e}"],
                failing_file=file_path,
            )

        # 1. In-process AST parse
        try:
            ast.parse(source, filename=str(file_path))
        except SyntaxError as se:
            return SyntaxCheckResult(
                is_clean=False,
                error_count=1,
                error_messages=[f"SyntaxError: {se.msg} (line {se.lineno}, col {se.offset})"],
                failing_file=file_path,
                line_number=se.lineno,
                column_number=se.offset,
            )

        # 2. py_compile check
        import py_compile
        try:
            py_compile.compile(str(file_path), doraise=True)
        except py_compile.PyCompileError as pce:
            return SyntaxCheckResult(
                is_clean=False,
                error_count=1,
                error_messages=[str(pce)],
                failing_file=file_path,
            )
        except Exception:
            pass

        return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        ruff = shutil.which("ruff")
        if ruff:
            proc = subprocess.run([ruff, "format", "."], cwd=workspace, capture_output=True, text=True)
            return proc.returncode == 0, proc.stdout
        return True, "No python autofix tool found; skipped."

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        ruff = shutil.which("ruff")
        if ruff:
            proc = subprocess.run([ruff, "check", "--output-format=json", "."], cwd=workspace, capture_output=True, text=True)
            if proc.returncode != 0:
                try:
                    data = json.loads(proc.stdout)
                    violations = [f"{item.get('filename')}:{item.get('location', {}).get('row')} - {item.get('message')} ({item.get('code')})" for item in data]
                    return StaticAnalysisResult(is_clean=False, violation_count=len(violations), violations=violations[:10], tool_name="ruff")
                except Exception:
                    return StaticAnalysisResult(is_clean=False, violation_count=1, violations=[proc.stderr[:400]], tool_name="ruff")
        return StaticAnalysisResult(is_clean=True, violation_count=0, violations=[], tool_name="none")

    def has_test_suite(self, workspace: Path) -> bool:
        test_indicators = ["pytest.ini", "tox.ini", "pyproject.toml", "tests"]
        return any((workspace / ind).exists() for ind in test_indicators)

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        if target_test:
            return f"pytest {target_test} -v"
        return "pytest tests/ -v"

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        cmd = self.get_default_test_command(workspace, target_test)
        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            failures = self.parse_test_diagnostics(proc.stdout, proc.stderr, proc.returncode)
            status = TestStatus.PASSED if proc.returncode == 0 else TestStatus.FAILED
            summary = f"Pytest suite: {'PASSED' if proc.returncode == 0 else 'FAILED'} (Exit code: {proc.returncode})"
            return TestExecutionOutcome(
                status=status,
                exit_code=proc.returncode,
                total_tests=len(failures) if status == TestStatus.FAILED else 1,
                passed_tests=0 if status == TestStatus.FAILED else 1,
                failed_tests=len(failures),
                skipped_tests=0,
                duration_seconds=duration,
                raw_stdout=proc.stdout,
                raw_stderr=proc.stderr,
                compacted_failures=failures,
                compaction_summary=summary,
            )
        except subprocess.TimeoutExpired as te:
            return TestExecutionOutcome(
                status=TestStatus.TIMEOUT,
                exit_code=124,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                duration_seconds=float(timeout_seconds),
                raw_stdout=te.stdout or "",
                raw_stderr=te.stderr or "Execution timed out.",
                compacted_failures=[],
                compaction_summary=f"Python test execution timed out after {timeout_seconds}s.",
            )

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        failures: List[CompactedFailureFrame] = []
        combined = stdout + "\n" + stderr
        # Extract pytest FAILURES sections
        fail_re = re.compile(r"_{5,}\s+(.*?)\s+_{5,}\n(.*?)(?=\n_{5,}|\n={5,}|\Z)", re.DOTALL)
        for match in fail_re.finditer(combined):
            test_name = match.group(1).strip()
            body = match.group(2).strip()
            lines = body.splitlines()
            
            # Find failure line
            loc_match = re.search(r"^(.*?):(\d+):\s+(?:in\s+\w+|AssertionError|.*Error)", body, re.MULTILINE)
            f_path = loc_match.group(1) if loc_match else "unknown"
            line_no = int(loc_match.group(2)) if loc_match else None
            
            # Error type & diagnostic
            err_line = lines[-1] if lines else "AssertionError"
            for l in reversed(lines):
                if "Error:" in l or "AssertionError" in l or "FAILED" in l:
                    err_line = l
                    break

            failures.append(
                CompactedFailureFrame(
                    test_identifier=test_name,
                    file_path=f_path,
                    line_number=line_no,
                    error_type="AssertionError" if "Assertion" in err_line else "PytestFailure",
                    diagnostic_message=err_line[:300],
                    context_snippet="\n".join(lines[-6:]),
                )
            )

        if not failures and exit_code != 0:
            failures.append(
                CompactedFailureFrame(
                    test_identifier="PytestRunFailure",
                    file_path="tests",
                    line_number=None,
                    error_type="ExecutionError",
                    diagnostic_message=combined[-400:].strip() if combined.strip() else "Pytest failed.",
                    context_snippet=None,
                )
            )
        return failures

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        violations: List[StubViolation] = []
        if not file_path.is_file():
            return violations

        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            # 1. Regex comment scanner
            for idx, line in enumerate(source.splitlines(), start=1):
                for pat, name, sev in self._stub_comment_patterns:
                    if pat.search(line):
                        violations.append(
                            StubViolation(
                                file_path=file_path,
                                line_number=idx,
                                severity=sev,
                                symbol_name=name,
                                pattern_matched=pat.pattern,
                                snippet=line.strip(),
                            )
                        )

            # 2. AST-based placeholder body inspection
            try:
                tree = ast.parse(source, filename=str(file_path))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Inspect function body
                        body = node.body
                        is_stub = False
                        matched_reason = ""
                        
                        # Filter out docstrings
                        statements = [stmt for stmt in body if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str))]
                        
                        if not statements:
                            is_stub = True
                            matched_reason = "Empty function body (docstring only)"
                        elif len(statements) == 1:
                            stmt = statements[0]
                            if isinstance(stmt, ast.Pass):
                                is_stub = True
                                matched_reason = "pass statement only"
                            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value == Ellipsis:
                                is_stub = True
                                matched_reason = "... (Ellipsis) body only"
                            elif isinstance(stmt, ast.Raise):
                                if isinstance(stmt.exc, ast.Name) and stmt.exc.id == "NotImplementedError":
                                    is_stub = True
                                    matched_reason = "raise NotImplementedError body only"
                                elif isinstance(stmt.exc, ast.Call) and isinstance(stmt.exc.func, ast.Name) and stmt.exc.func.id == "NotImplementedError":
                                    is_stub = True
                                    matched_reason = "raise NotImplementedError(...) body only"

                        if is_stub:
                            violations.append(
                                StubViolation(
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    severity=StubSeverity.CRITICAL,
                                    symbol_name=node.name,
                                    pattern_matched=matched_reason,
                                    snippet=f"def {node.name}(...): {matched_reason}",
                                )
                            )
            except Exception:
                pass
        except Exception:
            pass
        return violations

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        entities: List[SymbolEntity] = []
        lines: List[str] = []
        if file_path.is_file():
            try:
                source = file_path.read_text(encoding="utf-8", errors="replace")
                lines = source.splitlines()
                tree = ast.parse(source, filename=str(file_path))
                
                for node in tree.body:
                    if isinstance(node, ast.ClassDef):
                        methods: List[SymbolEntity] = []
                        for sub in node.body:
                            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                methods.append(
                                    SymbolEntity(
                                        name=sub.name,
                                        kind=SymbolKind.METHOD,
                                        start_line=sub.lineno,
                                        end_line=getattr(sub, "end_lineno", sub.lineno),
                                        signature=f"def {sub.name}(...)",
                                        docstring=ast.get_docstring(sub),
                                    )
                                )
                        entities.append(
                            SymbolEntity(
                                name=node.name,
                                kind=SymbolKind.CLASS,
                                start_line=node.lineno,
                                end_line=getattr(node, "end_lineno", node.lineno),
                                signature=f"class {node.name}",
                                docstring=ast.get_docstring(node),
                                children=methods,
                            )
                        )
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        entities.append(
                            SymbolEntity(
                                name=node.name,
                                kind=SymbolKind.FUNCTION,
                                start_line=node.lineno,
                                end_line=getattr(node, "end_lineno", node.lineno),
                                signature=f"def {node.name}(...)",
                                docstring=ast.get_docstring(node),
                            )
                        )
            except Exception:
                pass

        outline_text = f"# === OUTLINE: {file_path.name} (Total: {len(lines)} LOC) ===\n"
        for e in entities:
            outline_text += f"{e.signature} [Lines: {e.start_line}-{e.end_line}]\n"
            for child in e.children:
                outline_text += f"    {child.signature} [Line: {child.start_line}]\n"

        return SymbolOutline(file_path=file_path, total_lines=len(lines), entities=entities, raw_outline_text=outline_text)

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        lines = content.splitlines()
        if len(lines) <= max_lines:
            return content
        return "\n".join(lines[:15]) + f"\n    ... # [Folded: {len(lines) - 30} lines]\n" + "\n".join(lines[-15:])

    def get_developer_prompt_guidance(self) -> str:
        return (
            "Python 3.12+ Guidelines:\n"
            "- Use strict type annotations everywhere.\n"
            "- Adhere to Hexagonal Architecture; keep domain core free of I/O.\n"
            "- Never leave placeholder `pass`, `...`, or stub comments."
        )

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        files = list(workspace.glob("**/*.py"))
        total_loc = 0
        for f in files:
            try:
                total_loc += len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            except Exception:
                pass
        test_files = [f for f in files if "test" in f.name.lower()]
        return CodebaseMetrics(
            language=LanguageType.PYTHON,
            total_files=len(files),
            total_loc=total_loc,
            test_files_count=len(test_files),
            test_loc=0,
            ecosystem_metadata={"pyproject_exists": (workspace / "pyproject.toml").is_file()},
        )


# ============================================================================
# CONCRETE DRIVER: NodeDriver (TypeScript / JavaScript)
# ============================================================================

class NodeDriver:
    """Driver for JavaScript, TypeScript, and Node.js ecosystems."""

    def __init__(self) -> None:
        self._stub_patterns: List[Tuple[Pattern[str], str, StubSeverity]] = [
            (re.compile(r'throw\s+new\s+Error\s*\(\s*["\'](?:TODO|Not implemented|NotImplemented|stub)[^"\']*["\']\s*\)', re.IGNORECASE), "throw new Error(TODO)", StubSeverity.CRITICAL),
            (re.compile(r'//\s*TODO\s*:\s*implement', re.IGNORECASE), "// TODO: implement", StubSeverity.CRITICAL),
            (re.compile(r'/\*\s*TODO\s*:\s*implement\s*\*/', re.IGNORECASE), "/* TODO: implement */", StubSeverity.CRITICAL),
            (re.compile(r'return\s+null\s*;\s*//\s*stub', re.IGNORECASE), "return null; // stub", StubSeverity.CRITICAL),
        ]

    @property
    def language_type(self) -> LanguageType:
        return LanguageType.TYPESCRIPT

    @property
    def language_name(self) -> str:
        return "Node.js / TypeScript"

    def detect(self, workspace: Path) -> bool:
        return (workspace / "package.json").is_file() or (workspace / "tsconfig.json").is_file()

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        if not file_path.is_file():
            return SyntaxCheckResult(is_clean=False, error_count=1, error_messages=[f"File not found: {file_path}"], failing_file=file_path)

        ext = file_path.suffix.lower()
        if ext in (".ts", ".tsx"):
            tsc_bin = shutil.which("tsc")
            if tsc_bin:
                proc = subprocess.run(
                    [tsc_bin, "--noEmit", "--isolatedModules", str(file_path)],
                    capture_output=True,
                    text=True,
                    shell=False,
                )
                if proc.returncode != 0:
                    lines = [l.strip() for l in proc.stdout.splitlines() if l.strip()]
                    return SyntaxCheckResult(is_clean=False, error_count=len(lines), error_messages=lines[:5], failing_file=file_path)
            return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

        node_bin = shutil.which("node")
        if node_bin:
            proc = subprocess.run(
                [node_bin, "--check", str(file_path)],
                capture_output=True,
                text=True,
                shell=False,
            )
            if proc.returncode != 0:
                err = proc.stderr.strip() or proc.stdout.strip()
                return SyntaxCheckResult(is_clean=False, error_count=1, error_messages=[err], failing_file=file_path)

        return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        prettier_bin = shutil.which("prettier")
        if prettier_bin:
            proc = subprocess.run(
                [prettier_bin, "--write", "src/**/*.{ts,tsx,js,jsx}"],
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=False,
            )
            return proc.returncode == 0, proc.stdout
        return True, "No autofix tool found; skipped."

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        eslint_bin = shutil.which("eslint")
        if eslint_bin:
            proc = subprocess.run(
                [eslint_bin, ".", "--format", "json"],
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=False,
            )
            if proc.returncode != 0:
                try:
                    data = json.loads(proc.stdout)
                    violations = []
                    for item in data:
                        for msg in item.get("messages", []):
                            violations.append(f"{item.get('filePath')}:{msg.get('line')}:{msg.get('column')} - {msg.get('message')} ({msg.get('ruleId')})")
                    return StaticAnalysisResult(is_clean=False, violation_count=len(violations), violations=violations[:10], tool_name="eslint")
                except Exception:
                    return StaticAnalysisResult(is_clean=False, violation_count=1, violations=[proc.stderr[:500]], tool_name="eslint")
        return StaticAnalysisResult(is_clean=True, violation_count=0, violations=[], tool_name="none")

    def has_test_suite(self, workspace: Path) -> bool:
        pkg = workspace / "package.json"
        if pkg.is_file():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
                scripts = data.get("scripts", {})
                return "test" in scripts
            except Exception:
                pass
        return bool(list(workspace.glob("**/*.test.ts")) or list(workspace.glob("**/*.spec.ts")) or list(workspace.glob("**/*.test.js")))

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        base = "npm test"
        if (workspace / "pnpm-lock.yaml").is_file():
            base = "pnpm test"
        elif (workspace / "yarn.lock").is_file():
            base = "yarn test"
        if target_test:
            return f"{base} -- -t \"{target_test}\""
        return f"{base} -- --watchAll=false"

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        cmd = self.get_default_test_command(workspace, target_test)
        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            failures = self.parse_test_diagnostics(proc.stdout, proc.stderr, proc.returncode)
            status = TestStatus.PASSED if proc.returncode == 0 else TestStatus.FAILED
            summary = f"Node test suite: {'PASSED' if proc.returncode == 0 else 'FAILED'} (Exit code: {proc.returncode})"
            return TestExecutionOutcome(
                status=status,
                exit_code=proc.returncode,
                total_tests=len(failures) if status == TestStatus.FAILED else 1,
                passed_tests=0 if status == TestStatus.FAILED else 1,
                failed_tests=len(failures),
                skipped_tests=0,
                duration_seconds=duration,
                raw_stdout=proc.stdout,
                raw_stderr=proc.stderr,
                compacted_failures=failures,
                compaction_summary=summary,
            )
        except subprocess.TimeoutExpired as te:
            return TestExecutionOutcome(
                status=TestStatus.TIMEOUT,
                exit_code=124,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                duration_seconds=float(timeout_seconds),
                raw_stdout=te.stdout or "",
                raw_stderr=te.stderr or "Execution timed out.",
                compacted_failures=[],
                compaction_summary=f"Execution timed out after {timeout_seconds}s.",
            )

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        failures: List[CompactedFailureFrame] = []
        combined = stdout + "\n" + stderr
        # Match Jest / Vitest failure markers
        jest_fail_re = re.compile(r"●\s+(.*?)\n\n(.*?)(?=\n\s*●|\n\s*Test Suites:|\Z)", re.DOTALL)
        for match in jest_fail_re.finditer(combined):
            title = match.group(1).strip()
            body = match.group(2).strip()
            lines = body.splitlines()
            diag = lines[0] if lines else "Assertion failure"
            loc_match = re.search(r"at\s+.*?\((.*?):(\d+):(\d+)\)", body)
            f_path = loc_match.group(1) if loc_match else "unknown"
            line_no = int(loc_match.group(2)) if loc_match else None
            failures.append(
                CompactedFailureFrame(
                    test_identifier=title,
                    file_path=f_path,
                    line_number=line_no,
                    error_type="AssertionError",
                    diagnostic_message=diag[:300],
                    context_snippet="\n".join(lines[:6]),
                )
            )
        if not failures and exit_code != 0:
            failures.append(
                CompactedFailureFrame(
                    test_identifier="SuiteFailure",
                    file_path="workspace",
                    line_number=None,
                    error_type="ExecutionError",
                    diagnostic_message=combined[-400:].strip(),
                    context_snippet=None,
                )
            )
        return failures

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        violations: List[StubViolation] = []
        if not file_path.is_file():
            return violations
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for idx, line in enumerate(content.splitlines(), start=1):
                for pattern, name, severity in self._stub_patterns:
                    if pattern.search(line):
                        violations.append(
                            StubViolation(
                                file_path=file_path,
                                line_number=idx,
                                severity=severity,
                                symbol_name=name,
                                pattern_matched=pattern.pattern,
                                snippet=line.strip(),
                            )
                        )
        except Exception:
            pass
        return violations

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        entities: List[SymbolEntity] = []
        lines: List[str] = []
        if file_path.is_file():
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
                sym_re = re.compile(r"^(?:export\s+)?(?:default\s+)?(class|interface|type|enum|function|const|async\s+function)\s+([A-Za-z0-9_$]+)")
                for idx, line in enumerate(lines, start=1):
                    m = sym_re.match(line.strip())
                    if m:
                        kind_str, name = m.group(1), m.group(2)
                        kind = SymbolKind.FUNCTION
                        if "class" in kind_str:
                            kind = SymbolKind.CLASS
                        elif "interface" in kind_str:
                            kind = SymbolKind.INTERFACE
                        elif "enum" in kind_str:
                            kind = SymbolKind.ENUM
                        elif "type" in kind_str:
                            kind = SymbolKind.TYPE_ALIAS
                        entities.append(
                            SymbolEntity(
                                name=name,
                                kind=kind,
                                start_line=idx,
                                end_line=idx,
                                signature=line.strip()[:100],
                            )
                        )
            except Exception:
                pass
        outline_text = f"// === OUTLINE: {file_path.name} (Total: {len(lines)} LOC) ===\n"
        for e in entities:
            outline_text += f"{e.signature} [Line: {e.start_line}]\n"
        return SymbolOutline(file_path=file_path, total_lines=len(lines), entities=entities, raw_outline_text=outline_text)

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        lines = content.splitlines()
        if len(lines) <= max_lines:
            return content
        return "\n".join(lines[:15]) + f"\n    // ... [Folded: {len(lines) - 30} lines] ...\n" + "\n".join(lines[-15:])

    def get_developer_prompt_guidance(self) -> str:
        return (
            "Node.js / TypeScript Guidelines:\n"
            "- Always declare explicit return types on exported functions.\n"
            "- Use strict null checks and avoid 'any' types.\n"
            "- Never leave empty function stubs or throw placeholder errors."
        )

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        files = list(workspace.glob("**/*.ts")) + list(workspace.glob("**/*.tsx")) + list(workspace.glob("**/*.js"))
        total_loc = 0
        for f in files:
            try:
                total_loc += len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            except Exception:
                pass
        tests = [f for f in files if ".test." in f.name or ".spec." in f.name]
        return CodebaseMetrics(
            language=LanguageType.TYPESCRIPT,
            total_files=len(files),
            total_loc=total_loc,
            test_files_count=len(tests),
            test_loc=0,
            ecosystem_metadata={"package_json_exists": (workspace / "package.json").is_file()},
        )


# ============================================================================
# CONCRETE DRIVER: CDriver (C / C++)
# ============================================================================

class CDriver:
    """Driver for C and C++ ecosystems (GCC, Clang, CMake, CTest)."""

    def __init__(self) -> None:
        self._stub_patterns: List[Tuple[Pattern[str], str, StubSeverity]] = [
            (re.compile(r'\babort\s*\(\s*\)\s*;', re.IGNORECASE), "abort()", StubSeverity.CRITICAL),
            (re.compile(r'//\s*TODO\s*:\s*implement', re.IGNORECASE), "// TODO: implement", StubSeverity.CRITICAL),
            (re.compile(r'/\*\s*TODO\s*:\s*implement\s*\*/', re.IGNORECASE), "/* TODO: implement */", StubSeverity.CRITICAL),
            (re.compile(r'assert\s*\(\s*false\s*\)\s*;', re.IGNORECASE), "assert(false)", StubSeverity.CRITICAL),
            (re.compile(r'__builtin_unreachable\s*\(\s*\)\s*;', re.IGNORECASE), "__builtin_unreachable()", StubSeverity.CRITICAL),
        ]

    @property
    def language_type(self) -> LanguageType:
        return LanguageType.CPP

    @property
    def language_name(self) -> str:
        return "C / C++"

    def detect(self, workspace: Path) -> bool:
        return (workspace / "CMakeLists.txt").is_file() or (workspace / "Makefile").is_file() or (workspace / "meson.build").is_file()

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        if not file_path.is_file():
            return SyntaxCheckResult(is_clean=False, error_count=1, error_messages=[f"File not found: {file_path}"], failing_file=file_path)

        compiler = shutil.which("clang++") or shutil.which("g++") or shutil.which("gcc") or shutil.which("clang")
        if not compiler:
            return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=["Compiler not found in path; skipping syntax check."])

        proc = subprocess.run(
            [compiler, "-fsyntax-only", "-Wall", "-Wextra", str(file_path)],
            capture_output=True,
            text=True,
            shell=False,
        )
        if proc.returncode != 0:
            err_lines = [l.strip() for l in proc.stderr.splitlines() if l.strip()]
            return SyntaxCheckResult(
                is_clean=False,
                error_count=len(err_lines),
                error_messages=err_lines[:5],
                failing_file=file_path,
            )
        return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        clang_format = shutil.which("clang-format")
        if clang_format:
            files = list(workspace.glob("**/*.cpp")) + list(workspace.glob("**/*.hpp")) + list(workspace.glob("**/*.c")) + list(workspace.glob("**/*.h"))
            for f in files[:50]:
                subprocess.run([clang_format, "-i", str(f)], capture_output=True, shell=False)
            return True, "clang-format executed."
        return True, "clang-format not found; skipped."

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        cppcheck = shutil.which("cppcheck")
        if cppcheck:
            proc = subprocess.run(
                [cppcheck, "--enable=warning,performance", "--quiet", str(workspace)],
                capture_output=True,
                text=True,
                shell=False,
            )
            lines = [l.strip() for l in proc.stderr.splitlines() if l.strip()]
            return StaticAnalysisResult(is_clean=len(lines) == 0, violation_count=len(lines), violations=lines[:10], tool_name="cppcheck")
        return StaticAnalysisResult(is_clean=True, violation_count=0, violations=[], tool_name="none")

    def has_test_suite(self, workspace: Path) -> bool:
        return (workspace / "CMakeLists.txt").is_file() or (workspace / "Makefile").is_file()

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        if (workspace / "build").is_dir():
            return "ctest --test-dir build --output-on-failure"
        return "make test"

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        cmd = self.get_default_test_command(workspace, target_test)
        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            failures = self.parse_test_diagnostics(proc.stdout, proc.stderr, proc.returncode)
            status = TestStatus.PASSED if proc.returncode == 0 else TestStatus.FAILED
            summary = f"C/C++ test suite: {'PASSED' if proc.returncode == 0 else 'FAILED'} (Exit code: {proc.returncode})"
            return TestExecutionOutcome(
                status=status,
                exit_code=proc.returncode,
                total_tests=len(failures) if status == TestStatus.FAILED else 1,
                passed_tests=0 if status == TestStatus.FAILED else 1,
                failed_tests=len(failures),
                skipped_tests=0,
                duration_seconds=duration,
                raw_stdout=proc.stdout,
                raw_stderr=proc.stderr,
                compacted_failures=failures,
                compaction_summary=summary,
            )
        except subprocess.TimeoutExpired as te:
            return TestExecutionOutcome(
                status=TestStatus.TIMEOUT,
                exit_code=124,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                duration_seconds=float(timeout_seconds),
                raw_stdout=te.stdout or "",
                raw_stderr=te.stderr or "Execution timed out.",
                compacted_failures=[],
                compaction_summary=f"C/C++ test execution timed out after {timeout_seconds}s.",
            )

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        failures: List[CompactedFailureFrame] = []
        combined = stdout + "\n" + stderr
        # Google Test Failure Pattern: capture test run block leading to FAILED
        gtest_block_re = re.compile(r"\[\s*RUN\s*\]\s*([A-Za-z0-9_]+\.[A-Za-z0-9_]+)\n(.*?)(?=\[\s*FAILED\s*\]|\Z)", re.DOTALL)
        for match in gtest_block_re.finditer(combined):
            t_name = match.group(1).strip()
            body = match.group(2).strip()
            loc_match = re.search(r"^(.*?):(\d+):\s*Failure", body, re.MULTILINE)
            f_path = loc_match.group(1) if loc_match else "unknown"
            line_no = int(loc_match.group(2)) if loc_match else None
            failures.append(
                CompactedFailureFrame(
                    test_identifier=t_name,
                    file_path=f_path,
                    line_number=line_no,
                    error_type="GTestFailure",
                    diagnostic_message=body.splitlines()[0] if body else "Test failed",
                    context_snippet="\n".join(body.splitlines()[:5]),
                )
            )
        # Fallback to direct FAILED marker if block pattern didn't capture
        if not failures:
            gtest_re = re.compile(r"\[\s*FAILED\s*\]\s*([A-Za-z0-9_]+\.[A-Za-z0-9_]+)")
            for match in gtest_re.finditer(combined):
                t_name = match.group(1).strip()
                failures.append(
                    CompactedFailureFrame(
                        test_identifier=t_name,
                        file_path="unknown",
                        line_number=None,
                        error_type="GTestFailure",
                        diagnostic_message="Test failed",
                        context_snippet=None,
                    )
                )
        if not failures and exit_code != 0:
            failures.append(
                CompactedFailureFrame(
                    test_identifier="CTestFailure",
                    file_path="build",
                    line_number=None,
                    error_type="BuildOrRunError",
                    diagnostic_message=combined[-400:].strip(),
                    context_snippet=None,
                )
            )
        return failures

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        violations: List[StubViolation] = []
        if not file_path.is_file():
            return violations
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for idx, line in enumerate(content.splitlines(), start=1):
                for pattern, name, severity in self._stub_patterns:
                    if pattern.search(line):
                        violations.append(
                            StubViolation(
                                file_path=file_path,
                                line_number=idx,
                                severity=severity,
                                symbol_name=name,
                                pattern_matched=pattern.pattern,
                                snippet=line.strip(),
                            )
                        )
        except Exception:
            pass
        return violations

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        entities: List[SymbolEntity] = []
        lines: List[str] = []
        if file_path.is_file():
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
                sym_re = re.compile(r"^(?:template<.*?>\s*)?(?:class|struct|enum\s+class|enum)\s+([A-Za-z0-9_]+)")
                fn_re = re.compile(r"^[A-Za-z0-9_:<>&*]+\s+([A-Za-z0-9_:]+)\s*\([^)]*\)\s*(?:const)?\s*(?:noexcept)?\s*[{;]")
                for idx, line in enumerate(lines, start=1):
                    s_match = sym_re.match(line.strip())
                    if s_match:
                        entities.append(
                            SymbolEntity(
                                name=s_match.group(1),
                                kind=SymbolKind.STRUCT if "struct" in line else SymbolKind.CLASS,
                                start_line=idx,
                                end_line=idx,
                                signature=line.strip()[:100],
                            )
                        )
                    else:
                        f_match = fn_re.match(line.strip())
                        if f_match and not line.strip().startswith("return"):
                            entities.append(
                                SymbolEntity(
                                    name=f_match.group(1),
                                    kind=SymbolKind.FUNCTION,
                                    start_line=idx,
                                    end_line=idx,
                                    signature=line.strip()[:100],
                                )
                            )
            except Exception:
                pass
        outline_text = f"// === OUTLINE: {file_path.name} (Total: {len(lines)} LOC) ===\n"
        for e in entities:
            outline_text += f"{e.signature} [Line: {e.start_line}]\n"
        return SymbolOutline(file_path=file_path, total_lines=len(lines), entities=entities, raw_outline_text=outline_text)

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        lines = content.splitlines()
        if len(lines) <= max_lines:
            return content
        return "\n".join(lines[:15]) + f"\n    // ... [Folded: {len(lines) - 30} lines] ...\n" + "\n".join(lines[-15:])

    def get_developer_prompt_guidance(self) -> str:
        return (
            "C / C++ Guidelines:\n"
            "- Follow RAII and use smart pointers (`std::unique_ptr`, `std::shared_ptr`) instead of raw `new`/`delete`.\n"
            "- Avoid undefined behavior and ensure all switch branches and non-void functions return a valid value.\n"
            "- Never leave placeholder `abort()` or empty function stubs."
        )

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        files = list(workspace.glob("**/*.cpp")) + list(workspace.glob("**/*.hpp")) + list(workspace.glob("**/*.c")) + list(workspace.glob("**/*.h"))
        total_loc = 0
        for f in files:
            try:
                total_loc += len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            except Exception:
                pass
        return CodebaseMetrics(
            language=LanguageType.CPP,
            total_files=len(files),
            total_loc=total_loc,
            test_files_count=len([f for f in files if "test" in f.name.lower()]),
            test_loc=0,
            ecosystem_metadata={"cmake_exists": (workspace / "CMakeLists.txt").is_file()},
        )


# ============================================================================
# CONCRETE DRIVER: RustDriver
# ============================================================================

class RustDriver:
    """Driver for Rust ecosystem (Cargo check, Cargo test, JSON diagnostics)."""

    def __init__(self) -> None:
        self._stub_patterns: List[Tuple[Pattern[str], str, StubSeverity]] = [
            (re.compile(r'\btodo!\s*\(.*?\)', re.IGNORECASE), "todo!()", StubSeverity.CRITICAL),
            (re.compile(r'\bunimplemented!\s*\(.*?\)', re.IGNORECASE), "unimplemented!()", StubSeverity.CRITICAL),
            (re.compile(r'\bpanic!\s*\(\s*["\'](?:TODO|Not implemented|implement me)["\']\s*\)', re.IGNORECASE), 'panic!("TODO")', StubSeverity.CRITICAL),
            (re.compile(r'\bunreachable!\s*\(.*?\)', re.IGNORECASE), "unreachable!()", StubSeverity.CRITICAL),
            (re.compile(r'//\s*TODO\s*:\s*implement', re.IGNORECASE), "// TODO: implement", StubSeverity.CRITICAL),
            (re.compile(r'/\*\s*TODO\s*:\s*implement\s*\*/', re.IGNORECASE), "/* TODO: implement */", StubSeverity.CRITICAL),
        ]

    @property
    def language_type(self) -> LanguageType:
        return LanguageType.RUST

    @property
    def language_name(self) -> str:
        return "Rust"

    def detect(self, workspace: Path) -> bool:
        return (workspace / "Cargo.toml").is_file()

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        if not file_path.is_file():
            return SyntaxCheckResult(is_clean=False, error_count=1, error_messages=[f"File not found: {file_path}"], failing_file=file_path)

        cargo_bin = shutil.which("cargo")
        if not cargo_bin:
            return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=["cargo not found in path; skipping check."])

        # Find workspace root with Cargo.toml
        curr = file_path.parent
        ws = curr
        while curr != curr.parent:
            if (curr / "Cargo.toml").is_file():
                ws = curr
                break
            curr = curr.parent

        proc = subprocess.run(
            [cargo_bin, "check", "--message-format=json", "--quiet"],
            cwd=ws,
            capture_output=True,
            text=True,
            shell=False,
        )

        errors = []
        line_no = None
        col_no = None
        if proc.returncode != 0:
            for line in proc.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    diag = json.loads(line)
                    if diag.get("reason") == "compiler-message":
                        msg = diag.get("message", {})
                        if msg.get("level") == "error":
                            errors.append(msg.get("rendered", msg.get("message", "Rust error")))
                            spans = msg.get("spans", [])
                            if spans:
                                line_no = spans[0].get("line_start")
                                col_no = spans[0].get("column_start")
                except Exception:
                    pass
            if not errors and proc.stderr:
                errors = [proc.stderr.strip()]

            return SyntaxCheckResult(
                is_clean=len(errors) == 0,
                error_count=len(errors),
                error_messages=errors[:5],
                failing_file=file_path,
                line_number=line_no,
                column_number=col_no,
            )

        return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        cargo_bin = shutil.which("cargo")
        if cargo_bin:
            proc = subprocess.run([cargo_bin, "fmt"], cwd=workspace, capture_output=True, text=True)
            return proc.returncode == 0, proc.stdout
        return True, "cargo not found; skipped."

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        cargo_bin = shutil.which("cargo")
        if cargo_bin:
            proc = subprocess.run([cargo_bin, "clippy", "--message-format=json", "--", "-D", "warnings"], cwd=workspace, capture_output=True, text=True)
            violations = []
            for line in proc.stdout.splitlines():
                if not line.strip():
                    continue
                try:
                    diag = json.loads(line)
                    if diag.get("reason") == "compiler-message":
                        msg = diag.get("message", {})
                        if msg.get("level") in ("warning", "error"):
                            violations.append(msg.get("rendered", msg.get("message")))
                except Exception:
                    pass
            return StaticAnalysisResult(is_clean=len(violations) == 0, violation_count=len(violations), violations=violations[:10], tool_name="clippy")
        return StaticAnalysisResult(is_clean=True, violation_count=0, violations=[], tool_name="none")

    def has_test_suite(self, workspace: Path) -> bool:
        return (workspace / "Cargo.toml").is_file()

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        if target_test:
            return f"cargo test {target_test} -- --nocapture"
        return "cargo test -- --nocapture"

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        cmd = self.get_default_test_command(workspace, target_test)
        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            failures = self.parse_test_diagnostics(proc.stdout, proc.stderr, proc.returncode)
            status = TestStatus.PASSED if proc.returncode == 0 else TestStatus.FAILED
            summary = f"Rust test suite: {'PASSED' if proc.returncode == 0 else 'FAILED'} (Exit code: {proc.returncode})"
            return TestExecutionOutcome(
                status=status,
                exit_code=proc.returncode,
                total_tests=len(failures) if status == TestStatus.FAILED else 1,
                passed_tests=0 if status == TestStatus.FAILED else 1,
                failed_tests=len(failures),
                skipped_tests=0,
                duration_seconds=duration,
                raw_stdout=proc.stdout,
                raw_stderr=proc.stderr,
                compacted_failures=failures,
                compaction_summary=summary,
            )
        except subprocess.TimeoutExpired as te:
            return TestExecutionOutcome(
                status=TestStatus.TIMEOUT,
                exit_code=124,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                duration_seconds=float(timeout_seconds),
                raw_stdout=te.stdout or "",
                raw_stderr=te.stderr or "Execution timed out.",
                compacted_failures=[],
                compaction_summary=f"Rust test execution timed out after {timeout_seconds}s.",
            )

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        failures: List[CompactedFailureFrame] = []
        combined = stdout + "\n" + stderr
        # Match cargo test failure blocks: ---- test_name stdout ----
        rust_fail_re = re.compile(r"----\s+([A-Za-z0-9_:]+)\s+stdout\s+----\n(.*?)(?=\n----\s+[A-Za-z0-9_:]+\s+stdout\s+----|\nfailures:|\Z)", re.DOTALL)
        for match in rust_fail_re.finditer(combined):
            t_name = match.group(1).strip()
            body = match.group(2).strip()
            lines = body.splitlines()
            panic_msg = "Test failed"
            loc_path = "src"
            line_no = None
            for l in lines:
                if "panicked at" in l:
                    panic_msg = l.strip()
                    loc_m = re.search(r"panicked at .*?([A-Za-z0-9_./\\-]+\.rs):(\d+)", l)
                    if loc_m:
                        loc_path = loc_m.group(1)
                        line_no = int(loc_m.group(2))
                    break

            failures.append(
                CompactedFailureFrame(
                    test_identifier=t_name,
                    file_path=loc_path,
                    line_number=line_no,
                    error_type="RustPanic",
                    diagnostic_message=panic_msg[:300],
                    context_snippet="\n".join(lines[:6]),
                )
            )

        if not failures and exit_code != 0:
            failures.append(
                CompactedFailureFrame(
                    test_identifier="CargoTestFailure",
                    file_path="src",
                    line_number=None,
                    error_type="ExecutionError",
                    diagnostic_message=combined[-400:].strip(),
                    context_snippet=None,
                )
            )
        return failures

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        violations: List[StubViolation] = []
        if not file_path.is_file():
            return violations
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for idx, line in enumerate(content.splitlines(), start=1):
                for pattern, name, severity in self._stub_patterns:
                    if pattern.search(line):
                        violations.append(
                            StubViolation(
                                file_path=file_path,
                                line_number=idx,
                                severity=severity,
                                symbol_name=name,
                                pattern_matched=pattern.pattern,
                                snippet=line.strip(),
                            )
                        )
        except Exception:
            pass
        return violations

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        entities: List[SymbolEntity] = []
        lines: List[str] = []
        if file_path.is_file():
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
                sym_re = re.compile(r"^\s*(?:pub(?:\([a-z\s_]+\))?\s+)?(struct|enum|trait|fn|impl|mod)\s+([A-Za-z0-9_]+)")
                for idx, line in enumerate(lines, start=1):
                    m = sym_re.match(line)
                    if m:
                        kind_str, name = m.group(1), m.group(2)
                        kind = SymbolKind.FUNCTION
                        if kind_str == "struct":
                            kind = SymbolKind.STRUCT
                        elif kind_str == "enum":
                            kind = SymbolKind.ENUM
                        elif kind_str == "trait":
                            kind = SymbolKind.TRAIT
                        elif kind_str == "mod":
                            kind = SymbolKind.MODULE
                        elif kind_str == "impl":
                            kind = SymbolKind.CLASS
                        entities.append(
                            SymbolEntity(
                                name=name,
                                kind=kind,
                                start_line=idx,
                                end_line=idx,
                                signature=line.strip()[:100],
                            )
                        )
            except Exception:
                pass
        outline_text = f"// === OUTLINE: {file_path.name} (Total: {len(lines)} LOC) ===\n"
        for e in entities:
            outline_text += f"{e.signature} [Line: {e.start_line}]\n"
        return SymbolOutline(file_path=file_path, total_lines=len(lines), entities=entities, raw_outline_text=outline_text)

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        lines = content.splitlines()
        if len(lines) <= max_lines:
            return content
        return "\n".join(lines[:15]) + f"\n    // ... [Folded: {len(lines) - 30} lines] ...\n" + "\n".join(lines[-15:])

    def get_developer_prompt_guidance(self) -> str:
        return (
            "Rust Guidelines:\n"
            "- Strictly respect ownership, borrowing, and lifetime rules without unnecessary clones.\n"
            "- Prefer Result<T, E> and custom error enums with `thiserror` over panicking.\n"
            "- Never leave placeholder `todo!()` or `unimplemented!()` macros."
        )

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        files = list(workspace.glob("**/*.rs"))
        total_loc = 0
        for f in files:
            try:
                total_loc += len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            except Exception:
                pass
        return CodebaseMetrics(
            language=LanguageType.RUST,
            total_files=len(files),
            total_loc=total_loc,
            test_files_count=len([f for f in files if "test" in f.name.lower()]),
            test_loc=0,
            ecosystem_metadata={"cargo_exists": (workspace / "Cargo.toml").is_file()},
        )


# ============================================================================
# CONCRETE DRIVER: GoDriver
# ============================================================================

class GoDriver:
    """Driver for Go ecosystem (go vet, go build, go test -json)."""

    def __init__(self) -> None:
        self._stub_patterns: List[Tuple[Pattern[str], str, StubSeverity]] = [
            (re.compile(r'panic\s*\(\s*["\'](?:TODO|not implemented|implement me)["\']\s*\)', re.IGNORECASE), 'panic("TODO")', StubSeverity.CRITICAL),
            (re.compile(r'//\s*TODO\s*:\s*implement', re.IGNORECASE), "// TODO: implement", StubSeverity.CRITICAL),
            (re.compile(r'/\*\s*TODO\s*:\s*implement\s*\*/', re.IGNORECASE), "/* TODO: implement */", StubSeverity.CRITICAL),
        ]

    @property
    def language_type(self) -> LanguageType:
        return LanguageType.GO

    @property
    def language_name(self) -> str:
        return "Go"

    def detect(self, workspace: Path) -> bool:
        return (workspace / "go.mod").is_file() or (workspace / "go.work").is_file() or bool(list(workspace.glob("*.go")))

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        if not file_path.is_file():
            return SyntaxCheckResult(is_clean=False, error_count=1, error_messages=[f"File not found: {file_path}"], failing_file=file_path)

        go_bin = shutil.which("go")
        if not go_bin:
            return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=["go not found in path; skipping check."])

        proc = subprocess.run(
            [go_bin, "vet", str(file_path)],
            cwd=file_path.parent,
            capture_output=True,
            text=True,
            shell=False,
        )
        if proc.returncode != 0:
            lines = [l.strip() for l in proc.stderr.splitlines() if l.strip()]
            return SyntaxCheckResult(is_clean=False, error_count=len(lines), error_messages=lines[:5], failing_file=file_path)

        return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        gofmt = shutil.which("gofmt")
        if gofmt:
            proc = subprocess.run([gofmt, "-w", "."], cwd=workspace, capture_output=True, text=True)
            return proc.returncode == 0, proc.stdout
        return True, "gofmt not found; skipped."

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        golangci = shutil.which("golangci-lint")
        if golangci:
            proc = subprocess.run([golangci, "run", "--out-format=json"], cwd=workspace, capture_output=True, text=True)
            if proc.returncode != 0:
                try:
                    data = json.loads(proc.stdout)
                    violations = [f"{item.get('Pos', {}).get('Filename')}:{item.get('Pos', {}).get('Line')} - {item.get('Text')}" for item in data.get("Issues", [])]
                    return StaticAnalysisResult(is_clean=False, violation_count=len(violations), violations=violations[:10], tool_name="golangci-lint")
                except Exception:
                    pass
        return StaticAnalysisResult(is_clean=True, violation_count=0, violations=[], tool_name="none")

    def has_test_suite(self, workspace: Path) -> bool:
        return bool(list(workspace.glob("**/*_test.go")))

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        if target_test:
            return f"go test -v -run {target_test} ./..."
        return "go test -v ./..."

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        cmd = self.get_default_test_command(workspace, target_test)
        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            failures = self.parse_test_diagnostics(proc.stdout, proc.stderr, proc.returncode)
            status = TestStatus.PASSED if proc.returncode == 0 else TestStatus.FAILED
            summary = f"Go test suite: {'PASSED' if proc.returncode == 0 else 'FAILED'} (Exit code: {proc.returncode})"
            return TestExecutionOutcome(
                status=status,
                exit_code=proc.returncode,
                total_tests=len(failures) if status == TestStatus.FAILED else 1,
                passed_tests=0 if status == TestStatus.FAILED else 1,
                failed_tests=len(failures),
                skipped_tests=0,
                duration_seconds=duration,
                raw_stdout=proc.stdout,
                raw_stderr=proc.stderr,
                compacted_failures=failures,
                compaction_summary=summary,
            )
        except subprocess.TimeoutExpired as te:
            return TestExecutionOutcome(
                status=TestStatus.TIMEOUT,
                exit_code=124,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                duration_seconds=float(timeout_seconds),
                raw_stdout=te.stdout or "",
                raw_stderr=te.stderr or "Execution timed out.",
                compacted_failures=[],
                compaction_summary=f"Go test execution timed out after {timeout_seconds}s.",
            )

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        failures: List[CompactedFailureFrame] = []
        combined = stdout + "\n" + stderr
        # Match Go test run blocks: === RUN TestName ... --- FAIL: TestName
        go_block_re = re.compile(r"===\s+RUN\s+([A-Za-z0-9_]+)\n(.*?)(?=---\s+FAIL:\s+\1|\Z)", re.DOTALL)
        for match in go_block_re.finditer(combined):
            t_name = match.group(1).strip()
            body = match.group(2).strip()
            lines = body.splitlines()
            loc_match = re.search(r"^\s*([A-Za-z0-9_./\\-]+\.go):(\d+):", body, re.MULTILINE)
            f_path = loc_match.group(1) if loc_match else "unknown"
            line_no = int(loc_match.group(2)) if loc_match else None
            failures.append(
                CompactedFailureFrame(
                    test_identifier=t_name,
                    file_path=f_path,
                    line_number=line_no,
                    error_type="GoTestFailure",
                    diagnostic_message=lines[0] if lines else "Test failed",
                    context_snippet="\n".join(lines[:5]),
                )
            )

        # Fallback to direct --- FAIL: TestName if block pattern didn't match
        if not failures:
            go_fail_re = re.compile(r"---\s+FAIL:\s+([A-Za-z0-9_]+)")
            for match in go_fail_re.finditer(combined):
                t_name = match.group(1).strip()
                failures.append(
                    CompactedFailureFrame(
                        test_identifier=t_name,
                        file_path="unknown",
                        line_number=None,
                        error_type="GoTestFailure",
                        diagnostic_message="Test failed",
                        context_snippet=None,
                    )
                )

        if not failures and exit_code != 0:
            failures.append(
                CompactedFailureFrame(
                    test_identifier="GoSuiteFailure",
                    file_path="pkg",
                    line_number=None,
                    error_type="ExecutionError",
                    diagnostic_message=combined[-400:].strip(),
                    context_snippet=None,
                )
            )
        return failures

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        violations: List[StubViolation] = []
        if not file_path.is_file():
            return violations
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for idx, line in enumerate(content.splitlines(), start=1):
                for pattern, name, severity in self._stub_patterns:
                    if pattern.search(line):
                        violations.append(
                            StubViolation(
                                file_path=file_path,
                                line_number=idx,
                                severity=severity,
                                symbol_name=name,
                                pattern_matched=pattern.pattern,
                                snippet=line.strip(),
                            )
                        )
        except Exception:
            pass
        return violations

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        entities: List[SymbolEntity] = []
        lines: List[str] = []
        if file_path.is_file():
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
                type_re = re.compile(r"^type\s+([A-Za-z0-9_]+)\s+(struct|interface)")
                fn_re = re.compile(r"^func\s+(?:\([A-Za-z0-9_*,\s]+\)\s+)?([A-Za-z0-9_]+)\s*\(")
                for idx, line in enumerate(lines, start=1):
                    t_m = type_re.match(line.strip())
                    if t_m:
                        entities.append(
                            SymbolEntity(
                                name=t_m.group(1),
                                kind=SymbolKind.STRUCT if t_m.group(2) == "struct" else SymbolKind.INTERFACE,
                                start_line=idx,
                                end_line=idx,
                                signature=line.strip()[:100],
                            )
                        )
                    else:
                        f_m = fn_re.match(line.strip())
                        if f_m:
                            entities.append(
                                SymbolEntity(
                                    name=f_m.group(1),
                                    kind=SymbolKind.FUNCTION,
                                    start_line=idx,
                                    end_line=idx,
                                    signature=line.strip()[:100],
                                )
                            )
            except Exception:
                pass
        outline_text = f"// === OUTLINE: {file_path.name} (Total: {len(lines)} LOC) ===\n"
        for e in entities:
            outline_text += f"{e.signature} [Line: {e.start_line}]\n"
        return SymbolOutline(file_path=file_path, total_lines=len(lines), entities=entities, raw_outline_text=outline_text)

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        lines = content.splitlines()
        if len(lines) <= max_lines:
            return content
        return "\n".join(lines[:15]) + f"\n    // ... [Folded: {len(lines) - 30} lines] ...\n" + "\n".join(lines[-15:])

    def get_developer_prompt_guidance(self) -> str:
        return (
            "Go Guidelines:\n"
            "- Handle all errors explicitly with `if err != nil { return ... }`.\n"
            "- Use idiomatic goroutines and channels; ensure proper synchronization with `sync.WaitGroup` or context.\n"
            "- Never leave placeholder `panic(\"TODO\")` stubs."
        )

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        files = list(workspace.glob("**/*.go"))
        total_loc = 0
        for f in files:
            try:
                total_loc += len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            except Exception:
                pass
        return CodebaseMetrics(
            language=LanguageType.GO,
            total_files=len(files),
            total_loc=total_loc,
            test_files_count=len([f for f in files if f.name.endswith("_test.go")]),
            test_loc=0,
            ecosystem_metadata={"go_mod_exists": (workspace / "go.mod").is_file()},
        )


# ============================================================================
# CONCRETE DRIVER: SelfAdaptingPolyglotDriver (Dynamic Polyglot Adaptation)
# ============================================================================

class SelfAdaptingPolyglotDriver:
    """Dynamic, self-adapting language driver for unmapped or modern ecosystems.

    Governed by the "One-Time Dynamic Probe & Persistent Cache" lifecycle:
    1. If `<workspace>/.oragai/language_profile.json` exists, it is loaded deterministically.
       All subsequent operations execute with zero LLM token consumption.
    2. If missing, a one-time bounded dynamic probe synthesizes an ecosystem profile,
       validates commands through P9's CommandGrammarValidator, and caches it atomically.
    3. All command execution routes through P9's TerminalSandboxEngine / hardened subprocess.
    """

    PROFILE_FILENAME: str = "language_profile.json"
    ORAGAI_DIR: str = ".oragai"

    # Known fallback discovery signatures for unmapped languages
    DISCOVERY_SIGNATURES: Dict[str, Tuple[List[str], str, str, List[str], List[str]]] = {
        "zig": (
            ["build.zig", "build.zig.zon"],
            "zig ast-check {file_path}",
            "zig test {target_test}",
            [
                r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<message>.+)$",
                r"^(?P<test>[^\n]+)\.\.\.FAIL\s+\((?P<message>[^\)]+)\)$",
            ],
            [
                r"@panic\s*\(\s*[\"'](?:TODO|Not implemented|implement me)[\"']\s*\)",
                r"//\s*TODO\s*:\s*implement",
            ],
        ),
        "elixir": (
            ["mix.exs"],
            "mix compile --warnings-as-errors",
            "mix test {target_test}",
            [
                r"^\s*\d+\)\s+test\s+(?P<test>.+)\s+\((?P<file>.+):(?P<line>\d+)\)\s*\n\s+(?P<message>.+)$",
                r"\*\* \((?P<type>\w+)\)\s+(?P<message>.+)",
            ],
            [
                r"raise\s+[\"']TODO[\"']",
                r"#\s*TODO\s*:\s*implement",
            ],
        ),
        "swift": (
            ["Package.swift"],
            "swiftc -typecheck {file_path}",
            "swift test --filter {target_test}",
            [
                r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<message>.+)$",
                r"Test Case '(?P<test>[^']+)' failed",
            ],
            [
                r"fatalError\s*\(\s*[\"'](?:TODO|Not implemented)[\"']\s*\)",
                r"//\s*TODO\s*:\s*implement",
            ],
        ),
        "kotlin": (
            ["build.gradle.kts"],
            "kotlinc -Werror -nowarn {file_path}",
            "gradle test --tests {target_test}",
            [
                r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<message>.+)$",
                r"FAILURE: Test (?P<test>.+) failed",
            ],
            [
                r"\bTODO\s*\(\s*[\"']?.*?[\"']?\s*\)",
                r"//\s*TODO\s*:\s*implement",
            ],
        ),
        "nim": (
            ["nim.cfg"],
            "nim check {file_path}",
            "nim c -r {target_test}",
            [
                r"^(?P<file>[^:\n]+)\((?P<line>\d+),\s*(?P<col>\d+)\)\s+Error:\s+(?P<message>.+)$",
            ],
            [
                r"quit\s*\(\s*[\"']TODO[\"']\s*\)",
                r"#\s*TODO\s*:\s*implement",
            ],
        ),
    }

    def __init__(
        self,
        workspace: Optional[Path] = None,
        probe_fn: Optional[Callable[[Path], DynamicEcosystemProfile]] = None,
    ) -> None:
        self._workspace: Optional[Path] = workspace
        self._probe_fn: Optional[Callable[[Path], DynamicEcosystemProfile]] = probe_fn
        self._profile: Optional[DynamicEcosystemProfile] = None
        self._compiled_failure_regexes: List[Pattern[str]] = []
        self._compiled_stub_regexes: List[Tuple[Pattern[str], str, StubSeverity]] = []
        self._discovery_probe_invoked: bool = False

        if self._workspace:
            profile_path = self._workspace / self.ORAGAI_DIR / self.PROFILE_FILENAME
            if profile_path.is_file():
                self._load_cached_profile(profile_path)

    @property
    def language_type(self) -> LanguageType:
        return LanguageType.GENERIC

    @property
    def language_name(self) -> str:
        if self._profile:
            return f"Self-Adapting ({self._profile.language_name})"
        return "Self-Adapting Polyglot Dynamic Driver"

    @property
    def active_profile(self) -> Optional[DynamicEcosystemProfile]:
        """Return the loaded ecosystem profile if initialized."""
        return self._profile

    def detect(self, workspace: Path) -> bool:
        """Evaluate if cached profile exists or if unknown manifests are present."""
        if (workspace / self.ORAGAI_DIR / self.PROFILE_FILENAME).is_file():
            return True
        for lang, (manifests, _, _, _, _) in self.DISCOVERY_SIGNATURES.items():
            if any((workspace / m).is_file() for m in manifests):
                return True
        return (workspace / "Makefile").is_file() or (workspace / "Dockerfile").is_file()

    def ensure_profile_loaded(self, workspace: Path) -> DynamicEcosystemProfile:
        """Deterministic loader: read cached profile or trigger one-time discovery probe."""
        if self._profile and self._workspace == workspace:
            return self._profile

        self._workspace = workspace
        profile_path = workspace / self.ORAGAI_DIR / self.PROFILE_FILENAME

        if profile_path.is_file():
            # FAST PATH: Cached profile on disk, zero LLM tokens consumed
            self._load_cached_profile(profile_path)
            return self._profile

        # ONE-TIME DISCOVERY PROBE: synthesize, validate, persist
        profile = self._execute_one_time_discovery_probe(workspace)
        self._validate_profile_security(profile)
        self._persist_profile(workspace, profile)
        self._apply_profile(profile)
        return self._profile

    def _load_cached_profile(self, profile_path: Path) -> None:
        """Load and deserialize profile JSON from disk with zero token consumption."""
        raw_text = profile_path.read_text(encoding="utf-8")
        profile = DynamicEcosystemProfile.model_validate_json(raw_text)
        self._apply_profile(profile)

    def _apply_profile(self, profile: DynamicEcosystemProfile) -> None:
        """Compile failure and stub regex patterns from the profile."""
        self._profile = profile
        self._compiled_failure_regexes = []
        for pat in profile.failure_regexes:
            try:
                self._compiled_failure_regexes.append(re.compile(pat, re.MULTILINE))
            except re.error:
                continue

        self._compiled_stub_regexes = []
        for pat in profile.stub_regexes:
            try:
                compiled = re.compile(pat, re.IGNORECASE)
                self._compiled_stub_regexes.append((compiled, pat[:40], StubSeverity.CRITICAL))
            except re.error:
                continue

    def _execute_one_time_discovery_probe(self, workspace: Path) -> DynamicEcosystemProfile:
        """Execute the one-time Architect/Discovery persona probe or deterministic fallback."""
        self._discovery_probe_invoked = True

        if self._probe_fn:
            return self._probe_fn(workspace)

        # Built-in deterministic probe heuristic across known signatures
        for lang_name, (manifests, syntax_cmd, test_cmd, failure_pats, stub_pats) in self.DISCOVERY_SIGNATURES.items():
            if any((workspace / m).is_file() for m in manifests):
                return DynamicEcosystemProfile(
                    language_name=lang_name,
                    manifest_files=manifests,
                    file_extensions=[f".{lang_name}"],
                    syntax_check_template=syntax_cmd,
                    test_command_template=test_cmd,
                    failure_regexes=failure_pats,
                    stub_regexes=stub_pats,
                    symbol_outline_command=None,
                    version="1.0.0",
                )

        # Default generic fallback profile
        return DynamicEcosystemProfile(
            language_name="generic",
            manifest_files=["Makefile"],
            file_extensions=[],
            syntax_check_template="make -n",
            test_command_template="make test {target_test}",
            failure_regexes=[
                r"(?i)(?:FAIL|ERROR|Exception|AssertionError):\s*(?P<message>.+)",
                r"(?P<file>[^:\n]+):(?P<line>\d+):\s*(?P<message>.+)",
            ],
            stub_regexes=[
                r"\b(?:TODO|FIXME|XXX|NOT_IMPLEMENTED)\b",
            ],
            symbol_outline_command=None,
            version="1.0.0",
        )

    def _validate_profile_security(self, profile: DynamicEcosystemProfile) -> None:
        """P9 CommandGrammarValidator Seam: verify command templates for shell injection."""
        dangerous_operators = [";", "&&", "||", "`", "$(", ">", "<", "\n", "\r"]
        for tmpl in (profile.syntax_check_template, profile.test_command_template, profile.symbol_outline_command):
            if not tmpl:
                continue
            for op in dangerous_operators:
                if op in tmpl:
                    raise ValueError(
                        f"P9 Security Violation: Command template '{tmpl}' contains disallowed shell operator '{op}'."
                    )

    def _persist_profile(self, workspace: Path, profile: DynamicEcosystemProfile) -> None:
        """Atomically persist synthesized profile to disk at `<workspace>/.oragai/language_profile.json`."""
        target_dir = workspace / self.ORAGAI_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        final_path = target_dir / self.PROFILE_FILENAME

        # Write to temporary file first, then atomically replace
        temp_fd, temp_path_str = tempfile.mkstemp(dir=target_dir, prefix="lang_prof_", suffix=".tmp")
        temp_path = Path(temp_path_str)
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                f.write(profile.model_dump_json(indent=2))
            temp_path.replace(final_path)
        except Exception:
            if temp_path.is_file():
                temp_path.unlink()
            raise

    def check_syntax(self, file_path: Path) -> SyntaxCheckResult:
        """Execute cached syntax check template via local subprocess (zero LLM tokens)."""
        workspace = self._workspace or file_path.parent
        profile = self.ensure_profile_loaded(workspace)

        cmd_str = profile.syntax_check_template.replace("{file_path}", str(file_path.resolve()))
        args = shlex.split(cmd_str, posix=False)

        try:
            proc = subprocess.run(
                args,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=False,
                timeout=30,
            )
            if proc.returncode == 0:
                return SyntaxCheckResult(is_clean=True, error_count=0, error_messages=[])

            combined = proc.stderr.strip() or proc.stdout.strip()
            errors = [l.strip() for l in combined.splitlines() if l.strip()]
            line_no = None
            for pat in self._compiled_failure_regexes:
                match = pat.search(combined)
                if match and "line" in match.groupdict():
                    try:
                        line_no = int(match.group("line"))
                        break
                    except (ValueError, TypeError):
                        pass

            return SyntaxCheckResult(
                is_clean=False,
                error_count=len(errors) if errors else 1,
                error_messages=errors[:5] if errors else [combined[:300]],
                failing_file=file_path,
                line_number=line_no,
            )
        except Exception as e:
            return SyntaxCheckResult(
                is_clean=False,
                error_count=1,
                error_messages=[f"Syntax check execution error: {str(e)}"],
                failing_file=file_path,
            )

    def run_zero_token_autofix(self, workspace: Path) -> Tuple[bool, str]:
        return True, "No dynamic autofix configured; skipped."

    def run_static_analysis(self, workspace: Path) -> StaticAnalysisResult:
        return StaticAnalysisResult(is_clean=True, violation_count=0, violations=[], tool_name="dynamic")

    def has_test_suite(self, workspace: Path) -> bool:
        profile = self.ensure_profile_loaded(workspace)
        return any((workspace / m).is_file() for m in profile.manifest_files)

    def get_default_test_command(
        self, workspace: Path, target_test: Optional[str] = None
    ) -> str:
        profile = self.ensure_profile_loaded(workspace)
        target = target_test.strip() if target_test else ""
        return profile.test_command_template.replace("{target_test}", target).strip()

    def execute_test_suite(
        self,
        workspace: Path,
        target_test: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> TestExecutionOutcome:
        profile = self.ensure_profile_loaded(workspace)
        cmd_str = self.get_default_test_command(workspace, target_test)
        args = shlex.split(cmd_str, posix=False)

        start_time = time.time()
        try:
            proc = subprocess.run(
                args,
                cwd=workspace,
                capture_output=True,
                text=True,
                shell=False,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            failures = self.parse_test_diagnostics(proc.stdout, proc.stderr, proc.returncode)
            status = TestStatus.PASSED if proc.returncode == 0 else TestStatus.FAILED
            summary = (
                f"{profile.language_name} test suite: "
                f"{'PASSED' if proc.returncode == 0 else 'FAILED'} (Exit code: {proc.returncode})"
            )
            return TestExecutionOutcome(
                status=status,
                exit_code=proc.returncode,
                total_tests=len(failures) if status == TestStatus.FAILED else 1,
                passed_tests=0 if status == TestStatus.FAILED else 1,
                failed_tests=len(failures),
                skipped_tests=0,
                duration_seconds=duration,
                raw_stdout=proc.stdout,
                raw_stderr=proc.stderr,
                compacted_failures=failures,
                compaction_summary=summary,
            )
        except subprocess.TimeoutExpired as te:
            return TestExecutionOutcome(
                status=TestStatus.TIMEOUT,
                exit_code=124,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                duration_seconds=float(timeout_seconds),
                raw_stdout=te.stdout or "",
                raw_stderr=te.stderr or "Execution timed out.",
                compacted_failures=[],
                compaction_summary=f"Dynamic test execution timed out after {timeout_seconds}s.",
            )

    def parse_test_diagnostics(
        self, stdout: str, stderr: str, exit_code: int
    ) -> List[CompactedFailureFrame]:
        failures: List[CompactedFailureFrame] = []
        combined = stdout + "\n" + stderr

        for pat in self._compiled_failure_regexes:
            for match in pat.finditer(combined):
                groups = match.groupdict()
                t_id = groups.get("test") or "TestFailure"
                f_path = groups.get("file") or "workspace"
                line_str = groups.get("line")
                line_no = int(line_str) if line_str and line_str.isdigit() else None
                diag = groups.get("message") or match.group(0)[:200]

                failures.append(
                    CompactedFailureFrame(
                        test_identifier=t_id.strip(),
                        file_path=f_path.strip(),
                        line_number=line_no,
                        error_type="DynamicEcosystemFailure",
                        diagnostic_message=diag.strip()[:300],
                        context_snippet=match.group(0)[:400].strip(),
                    )
                )

        if not failures and exit_code != 0:
            failures.append(
                CompactedFailureFrame(
                    test_identifier="DynamicProcessFailure",
                    file_path="workspace",
                    line_number=None,
                    error_type="ExecutionError",
                    diagnostic_message=combined[-400:].strip() if combined.strip() else "Process failed with non-zero exit code.",
                    context_snippet=None,
                )
            )
        return failures

    def detect_placeholders_and_stubs(self, file_path: Path) -> List[StubViolation]:
        violations: List[StubViolation] = []
        if not file_path.is_file():
            return violations
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for idx, line in enumerate(content.splitlines(), start=1):
                for pattern, name, severity in self._compiled_stub_regexes:
                    if pattern.search(line):
                        violations.append(
                            StubViolation(
                                file_path=file_path,
                                line_number=idx,
                                severity=severity,
                                symbol_name=name,
                                pattern_matched=pattern.pattern,
                                snippet=line.strip(),
                            )
                        )
        except Exception:
            pass
        return violations

    def extract_symbol_outline(self, file_path: Path) -> SymbolOutline:
        entities: List[SymbolEntity] = []
        lines: List[str] = []
        if file_path.is_file():
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
                sym_re = re.compile(r"^\s*(?:pub\s+)?(fn|def|func|function|type|struct|class|enum|trait)\s+([A-Za-z0-9_]+)")
                for idx, line in enumerate(lines, start=1):
                    m = sym_re.match(line)
                    if m:
                        kind_str, name = m.group(1), m.group(2)
                        kind = SymbolKind.FUNCTION
                        if kind_str in ("struct", "class"):
                            kind = SymbolKind.CLASS
                        elif kind_str in ("trait", "interface"):
                            kind = SymbolKind.INTERFACE
                        elif kind_str == "enum":
                            kind = SymbolKind.ENUM
                        entities.append(
                            SymbolEntity(
                                name=name,
                                kind=kind,
                                start_line=idx,
                                end_line=idx,
                                signature=line.strip()[:100],
                            )
                        )
            except Exception:
                pass
        outline_text = f"// === OUTLINE: {file_path.name} (Total: {len(lines)} LOC) ===\n"
        for e in entities:
            outline_text += f"{e.signature} [Line: {e.start_line}]\n"
        return SymbolOutline(file_path=file_path, total_lines=len(lines), entities=entities, raw_outline_text=outline_text)

    def fold_code_block(self, content: str, max_lines: int = 50) -> str:
        lines = content.splitlines()
        if len(lines) <= max_lines:
            return content
        return "\n".join(lines[:15]) + f"\n    // ... [Folded: {len(lines) - 30} lines] ...\n" + "\n".join(lines[-15:])

    def get_developer_prompt_guidance(self) -> str:
        name = self._profile.language_name if self._profile else "Generic Polyglot"
        return (
            f"{name.capitalize()} Dynamic Ecosystem Guidelines:\n"
            f"- Strictly observe idiomatic patterns for {name}.\n"
            "- Implement all functions fully without leaving placeholder comments or stub exceptions.\n"
            "- Ensure all return types and error conditions match the module interface."
        )

    def collect_codebase_metrics(self, workspace: Path) -> CodebaseMetrics:
        profile = self.ensure_profile_loaded(workspace)
        extensions = set(profile.file_extensions) if profile.file_extensions else {".txt"}
        all_files: List[Path] = []
        for root, _, filenames in os.walk(workspace):
            if any(d in root for d in (".git", ".oragai", "target", "vendor", "node_modules")):
                continue
            for fn in filenames:
                if any(fn.endswith(ext) for ext in extensions):
                    all_files.append(Path(root) / fn)

        total_loc = 0
        for f in all_files:
            try:
                total_loc += len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            except Exception:
                pass

        test_files = [f for f in all_files if "test" in f.name.lower()]
        return CodebaseMetrics(
            language=LanguageType.GENERIC,
            total_files=len(all_files),
            total_loc=total_loc,
            test_files_count=len(test_files),
            test_loc=0,
            ecosystem_metadata={"profile": profile.language_name, "version": profile.version},
        )


# ============================================================================
# DRIVER REGISTRY
# ============================================================================

class PolyglotDriverRegistry:
    """Central registry and routing engine for Language Drivers."""

    def __init__(self) -> None:
        self._drivers: Dict[LanguageType, ILanguageDriver] = {}
        self._sub_workspace_cache: Dict[Path, ILanguageDriver] = {}
        
        # Register standard built-in drivers by default
        self.register(PythonDriver())
        self.register(NodeDriver())
        self.register(CDriver())
        self.register(RustDriver())
        self.register(GoDriver())
        self.register(SelfAdaptingPolyglotDriver())

    def register(self, driver: ILanguageDriver) -> None:
        """Register a concrete language driver instance."""
        self._drivers[driver.language_type] = driver

    def get_driver(self, language_type: LanguageType) -> Optional[ILanguageDriver]:
        """Retrieve driver by LanguageType."""
        return self._drivers.get(language_type)

    def resolve_driver_for_path(
        self, file_or_dir_path: Path, root_workspace: Path
    ) -> ILanguageDriver:
        """Resolve the most specific driver for a given file or directory path."""
        abs_path = file_or_dir_path.resolve()
        abs_root = root_workspace.resolve()

        # Check sub-workspace cache
        for sub_path, driver in self._sub_workspace_cache.items():
            if abs_path == sub_path or abs_path.is_relative_to(sub_path):
                return driver

        # Walk upward from file_or_dir_path to root_workspace to find sub-manifest
        current = abs_path if abs_path.is_dir() else abs_path.parent
        while current >= abs_root:
            for driver in self._drivers.values():
                if driver.language_type != LanguageType.GENERIC and driver.detect(current):
                    self._sub_workspace_cache[current] = driver
                    return driver
            if current == abs_root:
                break
            current = current.parent

        # Fallback to root detection
        for driver in self._drivers.values():
            if driver.language_type != LanguageType.GENERIC and driver.detect(abs_root):
                return driver

        # Fallback to SelfAdaptingPolyglotDriver
        self_adapting = self._drivers.get(LanguageType.GENERIC)
        if self_adapting:
            return self_adapting
        raise RuntimeError("No suitable LanguageDriver registered, including SelfAdaptingPolyglotDriver.")
