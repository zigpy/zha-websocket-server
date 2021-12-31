"""Typing helpers for zhawss."""
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict

ControllerType = "Controller"
WebSocketCommandHandler = Callable[[Any, Any, Dict[str, Any]], None]
AsyncWebSocketCommandHandler = Callable[[Any, Any, Dict[str, Any]], Awaitable[None]]


if TYPE_CHECKING:
    from zhawss.application.controller import Controller

    ControllerType = Controller
