"""Topological Cluster Partition Engine for Bounded Deep Inspection (P7)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

from orchestrator.analysis.audit.models import ClusterPartition


class ClusterPartitionEngine:
    """Partitions workspace files into cohesive, bounded topological clusters."""

    EXCLUDE_DIRS = {
        ".venv", "venv", ".git", "__pycache__", "build", "dist",
        ".pytest_cache", ".ruff_cache", "site-packages", "node_modules"
    }

    def __init__(
        self,
        workspace_path: Path,
        max_files_per_cluster: int = 15,
        max_loc_per_cluster: int = 3000,
    ):
        self.workspace_path = workspace_path.resolve()
        self.max_files = max_files_per_cluster
        self.max_loc = max_loc_per_cluster

    def partition_workspace(self) -> List[ClusterPartition]:
        """Group all workspace Python files into balanced, bounded functional clusters."""
        dir_buckets: Dict[str, List[str]] = {}

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

                parts = rel_path.split("/")
                top_bucket = "/".join(parts[:2]) if len(parts) >= 2 else parts[0]
                dir_buckets.setdefault(top_bucket, []).append(rel_path)

        clusters: List[ClusterPartition] = []
        cluster_idx = 1

        # Process each directory bucket deterministically
        for bucket_name in sorted(dir_buckets.keys()):
            file_list = sorted(dir_buckets[bucket_name])
            current_files: List[str] = []
            current_loc = 0
            part_num = 1

            for f in file_list:
                full = self.workspace_path / f
                try:
                    loc = len(full.read_text(encoding="utf-8", errors="replace").splitlines())
                except Exception:
                    loc = 0

                # Check if adding this file exceeds max_files or max_loc
                if current_files and (
                    len(current_files) + 1 > self.max_files or current_loc + loc > self.max_loc
                ):
                    clusters.append(
                        ClusterPartition(
                            cluster_id=f"CLUSTER-{cluster_idx:02d}",
                            cluster_name=f"{bucket_name} (Part {part_num})",
                            files=list(current_files),
                            total_loc=current_loc,
                            dominant_layer=bucket_name,
                        )
                    )
                    cluster_idx += 1
                    part_num += 1
                    current_files = []
                    current_loc = 0

                current_files.append(f)
                current_loc += loc

            if current_files:
                name = f"{bucket_name} (Part {part_num})" if part_num > 1 else bucket_name
                clusters.append(
                    ClusterPartition(
                        cluster_id=f"CLUSTER-{cluster_idx:02d}",
                        cluster_name=name,
                        files=list(current_files),
                        total_loc=current_loc,
                        dominant_layer=bucket_name,
                    )
                )
                cluster_idx += 1

        return clusters
