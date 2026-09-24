"""Cross-run agent conversation memory and persistent intelligence."""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from orchestrator.config import DEFAULT_DIAGNOSTICS_DIR


class MemoryEntry(BaseModel):
    """Schema for persisted task execution memory."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    task: str
    summary: str
    files_touched: list[str] = Field(default_factory=list)
    tests_passed: bool = True
    lessons: Optional[str] = None


COMMON_TASK_STOPWORDS: set[str] = {
    "create",
    "implement",
    "build",
    "write",
    "add",
    "make",
    "with",
    "test",
    "tests",
    "file",
    "files",
    "using",
    "from",
    "service",
    "code",
    "the",
    "and",
    "for",
    "that",
    "this",
    "into",
    "onto",
    "then",
    "should",
    "must",
    "have",
    "will",
    "does",
    "done",
    "what",
    "when",
    "where",
    "which",
    "your",
    "task",
    "class",
    "function",
    "module",
}


class ConversationStore:
    """Manages persistent cross-run task memory stored in diagnostics/memory/ with indexing and retention."""

    def __init__(
        self,
        memory_dir: Optional[Path] = None,
        workspace_path: Optional[Path] = None,
        max_retained_memories: int = 30,
    ):
        if memory_dir:
            target = memory_dir
        elif workspace_path:
            target = workspace_path / "diagnostics" / "memory"
        else:
            target = DEFAULT_DIAGNOSTICS_DIR / "memory"

        if target.name != "memory":
            target = target / "memory"
        self.memory_dir = target.resolve()
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.max_retained_memories = max_retained_memories
        self.index_file = self.memory_dir / "index.json"

    def save_run_memory(
        self,
        task: str,
        summary: str,
        files_touched: Optional[list[str]] = None,
        tests_passed: bool = True,
        lessons: Optional[str] = None,
    ) -> Path:
        """Persist a task execution memory entry to disk with atomic write and index update."""
        entry = MemoryEntry(
            task=task,
            summary=summary,
            files_touched=files_touched or [],
            tests_passed=tests_passed,
            lessons=lessons,
        )
        file_path = (
            self.memory_dir
            / f"{entry.id}_{int(datetime.now(timezone.utc).timestamp())}.json"
        )
        tmp_path = file_path.with_suffix(".tmp")
        tmp_path.write_text(entry.model_dump_json(indent=2), encoding="utf-8")
        tmp_path.replace(file_path)

        # Enforce FIFO retention policy
        self._prune_old_memories()

        # Re-build central memory index
        self._rebuild_index()

        return file_path

    def load_all_memories(self) -> list[MemoryEntry]:
        """Load all valid memory entries from disk sorted newest first."""
        entries: list[MemoryEntry] = []
        for p in self.memory_dir.glob("*.json"):
            if p.name == "index.json":
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                entries.append(MemoryEntry(**data))
            except Exception:
                continue
        # Sort newest first
        entries.sort(key=lambda m: m.timestamp, reverse=True)
        return entries

    def find_relevant_memories(
        self,
        task: str,
        files: Optional[list[str]] = None,
        max_results: int = 3,
        min_score: float = 3.0,
    ) -> list[MemoryEntry]:
        """Retrieve memories relevant to the given task or touched files using filtered keywords."""
        all_memories = self.load_all_memories()
        if not all_memories:
            return []

        task_words = {
            w
            for w in re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", task.lower())
            if w not in COMMON_TASK_STOPWORDS
        }
        target_files = set(f.lower() for f in (files or []))

        scored: list[tuple[float, MemoryEntry]] = []
        for mem in all_memories:
            score = 0.0
            mem_words = {
                w
                for w in re.findall(
                    r"\b[a-zA-Z0-9_-]{3,}\b", (mem.task + " " + mem.summary).lower()
                )
                if w not in COMMON_TASK_STOPWORDS
            }
            overlap_count = 0
            for tw in task_words:
                for mw in mem_words:
                    if tw == mw:
                        overlap_count += 1
                        break
                    elif len(tw) >= 4 and len(mw) >= 4 and tw[:4] == mw[:4]:
                        overlap_count += 1
                        break
            score += overlap_count * 2.0

            mem_files = set(f.lower() for f in mem.files_touched)
            file_overlap = target_files.intersection(mem_files)
            score += len(file_overlap) * 5.0

            if score >= min_score:
                scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:max_results]]

    def search_memories(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Perform a direct substring/token query across task, summary, and lessons."""
        query_terms = [t.lower() for t in query.split() if t.strip()]
        if not query_terms:
            return self.load_all_memories()[:limit]

        matches: list[MemoryEntry] = []
        for mem in self.load_all_memories():
            searchable = f"{mem.task} {mem.summary} {mem.lessons or ''} {' '.join(mem.files_touched)}".lower()
            if any(term in searchable for term in query_terms):
                matches.append(mem)
                if len(matches) >= limit:
                    break
        return matches

    def format_memory_context(
        self,
        task: str,
        files: Optional[list[str]] = None,
        max_chars: int = 1500,
        min_score: float = 3.0,
    ) -> Optional[str]:
        """Format matching memories into a prompt injection block if relevance threshold met."""
        relevant = self.find_relevant_memories(
            task, files, max_results=2, min_score=min_score
        )
        if not relevant:
            return None

        lines = ["[HISTORICAL EXECUTION MEMORY]:", "Learnings from related past tasks:"]
        for mem in relevant:
            status = "PASSED" if mem.tests_passed else "FAILED"
            lines.append(f"- Task: {mem.task} (Status: {status})")
            lines.append(f"  Summary: {mem.summary}")
            if mem.lessons:
                lines.append(f"  Key Insight: {mem.lessons}")
            if mem.files_touched:
                lines.append(f"  Relevant Files: {', '.join(mem.files_touched[:5])}")

        res = "\n".join(lines).strip()
        return res[:max_chars]

    def _prune_old_memories(self) -> int:
        """Prune oldest memory JSON files when total exceeds max_retained_memories."""
        if self.max_retained_memories <= 0:
            return 0
        try:
            files = [
                p for p in self.memory_dir.glob("*.json") if p.name != "index.json"
            ]
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            pruned = 0
            if len(files) > self.max_retained_memories:
                for old in files[self.max_retained_memories :]:
                    try:
                        old.unlink()
                        pruned += 1
                    except OSError:
                        pass
            return pruned
        except Exception:
            return 0

    def _rebuild_index(self) -> None:
        """Rebuild index.json with a structured overview of all stored memories."""
        try:
            memories = self.load_all_memories()
            index_data = {
                "total_memories": len(memories),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "memories": [
                    {
                        "id": m.id,
                        "timestamp": m.timestamp,
                        "task": m.task,
                        "summary": m.summary[:150]
                        + ("..." if len(m.summary) > 150 else ""),
                        "tests_passed": m.tests_passed,
                        "files_touched": m.files_touched,
                        "has_lessons": bool(m.lessons),
                    }
                    for m in memories
                ],
            }
            tmp_idx = self.index_file.with_suffix(".tmp")
            tmp_idx.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
            tmp_idx.replace(self.index_file)
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate stats on stored memories."""
        memories = self.load_all_memories()
        passed = sum(1 for m in memories if m.tests_passed)
        failed = len(memories) - passed
        unique_files = set()
        for m in memories:
            unique_files.update(m.files_touched)
        return {
            "total_memories": len(memories),
            "passed_tasks": passed,
            "failed_tasks": failed,
            "unique_files_touched": len(unique_files),
        }


# Backward compatibility and contextual aliases
ConversationMemoryStore = ConversationStore
SessionMemoryStore = ConversationStore
