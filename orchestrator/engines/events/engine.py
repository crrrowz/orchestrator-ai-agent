"""Asynchronous high-performance Pub/Sub Event Bus and Engine."""

import asyncio
import fnmatch
from typing import Any, Callable, Coroutine, Dict, List, Optional
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.events.models import Event

EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventEngine(IEngine):
    """Event-driven messaging and telemetry engine."""

    engine_name: str = "events"

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._history: List[Event] = []
        self._max_history: int = 5000
        self._is_running: bool = False

    async def initialize(self, container: IContainer) -> None:
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    def subscribe(self, topic_pattern: str, handler: EventHandler) -> None:
        """Subscribe an async handler to a topic or wildcard pattern (e.g. 'agent.*')."""
        if topic_pattern not in self._subscribers:
            self._subscribers[topic_pattern] = []
        self._subscribers[topic_pattern].append(handler)

    def unsubscribe(self, topic_pattern: str, handler: EventHandler) -> None:
        if topic_pattern in self._subscribers and handler in self._subscribers[topic_pattern]:
            self._subscribers[topic_pattern].remove(handler)

    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        source: str = "core",
        session_id: Optional[str] = None,
    ) -> Event:
        """Publish an event across all matching subscribers."""
        event = Event(
            topic=topic,
            payload=payload,
            source_engine=source,
            session_id=session_id,
        )
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        tasks = []
        for pattern, handlers in self._subscribers.items():
            if fnmatch.fnmatch(topic, pattern):
                for handler in handlers:
                    tasks.append(self._safe_dispatch(handler, event))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return event

    async def _safe_dispatch(self, handler: EventHandler, event: Event) -> None:
        try:
            await handler(event)
        except Exception:
            # Isolated subscriber error handling
            pass

    def get_history(self, topic_pattern: Optional[str] = None, session_id: Optional[str] = None) -> List[Event]:
        events = self._history
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        if topic_pattern:
            events = [e for e in events if fnmatch.fnmatch(e.topic, topic_pattern)]
        return list(events)

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "subscribers_count": sum(len(h) for h in self._subscribers.values()),
            "total_events_recorded": len(self._history),
        }
