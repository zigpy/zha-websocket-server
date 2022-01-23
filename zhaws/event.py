"""Provide Event base classes for zhaws."""
from __future__ import annotations

import asyncio
import inspect
import logging
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from zhaws.model import BaseEvent

_LOGGER = logging.getLogger(__package__)


class EventBase:
    """Base class for event handling and emitting objects."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize event base."""
        super().__init__(*args, **kwargs)
        self._listeners: dict[str, list[Callable]] = {}

    def on_event(  # pylint: disable=invalid-name
        self, event_name: str, callback: Callable
    ) -> Callable:
        """Register an event callback."""
        listeners: list = self._listeners.setdefault(event_name, [])
        listeners.append(callback)

        def unsubscribe() -> None:
            """Unsubscribe listeners."""
            if callback in listeners:
                listeners.remove(callback)

        return unsubscribe

    def once(self, event_name: str, callback: Callable) -> Callable:
        """Listen for an event exactly once."""

        def event_listener(data: dict) -> None:
            unsub()
            callback(data)

        unsub = self.on_event(event_name, event_listener)

        return unsub

    def emit(self, event_name: str, data: BaseEvent) -> None:
        """Run all callbacks for an event."""
        for listener in self._listeners.get(event_name, []):
            if inspect.iscoroutinefunction(listener):
                asyncio.create_task(listener(data))
            else:
                listener(data)

    def _handle_event_protocol(self, event: BaseEvent) -> None:
        """Process an event based on event protocol."""
        _LOGGER.debug("handling event protocol for event: %s", event)
        handler = getattr(self, f"handle_{event.event.replace(' ', '_')}", None)
        if handler is None:
            _LOGGER.warning("Received unknown event: %s", event)
            return
        handler(event)
