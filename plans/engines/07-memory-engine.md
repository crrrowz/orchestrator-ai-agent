# Engine Plan 07: Memory Engine

## 1. Objective
Design a multi-tiered, modular Memory Engine providing structured conversation storage, project context caching, task artifacts, cross-agent handoff compaction, and long-term semantic knowledge retrieval.

## 2. Current Architecture Involved
- `orchestrator/memory/conversation_store.py`
- `orchestrator/context/manager.py`
- `orchestrator/context/handoff/` (`manager.py`, `compactor.py`, `freshness.py`, `synthesizer.py`)

## 3. Problem
Memory is currently limited to ephemeral conversation logs and rudimentary JSON files. There is no unified semantic retrieval, persistent cross-session knowledge base, or tiered scoping (Conversation vs. Task vs. Project vs. Long-Term).

## 4. Proposed Design
Implement `MemoryEngine` with 5 distinct memory scopes:
1. **Conversation Memory**: High-fidelity short-term message buffer with sliding-window FIFO and summarization.
2. **Task Memory**: Scoped working memory containing active subtasks, intermediate tool outputs, and local variables.
3. **Project Memory**: Codebase structure, AST graphs (Graft integration), dependency manifests, and architectural invariants.
4. **Agent Memory**: Private scratchpad for reasoning, planning, and self-reflection per agent session.
5. **Long-Term Memory**: Vector/SQLite-backed knowledge store for storing historical solutions, error patterns, and audit learnings.

## 5. Files/Components Affected
- `orchestrator/engines/memory/engine.py`
- `orchestrator/engines/memory/scopes/` (`conversation.py`, `task.py`, `project.py`, `agent.py`, `long_term.py`)
- `orchestrator/engines/memory/stores/` (`sqlite_store.py`, `chroma_store.py`, `file_store.py`)
- `orchestrator/engines/memory/handoff.py`
- `orchestrator/engines/memory/compactor.py`

## 6. Interfaces/Contracts
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from orchestrator.engines.core.engine import IEngine

class MemoryItem(BaseModel):
    id: str
    scope: str
    key: str
    value: Any
    metadata: Dict[str, Any] = {}
    timestamp: float

class IMemoryEngine(IEngine):
    async def store(self, scope: str, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> str: ...
    async def retrieve(self, scope: str, query: str, limit: int = 5) -> List[MemoryItem]: ...
    async def get_by_key(self, scope: str, key: str) -> Optional[MemoryItem]: ...
    async def compact_context(self, scope: str, max_tokens: int) -> str: ...
    async def create_handoff(self, from_agent: str, to_agent: str, state: Dict[str, Any]) -> str: ...
```

## 7. Data Flow
Agent/Engine stores memory item -> Memory Engine routes to target scope and storage backend -> Vector embedding generated if long-term queryable -> Context retrieval queries perform hybrid BM25/Vector search -> Compactor synthesizes concise context for prompt injection.

## 8. State Transitions
`ITEM_RECEIVED -> STORED -> INDEXED -> RETRIEVED -> COMPACTED -> EXPIRED_PURGED`.

## 9. Error Handling
Storage backend disconnections trigger in-memory FIFO fallback to prevent interrupting active agent execution.

## 10. Migration Strategy
Port existing `ConversationStore` and `HandoffManager` into `ConversationMemory` and `HandoffHandler` under `engines/memory/`.

## 11. Tests
- Cross-agent handoff serialization and synthesis tests.
- Context window token compaction tests.
- SQLite vector and lexical retrieval precision tests.

## 12. Acceptance Criteria
- Clean separation of the 5 memory tiers.
- High-performance context retrieval (<10ms for local SQLite/BM25).
- Seamless handoff synthesis between disparate agent instances.

## 13. Dependencies
Depends on Core Engine, Event Engine, Model Engine. Blocks Agent Engine and Execution Engine.

## 14. Risks
Context degradation due to lossy compaction; mitigated by preserving structured execution artifacts alongside narrative summaries.

## 15. Rollback Strategy
Fallback to `orchestrator/memory/conversation_store.py`.
