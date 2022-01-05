"""Websocket api for zhawss."""

from typing import Union, cast

import voluptuous

from zhawss.const import WEBSOCKET_API
from zhawss.websocket.api.types import WebSocketCommandHandler
from zhawss.websocket.types import ServerType


def register_api_command(
    server: ServerType,
    command_or_handler: Union[str, WebSocketCommandHandler],
    handler: Union[WebSocketCommandHandler, None] = None,
    schema: Union[voluptuous.Schema, None] = None,
) -> None:
    """Register a websocket command."""
    # pylint: disable=protected-access
    if handler is None:
        handler = cast(WebSocketCommandHandler, command_or_handler)
        command = handler._ws_command  # type: ignore[attr-defined]
        schema = handler._ws_schema  # type: ignore[attr-defined]
    else:
        command = command_or_handler
    if (handlers := server.data.get(WEBSOCKET_API)) is None:
        handlers = server.data[WEBSOCKET_API] = {}
    handlers[command] = (handler, schema)
