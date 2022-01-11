"""Provide Event base classes for ZHAWSSClient."""
import logging
from typing import Callable, Dict, List

_LOGGER = logging.getLogger(__package__)


class EventBase:
    """Represent a zhawssclient base class for event handling models."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize event base."""
        super().__init__(*args, **kwargs)
        self._listeners: Dict[str, List[Callable]] = {}

    def on(  # pylint: disable=invalid-name
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

        unsub = self.on(event_name, event_listener)

        return unsub

    def emit(self, event_name: str, data: dict) -> None:
        """Run all callbacks for an event."""
        for listener in self._listeners.get(event_name, []):
            listener(data)

    def _handle_event_protocol(self, event) -> None:
        """Process an event based on event protocol."""
        handler = getattr(self, f"handle_{event.event.replace(' ', '_')}", None)
        if handler is None:
            _LOGGER.debug("Received unknown event: %s", event)
            return
        handler(event)
