"""Websocket api for zhawss."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from zhaws.server.const import WEBSOCKET_API
from zhaws.server.websocket.api.model import WebSocketCommand
from zhaws.server.websocket.api.types import WebSocketCommandHandler

if TYPE_CHECKING:
    from zhaws.server.websocket.server import Server


def register_api_command(
    server: Server,
    command_or_handler: str | WebSocketCommandHandler,
    handler: WebSocketCommandHandler | None = None,
    model: type[WebSocketCommand] | None = None,
) -> None:
    """Register a websocket command."""
    # pylint: disable=protected-access
    if handler is None:
        handler = cast(WebSocketCommandHandler, command_or_handler)
        command = handler._ws_command  # type: ignore[attr-defined]
        model = handler._ws_command_model  # type: ignore[attr-defined]
    else:
        command = command_or_handler
    if (handlers := server.data.get(WEBSOCKET_API)) is None:
        handlers = server.data[WEBSOCKET_API] = {}
    handlers[command] = (handler, model)
