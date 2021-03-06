"""Type information for the websocket api module."""
from __future__ import annotations

from typing import Any, Callable, Coroutine, TypeVar

from zhaws.server.websocket.api.model import WebSocketCommand

T_WebSocketCommand = TypeVar("T_WebSocketCommand", bound=WebSocketCommand)

AsyncWebSocketCommandHandler = Callable[
    [Any, Any, T_WebSocketCommand], Coroutine[Any, Any, None]
]
WebSocketCommandHandler = Callable[[Any, Any, T_WebSocketCommand], None]
