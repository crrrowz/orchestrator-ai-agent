# Engine Plan 12: Event Engine

## 1. Objective
Design an asynchronous, typed, high-throughput Event Engine providing a decoupled Publish/Subscribe (Pub/Sub) messaging bus across all ORAGAI engines, components, and UI listeners.

## 2. Current Architecture Involved
- `orchestrator/telemetry/` (`recorder.py`, `schemas.py`)
- Direct synchronous function calls across pipeline and sentinel classes.

## 3. Problem
Engines and pipelines are directly coupled via hardcoded references and synchronous callbacks, preventing real-time streaming to UI, telemetry isolation, and asynchronous inter-engine communication.

## 4. Proposed Design
Implement `EventEngine`:
- **Strongly-Typed Event Hierarchy**: Standardized Pydantic event payloads with unique event IDs, timestamps, origin engine, and payload schemas.
- **Async Pub/Sub Bus**: High-performance in-memory event distributor using `asyncio.Queue` and typed topic matching (`agent.*`, `tool.*`, `governance.*`, `graph.*`).
- **Event Persistence & Replay**: Optional event ledger (SQLite/JSONL) for post-mortem debugging, session replay, and audit compliance.
- **WebSocket Streaming Bridge**: Real-time event streaming to the Visual Studio / UI client.

```text
               ┌─────────────────────────────┐
               │         Event Bus           │
               └──────────────┬──────────────┘
                              │
     ┌────────────────┬───────┴────────┬────────────────┐
     ▼                ▼                ▼                ▼
[Graph Events]  [Agent Events]  [Governance Ev.]  [UI Streaming]
```

## 5. Files/Components Affected
- `orchestrator/engines/events/engine.py`
- `orchestrator/engines/events/models.py`
- `orchestrator/engines/events/bus.py`
- `orchestrator/engines/events/ledger.py`
- `orchestrator/engines/events/topics.py`

## 6. Interfaces/Contracts
```python
from typing import Any, Callable, Coroutine, Dict, List, Optional
from pydantic import BaseModel, Field
from orchestrator.engines.core.engine import IEngine

class Event(BaseModel):
    id: str
    topic: str
    source_engine: str
    timestamp: float
    payload: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None

EventHandler = Callable[[Event], Coroutine[Any, Any, None]]

class IEventEngine(IEngine):
    async def publish(self, topic: str, payload: Dict[str, Any], source: str = "core") -> Event: ...
    def subscribe(self, topic_pattern: str, handler: EventHandler) -> str: ...
    def unsubscribe(self, subscription_id: str) -> None: ...
    async def get_history(self, session_id: str, topic_prefix: Optional[str] = None) -> List[Event]: ...
```

## 7. Data Flow
Any component calls `publish(topic, payload)` -> Event Bus wraps payload in `Event` -> Dispatches non-blocking tasks to all matching topic subscribers -> Writes to Event Ledger -> Broadcasts to WebSocket connections.

## 8. State Transitions
`EVENT_CREATED -> QUEUED -> DISPATCHED_TO_SUBSCRIBERS -> PERSISTED -> COMPLETED`.

## 9. Error Handling
Exceptions raised inside subscriber handlers are caught and isolated; a subscriber crash never disrupts the event publisher or other subscribers.

## 10. Migration Strategy
`TelemetryRecorder` in `orchestrator/telemetry/recorder.py` becomes an event subscriber listening to `*` wildcard topics.

## 11. Tests
- Topic pattern matching tests (exact, wildcard `agent.*`, global `*`).
- Concurrent event burst throughput tests (>10,000 events/sec).
- Subscriber fault isolation tests.

## 12. Acceptance Criteria
- Fully decoupled inter-engine communication.
- Zero publisher blocking on slow subscribers.
- Complete event replay and ledger persistence.

## 13. Dependencies
Depends on Core Engine. Primitive for all other engines.

## 14. Risks
Memory accumulation in queues during high event volumes; mitigated by bounded queue sizes and background ledger draining.

## 15. Rollback Strategy
Non-breaking; can run synchronously in fallback mode.
