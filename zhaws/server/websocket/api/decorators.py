"""Decorators for the Websocket API."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import wraps
import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol

from zhaws.server.const import COMMAND, MINIMAL_MESSAGE_SCHEMA

if TYPE_CHECKING:
    from zhaws.server.websocket.api.types import (
        AsyncWebSocketCommandHandler,
        WebSocketCommandHandler,
    )
    from zhaws.server.websocket.client import Client
    from zhaws.server.websocket.server import Server

POSITIVE_INT = vol.All(vol.Coerce(int), vol.Range(min=0))
_LOGGER = logging.getLogger(__name__)


async def _handle_async_response(
    func: AsyncWebSocketCommandHandler,
    server: Server,
    client: Client,
    msg: dict[str, Any],
) -> None:
    """Create a response and handle exception."""
    try:
        await func(server, client, msg)
    except Exception as err:  # pylint: disable=broad-except
        # TODO fix this to send a real error code and message
        _LOGGER.exception("Error handling message: %s", err, exc_info=err)
        client.send_result_error(msg, "API_COMMAND_HANDLER_ERROR", str(err))


def async_response(
    func: AsyncWebSocketCommandHandler,
) -> WebSocketCommandHandler:
    """Decorate an async function to handle WebSocket API messages."""

    @wraps(func)
    def schedule_handler(server: Server, client: Client, msg: dict[str, Any]) -> None:
        """Schedule the handler."""
        # As the webserver is now started before the start
        # event we do not want to block for websocket responders
        asyncio.create_task(_handle_async_response(func, server, client, msg))

    return schedule_handler


def websocket_command(
    schema: dict[vol.Marker, Any],
) -> Callable[[WebSocketCommandHandler], WebSocketCommandHandler]:
    """Tag a function as a websocket command."""
    command = schema[COMMAND]

    def decorate(func: WebSocketCommandHandler) -> WebSocketCommandHandler:
        """Decorate ws command function."""
        # pylint: disable=protected-access
        func._ws_schema = MINIMAL_MESSAGE_SCHEMA.extend(schema)  # type: ignore[attr-defined]
        func._ws_command = command  # type: ignore[attr-defined]
        return func

    return decorate
