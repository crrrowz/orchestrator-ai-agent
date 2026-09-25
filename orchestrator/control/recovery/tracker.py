"""Semantic Progress Tracker for ORAGAI (P8).

Evaluates the 4-dimensional velocity vector (V_code, V_verif, V_evid, V_defect),
Progress Efficiency Ratio 2.0 (PER 2.0), and normalized progress score.
Filters cosmetic whitespace, formatting, comments, and docstrings via AST symbol normalization.
"""

from __future__ import annotations

import ast
import hashlib
import math
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import (
    ASTSymbolSignature,
    ProgressHealth,
    ProgressVelocityMetrics,
)


class SemanticProgressTracker:
    """
    Computes 4-Dimensional Progress Velocity Vector and PER 2.0 score.
    Filters cosmetic whitespace/comment churn via normalized AST comparisons.
    """

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self._last_symbols: Dict[str, Set[ASTSymbolSignature]] = {}
        self._last_passed_tests: Set[str] = set()
        self._last_failed_tests: Dict[str, str] = {}
        self._last_satisfied_acs: Set[str] = set()
        self._last_open_defects: Set[str] = set()
        self._is_initialized: bool = False

    def _strip_docstring(self, body: List[ast.stmt]) -> List[ast.stmt]:
        """Strip docstring expression statement from the beginning of a block."""
        if not body:
            return body
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            return body[1:]
        return body

    def _extract_file_ast_symbols(self, file_path: Path) -> Set[ASTSymbolSignature]:
        """
        Extract normalized AST symbols (classes, functions, async functions, imports).
        Ignores comments, whitespace, and docstrings.
        """
        symbols: Set[ASTSymbolSignature] = set()
        if not file_path.is_file() or file_path.suffix != ".py":
            return symbols

        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(code, filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    cleaned_body = self._strip_docstring(node.body)
                    body_dumps = [
                        ast.dump(stmt, annotate_fields=False, include_attributes=False)
                        for stmt in cleaned_body
                    ]
                    body_hash = hashlib.sha256("".join(body_dumps).encode("utf-8")).hexdigest()[:16]
                    symbols.add(
                        ASTSymbolSignature(
                            symbol_type=type(node).__name__,
                            name=node.name,
                            body_ast_hash=body_hash,
                        )
                    )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        symbols.add(
                            ASTSymbolSignature(
                                symbol_type="Import",
                                name=f"{alias.name}:{alias.asname or ''}",
                                body_ast_hash="",
                            )
                        )
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        symbols.add(
                            ASTSymbolSignature(
                                symbol_type="ImportFrom",
                                name=f"{node.module or ''}:{alias.name}:{alias.asname or ''}",
                                body_ast_hash="",
                            )
                        )
        except SyntaxError:
            pass
        return symbols

    def _get_workspace_symbols(self) -> Dict[str, Set[ASTSymbolSignature]]:
        """Collect AST symbol signatures across workspace Python files."""
        ws_symbols: Dict[str, Set[ASTSymbolSignature]] = {}
        ignored_dirs = {
            ".git",
            ".venv",
            "venv",
            "build",
            "dist",
            "site-packages",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
        }
        for py_file in self.workspace_path.rglob("*.py"):
            if any(part in ignored_dirs for part in py_file.parts):
                continue
            rel = str(py_file.relative_to(self.workspace_path)).replace("\\", "/")
            ws_symbols[rel] = self._extract_file_ast_symbols(py_file)
        return ws_symbols

    def initialize_baseline(
        self,
        passed_test_nodes: Optional[Set[str]] = None,
        failed_test_nodes: Optional[Dict[str, str]] = None,
        satisfied_ac_ids: Optional[Set[str]] = None,
        open_defect_ids: Optional[Set[str]] = None,
    ) -> None:
        """Capture baseline workspace symbols and test state prior to turn 1."""
        self._last_symbols = self._get_workspace_symbols()
        self._last_passed_tests = set(passed_test_nodes or set())
        self._last_failed_tests = dict(failed_test_nodes or {})
        self._last_satisfied_acs = set(satisfied_ac_ids or set())
        self._last_open_defects = set(open_defect_ids or set())
        self._is_initialized = True

    def record_turn_snapshot(
        self,
        turn_index: int,
        passed_test_nodes: Set[str],
        failed_test_nodes: Dict[str, str],
        satisfied_ac_ids: Set[str],
        open_defect_ids: Set[str],
        tokens_consumed: int,
    ) -> ProgressVelocityMetrics:
        """
        Record the completion of turn `turn_index`, comparing against the preceding state.
        Computes the 4-dimensional velocity vector and returns ProgressVelocityMetrics.
        """
        curr_symbols = self._get_workspace_symbols()

        # If tracker was not explicitly initialized beforehand, initialize on first turn
        if not self._is_initialized and turn_index <= 1:
            if not self._last_symbols:
                self._last_symbols = curr_symbols
                self._last_passed_tests = set(passed_test_nodes)
                self._last_failed_tests = dict(failed_test_nodes)
                self._last_satisfied_acs = set(satisfied_ac_ids)
                self._last_open_defects = set(open_defect_ids)
                self._is_initialized = True

        # 1. AST Structural Velocity (V_code)
        structural_delta = 0
        all_files = set(curr_symbols.keys()) | set(self._last_symbols.keys())
        for f in all_files:
            c_set = curr_symbols.get(f, set())
            l_set = self._last_symbols.get(f, set())
            structural_delta += len(c_set ^ l_set)
        v_code = min(1.0, structural_delta / 10.0)

        # 2. Verification Delta Velocity (V_verif)
        delta_pass = len(passed_test_nodes - self._last_passed_tests) - len(
            self._last_passed_tests - passed_test_nodes
        )
        delta_fail = len(set(self._last_failed_tests.keys()) - set(failed_test_nodes.keys())) - len(
            set(failed_test_nodes.keys()) - set(self._last_failed_tests.keys())
        )
        v_verif = float(delta_pass) + 0.5 * float(delta_fail)

        # 3. Evidence Delta Velocity (V_evid)
        delta_ac_sat = len(satisfied_ac_ids - self._last_satisfied_acs)
        delta_ac_lost = len(self._last_satisfied_acs - satisfied_ac_ids)
        v_evid = 2.0 * float(delta_ac_sat) - 5.0 * float(delta_ac_lost)

        # 4. Defect Resolution Velocity (V_defect)
        delta_def_resolved = len(self._last_open_defects - open_defect_ids)
        delta_def_introduced = len(open_defect_ids - self._last_open_defects)
        v_defect = float(delta_def_resolved) - 1.5 * float(delta_def_introduced)

        # Unified PER 2.0 calculation
        alpha, beta, gamma, delta = 1.0, 3.0, 4.0, 2.5
        numerator = alpha * v_code + beta * v_verif + gamma * v_evid + delta * v_defect
        denominator = (tokens_consumed / 1000.0) + 0.1
        per_score = numerator / denominator

        # Normalized Sigmoidal Score in [0.0, 1.0]
        raw_signal = numerator
        normalized_score = 1.0 / (1.0 + math.exp(-max(-10.0, min(10.0, raw_signal))))

        # Determine Health Classification
        if v_verif < 0 or v_defect < 0 or normalized_score < 0.20:
            health = ProgressHealth.REGRESSING
        elif v_verif > 0 or v_evid > 0 or v_defect > 0 or normalized_score >= 0.80:
            health = ProgressHealth.THRIVING
        elif v_code > 0 and v_verif >= 0 and v_defect >= 0:
            health = ProgressHealth.MAKING_PROGRESS
        elif v_code > 0:
            health = ProgressHealth.MARGINAL_CHURN
        else:
            health = ProgressHealth.STAGNANT

        # Update cache for next turn comparison
        self._last_symbols = curr_symbols
        self._last_passed_tests = set(passed_test_nodes)
        self._last_failed_tests = dict(failed_test_nodes)
        self._last_satisfied_acs = set(satisfied_ac_ids)
        self._last_open_defects = set(open_defect_ids)

        return ProgressVelocityMetrics(
            v_code=v_code,
            v_verif=v_verif,
            v_evid=v_evid,
            v_defect=v_defect,
            tokens_consumed=tokens_consumed,
            per_score=per_score,
            normalized_score=normalized_score,
            health=health,
        )
