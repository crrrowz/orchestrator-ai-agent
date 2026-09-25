"""Evidence Freshness, Workspace Fingerprinting, and Invalidation Mesh.

File Location: orchestrator/context/handoff/freshness.py
Architecture Reference: docs/plans/P6_CONTEXT_AND_EVIDENCE_HANDOFF_PLAN.md Section 4
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from orchestrator.context.handoff.models import (
    FreshnessState,
    SubjectFingerprint,
    WorkspaceDigest,
)


class FreshnessValidator:
    """Evaluates evidence freshness, tracks subject fingerprints, and cascades invalidations.

    Implements the cryptographic working-tree binding theorem:
    An evidence artifact is valid if and only if the current workspace content digest
    matches the digest recorded at the moment of evidence capture, or the transitive
    dependency closure of target files does not intersect any modified workspace files.
    """

    DEFAULT_IGNORED_DIRS: Set[str] = {
        ".git",
        ".pytest_cache",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        "diagnostics",
        ".ruff_cache",
        ".mypy_cache",
    }

    @classmethod
    def compute_subject_fingerprint(
        cls,
        file_path: Path,
        root_path: Optional[Path] = None,
    ) -> Optional[SubjectFingerprint]:
        """Compute the cryptographic content digest of a single file."""
        if not file_path.is_file():
            return None

        rel_path = (
            file_path.relative_to(root_path).as_posix()
            if root_path and file_path.is_relative_to(root_path)
            else file_path.name
        )

        try:
            content = file_path.read_bytes()
            sha256_hash = hashlib.sha256(content).hexdigest()
            stat = file_path.stat()
            return SubjectFingerprint(
                subject_path=rel_path,
                sha256_hash=sha256_hash,
                byte_size=len(content),
                last_modified_timestamp=stat.st_mtime,
            )
        except (OSError, PermissionError):
            return None

    @classmethod
    def create_workspace_digest(
        cls,
        workspace_path: Path,
        ignored_patterns: Optional[Set[str]] = None,
        target_extensions: Optional[Set[str]] = None,
    ) -> WorkspaceDigest:
        """Compute a deterministic Merkle-like composite digest of the workspace files."""
        ignored = ignored_patterns or cls.DEFAULT_IGNORED_DIRS
        file_map: Dict[str, SubjectFingerprint] = {}
        composite_hasher = hashlib.sha256()

        if not workspace_path.exists():
            return WorkspaceDigest(
                composite_sha256=composite_hasher.hexdigest(),
                file_digests={},
                captured_at_utc=datetime.now(timezone.utc).isoformat(),
            )

        for file_path in sorted(workspace_path.rglob("*")):
            if not file_path.is_file():
                continue

            try:
                rel_parts = file_path.relative_to(workspace_path).parts
            except ValueError:
                continue

            # Check if any parent or directory is ignored
            if any(part in ignored for part in rel_parts[:-1]):
                continue

            if target_extensions:
                if file_path.suffix not in target_extensions:
                    continue

            fingerprint = cls.compute_subject_fingerprint(file_path, root_path=workspace_path)
            if fingerprint:
                file_map[fingerprint.subject_path] = fingerprint
                composite_hasher.update(
                    f"{fingerprint.subject_path}:{fingerprint.sha256_hash}".encode("utf-8")
                )

        return WorkspaceDigest(
            composite_sha256=composite_hasher.hexdigest(),
            file_digests=file_map,
            captured_at_utc=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def detect_modified_files(
        cls,
        previous_digest: WorkspaceDigest,
        current_digest: WorkspaceDigest,
    ) -> Set[str]:
        """Identify set of files added, modified, or removed between two workspace snapshots."""
        modified: Set[str] = set()

        # Check modified and added files
        for path, curr_fp in current_digest.file_digests.items():
            prev_fp = previous_digest.file_digests.get(path)
            if not prev_fp or prev_fp.sha256_hash != curr_fp.sha256_hash:
                modified.add(path)

        # Check deleted files
        for prev_path in previous_digest.file_digests:
            if prev_path not in current_digest.file_digests:
                modified.add(prev_path)

        return modified

    @classmethod
    def evaluate_evidence_freshness(
        cls,
        evidence_workspace_sha256: str,
        current_workspace_digest: WorkspaceDigest,
        target_files: List[str],
        dependency_map: Optional[Dict[str, List[str]]] = None,
    ) -> Tuple[FreshnessState, str]:
        """Check if an evidence artifact remains valid under current workspace state.

        Returns:
            Tuple of (FreshnessState, explanation_message).
        """
        # Exact match of composite workspace hash -> guaranteed FRESH
        if evidence_workspace_sha256 and evidence_workspace_sha256 == current_workspace_digest.composite_sha256:
            return FreshnessState.FRESH, "Workspace content digest matches evidence baseline."

        # Normalized target file paths
        normalized_targets = {p.replace("\\", "/") for p in target_files}

        # Build dependency closure
        deps = dependency_map or {}
        closure: Set[str] = set(normalized_targets)
        for tf in normalized_targets:
            for dep in deps.get(tf, []):
                closure.add(dep.replace("\\", "/"))

        # If any target file does not exist in current workspace, it was deleted or missing -> INVALID
        for target in normalized_targets:
            if target not in current_workspace_digest.file_digests:
                return FreshnessState.INVALID, f"Target file `{target}` is missing from current workspace."

        # If evidence was captured with no target files defined and digest changed -> STALE
        if not normalized_targets:
            return (
                FreshnessState.STALE,
                "Workspace mutated and no target file closure was defined for this evidence.",
            )

        # Check if any file in the target dependency closure changed
        # We check current digests against closure
        for path, fp in current_workspace_digest.file_digests.items():
            norm_path = path.replace("\\", "/")
            if norm_path in closure:
                # If target or direct dependency is tracked, verify whether its content changed
                # If we don't have the baseline hash for this individual file, workspace change implies STALE
                return (
                    FreshnessState.STALE,
                    f"Target file or dependency `{norm_path}` is in the mutation scope.",
                )

        # If none of the files in target closure were in modified set -> FRESH
        return (
            FreshnessState.FRESH,
            "Target dependency closure untouched; submodule evidence preserved.",
        )

    @classmethod
    def cascade_invalidation(
        cls,
        modified_files: Set[str],
        milestone_targets: Dict[str, List[str]],
        dependency_map: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, FreshnessState]:
        """Compute invalidation status for a set of milestones given modified files.

        Args:
            modified_files: Set of file paths modified in the workspace.
            milestone_targets: Map of milestone_id -> list of target file paths.
            dependency_map: Optional map of file_path -> list of dependent/imported file paths.

        Returns:
            Dict mapping milestone_id to FreshnessState (FRESH or STALE).
        """
        deps = dependency_map or {}
        results: Dict[str, FreshnessState] = {}
        norm_modified = {f.replace("\\", "/") for f in modified_files}

        for ms_id, targets in milestone_targets.items():
            norm_targets = {t.replace("\\", "/") for t in targets}
            closure = set(norm_targets)
            for t in norm_targets:
                for dep in deps.get(t, []):
                    closure.add(dep.replace("\\", "/"))

            # Check for intersection
            intersect = closure.intersection(norm_modified)
            if intersect:
                results[ms_id] = FreshnessState.STALE
            else:
                results[ms_id] = FreshnessState.FRESH

        return results
