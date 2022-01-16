"""Type information for the websocket api module."""
from __future__ import annotations

from typing import Any, Callable, Coroutine

AsyncWebSocketCommandHandler = Callable[
    [Any, Any, dict[str, Any]], Coroutine[Any, Any, None]
]
WebSocketCommandHandler = Callable[[Any, Any, dict[str, Any]], None]
