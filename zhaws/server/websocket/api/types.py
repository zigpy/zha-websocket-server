"""Type information for the websocket api module."""

from typing import Any, Awaitable, Callable, Dict

from zhaws.server.websocket.types import ClientType, ServerType

AsyncWebSocketCommandHandler = Callable[
    [ServerType, ClientType, Dict[str, Any]], Awaitable[None]
]
WebSocketCommandHandler = Callable[[ServerType, ClientType, Dict[str, Any]], None]
