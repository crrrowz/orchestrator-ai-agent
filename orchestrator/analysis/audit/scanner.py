"""Zero-Token Deterministic Pre-Audit Static Analysis Scanner (P7)."""

from __future__ import annotations

import ast
import hashlib
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from orchestrator.analysis.audit.models import (
    FindingCategory,
    FindingSeverity,
    FindingSource,
    VerifiedAuditFinding,
)


class StaticAnalysisScanner:
    """Executes zero-token AST, security regex, and linter inspection across workspace."""

    SECRET_PATTERNS = [
        (re.compile(r"sk-[a-zA-Z0-9]{32,}"), "OpenAI API Key Leakage", "CWE-798"),
        (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Personal Access Token Leakage", "CWE-798"),
        (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID Leakage", "CWE-798"),
        (re.compile(r"subprocess\.(?:Popen|run|call)\([^)]*shell\s*=\s*True"), "Insecure shell=True Subprocess Execution", "CWE-78"),
        (re.compile(r"pickle\.loads\("), "Insecure Object Deserialization via pickle.loads", "CWE-502"),
    ]

    STUB_PATTERNS = [
        (re.compile(r"#\s*(?:TODO|FIXME|STUB|PLACEHOLDER):?\s*(.*)", re.IGNORECASE), "Unresolved Codebase TODO / Placeholder"),
    ]

    EXCLUDE_DIRS = {
        ".venv", "venv", ".git", "__pycache__", "build", "dist",
        ".pytest_cache", ".ruff_cache", "site-packages", "node_modules"
    }

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path.resolve()

    def scan_workspace(self) -> List[VerifiedAuditFinding]:
        """Perform full zero-token static scan across all Python files in the workspace."""
        findings: List[VerifiedAuditFinding] = []

        for root, dirs, files in os.walk(self.workspace_path):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]

            for file in files:
                if not file.endswith(".py"):
                    continue
                full_path = Path(root) / file
                try:
                    rel_path = str(full_path.relative_to(self.workspace_path)).replace("\\", "/")
                except ValueError:
                    continue

                if any(part in self.EXCLUDE_DIRS for part in rel_path.split("/")):
                    continue

                try:
                    content = full_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue

                # 1. AST Syntax & Complexity Scan
                findings.extend(self._scan_ast(rel_path, content))

                # 2. Security Regex Scan
                findings.extend(self._scan_security_regex(rel_path, content))

                # 3. Banned Stub Scan
                findings.extend(self._scan_stubs(rel_path, content))

        # 4. Circular Import Dependency Scan
        findings.extend(self._scan_circular_dependencies())

        return findings

    def _scan_ast(self, rel_path: str, content: str) -> List[VerifiedAuditFinding]:
        findings: List[VerifiedAuditFinding] = []
        try:
            tree = ast.parse(content, filename=rel_path)
        except SyntaxError as e:
            finding = VerifiedAuditFinding(
                finding_id=f"SYNTAX-{hashlib.sha256(rel_path.encode()).hexdigest()[:6]}",
                category=FindingCategory.RELIABILITY,
                severity=FindingSeverity.CRITICAL,
                source=FindingSource.STATIC_AST,
                file_path=rel_path,
                line_start=e.lineno or 1,
                line_end=e.lineno or 1,
                ast_symbol="",
                code_snippet=e.text.strip() if e.text else "SyntaxError",
                problem_statement=f"Python Syntax Error: {e.msg}",
                remediation_proposal="Fix malformed Python syntax to restore valid AST compilation.",
                confidence=1.0,
            )
            finding.sha256_fingerprint = finding.compute_fingerprint()
            findings.append(finding)
            return findings

        # AST Function Complexity & Public Stub Inspection
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Detect empty stub functions (body is only pass, Ellipsis, or raise NotImplementedError)
                real_stmts: List[ast.stmt] = []
                for idx, stmt in enumerate(node.body):
                    if idx == 0 and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                        # Docstring
                        continue
                    real_stmts.append(stmt)

                is_stub = False
                if len(real_stmts) == 1:
                    stmt = real_stmts[0]
                    if isinstance(stmt, ast.Pass):
                        is_stub = True
                    elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
                        is_stub = True
                    elif isinstance(stmt, ast.Raise):
                        if isinstance(stmt.exc, ast.Name) and stmt.exc.id == "NotImplementedError":
                            is_stub = True
                        elif isinstance(stmt.exc, ast.Call) and isinstance(stmt.exc.func, ast.Name) and stmt.exc.func.id == "NotImplementedError":
                            is_stub = True

                if is_stub and not node.name.startswith("_"):
                    finding = VerifiedAuditFinding(
                        finding_id=f"STUB-{hashlib.sha256(f'{rel_path}:{node.name}'.encode()).hexdigest()[:6]}",
                        category=FindingCategory.ARCHITECTURE,
                        severity=FindingSeverity.HIGH,
                        source=FindingSource.STATIC_AST,
                        file_path=rel_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        ast_symbol=node.name,
                        code_snippet=f"def {node.name}(...): ...",
                        problem_statement=f"Public function '{node.name}' is an unimplemented placeholder/stub.",
                        remediation_proposal=f"Provide complete, production-grade implementation for '{node.name}'.",
                        confidence=1.0,
                    )
                    finding.sha256_fingerprint = finding.compute_fingerprint()
                    findings.append(finding)

                # Cyclomatic Complexity Calculation
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 15:
                    finding = VerifiedAuditFinding(
                        finding_id=f"COMPLEX-{hashlib.sha256(f'{rel_path}:{node.name}'.encode()).hexdigest()[:6]}",
                        category=FindingCategory.MAINTAINABILITY,
                        severity=FindingSeverity.MEDIUM,
                        source=FindingSource.STATIC_AST,
                        file_path=rel_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        ast_symbol=node.name,
                        code_snippet=f"def {node.name}(...): [Complexity = {complexity}]",
                        problem_statement=f"Function '{node.name}' has excessive cyclomatic complexity ({complexity} > 15).",
                        remediation_proposal=f"Decompose '{node.name}' into modular, single-responsibility helper functions.",
                        confidence=1.0,
                    )
                    finding.sha256_fingerprint = finding.compute_fingerprint()
                    findings.append(finding)

        return findings

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of an AST function node."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.IfExp, ast.Match)):
                complexity += 1
        return complexity

    def _scan_security_regex(self, rel_path: str, content: str) -> List[VerifiedAuditFinding]:
        findings: List[VerifiedAuditFinding] = []
        lines = content.splitlines()
        for pattern, desc, cwe in self.SECRET_PATTERNS:
            for idx, line in enumerate(lines, start=1):
                if pattern.search(line):
                    finding = VerifiedAuditFinding(
                        finding_id=f"SEC-{hashlib.sha256(f'{rel_path}:{idx}'.encode()).hexdigest()[:6]}",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.CRITICAL,
                        source=FindingSource.SECRET_SCAN,
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        ast_symbol="",
                        code_snippet=line.strip()[:100],
                        problem_statement=f"Security Hazard: {desc}",
                        remediation_proposal="Sanitize secrets or replace insecure calls with parameterized APIs.",
                        cwe_id=cwe,
                        confidence=1.0,
                    )
                    finding.sha256_fingerprint = finding.compute_fingerprint()
                    findings.append(finding)
        return findings

    def _scan_stubs(self, rel_path: str, content: str) -> List[VerifiedAuditFinding]:
        findings: List[VerifiedAuditFinding] = []
        lines = content.splitlines()
        for pattern, desc in self.STUB_PATTERNS:
            for idx, line in enumerate(lines, start=1):
                m = pattern.search(line)
                if m:
                    todo_text = m.group(1).strip()
                    finding = VerifiedAuditFinding(
                        finding_id=f"TODO-{hashlib.sha256(f'{rel_path}:{idx}'.encode()).hexdigest()[:6]}",
                        category=FindingCategory.MAINTAINABILITY,
                        severity=FindingSeverity.LOW,
                        source=FindingSource.STATIC_AST,
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        ast_symbol="",
                        code_snippet=line.strip(),
                        problem_statement=f"{desc}: '{todo_text}'",
                        remediation_proposal="Resolve the pending TODO item or remove obsolete comment.",
                        confidence=0.9,
                    )
                    finding.sha256_fingerprint = finding.compute_fingerprint()
                    findings.append(finding)
        return findings

    def _scan_circular_dependencies(self) -> List[VerifiedAuditFinding]:
        """Detect circular import cycles across workspace packages using Tarjan's SCC."""
        findings: List[VerifiedAuditFinding] = []
        import_graph: Dict[str, Set[str]] = {}
        file_map: Dict[str, str] = {}

        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            for file in files:
                if not file.endswith(".py"):
                    continue
                full_path = Path(root) / file
                try:
                    rel_path = str(full_path.relative_to(self.workspace_path)).replace("\\", "/")
                except ValueError:
                    continue

                if any(part in self.EXCLUDE_DIRS for part in rel_path.split("/")):
                    continue

                mod_name = rel_path.replace(".py", "").replace("/", ".")
                # Also handle __init__.py module names (e.g. pkg.__init__ -> pkg)
                if mod_name.endswith(".__init__"):
                    clean_mod = mod_name[:-9]
                    file_map[clean_mod] = rel_path
                file_map[mod_name] = rel_path
                import_graph[mod_name] = set()

                try:
                    tree = ast.parse(full_path.read_text(encoding="utf-8", errors="replace"))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                import_graph[mod_name].add(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                import_graph[mod_name].add(node.module)
                            elif node.level and node.level > 0:
                                # Relative import resolution
                                mod_parts = mod_name.split(".")
                                if mod_name.endswith(".__init__"):
                                    mod_parts = mod_parts[:-1]
                                base_parts = mod_parts[:max(0, len(mod_parts) - node.level + 1)]
                                rel_mod = ".".join(base_parts)
                                if rel_mod:
                                    import_graph[mod_name].add(rel_mod)
                except Exception:
                    continue

        # Filter import_graph edges to only target internal workspace modules
        filtered_graph: Dict[str, Set[str]] = {m: set() for m in import_graph}
        for mod, targets in import_graph.items():
            for t in targets:
                # Direct match
                if t in file_map and t != mod:
                    filtered_graph[mod].add(t)
                else:
                    # Check prefix matching (e.g., imported pkg.sub.func where pkg.sub is in file_map)
                    parts = t.split(".")
                    for i in range(len(parts), 0, -1):
                        prefix = ".".join(parts[:i])
                        if prefix in file_map and prefix != mod:
                            filtered_graph[mod].add(prefix)
                            break

        # Detect cycles using Tarjan's SCC
        sccs = self._tarjan_scc(filtered_graph)
        for scc in sccs:
            if len(scc) > 1:
                cycle_mods = sorted(list(scc))
                primary_file = file_map.get(cycle_mods[0], f"{cycle_mods[0].replace('.', '/')}.py")
                finding = VerifiedAuditFinding(
                    finding_id=f"ARCH-CYCLE-{hashlib.sha256('->'.join(cycle_mods).encode()).hexdigest()[:6]}",
                    category=FindingCategory.ARCHITECTURE,
                    severity=FindingSeverity.HIGH,
                    source=FindingSource.COUPLING_ANALYZER,
                    file_path=primary_file,
                    line_start=1,
                    line_end=1,
                    ast_symbol="",
                    code_snippet=" -> ".join(cycle_mods[:4]) + (" -> ..." if len(cycle_mods) > 4 else ""),
                    problem_statement=f"Circular import dependency detected involving {len(cycle_mods)} modules: {', '.join(cycle_mods[:3])}...",
                    remediation_proposal="Decouple cyclic dependency using Inversion of Control, protocol abstraction, or local imports.",
                    blast_radius_files=[file_map[m] for m in cycle_mods if m in file_map],
                    confidence=1.0,
                )
                finding.sha256_fingerprint = finding.compute_fingerprint()
                findings.append(finding)

        return findings

    def _tarjan_scc(self, graph: Dict[str, Set[str]]) -> List[Set[str]]:
        """Tarjan's algorithm for finding Strongly Connected Components."""
        index = 0
        indices: Dict[str, int] = {}
        lowlinks: Dict[str, int] = {}
        stack: List[str] = []
        on_stack: Set[str] = set()
        sccs: List[Set[str]] = []

        def strongconnect(node: str) -> None:
            nonlocal index
            indices[node] = index
            lowlinks[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in indices:
                    strongconnect(neighbor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
                elif neighbor in on_stack:
                    lowlinks[node] = min(lowlinks[node], indices[neighbor])

            if lowlinks[node] == indices[node]:
                scc: Set[str] = set()
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.add(w)
                    if w == node:
                        break
                sccs.append(scc)

        for n in list(graph.keys()):
            if n not in indices:
                strongconnect(n)

        return sccs
